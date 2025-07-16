import os
import sys
import json
import pandas as pd
import numpy as np
import unittest
from unittest.mock import patch, MagicMock
import subprocess

# 添加项目根目录到系统路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 模拟精算平台的核心功能
class ActuarialPlatformTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # 加载测试数据（包含疫情年份）
        cls.hmd_data = cls.load_hmd_data()
        cls.cdc_data = cls.load_cdc_data()
        
        # 定义测试模型
        cls.models = {
            "lee-carter": {
                "name": "Lee-Carter Model",
                "type": "mortality",
                "language": "python"
            },
            "cbd": {
                "name": "CBD Model",
                "type": "mortality",
                "language": "python"
            },
            "r-lee-carter": {
                "name": "Lee-Carter Model (R)",
                "type": "mortality",
                "language": "r"
            },
            "poor-model": {
                "name": "Random Walk Model",
                "type": "poor_performance",
                "language": "python"
            }
        }

    @staticmethod
    def load_hmd_data():
        """加载HMD死亡率数据（包含疫情年份）"""
        try:
            return pd.DataFrame({
                'year': [2018, 2019, 2020, 2021, 2022, 2023],
                'age': [65, 66, 67, 68, 69, 70],
                'mortality_rate': [0.015, 0.016, 0.025, 0.023, 0.020, 0.019]  # 2020年死亡率显著上升
            })
        except Exception as e:
            print(f"加载HMD数据失败: {str(e)}")
            return pd.DataFrame()

    @staticmethod
    def load_cdc_data():
        """加载CDC超额死亡率数据（包含疫情年份）"""
        try:
            return pd.DataFrame({
                'year': [2018, 2019, 2020, 2021, 2022, 2023],
                'excess_mortality': [0.02, 0.025, 0.15, 0.10, 0.06, 0.03]  # 2020-2022年超额死亡率激增
            })
        except Exception as e:
            print(f"加载CDC数据失败: {str(e)}")
            return pd.DataFrame()

    def test_data_loading(self):
        """测试数据加载功能（包含疫情数据）"""
        self.assertFalse(self.hmd_data.empty, "HMD数据加载失败")
        self.assertFalse(self.cdc_data.empty, "CDC数据加载失败")
        
        # 验证疫情年份数据存在
        self.assertIn(2020, self.hmd_data['year'].values, "缺少疫情年份数据")
        self.assertGreater(
            self.hmd_data[self.hmd_data['year'] == 2020]['mortality_rate'].values[0],
            0.02,
            "疫情年份死亡率数据异常"
        )
        
        print("✅ 数据加载测试通过（包含疫情数据）")

    def test_pandemic_impact_analysis(self):
        """测试疫情冲击分析功能"""
        # 计算基线死亡率（2018-2019平均）
        baseline = self.hmd_data[self.hmd_data['year'].isin([2018, 2019])]['mortality_rate'].mean()
        
        # 计算疫情冲击
        pandemic_impact = {}
        for year in [2020, 2021, 2022]:
            rate = self.hmd_data[self.hmd_data['year'] == year]['mortality_rate'].values[0]
            impact = (rate - baseline) / baseline
            pandemic_impact[year] = impact
            
            # 验证冲击幅度合理
            self.assertGreater(impact, 0.2, f"{year}年疫情冲击不足")
        
        # 验证2023年恢复情况
        rate_2023 = self.hmd_data[self.hmd_data['year'] == 2023]['mortality_rate'].values[0]
        impact_2023 = (rate_2023 - baseline) / baseline
        self.assertLess(impact_2023, 0.2, "2023年死亡率未恢复")
        
        print(f"✅ 疫情冲击分析测试通过: {pandemic_impact}")

    def test_mortality_analysis_with_pandemic(self):
        """测试包含疫情影响的死亡率分析"""
        for model_id, model_info in self.models.items():
            with self.subTest(model=model_id):
                # 运行模型分析
                results = self.run_analysis(model_id, self.hmd_data)
                
                # 验证结果结构
                self.assertIn('parameters', results, "缺少参数估计结果")
                self.assertIn('forecast', results, "缺少预测结果")
                self.assertIn('pandemic_impact', results, "缺少疫情冲击分析")
                
                # 验证模型处理疫情的能力
                if "lee-carter" in model_id:
                    # Lee-Carter模型应有疫情调整参数
                    self.assertIn('pandemic_adjustment', results['parameters'], "缺少疫情调整参数")
                    
                    # 验证疫情冲击幅度合理
                    self.assertGreater(
                        results['pandemic_impact']['2020'],
                        0.3,
                        "2020年疫情冲击分析不足"
                    )
                elif model_id == "poor-model":
                    # 糟糕模型不应有疫情调整
                    self.assertNotIn('pandemic_adjustment', results['parameters'], "糟糕模型不应有疫情调整")
                    
                    # 糟糕模型的预测应偏离实际
                    self.assertGreater(
                        abs(results['forecast'][0]['value'] - 0.021),
                        0.005,
                        "糟糕模型预测异常准确"
                    )
                
                print(f"✅ {model_info['name']} 疫情分析测试通过")

    def test_r_vs_python_comparison(self):
        """测试R和Python模型实现的等效性"""
        # 获取Python实现的Lee-Carter结果
        py_results = self.run_analysis("lee-carter", self.hmd_data)
        
        # 获取R实现的Lee-Carter结果
        r_results = self.run_analysis("r-lee-carter", self.hmd_data)
        
        # 比较关键参数
        tolerance = 0.01  # 允许1%的差异
        for param in ['alpha', 'beta', 'kappa']:
            py_val = py_results['parameters'][param]['value']
            r_val = r_results['parameters'][param]['value']
            diff = abs(py_val - r_val) / py_val
            
            self.assertLess(
                diff,
                tolerance,
                f"参数 {param} 差异过大: Python={py_val:.4f}, R={r_val:.4f}, diff={diff:.2%}"
            )
        
        # 比较预测值
        for i in range(len(py_results['forecast'])):
            py_forecast = py_results['forecast'][i]['value']
            r_forecast = r_results['forecast'][i]['value']
            diff = abs(py_forecast - r_forecast) / py_forecast
            
            self.assertLess(
                diff,
                tolerance,
                f"预测 {i} 差异过大: Python={py_forecast:.4f}, R={r_forecast:.4f}, diff={diff:.2%}"
            )
        
        print("✅ R/Python模型等效性测试通过")

    def run_analysis(self, model_id, data):
        """模拟运行精算分析（包含疫情调整）"""
        # 实际项目中会调用后端API
        # 这里简化为模拟实现
        
        if model_id == "lee-carter":
            return {
                "model": "Lee-Carter",
                "parameters": {
                    "alpha": {"value": 0.05, "std_err": 0.002},
                    "beta": {"value": 0.12, "std_err": 0.005},
                    "kappa": {"value": -0.8, "std_err": 0.03},
                    "pandemic_adjustment": {"value": 0.35, "std_err": 0.05}
                },
                "forecast": [
                    {"year": 2024, "value": 0.021, "lower": 0.018, "upper": 0.024},
                    {"year": 2025, "value": 0.020, "lower": 0.017, "upper": 0.023}
                ],
                "pandemic_impact": {
                    "2020": 0.42,
                    "2021": 0.30,
                    "2022": 0.15
                },
                "diagnostics": {
                    "aic": 243.2,
                    "bic": 251.5,
                    "residual_autocorr": 0.08
                }
            }
        elif model_id == "r-lee-carter":
            # R实现 - 与Python略有差异
            return {
                "model": "Lee-Carter (R)",
                "parameters": {
                    "alpha": {"value": 0.0502, "std_err": 0.0021},
                    "beta": {"value": 0.121, "std_err": 0.0052},
                    "kappa": {"value": -0.799, "std_err": 0.031},
                    "pandemic_adjustment": {"value": 0.352, "std_err": 0.051}
                },
                "forecast": [
                    {"year": 2024, "value": 0.0211, "lower": 0.0182, "upper": 0.0241},
                    {"year": 2025, "value": 0.0202, "lower": 0.0173, "upper": 0.0232}
                ],
                "pandemic_impact": {
                    "2020": 0.421,
                    "2021": 0.302,
                    "2022": 0.151
                },
                "diagnostics": {
                    "aic": 243.5,
                    "bic": 251.8,
                    "residual_autocorr": 0.079
                }
            }
        elif model_id == "cbd":
            return {
                "model": "CBD",
                "parameters": {
                    "kappa1": {"value": -0.7, "std_err": 0.04},
                    "kappa2": {"value": 0.15, "std_err": 0.008},
                    "pandemic_adjustment": {"value": 0.32, "std_err": 0.06}
                },
                "forecast": [
                    {"year": 2024, "value": 0.022, "lower": 0.019, "upper": 0.025},
                    {"year": 2025, "value": 0.021, "lower": 0.018, "upper": 0.024}
                ],
                "pandemic_impact": {
                    "2020": 0.40,
                    "2021": 0.28,
                    "2022": 0.14
                },
                "diagnostics": {
                    "aic": 248.7,
                    "bic": 256.2,
                    "residual_autocorr": 0.10
                }
            }
        else:  # poor-model
            return {
                "model": "Random Walk",
                "parameters": {
                    "drift": {"value": 0.001, "std_err": 0.0005}
                },
                "forecast": [
                    {"year": 2024, "value": 0.025, "lower": 0.020, "upper": 0.030},
                    {"year": 2025, "value": 0.026, "lower": 0.021, "upper": 0.031}
                ],
                "pandemic_impact": {
                    "2020": 0.10,  # 严重低估疫情冲击
                    "2021": 0.08,
                    "2022": 0.05
                },
                "diagnostics": {
                    "aic": 1200.5,
                    "bic": 1205.3,
                    "residual_autocorr": 0.85
                }
            }

    def test_comparison_analysis(self):
        """测试对比分析功能（包含疫情处理能力评估）"""
        # 运行不同模型的分析
        results = {}
        for model_id in self.models:
            results[model_id] = self.run_analysis(model_id, self.hmd_data)
        
        # 执行对比分析
        comparison_report = self.run_comparison(results)
        
        # 验证对比报告
        self.assertIn('summary', comparison_report, "对比报告缺少摘要")
        self.assertIn('pandemic_performance', comparison_report, "对比报告缺少疫情表现评估")
        
        # 验证模型排名
        model_ranking = comparison_report['summary']['model_ranking']
        self.assertEqual(model_ranking[0]['model_id'], "lee-carter", "模型排名异常")
        self.assertEqual(model_ranking[1]['model_id'], "r-lee-carter", "R模型应排名第二")
        self.assertEqual(model_ranking[-1]['model_id'], "poor-model", "糟糕模型应排名最后")
        
        # 验证疫情表现评估
        pandemic_scores = comparison_report['pandemic_performance']
        self.assertLess(
            pandemic_scores["lee-carter"]["score"],
            pandemic_scores["poor-model"]["score"],
            "优质模型疫情评分应更低"
        )
        self.assertGreater(
            pandemic_scores["poor-model"]["error_2020"],
            0.2,
            "糟糕模型应高估疫情误差"
        )
        
        print("✅ 对比分析测试通过（包含疫情评估）")

    def run_comparison(self, results):
        """模拟运行对比分析（包含疫情表现评估）"""
        # 计算模型评分 (越低越好)
        model_scores = []
        pandemic_performance = {}
        
        for model_id, result in results.items():
            # 基本模型评分
            score = result['diagnostics']['aic'] + 100 * abs(result['diagnostics']['residual_autocorr'])
            
            # 疫情表现评估
            actual_2020 = self.hmd_data[self.hmd_data['year'] == 2020]['mortality_rate'].values[0]
            predicted_2020 = 0.016 * (1 + result['pandemic_impact']['2020'])  # 基线为2019年
            error_2020 = abs(actual_2020 - predicted_2020) / actual_2020
            
            pandemic_score = error_2020 * 1000
            
            model_scores.append({
                "model_id": model_id,
                "model_name": self.models[model_id]["name"],
                "score": score,
                "pandemic_score": pandemic_score,
                "aic": result['diagnostics']['aic'],
                "residual_autocorr": result['diagnostics']['residual_autocorr'],
                "error_2020": error_2020
            })
            
            pandemic_performance[model_id] = {
                "score": pandemic_score,
                "error_2020": error_2020,
                "impact_strength": result['pandemic_impact']['2020']
            }
        
        # 按综合评分排序
        model_scores.sort(key=lambda x: x['score'] + x['pandemic_score'])
        
        return {
            "summary": {
                "model_ranking": model_scores,
                "best_model": model_scores[0]['model_id'],
                "worst_model": model_scores[-1]['model_id']
            },
            "pandemic_performance": pandemic_performance,
            "visualizations": {
                "pandemic_impact_comparison": [
                    {"model": self.models[model_id]["name"], "impact": result['pandemic_impact']['2020']}
                    for model_id, result in results.items()
                ]
            }
        }

if __name__ == '__main__':
    # 运行测试
    suite = unittest.TestLoader().loadTestsFromTestCase(ActuarialPlatformTest)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 生成测试报告
    report = {
        "tests_run": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "success": result.wasSuccessful()
    }
    
    # 保存测试报告
    with open("test_report.json", "w") as f:
        json.dump(report, f, indent=2)
    
    print("\n测试报告已保存至 test_report.json")
