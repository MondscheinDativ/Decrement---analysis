import pandas as pd

def verify_results():
    print("验证测试结果...")
    
    try:
        # 验证数据清洗结果
        cleaning = pd.read_csv("test_outputs/cleaning_results.csv")
        best_method = cleaning.loc[cleaning['KS_pvalue'].idxmax()]
        assert best_method['KS_pvalue'] > 0.05
        print(f"✅ 数据清洗验证通过: {best_method['Method']} (p={best_method['KS_pvalue']:.2f})")
        
        # 验证死亡率预测
        mortality = pd.read_csv("test_outputs/mortality_mape.csv")
        elderly = mortality[mortality['Age Group'] == '80+']
        assert elderly['MAPE'].values[0] < 8.0
        print(f"✅ 死亡率验证通过: 80+岁组MAPE={elderly['MAPE'].values[0]}%")
        
        print("所有核心测试验证通过!")
        
    except Exception as e:
        print(f"验证失败: {str(e)}")
        exit(1)

if __name__ == "__main__":
    verify_results()
