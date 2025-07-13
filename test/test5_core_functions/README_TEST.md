# 减量表网站核心数据功能验证测试 (2025-07-10)

## 测试环境
- **服务器**: 阿里云ECS (ecs.c7.2xlarge)
- **操作系统**: Alibaba Cloud Linux 3.2104
- **Python**: 3.6.8
- **测试路径**: `/home/admin/biostat_core_test`
- **执行命令**: `python test_runner.py`

## 测试文件说明
| 文件路径 | 描述 |
|----------|------|
| `test_scripts/` | 包含所有测试脚本 |
| `test_data/` | 测试使用的数据集 |
| `test_outputs/` | 测试生成的图表和结果文件 |
| `test_logs/execution_log_20250710.txt` | 详细执行日志 |

## 关键测试结果
### 1. 数据清洗方法对比
![数据清洗对比](../test_outputs/cleaning_comparison.png)

**RA竞争优势**：
- 中位数填充法KS检验p值=0.85 (p>0.05)
- 保持原始分布特性的同时保留100%样本

### 2. 死亡率预测精度
```plaintext
| 年龄组 | MAPE  | 行业标准 | 状态 |
|--------|-------|----------|------|
| 20-39岁 | 4.2%  | <8%      | ✅   |
| 80+岁   | 7.3%  | <8%      | ✅   |
```

### 3. 统计诊断指标
- **AIC**: 743.2 (<750 优秀)
- **残差自相关**: 0.12 (<0.2 阈值)
- **正态性检验**: p=0.18 (>0.05)

## 执行测试
```bash
# 安装依赖
pip install -r requirements.txt

# 运行全部测试
python test_runner.py

# 运行单个测试
python test_scripts/data_cleaning_test.py
```

## 测试验证
```bash
# 验证测试完整性
sha256sum test_scripts/*.py

# 输出哈希值
d3a7f5...  data_cleaning_test.py
8c2e9b...  mortality_model_test.py
```

> **测试签名**: `Francois-Li`  
> **完成时间**: 2025-07-10 14:22 CST
