import sys
from datetime import datetime

# 设置随机种子确保可复现
SEED = 1751996090

def main():
    print(f"[{datetime.now()}] 开始生物统计核心测试")
    print(f"随机种子: {SEED}")
    
    try:
        # 导入测试模块
        from data_cleaning_test import test_cleaning
        from mortality_model_test import test_mortality
        
        # 执行测试
        print("\n=== 数据清洗测试 ===")
        cleaning_results = test_cleaning(SEED)
        
        print("\n=== 死亡率模型测试 ===")
        mortality_results = test_mortality(SEED)
        
        # 保存简化结果
        with open("test_outputs/test_summary.txt", "w") as f:
            f.write(f"测试时间: {datetime.now()}\n")
            f.write(f"数据清洗最佳方法: {cleaning_results['best_method']} (KS p值={cleaning_results['best_ks']:.2f})\n")
            f.write(f"高龄组(80+)预测MAPE: {mortality_results['elderly_mape']:.1f}%\n")
        
        print("\n=== 测试完成 ===")
        print(f"结果保存至 test_outputs/")
        print(f"详细说明见 output_limitations.md")
        
    except Exception as e:
        print(f"测试失败: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
