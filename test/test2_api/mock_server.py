from flask import Flask, jsonify, request

app = Flask(__name__)

# 定义所有API端点
@app.route('/')
def home():
    return "API 服务运行正常！"

@app.route('/api/models')
def models():
    return jsonify({"models": ["lee-carter", "cairns-blake-dowd"]})

@app.route('/api/model/<model_id>')
def model_details(model_id):
    return jsonify({
        "name": model_id,
        "formula": f"{model_id}模型的公式描述",
        "description": f"这是{model_id}模型的详细说明"
    })

@app.route('/api/upload-custom-data', methods=['POST'])
def upload_custom_data():
    if 'file' in request.files:
        return jsonify({
            "status": "success",
            "message": "文件上传成功",
            "data": {
                "filename": request.files['file'].filename,
                "size": request.content_length
            }
        })
    return jsonify({"status": "error", "message": "未接收到文件"}), 400

@app.route('/api/clean-data', methods=['POST'])
def clean_data():
    return jsonify({
        "cleanedData": request.json.get('data', []),
        "stats": {
            "missingValues": 0,
            "outliers": 2,
            "rowsProcessed": len(request.json.get('data', []))
        }
    })

@app.route('/api/generate-report', methods=['POST'])
def generate_report():
    return jsonify({
        "report": {
            "summary": "数据质量报告摘要",
            "missingValues": [],
            "outliers": [{"index": 5, "value": 0.42}],
            "recommendations": ["建议处理检测到的异常值"]
        }
    })

@app.route('/api/analyze', methods=['POST'])
def analyze():
    return jsonify({
        "parameters": {
            "alpha": 0.85,
            "beta": -0.02,
            "kappa": [0.1, 0.05, -0.03]
        },
        "forecast": [
            {"year": 2025, "mortality": 0.0012},
            {"year": 2026, "mortality": 0.0013},
            {"year": 2027, "mortality": 0.0014}
        ],
        "diagnostics": {
            "rSquared": 0.95,
            "mse": 0.0002
        }
    })

@app.route('/api/comparison-items/models')
def comparison_items():
    return jsonify({
        "items": ["lee-carter", "cairns-blake-dowd", "mortality-trend"],
        "categories": ["models", "datasets", "results"]
    })

@app.route('/api/run-comparison', methods=['POST'])
def run_comparison():
    return jsonify({
        "results": {
            "comparisonType": request.json['options']['type'],
            "items": request.json['options']['items'],
            "metrics": {
                "AIC": [120.5, 115.3],
                "BIC": [125.7, 121.1]
            },
            "ranking": ["cairns-blake-dowd", "lee-carter"]
        }
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
