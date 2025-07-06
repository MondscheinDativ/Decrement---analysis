from flask import Flask, request, jsonify, send_file
import numpy as np
import pandas as pd
import statsmodels.api as sm
from io import BytesIO
import zipfile
import json
import threading
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB

# 全局分析进度
analysis_progress = {}

# 模型描述数据
MODEL_DESCRIPTIONS = {
    "gompertz": {
        "name": "Gompertz死亡率模型",
        "description": "Gompertz模型是一种指数模型，适用于描述成年人死亡率随年龄增长的变化规律。",
        "formula": "μ(x) = a * exp(b*x)",
        "parameters": [
            {"name": "a", "description": "初始死亡率水平"},
            {"name": "b", "description": "死亡率增长率"}
        ]
    },
    "lee-carter": {
        "name": "Lee-Carter模型",
        "description": "Lee-Carter模型是死亡率预测的标准模型，包含年龄别参数和时间趋势参数。",
        "formula": "ln(μ(x,t)) = a_x + b_x * k_t",
        "parameters": [
            {"name": "a_x", "description": "年龄别死亡率基准"},
            {"name": "b_x", "description": "年龄别变化率"},
            {"name": "k_t", "description": "时间趋势参数"}
        ]
    }
}

@app.route('/api/model-description/<model_id>', methods=['GET'])
def get_model_description(model_id):
    """获取模型描述信息"""
    model = MODEL_DESCRIPTIONS.get(model_id.lower())
    if model:
        return jsonify(model)
    return jsonify({"error": "Model not found"}), 404

@app.route('/api/available-datasets', methods=['GET'])
def get_available_datasets():
    """获取可用数据集列表"""
    # 实际应用中应从数据库获取
    datasets = [
        {"id": "hmd-2023", "name": "HMD 2023数据集", "rows": 15000, "columns": 25},
        {"id": "cdc-mortality", "name": "CDC死亡率数据集", "rows": 8500, "columns": 18}
    ]
    return jsonify({"datasets": datasets})

@app.route('/api/dataset-variables/<dataset_id>', methods=['GET'])
def get_dataset_variables(dataset_id):
    """获取数据集变量信息"""
    # 模拟数据 - 实际应从数据库或文件读取
    model_vars = ["age", "gender", "mortality_rate", "exposure"]
    
    if dataset_id == "hmd-2023":
        dataset_fields = ["Age", "Sex", "Deaths", "Exposure", "Country", "Year"]
    elif dataset_id == "cdc-mortality":
        dataset_fields = ["AGE", "SEX", "DEATHS", "POPULATION", "CAUSE", "YEAR"]
    else:
        return jsonify({"error": "Dataset not found"}), 404
    
    return jsonify({
        "modelVariables": model_vars,
        "datasetFields": dataset_fields
    })

@app.route('/api/load-dataset', methods=['POST'])
def load_dataset():
    """加载数据集并应用变量映射"""
    data = request.json
    dataset_id = data.get('datasetId')
    mappings = data.get('variableMappings')
    
    # 模拟数据集加载 - 实际应从数据库获取
    df = pd.DataFrame({
        'Age': np.random.randint(20, 100, 100),
        'Sex': np.random.choice(['M', 'F'], 100),
        'Deaths': np.random.randint(0, 50, 100),
        'Exposure': np.random.uniform(100, 1000, 100)
    })
    
    # 应用变量映射
    df = df.rename(columns={v: k for k, v in mappings.items()})
    
    # 返回标准化数据集
    return jsonify({
        "dataset": df.to_dict(orient='records'),
        "metadata": {
            "rows": len(df),
            "columns": list(df.columns),
            "mappings": mappings
        }
    })

@app.route('/api/run-analysis', methods=['POST'])
def run_analysis():
    """运行精算分析"""
    data = request.json
    model = data['model']
    dataset = data['dataset']
    options = data['options']
    
    # 创建分析线程
    thread_id = request.environ.get('werkzeug.server.thread')
    analysis_progress[thread_id] = 0
    
    # 转换为DataFrame
    df = pd.DataFrame(dataset)
    
    # 模拟分析过程
    results = {}
    
    # 参数估计 (模拟)
    if options['output']['estimates']:
        # 更新进度
        analysis_progress[thread_id] = 30
        results['estimates'] = [
            {"name": "α", "estimate": 0.0235, "stdError": 0.0012, "tValue": 19.58, "pValue": 0.0001, "ci": [0.0211, 0.0259]},
            {"name": "β", "estimate": 0.115, "stdError": 0.008, "tValue": 14.37, "pValue": 0.0001, "ci": [0.099, 0.131]}
        ]
    
    # 拟合优度 (模拟)
    if options['output']['goodness']:
        analysis_progress[thread_id] = 60
        results['goodness'] = {
            "LogLikelihood": -450.23,
            "AIC": 904.46,
            "BIC": 912.75,
            "R-squared": 0.894
        }
    
    # 图表生成
    if options['output']['charts']:
        analysis_progress[thread_id] = 80
        results['charts'] = [
            {
                "title": "死亡率曲线",
                "data": [{
                    "x": df['age'],
                    "y": np.exp(-0.05 * df['age']),
                    "type": "scatter",
                    "name": "拟合曲线"
                }],
                "layout": {
                    "title": "年龄别死亡率",
                    "xaxis": {"title": "年龄"},
                    "yaxis": {"title": "死亡率"}
                }
            }
        ]
    
    # 诊断信息
    if options['output']['diagnostics']:
        analysis_progress[thread_id] = 95
        results['diagnostics'] = {
            "converged": True,
            "iterations": 15,
            "residuals": "随机分布"
        }
    
    # 代码生成
    results['code'] = {
        "r": "# R代码示例\nmodel <- glm(deaths ~ age + gender, data = dataset, family = poisson)",
        "python": "# Python代码示例\nimport statsmodels.api as sm\nmodel = sm.GLM(endog=deaths, exog=exog, family=sm.families.Poisson()).fit()",
        "sas": "/* SAS代码示例 */\nproc genmod data=mortality;\nclass gender;\nmodel deaths = age gender / dist=poisson;\nrun;"
    }
    
    analysis_progress[thread_id] = 100
    return jsonify({"results": results})

@app.route('/api/analysis-progress', methods=['GET'])
def get_analysis_progress():
    """获取分析进度"""
    thread_id = request.environ.get('werkzeug.server.thread')
    return jsonify({"progress": analysis_progress.get(thread_id, 0)})

@app.route('/api/export-analysis-results', methods=['POST'])
def export_analysis_results():
    """导出分析结果"""
    data = request.json
    results = data['results']
    
    # 创建ZIP文件
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # 添加结果JSON
        zipf.writestr('results.json', json.dumps(results, indent=2))
        
        # 添加CSV报告
        if 'estimates' in results:
            df_estimates = pd.DataFrame(results['estimates'])
            zipf.writestr('estimates.csv', df_estimates.to_csv(index=False))
        
        # 添加图表
        if 'charts' in results:
            for i, chart in enumerate(results['charts']):
                img_data = plotly_to_image(chart)
                zipf.writestr(f'chart_{i}.png', img_data)
    
    zip_buffer.seek(0)
    return send_file(
        zip_buffer,
        mimetype='application/zip',
        as_attachment=True,
        download_name='analysis_results.zip'
    )

def plotly_to_image(chart):
    """将Plotly图表转换为PNG图像（模拟）"""
    # 实际实现应使用Plotly的图片导出功能
    return b"PNG_IMAGE_DATA"  # 模拟返回

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(host='0.0.0.0', port=5000, threaded=True)
