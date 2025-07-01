from flask import Flask, request, jsonify, send_file, render_template
from flask_cors import CORS
import pandas as pd
import numpy as np
import io
import os
import tempfile
import json
import logging
from datetime import datetime
from typing import Tuple, Dict, Optional
import re
import requests

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 初始化 Flask 应用
app = Flask(__name__)
CORS(app)  # 启用跨域资源共享

# 配置
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# 定义支持的模型
MODELS = {
    'lee-carter': {
        'name': 'Lee-Carter模型',
        'description': '经典的死亡率预测模型，使用对数线性方法捕捉死亡率趋势',
        'year': 1992,
        'required_variables': ['age', 'year', 'death_rate'],
        'optional_variables': ['population']
    },
    'cbd': {
        'name': 'CBD模型',
        'description': 'CBD (Currie, Durban, Eilers)模型，扩展了Lee-Carter模型，增加了年龄-时期交互项',
        'year': 2006,
        'required_variables': ['age', 'year', 'death_rate'],
        'optional_variables': ['population', 'gender']
    },
    'renshaw-haberman': {
        'name': 'Renshaw-Haberman模型',
        'description': 'RH模型，在Lee-Carter基础上增加了年龄-队列效应，提高了预测准确性',
        'year': 2006,
        'required_variables': ['age', 'year', 'death_rate', 'cohort'],
        'optional_variables': ['population']
    }
}

# 健康检查 API
@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查 API"""
    return jsonify({
        'status': 'ok',
        'version': '1.0.0'
    })

# 获取支持的模型列表
@app.route('/api/models', methods=['GET'])
def get_models():
    """获取支持的模型列表"""
    return jsonify(list(MODELS.values()))

# 获取特定模型所需变量
@app.route('/api/model-variables/<model_id>', methods=['GET'])
def get_model_variables(model_id):
    """获取特定模型所需变量"""
    if model_id not in MODELS:
        return jsonify({'error': f'不支持的模型: {model_id}'}), 400
    
    return jsonify({
        'model_id': model_id,
        'model_name': MODELS[model_id]['name'],
        'required_variables': MODELS[model_id]['required_variables'],
        'optional_variables': MODELS[model_id]['optional_variables']
    })

# 上传数据文件
@app.route('/api/upload', methods=['POST'])
def upload_file():
    """上传数据文件并预览"""
    try:
        # 检查是否有文件上传
        if 'file' not in request.files:
            return jsonify({'error': '未找到文件'}), 400
        
        file = request.files['file']
        
        # 检查文件名
        if file.filename == '':
            return jsonify({'error': '空文件名'}), 400
        
        # 保存文件
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"{timestamp}_{file.filename}"
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)
        
        # 检查文件类型并预览数据
        file_ext = os.path.splitext(filename)[1].lower()
        
        try:
            if file_ext == '.csv':
                df = pd.read_csv(file_path)
            elif file_ext in ['.xls', '.xlsx']:
                df = pd.read_excel(file_path)
            else:
                return jsonify({'error': '不支持的文件类型'}), 400
            
            # 返回数据预览
            preview = {
                'rows': len(df),
                'columns': list(df.columns),
                'data': df.head(10).to_dict('records'),
                'file_id': filename
            }
            
            return jsonify(preview)
            
        except Exception as e:
            logger.error(f"数据预览失败: {str(e)}")
            return jsonify({
                'file_id': filename,
                'message': '文件上传成功，但数据预览失败',
                'error': str(e)
            }), 200
            
    except Exception as e:
        logger.error(f"文件上传失败: {str(e)}")
        return jsonify({'error': '文件上传失败', 'details': str(e)}), 500

# 从 URL 获取数据
@app.route('/api/fetch-url', methods=['POST'])
def fetch_url():
    """从指定 URL 获取数据"""
    try:
        url = request.json.get('url')
        method = request.json.get('method', 'GET')
        format = request.json.get('format', 'csv')
        
        if not url:
            return jsonify({'error': 'URL不能为空'}), 400
        
        # 根据格式解析数据
        try:
            if format == 'csv':
                df = pd.read_csv(url)
            elif format == 'json':
                df = pd.read_json(url)
            else:
                return jsonify({'error': '不支持的数据格式'}), 400
            
            # 保存数据到临时文件
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            filename = f"{timestamp}_from_url.csv"
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            df.to_csv(file_path, index=False)
            
            # 返回数据预览
            preview = {
                'rows': len(df),
                'columns': list(df.columns),
                'data': df.head(10).to_dict('records'),
                'file_id': filename
            }
            
            return jsonify(preview)
            
        except Exception as e:
            logger.error(f"从URL获取数据失败: {str(e)}")
            return jsonify({'error': '获取数据失败', 'details': str(e)}), 500
            
    except Exception as e:
        logger.error(f"处理URL请求失败: {str(e)}")
        return jsonify({'error': '处理请求失败', 'details': str(e)}), 500

# 测试 API 连接
@app.route('/api/test-api', methods=['POST'])
def test_api():
    """测试外部 API 连接"""
    try:
        url = request.json.get('url')
        method = request.json.get('method', 'GET')
        headers = request.json.get('headers', {})
        body = request.json.get('body', {})
        
        if not url:
            return jsonify({'error': 'API URL不能为空'}), 400
        
        # 发送 API 请求
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                response = requests.post(url, headers=headers, json=body)
            else:
                return jsonify({'error': f'不支持的HTTP方法: {method}'}), 400
            
            response.raise_for_status()
            
            # 分析响应数据
            content_type = response.headers.get('Content-Type', '')
            
            if 'json' in content_type:
                data = response.json()
                if isinstance(data, list):
                    df = pd.DataFrame(data[:10])  # 取前10条记录预览
                elif isinstance(data, dict):
                    # 如果是单个对象，转换为包含一个元素的列表
                    df = pd.DataFrame([data])
                else:
                    return jsonify({'error': '无法解析JSON响应'}), 500
            elif 'csv' in content_type or 'text' in content_type:
                # 尝试将文本解析为CSV
                df = pd.read_csv(io.StringIO(response.text), nrows=10)
            else:
                # 尝试通用解析
                try:
                    df = pd.read_json(io.StringIO(response.text[:10000]), lines=True)
                except:
                    try:
                        df = pd.read_csv(io.StringIO(response.text[:10000]))
                    except:
                        return jsonify({
                            'status': 'success',
                            'message': 'API连接成功，但无法解析响应数据格式',
                            'headers': dict(response.headers),
                            'sample': response.text[:500] + '...'
                        })
            
            # 保存数据到临时文件
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            filename = f"{timestamp}_from_api.csv"
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            df.to_csv(file_path, index=False)
            
            # 返回数据预览
            preview = {
                'rows': len(df),
                'columns': list(df.columns),
                'data': df.head(10).to_dict('records'),
                'file_id': filename,
                'protocol_info': {
                    'https': url.startswith('https'),
                    'protocols': ['HTTPS', 'OAuth 2.0', 'JWT'] if url.startswith('https') else ['HTTP']
                }
            }
            
            return jsonify(preview)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API请求失败: {str(e)}")
            return jsonify({
                'status': 'error',
                'message': 'API请求失败',
                'details': str(e),
                'protocol_info': {
                    'https': url.startswith('https'),
                    'protocols': ['HTTPS'] if url.startswith('https') else ['HTTP', 'SOAP']
                }
            }), 400
            
    except Exception as e:
        logger.error(f"测试API连接失败: {str(e)}")
        return jsonify({'error': '处理请求失败', 'details': str(e)}), 500

# 数据清洗 API
@app.route('/api/clean-data', methods=['POST'])
def clean_data():
    """数据清洗 API"""
    try:
        file_id = request.json.get('file_id')
        operations = request.json.get('operations', [])
        
        if not file_id:
            return jsonify({'error': '缺少文件ID'}), 400
        
        file_path = os.path.join(UPLOAD_FOLDER, file_id)
        
        if not os.path.exists(file_path):
            return jsonify({'error': '文件不存在'}), 404
        
        # 检查文件类型
        file_ext = os.path.splitext(file_id)[1].lower()
        
        # 读取数据
        try:
            if file_ext == '.csv':
                df = pd.read_csv(file_path)
            elif file_ext in ['.xls', '.xlsx']:
                df = pd.read_excel(file_path)
            else:
                return jsonify({'error': '不支持的文件类型'}), 400
        except Exception as e:
            logger.error(f"读取数据失败: {str(e)}")
            return jsonify({'error': '读取数据失败', 'details': str(e)}), 500
        
        # 创建清洗报告
        report = {
            'operations': [],
            'statistics': {
                'original_rows': len(df),
                'original_columns': len(df.columns)
            }
        }
        
        # 执行数据清洗操作
        if 'clean_header' in operations:
            # 标准化表头
            original_headers = list(df.columns)
            df.columns = [col.strip().replace(' ', '_').upper() for col in df.columns]
            report['operations'].append({
                'name': '标准化表头',
                'description': '将表头转换为大写并替换空格为下划线',
                'changes': {
                    'original_headers': original_headers,
                    'new_headers': list(df.columns)
                }
            })
        
        if 'clean_duplicates' in operations:
            # 删除重复记录
            original_rows = len(df)
            df = df.drop_duplicates()
            removed_rows = original_rows - len(df)
            report['operations'].append({
                'name': '删除重复记录',
                'description': '删除完全重复的记录',
                'statistics': {
                    'original_rows': original_rows,
                    'cleaned_rows': len(df),
                    'removed_rows': removed_rows
                }
            })
        
        if 'clean_missing' in operations:
            # 处理缺失值
            missing_counts = df.isnull().sum()
            total_missing = missing_counts.sum()
            
            # 数值型列填充均值
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            for col in numeric_cols:
                mean_val = df[col].mean()
                df[col].fillna(mean_val, inplace=True)
            
            # 字符型列填充'UNKNOWN'
            categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
            for col in categorical_cols:
                df[col].fillna('UNKNOWN', inplace=True)
            
            report['operations'].append({
                'name': '处理缺失值',
                'description': '数值型列填充均值，字符型列填充"UNKNOWN"',
                'statistics': {
                    'total_missing_values': int(total_missing),
                    'missing_by_column': missing_counts.to_dict()
                }
            })
        
        if 'clean_outliers' in operations:
            # 处理异常值
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            outliers = {}
            
            for col in numeric_cols:
                # 使用IQR方法检测异常值
                Q1 = df[col].quantile(0.25)
                Q3 = df[col].quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                
                # 计算异常值数量
                outliers_count = len(df[(df[col] < lower_bound) | (df[col] > upper_bound)])
                if outliers_count > 0:
                    outliers[col] = outliers_count
                    
                    # 盖帽法处理异常值
                    df.loc[df[col] < lower_bound, col] = lower_bound
                    df.loc[df[col] > upper_bound, col] = upper_bound
            
            report['operations'].append({
                'name': '处理异常值',
                'description': '使用IQR方法检测并使用盖帽法处理异常值',
                'statistics': {
                    'outliers_by_column': outliers,
                    'total_outliers': sum(outliers.values())
                }
            })
        
        if 'clean_format' in operations:
            # 标准化数据格式
            # 日期列检测与转换
            date_cols = []
            for col in df.columns:
                try:
                    # 尝试将列转换为日期类型
                    df[col] = pd.to_datetime(df[col], errors='coerce')
                    if df[col].notnull().sum() > 0:  # 如果至少有一个成功转换
                        date_cols.append(col)
                except:
                    pass
            
            report['operations'].append({
                'name': '标准化数据格式',
                'description': '尝试将可能的列转换为日期格式',
                'statistics': {
                    'date_columns': date_cols
                }
            })
        
        # 计算最终统计信息
        report['statistics']['final_rows'] = len(df)
        report['statistics']['final_columns'] = len(df.columns)
        
        # 生成描述性统计
        desc_stats = df.describe().to_dict()
        report['statistics']['descriptive'] = desc_stats
        
        # 保存清洗后的数据
        cleaned_file_id = f"cleaned_{file_id}"
        cleaned_file_path = os.path.join(UPLOAD_FOLDER, cleaned_file_id)
        df.to_csv(cleaned_file_path, index=False)
        
        # 返回清洗报告和文件ID
        return jsonify({
            'report': report,
            'cleaned_file_id': cleaned_file_id
        })
        
    except Exception as e:
        logger.error(f"数据清洗失败: {str(e)}")
        return jsonify({'error': '数据清洗失败', 'details': str(e)}), 500

# 下载文件 API
@app.route('/api/download/<file_id>', methods=['GET'])
def download_file(file_id):
    """下载指定文件"""
    try:
        file_path = os.path.join(UPLOAD_FOLDER, file_id)
        
        if not os.path.exists(file_path):
            return jsonify({'error': '文件不存在'}), 404
        
        return send_file(file_path, as_attachment=True)
        
    except Exception as e:
        logger.error(f"下载文件失败: {str(e)}")
        return jsonify({'error': '下载文件失败', 'details': str(e)}), 500

# 模型分析 API
@app.route('/api/analyze', methods=['POST'])
def analyze_data():
    """执行模型分析"""
    try:
        file_id = request.json.get('file_id')
        model_id = request.json.get('model_id')
        variables = request.json.get('variables', {})
        
        if not file_id or not model_id:
            return jsonify({'error': '缺少必要参数'}), 400
        
        file_path = os.path.join(UPLOAD_FOLDER, file_id)
        
        if not os.path.exists(file_path):
            return jsonify({'error': '文件不存在'}), 404
        
        # 读取数据
        file_ext = os.path.splitext(file_id)[1].lower()
        try:
            if file_ext == '.csv':
                df = pd.read_csv(file_path)
            elif file_ext in ['.xls', '.xlsx']:
                df = pd.read_excel(file_path)
            else:
                return jsonify({'error': '不支持的文件类型'}), 400
        except Exception as e:
            logger.error(f"读取分析数据失败: {str(e)}")
            return jsonify({'error': '读取数据失败', 'details': str(e)}), 500
        
        # 检查模型所需变量
        if model_id not in MODELS:
            return jsonify({'error': f'不支持的模型: {model_id}'}), 400
        
        required_vars = MODELS[model_id]['required_variables']
        missing_vars = [var for var in required_vars if var not in df.columns]
        
        if missing_vars:
            return jsonify({
                'error': '缺少模型所需变量',
                'missing_variables': missing_vars,
                'required_variables': required_vars
            }), 400
        
        # 这里应实现实际的模型分析逻辑
        # 以下为示例响应
        analysis_result = {
            'model': MODELS[model_id]['name'],
            'variables_used': list(df.columns),
            'summary': f'{MODELS[model_id]["name"]} 分析完成，基于{len(df)}条记录',
            'statistics': {
                'mean_death_rate': df[required_vars[2]].mean(),
                'max_age': df[required_vars[0]].max(),
                'time_range': f'{df[required_vars[1]].min()}-{df[required_vars[1]].max()}'
            }
        }
        
        return jsonify(analysis_result)
        
    except Exception as e:
        logger.error(f"模型分析失败: {str(e)}")
        return jsonify({'error': '模型分析失败', 'details': str(e)}), 500

if __name__ == '__main__':
app.run(debug=True, port=5000)
