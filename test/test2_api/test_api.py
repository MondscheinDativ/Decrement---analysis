import os
import sys
import pytest
import requests
import json
import time
from io import BytesIO
import pandas as pd

# 配置基础URL - 使用服务器本地地址
BASE_URL = "http://localhost:5000"
HEADERS = {"Content-Type": "application/json"}

# 测试数据集
TEST_DATASET = [
    {"age": 30, "year": 2020, "mortality": 0.001},
    {"age": 30, "year": 2021, "mortality": 0.0012},
    {"age": 31, "year": 2020, "mortality": 0.0015}
]

# === 辅助函数 ===
def make_request(method, endpoint, payload=None, files=None):
    """统一的请求处理函数"""
    url = f"{BASE_URL}{endpoint}"
    try:
        # 打印请求详细信息
        print(f"\n{'='*50}")
        print(f"[TEST] 准备请求: {method} {url}")
        if payload:
            print(f"请求参数: {json.dumps(payload, indent=2)[:500]}")
        
        if method == "GET":
            response = requests.get(url, params=payload)
        elif method == "POST" and files:
            response = requests.post(url, files=files)
        else:
            response = requests.post(url, json=payload, headers=HEADERS)
        
        # 记录响应日志
        print(f"状态码: {response.status_code}")
        try:
            response_data = response.json()
            print("响应内容:")
            print(json.dumps(response_data, indent=2)[:1000])
            return response
        except json.JSONDecodeError:
            print("响应内容不是JSON格式")
            print("原始内容:", response.text[:500])
            return response
    except Exception as e:
        print(f"❌ 请求错误: {str(e)}")
        return None

# === 测试用例 ===
class TestDataPipeline:
    """数据管道功能测试"""
    
    def test_upload_custom_data(self):
        """测试自定义数据上传"""
        print("\n测试自定义数据上传...")
        csv_content = "age,year,mortality\n30,2020,0.001\n35,2020,0.0015"
        files = {'file': ('test_data.csv', BytesIO(csv_content.encode()))}
        response = make_request("POST", "/api/upload-custom-data", files=files)
        assert response.status_code == 200
        assert "data" in response.json()
        print("✅ 上传测试通过")
    
    def test_clean_data(self):
        """测试数据清洗"""
        print("\n测试数据清洗...")
        payload = {
            "data": TEST_DATASET,
            "options": {
                "missingValueTreatment": "mean",
                "outlierTreatment": "keep",
                "normalizationMethod": "none",
                "removeDuplicates": True,
                "convertDataTypes": True
            }
        }
        response = make_request("POST", "/api/clean-data", payload)
        assert response.status_code == 200
        assert "cleanedData" in response.json()
        print("✅ 清洗测试通过")
    
    def test_generate_report(self):
        """测试报告生成"""
        print("\n测试报告生成...")
        payload = {
            "data": TEST_DATASET,
            "options": {
                "summaryStats": True,
                "missingValueReport": True,
                "outlierReport": True
            }
        }
        response = make_request("POST", "/api/generate-report", payload)
        assert response.status_code == 200
        assert "report" in response.json()
        print("✅ 报告测试通过")

class TestAnalysis:
    """分析功能测试"""
    
    def test_get_models(self):
        """测试获取模型列表"""
        print("\n测试获取模型列表...")
        response = make_request("GET", "/api/models")
        assert response.status_code == 200
        assert "models" in response.json()
        assert len(response.json()["models"]) > 0
        print("✅ 模型列表测试通过")
    
    def test_get_model_details(self):
        """测试获取模型详情"""
        print("\n测试获取模型详情...")
        response = make_request("GET", "/api/model/lee-carter")
        assert response.status_code == 200
        assert "name" in response.json()
        assert "formula" in response.json()
        print("✅ 模型详情测试通过")
    
    def test_run_analysis(self):
        """测试运行分析"""
        print("\n测试运行分析...")
        payload = {
            "model_id": "lee-carter",
            "dataset": TEST_DATASET,
            "options": {
                "confidenceLevel": 95,
                "forecastYears": 10,
                "randomSimulations": 1000,
                "diagnostics": True
            }
        }
        response = make_request("POST", "/api/analyze", payload)
        assert response.status_code == 200
        assert "parameters" in response.json()
        assert "forecast" in response.json()
        print("✅ 分析测试通过")

class TestComparison:
    """结果对比功能测试"""
    
    def test_get_comparison_items(self):
        """测试获取对比项"""
        print("\n测试获取对比项...")
        response = make_request("GET", "/api/comparison-items/models")
        assert response.status_code == 200
        assert "items" in response.json()
        print("✅ 对比项测试通过")
    
    def test_run_comparison(self):
        """测试运行对比"""
        print("\n测试运行对比...")
        payload = {
            "options": {
                "type": "models",
                "items": ["lee-carter", "cairns-blake-dowd"],
                "metrics": ["AIC", "BIC"]
            }
        }
        response = make_request("POST", "/api/run-comparison", payload)
        assert response.status_code == 200
        assert "results" in response.json()
        assert "items" in response.json()["results"]
        print("✅ 对比运行测试通过")

# === 主测试函数 ===
def run_tests():
    """运行所有测试"""
    print("\n" + "="*70)
    print("🚀 开始运行API测试套件")
    print(f"📡 基础URL: {BASE_URL}")
    print(f"📊 测试数据集: {json.dumps(TEST_DATASET)[:100]}...")
    print("="*70 + "\n")
    
    # 使用pytest运行测试
    exit_code = pytest.main([__file__, "-v"])
    
    print("\n" + "="*70)
    print(f"✅ 测试完成! 退出代码: {exit_code}")
    print("="*70)
    return exit_code

if __name__ == "__main__":
    run_tests()
