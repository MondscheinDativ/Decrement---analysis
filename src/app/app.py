import os
import sys
import subprocess
import tempfile
import json
import uuid
import hashlib
import time
import pandas as pd
import numpy as np
from datetime import datetime
from flask import Flask, request, jsonify, current_app, session, send_file
from cryptography.fernet import Fernet
import redis
import saspy
from werkzeug.utils import secure_filename
import zipfile
import io

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # 允许跨域请求
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'supersecretkey')
app.config['DATA_KEY'] = Fernet.generate_key()
app.config['REDIS_URL'] = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
app.config['SAS_GRID_USER'] = os.environ.get('SAS_GRID_USER', 'griduser')
app.config['SAS_GRID_PASS'] = os.environ.get('SAS_GRID_PASS', 'gridpass')
app.config['DATASETS_DIR'] = 'datasets'
app.config['MODELS_DIR'] = 'models'

# Initialize Redis connection
cache = redis.Redis.from_url(app.config['REDIS_URL'])

# 创建必要目录
os.makedirs(app.config['DATASETS_DIR'], exist_ok=True)
os.makedirs(app.config['MODELS_DIR'], exist_ok=True)

# Custom exception classes
class ActuarialException(Exception):
    """Base exception for actuarial processing"""
    def __init__(self, message, code):
        super().__init__(message)
        self.code = code

class MortalityDataError(ActuarialException):
    """Mortality data exception"""
    def __init__(self, message="Mortality data processing error"):
        super().__init__(message, "ACT-1001")

class DataProcessingError(ActuarialException):
    """Data processing exception"""
    def __init__(self, message="Data processing error"):
        super().__init__(message, "ACT-2001")

class ReportGenerationError(ActuarialException):
    """Report generation exception"""
    def __init__(self, message="Report generation error"):
        super().__init__(message, "ACT-3001")

# Security utilities
def encrypt_data(data):
    """Encrypt sensitive data"""
    cipher = Fernet(current_app.config['DATA_KEY'])
    return cipher.encrypt(json.dumps(data).encode())

def decrypt_data(encrypted_data):
    """Decrypt data"""
    cipher = Fernet(current_app.config['DATA_KEY'])
    return json.loads(cipher.decrypt(encrypted_data).decode())

# SAS execution utilities
def run_sas_safely(script_content, input_data=None):
    """Execute SAS script in Docker container"""
    try:
        # Create temporary SAS script file
        with tempfile.NamedTemporaryFile(suffix='.sas', delete=False) as sas_file:
            sas_file.write(script_content.encode('utf-8'))
            sas_file_path = sas_file.name

        # Create temporary input data file if needed
        input_path = None
        if input_data:
            with tempfile.NamedTemporaryFile(suffix='.json.enc', delete=False) as input_file:
                encrypted_input = encrypt_data(input_data)
                input_file.write(encrypted_input)
                input_path = input_file.name

        # Build Docker command
        docker_cmd = [
            'docker', 'run', '--rm',
            '-v', f'{sas_file_path}:/script.sas',
            '-v', '/sas_lib:/sas_lib',
            '-v', '/keys:/keys',
        ]

        if input_path:
            docker_cmd.extend(['-v', f'{input_path}:/input_data.json.enc'])

        docker_cmd.extend([
            'sas-enterprise:9.4',
            'sas', '-sysin', '/script.sas'
        ])

        # Execute Docker command
        result = subprocess.run(
            docker_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=300  # 5-minute timeout
        )

        # Audit log
        audit_log(
            action="SAS_EXECUTION",
            details={
                "script": script_content[:500] + "..." if len(script_content) > 500 else script_content,
                "status": "SUCCESS" if result.returncode == 0 else "FAILED",
                "return_code": result.returncode
            }
        )

        if result.returncode != 0:
            raise DataProcessingError(f"SAS execution failed: {result.stderr.decode('utf-8')}")
            
        return result

    except subprocess.TimeoutExpired:
        audit_log("SAS_EXECUTION", {"status": "TIMEOUT"})
        raise DataProcessingError("SAS execution timeout")
    finally:
        # Cleanup temp files
        if os.path.exists(sas_file_path):
            os.unlink(sas_file_path)
        if input_path and os.path.exists(input_path):
            os.unlink(input_path)

def submit_to_sas_grid(script_content, input_data=None):
    """Submit job to SAS Grid cluster"""
    try:
        # Connect to SAS Grid
        sas = saspy.SASsession(
            omruser=current_app.config['SAS_GRID_USER'],
            omrpw=current_app.config['SAS_GRID_PASS'],
            cfgname='sasgrid'
        )

        # Prepare input data
        sas_data = None
        if input_data:
            sas_data = sas.df2sd(input_data, 'input_data')

        # Submit job
        job = sas.submit(
            code=script_content,
            data=sas_data,
            grid=True,
            gridpriority='HIGH'  # Actuarial high priority
        )

        # Wait for completion
        while job.status not in ['COMPLETED', 'FAILED']:
            time.sleep(5)
            job.update_status()

        # Audit log
        audit_log(
            action="SAS_GRID_SUBMIT",
            details={
                "script": script_content[:500] + "..." if len(script_content) > 500 else script_content,
                "job_id": job.jobid,
                "status": job.status,
                "duration": job.duration
            }
        )

        if job.status == 'COMPLETED':
            return job.results
        else:
            raise DataProcessingError(f"SAS Grid job failed: {job.error}")

    except Exception as e:
        audit_log("SAS_GRID_ERROR", {"error": str(e)})
        raise DataProcessingError(f"SAS Grid connection failed: {str(e)}")

# Audit logging
def audit_log(action, details):
    """Record audit log entry"""
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "action": action,
        "details": details,
        "user": session.get('user_id', 'SYSTEM') if hasattr(session, 'get') else 'SYSTEM',
        "ip": request.remote_addr if hasattr(request, 'remote_addr') else '127.0.0.1',
        "session_id": session.get('sid', str(uuid.uuid4())) if hasattr(session, 'get') else str(uuid.uuid4())
    }

    # Write to SIEM (simplified to file)
    log_path = "/var/log/actuarial/audit.log"
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    with open(log_path, "a") as logfile:
        logfile.write(json.dumps(log_entry) + "\n")

    # Production: Implement database saving
    # save_to_audit_db(log_entry)

# Data lineage tracking
def track_data_lineage(input_data, operation, parameters, output_data):
    """Create data lineage record"""
    lineage_id = str(uuid.uuid4())
    lineage_record = {
        "id": lineage_id,
        "timestamp": datetime.utcnow().isoformat(),
        "operation": operation,
        "parameters": parameters,
        "input_hash": hashlib.sha256(json.dumps(input_data).encode()).hexdigest(),
        "output_hash": hashlib.sha256(json.dumps(output_data).encode()).hexdigest(),
        "environment": {
            "sas_version": get_sas_version(),
            "r_version": get_r_version()
        },
        "auditor": session.get('user_id', 'SYSTEM') if hasattr(session, 'get') else 'SYSTEM'
    }

    # Save lineage record
    lineage_path = f"/var/log/actuarial/lineage/{lineage_id}.json"
    os.makedirs(os.path.dirname(lineage_path), exist_ok=True)
    with open(lineage_path, "w") as lineage_file:
        json.dump(lineage_record, lineage_file)

    audit_log("DATA_LINEAGE", lineage_record)
    return lineage_id

def get_sas_version():
    """Get SAS version info"""
    try:
        result = subprocess.run(['sas', '-version'], capture_output=True, text=True)
        return result.stdout.strip()
    except:
        return "Unknown"

def get_r_version():
    """Get R version info"""
    try:
        result = subprocess.run(['R', '--version'], capture_output=True, text=True)
        return result.stdout.split('\n')[0].strip()
    except:
        return "Unknown"

# Data pipeline API endpoints
@app.route('/api/fetch-data', methods=['POST'])
def fetch_data():
    """Fetch data from HMD or CDC"""
    data = request.get_json()
    source = data.get('source')
    try:
        if source == 'hmd':
            return fetch_hmd_data(data)
        elif source == 'cdc':
            return fetch_cdc_data(data)
        else:
            return jsonify({'error': 'Unsupported data source', 'code': 'DATA-001'}), 400
    except ActuarialException as ae:
        return jsonify({'error': str(ae), 'code': ae.code}), 500
    except Exception as e:
        audit_log("DATA_FETCH_ERROR", {"error": str(e), "source": source})
        return jsonify({'error': f'Data fetch failed: {str(e)}', 'code': 'SYS-001'}), 500

def fetch_hmd_data(data):
    """Fetch mortality data from HMD"""
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({'error': 'HMD credentials required', 'code': 'DATA-002'}), 400

    # Build R script
    r_script = f"""
    library(HMDHFDplus)
    library(jsonlite)
    usr <- "{username}"
    pwd <- "{password}"
    try {{
        countries <- getHMDcountries(usr, pwd)
        us_data <- readHMDweb(
            CNTRY = "USA",
            item = "Mx_1x1",
            username = usr,
            password = pwd
        )
        result <- list(
            data = us_data,
            tables = list(
                list(value = "mortality", label = "Mortality Table"),
                list(value = "population", label = "Population Table")
            ),
            metadata = list(
                source = "HMD",
                retrieved = Sys.time(),
                country = "USA"
            )
        )
        write(toJSON(result, auto_unbox = TRUE), "hmd_output.json")
    }} catch (e) {{
        write(toJSON(list(error = e$message)), "hmd_error.json")
    }}
    """

    # Execute R script
    with tempfile.NamedTemporaryFile(suffix='.R', delete=False) as r_file:
        r_file.write(r_script.encode('utf-8'))
        r_file_path = r_file.name

    try:
        subprocess.run(['Rscript', r_file_path], check=True, timeout=180)
        if os.path.exists('hmd_output.json'):
            with open('hmd_output.json') as f:
                result = json.load(f)
            os.unlink('hmd_output.json')
            
            # Audit log
            audit_log("HMD_DATA_FETCH", {
                "username": username,
                "records": len(result.get('data', [])),
                "tables": [t['value'] for t in result.get('tables', [])]
            })
            return jsonify(result)
        elif os.path.exists('hmd_error.json'):
            with open('hmd_error.json') as f:
                error_data = json.load(f)
            os.unlink('hmd_error.json')
            raise MortalityDataError(error_data.get('error', 'HMD fetch failed'))
        else:
            raise MortalityDataError("No output generated from HMD fetch")
    except subprocess.CalledProcessError as e:
        raise MortalityDataError(f"R script failed: {str(e)}")
    except subprocess.TimeoutExpired:
        raise MortalityDataError("HMD fetch timeout")
    finally:
        if os.path.exists(r_file_path):
            os.unlink(r_file_path)

def fetch_cdc_data(data):
    """Fetch data from CDC"""
    api_key = data.get('apiKey')
    if not api_key:
        return jsonify({'error': 'CDC API key required', 'code': 'DATA-003'}), 400

    # SAS script for CDC data
    sas_script = f"""
    /* Access CDC API */
    filename resp temp;
    proc http
        url="https://data.cdc.gov/api/endpoint"
        method="GET"
        query=("api_key"="{api_key}")
        out=resp;
    run;
    
    /* Process response */
    libname cdc json fileref=resp;
    
    /* Actuarial validation */
    proc actuarial_validate
        data=cdc.root
        out=work.validated_data
        method="CDC_STANDARD";
    run;
    
    /* Export as JSON */
    proc json
        out="cdc_output.json"
        pretty;
        export work.validated_data;
    run;
    """

    try:
        # Submit to SAS Grid
        result = submit_to_sas_grid(sas_script)
        if 'cdc_output.json' in result and os.path.exists('cdc_output.json'):
            with open('cdc_output.json') as f:
                output_data = json.load(f)
            
            # Audit log
            audit_log("CDC_DATA_FETCH", {
                "api_key": api_key[:4] + "***" + api_key[-4:],
                "records": len(output_data.get('DATA', []))
            })
            return jsonify({
                'data': output_data.get('DATA', []),
                'tables': [{'value': 'cdc_data', 'label': 'CDC Data'}],
                'metadata': {
                    'source': 'CDC',
                    'retrieved': datetime.utcnow().isoformat()
                }
            })
        else:
            raise DataProcessingError("CDC processing failed: No output file")
    except Exception as e:
        raise DataProcessingError(f"CDC processing failed: {str(e)}")

# File upload API
@app.route('/api/upload-custom-data', methods=['POST'])
def upload_custom_data():
    """Process uploaded custom data"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded', 'code': 'DATA-004'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file', 'code': 'DATA-005'}), 400

    try:
        # Get file extension
        file_ext = os.path.splitext(file.filename)[1].lower()
        allowed_ext = ['.csv', '.xls', '.xlsx', '.sas7bdat', '.dta', '.sav']
        if file_ext not in allowed_ext:
            return jsonify({'error': 'Unsupported file type', 'code': 'DATA-006'}), 400

        # Save uploaded file
        with tempfile.NamedTemporaryFile(suffix=file_ext, delete=False) as temp_file:
            file.save(temp_file.name)
            file_path = temp_file.name

        # Determine file type
        file_type = "csv" if file_ext == '.csv' else \
                   "excel" if file_ext in ['.xls', '.xlsx'] else \
                   "sas" if file_ext == '.sas7bdat' else \
                   "stata" if file_ext == '.dta' else "spss"

        # SAS processing script
        sas_script = f"""
        /* Import based on file type */
        filename infile "{file_path}";
        proc import
            datafile=infile
            out=work.imported_data
            dbms={file_type}
            replace;
            {"delimiter=','" if file_type == "csv" else ""}
            {"sheet='Sheet1'" if file_type == "excel" else ""}
            {"getnames=yes" if file_type in ["csv", "excel"] else ""};
        run;
        
        /* Actuarial data validation */
        proc actuarial_validate
            data=work.imported_data
            out=work.validated_data
            method="FULL";
        run;
        
        /* Export as JSON */
        proc json
            out="custom_output.json"
            pretty;
            export work.validated_data;
        run;
        """

        # Execute SAS safely
        run_sas_safely(sas_script)

        if os.path.exists('custom_output.json'):
            with open('custom_output.json') as f:
                output_data = json.load(f)
            
            # Audit log
            audit_log("CUSTOM_DATA_UPLOAD", {
                "filename": file.filename,
                "file_type": file_type,
                "records": len(output_data.get('DATA', []))
            })
            return jsonify({
                'data': output_data.get('DATA', []),
                'tables': [{'value': 'main', 'label': 'Main Table'}],
                'metadata': {
                    'source': 'custom',
                    'filename': file.filename,
                    'processed': datetime.utcnow().isoformat()
                }
            })
        else:
            raise DataProcessingError("Custom data processing failed")

    except ActuarialException as ae:
        return jsonify({'error': str(ae), 'code': ae.code}), 500
    except Exception as e:
        audit_log("UPLOAD_ERROR", {"error": str(e), "filename": file.filename})
        return jsonify({'error': f'File processing failed: {str(e)}', 'code': 'SYS-002'}), 500
    finally:
        if os.path.exists(file_path):
            os.unlink(file_path)

# Data cleaning API
@app.route('/api/clean-data', methods=['POST'])
def clean_data():
    """Clean and process data"""
    data = request.get_json()
    input_data = data.get('data', [])
    options = data.get('options', {})
    if not input_data:
        return jsonify({'error': 'No data to clean', 'code': 'DATA-007'}), 400

    try:
        # Check cache
        cache_key = f"clean:{hashlib.sha256(json.dumps(input_data).encode()).hexdigest()}:{hashlib.sha256(json.dumps(options).encode()).hexdigest()}"
        if cached := cache.get(cache_key):
            return jsonify({'cleanedData': json.loads(cached)})

        # Build SAS cleaning script
        sas_script = f"""
        /* Import JSON data */
        libname in json fileref=infile;
        filename infile "/input_data.json.enc";
        
        /* Data cleaning logic */
        data work.cleaned_data;
            set in.root;
            
            /* Missing value handling */
            %let missing_treatment={options.get('missingValueTreatment', 'drop')};
            %if &missing_treatment = drop %then %do;
                if nmiss(of _numeric_) > 0 then delete;
            %end;
            %else %if &missing_treatment = mean %then %do;
                array nums _numeric_;
                do over nums;
                    if missing(nums) then nums = mean(of _numeric_);
                end;
            %end;
            /* ... other treatments ... */
        run;
        
        /* Export cleaned data */
        proc json
            out="cleaned_output.json"
            pretty;
            export work.cleaned_data;
        run;
        """

        # Execute SAS safely
        run_sas_safely(sas_script, input_data)

        if os.path.exists('cleaned_output.json'):
            with open('cleaned_output.json') as f:
                cleaned_data = json.load(f).get('DATA', [])
            
            # Cache result
            cache.setex(cache_key, 3600, json.dumps(cleaned_data))  # 1-hour cache
            
            # Audit log
            audit_log("DATA_CLEANING", {
                "records_in": len(input_data),
                "records_out": len(cleaned_data),
                "options": options
            })
            return jsonify({
                'cleanedData': cleaned_data,
                'lineage_id': track_data_lineage(input_data, "cleaning", options, cleaned_data)
            })
        else:
            raise DataProcessingError("Data cleaning failed")

    except ActuarialException as ae:
        return jsonify({'error': str(ae), 'code': ae.code}), 500
    except Exception as e:
        audit_log("CLEANING_ERROR", {"error": str(e)})
        return jsonify({'error': f'Data cleaning failed: {str(e)}', 'code': 'SYS-003'}), 500

# Report generation API
@app.route('/api/generate-report', methods=['POST'])
def generate_report():
    """Generate diagnostic report"""
    data = request.get_json()
    input_data = data.get('data', [])
    options = data.get('options', {})
    if not input_data:
        return jsonify({'error': 'No data to analyze', 'code': 'DATA-008'}), 400

    try:
        # Check cache
        cache_key = f"report:{hashlib.sha256(json.dumps(input_data).encode()).hexdigest()}:{hashlib.sha256(json.dumps(options).encode()).hexdigest()}"
        if cached := cache.get(cache_key):
            return jsonify({'report': json.loads(cached)})

        # Build SAS report script
        sas_script = f"""
        /* Import JSON data */
        libname in json fileref=infile;
        filename infile "/input_data.json.enc";
        
        /* Include SOA report template */
        %include "/sas_lib/soa_standard_report.sas";
        
        /* Initialize report */
        proc soa_report_init
            data=in.root
            out=work.report_container
            standards="SOA2023";
        run;
        
        /* Conditional report sections */
        %if {1 if options.get('summaryStats', False) else 0} %then %do;
            proc soa_summary_stats
                data=in.root
                report=work.report_container;
            run;
        %end;
        /* ... other sections ... */
        
        /* Digital signature */
        proc digital_sign
            data=work.report_container
            key="/keys/actuary_key.pem"
            out=work.signed_report;
        run;
        
        /* Export report */
        proc json
            out="report_output.json"
            pretty;
            export work.signed_report;
        run;
        """

        # Submit to SAS Grid
        result = submit_to_sas_grid(sas_script, input_data)
        if 'report_output.json' in result and os.path.exists('report_output.json'):
            with open('report_output.json') as f:
                report = json.load(f)
            
            # Cache result
            cache.setex(cache_key, 1800, json.dumps(report))  # 30-minute cache
            
            # Audit log
            audit_log("REPORT_GENERATION", {
                "records": len(input_data),
                "options": options,
                "report_sections": list(report.keys())
            })
            return jsonify({
                'report': report,
                'lineage_id': track_data_lineage(input_data, "report", options, report)
            })
        else:
            raise ReportGenerationError("Report generation failed")

    except ActuarialException as ae:
        return jsonify({'error': str(ae), 'code': ae.code}), 500
    except Exception as e:
        audit_log("REPORT_ERROR", {"error": str(e)})
        return jsonify({'error': f'Report generation failed: {str(e)}', 'code': 'SYS-004'}), 500

# Analysis API endpoints
@app.route('/api/models', methods=['GET'])
def get_models():
    """获取可用模型列表"""
    models = [
        {
            "id": "lee-carter",
            "name": "Lee-Carter模型",
            "type": "死亡率预测",
            "description": "经典的随机死亡率预测模型",
            "formula": "ln(m_x,t) = a_x + b_x * k_t + e_x,t"
        },
        {
            "id": "cbd",
            "name": "CBD模型",
            "type": "死亡率预测",
            "description": "Cairns-Blake-Dowd死亡率模型",
            "formula": "logit(q_x,t) = k_t^1 + k_t^2 * (x - x_bar)"
        },
        {
            "id": "gompertz",
            "name": "Gompertz模型",
            "type": "生存分析",
            "description": "用于成人死亡率建模",
            "formula": "mu_x = B * c^x"
        }
    ]
    return jsonify({"models": models})

@app.route('/api/model/<model_id>', methods=['GET'])
def get_model_details(model_id):
    """获取模型详细信息"""
    model_details = {
        "lee-carter": {
            "id": "lee-carter",
            "name": "Lee-Carter模型",
            "description": "经典的随机死亡率预测模型，由Ronald D. Lee和Lawrence Carter于1992年提出",
            "formula": "ln(m_x,t) = a_x + b_x * k_t + e_x,t",
            "parameters": [
                {"name": "a_x", "description": "年龄别死亡率水平"},
                {"name": "b_x", "description": "年龄别死亡率变化模式"},
                {"name": "k_t", "description": "时间趋势指数"}
            ],
            "applicability": "适用于中长期人口死亡率预测，被广泛用于养老金和寿险定价",
            "soaReference": "SOA Study Note: Modeling Longevity Risk",
            "implementation": {
                "R": "library(demography)\nlee_carter(fd)",
                "Python": "from lifelines import LeeCarterFitter\nlc = LeeCarterFitter().fit(data)"
            }
        },
        "cbd": {
            "id": "cbd",
            "name": "CBD模型",
            "description": "Cairns-Blake-Dowd死亡率模型",
            "formula": "logit(q_x,t) = k_t^1 + k_t^2 * (x - x_bar)",
            "parameters": [
                {"name": "k_t^1", "description": "时间趋势参数1"},
                {"name": "k_t^2", "description": "时间趋势参数2"}
            ],
            "applicability": "适用于高龄人群死亡率建模",
            "soaReference": "SOA Research Paper: Mortality Density Forecasts"
        }
    }
    return jsonify(model_details.get(model_id, {}))

@app.route('/api/datasets', methods=['GET'])
def get_datasets():
    """获取可用数据集列表"""
    datasets = []
    datasets_dir = current_app.config['DATASETS_DIR']
    
    for file in os.listdir(datasets_dir):
        if file.endswith('.csv'):
            file_path = os.path.join(datasets_dir, file)
            size = f"{os.path.getsize(file_path)/(1024*1024):.2f} MB"
            datasets.append({
                "id": file,
                "name": file.replace('.csv', ''),
                "type": "CSV",
                "size": size,
                "date": datetime.fromtimestamp(os.path.getctime(file_path)).strftime('%Y-%m-%d')
            })
    return jsonify({"datasets": datasets})

@app.route('/api/analyze', methods=['POST'])
def analyze_data():
    """运行精算分析"""
    data = request.json
    model_id = data.get('model_id')
    dataset_id = data.get('dataset_id')
    options = data.get('options', {})
    
    # 1. 加载数据集
    try:
        datasets_dir = current_app.config['DATASETS_DIR']
        df = pd.read_csv(os.path.join(datasets_dir, dataset_id))
    except Exception as e:
        return jsonify({"error": f"数据集加载失败: {str(e)}"}), 400
    
    # 2. 根据模型运行分析
    results = {}
    if model_id == "lee-carter":
        results = run_lee_carter_analysis(df, options)
    elif model_id == "cbd":
        results = run_cbd_analysis(df, options)
    # 其他模型...
    
    # 3. 返回分析结果
    return jsonify(results)

def run_lee_carter_analysis(df, options):
    """运行Lee-Carter分析"""
    # 这里使用伪代码，实际实现需要完整的精算模型
    
    # 参数估计
    params = {
        "a_x": {"value": 0.05, "std_err": 0.002, "p_value": 0.001},
        "b_x": {"value": 0.12, "std_err": 0.005, "p_value": 0.0001},
        "k_t": {"value": -0.8, "std_err": 0.03, "p_value": 0.0001}
    }
    
    # 预测结果
    forecast_years = int(options.get('forecastYears', 10))
    forecast = []
    for year in range(1, forecast_years + 1):
        forecast.append({
            "year": datetime.now().year + year,
            "central": 0.75 - year * 0.02,
            "lower": 0.70 - year * 0.025,
            "upper": 0.80 - year * 0.015
        })
    
    # 模型诊断
    diagnostics = {
        "aic": 743.2,
        "bic": 801.5,
        "residual_autocorr": 0.12,
        "soa_compliance": "通过",
        "warnings": ["残差分布略有偏斜"]
    }
    
    # 生成代码
    code = {
        "R": "# Lee-Carter模型R实现\nlibrary(demography)\n# ...",
        "Python": "# Lee-Carter模型Python实现\nfrom lifelines import LeeCarterFitter\n# ...",
        "SAS": "/* Lee-Carter模型SAS实现 */\nPROC LIFEREG ..."
    }
    
    return {
        "model": "Lee-Carter",
        "parameters": params,
        "forecast": forecast,
        "diagnostics": diagnostics,
        "code": code,
        "visualization": generate_plotly_data(forecast)
    }

def generate_plotly_data(forecast):
    """生成Plotly可视化数据"""
    years = [f['year'] for f in forecast]
    central = [f['central'] for f in forecast]
    lower = [f['lower'] for f in forecast]
    upper = [f['upper'] for f in forecast]
    
    return {
        "data": [
            {
                "x": years,
                "y": central,
                "name": "中心预测",
                "type": "scatter",
                "mode": "lines+markers",
                "line": {"color": "#3a7bd5"}
            },
            {
                "x": years + years[::-1],
                "y": upper + lower[::-1],
                "name": "95%置信区间",
                "fill": "toself",
                "type": "scatter",
                "mode": "none",
                "fillcolor": "rgba(58, 123, 213, 0.2)"
            }
        ],
        "layout": {
            "title": "死亡率预测",
            "xaxis": {"title": "年份"},
            "yaxis": {"title": "死亡率"},
            "showlegend": True
        }
    }

# Comparison API endpoints
comparison_results_store = {}
datasets = {
    "dataset1": {"name": "HMD 2023", "rows": 10000},
    "dataset2": {"name": "CDC Mortality", "rows": 15000},
    "dataset3": {"name": "Custom Upload", "rows": 5000}
}
models = {
    "model1": {"name": "Lee-Carter", "type": "mortality"},
    "model2": {"name": "CBD", "type": "mortality"},
    "model3": {"name": "APC", "type": "morbidity"}
}

@app.route('/api/comparison-items/<type>', methods=['GET'])
def get_comparison_items(type):
    """获取可对比的项目列表"""
    items = []
    if type == 'models':
        for id, model in models.items():
            items.append({
                "id": id,
                "name": model['name'],
                "description": f"{model['type']} model"
            })
    elif type == 'datasets':
        for id, dataset in datasets.items():
            items.append({
                "id": id,
                "name": dataset['name'],
                "description": f"{dataset['rows']} rows"
            })
    elif type == 'parameters':
        # 示例参数对比项
        items = [
            {"id": "param1", "name": "Time Horizon", "description": "5 years"},
            {"id": "param2", "name": "Confidence Level", "description": "95%"},
            {"id": "param3", "name": "Pandemic Impact", "description": "Medium"}
        ]
    return jsonify({"items": items})

@app.route('/api/run-comparison', methods=['POST'])
def run_comparison():
    """运行对比分析"""
    data = request.json
    options = data['options']
    
    # 生成模拟对比结果
    results = {
        "items": [],
        "metrics": {
            "AIC": [],
            "BIC": [],
            "Residual": []
        },
        "details": [],
        "visualizations": []
    }
    
    # 添加项目详情
    for item_id in options['items']:
        if options['type'] == 'models':
            model = models.get(item_id, {"name": "Unknown Model"})
            results['items'].append({
                "id": item_id,
                "name": model['name'],
                "type": "Model"
            })
            results['details'].append({
                "itemId": item_id,
                "itemName": model['name'],
                "itemType": "Model",
                "data": {"parameters": ["alpha=0.5", "beta=0.2"]}
            })
        elif options['type'] == 'datasets':
            dataset = datasets.get(item_id, {"name": "Unknown Dataset"})
            results['items'].append({
                "id": item_id,
                "name": dataset['name'],
                "type": "Dataset"
            })
            results['details'].append({
                "itemId": item_id,
                "itemName": dataset['name'],
                "itemType": "Dataset",
                "data": {"size": "10,000 rows", "period": "2010-2023"}
            })
        else:  # parameters
            results['items'].append({
                "id": item_id,
                "name": f"Parameter {item_id}",
                "type": "Parameter"
            })
            results['details'].append({
                "itemId": item_id,
                "itemName": f"Param {item_id}",
                "itemType": "Parameter",
                "data": {"value": "0.75"}
            })
    
    # 添加模拟指标
    results['metrics']['AIC'].append(np.random.uniform(700, 800))
    results['metrics']['BIC'].append(np.random.uniform(750, 850))
    results['metrics']['Residual'].append(np.random.uniform(0.1, 0.3))
    
    # 添加可视化数据
    for metric in options['metrics']:
        results['visualizations'].append({
            "title": f"{metric} Comparison",
            "data": [
                {
                    "x": [item['name'] for item in results['items']],
                    "y": results['metrics'][metric],
                    "type": "bar",
                    "name": metric
                }
            ],
            "layout": {
                "title": f"{metric} Values Across Items",
                "xaxis": {"title": "Items"},
                "yaxis": {"title": metric}
            }
        })
    
    # 存储结果
    result_id = f"result_{len(comparison_results_store)}"
    comparison_results_store[result_id] = results
    
    return jsonify({"resultId": result_id, "results": results})

@app.route('/api/export-comparison', methods=['POST'])
def export_comparison():
    """导出对比结果"""
    data = request.json
    result_id = data.get('resultId')
    if not result_id or result_id not in comparison_results_store:
        return jsonify({"error": "Invalid result ID"}), 400
    
    results = comparison_results_store[result_id]
    
    # 创建ZIP文件
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
        # 添加摘要CSV
        summary_df = pd.DataFrame({
            "Item": [item['name'] for item in results['items']],
            **{metric: values for metric, values in results['metrics'].items()}
        })
        zip_file.writestr('summary.csv', summary_df.to_csv(index=False))
        
        # 添加JSON详情
        zip_file.writestr('details.json', json.dumps(results['details'], indent=2))
        
        # 添加图表HTML
        for i, viz in enumerate(results['visualizations']):
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <script src="https://cdn.plot.ly/plotly-2.24.1.min.js"></script>
            </head>
            <body>
                <div id="chart" style="width:800px;height:600px;"></div>
                <script>
                    Plotly.newPlot('chart', {json.dumps(viz['data'])}, {json.dumps(viz['layout'])});
                </script>
            </body>
            </html>
            """
            zip_file.writestr(f'chart_{i+1}.html', html_content)
    
    zip_buffer.seek(0)
    return send_file(
        zip_buffer,
        mimetype='application/zip',
        as_attachment=True,
        download_name=f'comparison_results_{result_id}.zip'
    )

@app.route('/api/save-comparison', methods=['POST'])
def save_comparison():
    """保存对比结果"""
    data = request.json
    results = data.get('results')
    if not results:
        return jsonify({"error": "No results provided"}), 400
    
    # 在实际应用中，这里会保存到数据库
    result_id = f"saved_{len(comparison_results_store)}"
    comparison_results_store[result_id] = results
    
    return jsonify({
        "status": "success",
        "message": "Comparison saved successfully",
        "resultId": result_id
    })

# Error handlers
@app.errorhandler(ActuarialException)
def handle_actuarial_exception(e):
    return jsonify({'error': str(e), 'code': e.code}), 500

@app.errorhandler(500)
def handle_server_error(e):
    return jsonify({'error': 'Internal server error', 'code': 'SYS-500'}), 500

# Configure routes
def configure_data_pipeline_routes(app):
    @app.before_request
    def check_auth():
        # Implement enterprise auth logic
        pass

    app.register_error_handler(ActuarialException, handle_actuarial_exception)
    app.register_error_handler(500, handle_server_error)

# Start application
if __name__ == '__main__':
    configure_data_pipeline_routes(app)
    app.run(host='0.0.0.0', port=5000, debug=True)
