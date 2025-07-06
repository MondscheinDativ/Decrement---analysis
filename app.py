import os
import sys
import subprocess
import tempfile
import json
import uuid
import hashlib
import time
from datetime import datetime
from flask import Flask, request, jsonify, current_app, session
from cryptography.fernet import Fernet
import redis
import saspy  # For SAS Grid integration

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'supersecretkey')
app.config['DATA_KEY'] = Fernet.generate_key()
app.config['REDIS_URL'] = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
app.config['SAS_GRID_USER'] = os.environ.get('SAS_GRID_USER', 'griduser')
app.config['SAS_GRID_PASS'] = os.environ.get('SAS_GRID_PASS', 'gridpass')

# Initialize Redis connection
cache = redis.Redis.from_url(app.config['REDIS_URL'])

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

# Data fetching API
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
