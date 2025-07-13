import numpy as np
import pandas as pd
from scipy import stats

def test_cleaning(seed):
    np.random.seed(seed)
    
    # 生成模拟数据
    data = pd.DataFrame({
        'value': np.clip(np.random.normal(50, 10, 1000), 30, 70)
    })
    
    # 添加20%缺失值
    missing_mask = np.random.choice([True, False], 1000, p=[0.2, 0.8])
    data.loc[missing_mask, 'value'] = np.nan
    original = data['value'].dropna()
    
    # 测试三种方法
    methods = {
        '删除法': data['value'].dropna(),
        '均值填充': data['value'].fillna(data['value'].mean()),
        '中位数填充': data['value'].fillna(data['value'].median())
    }
    
    # 评估指标
    results = []
    for name, method_data in methods.items():
        ks_test = stats.kstest(method_data, original)
        mean_shift = abs(method_data.mean() - original.mean())
        
        results.append({
            'Method': name,
            'Samples': len(method_data),
            'KS_pvalue': ks_test.pvalue,
            'Mean_Shift': mean_shift
        })
    
    # 保存结果
    result_df = pd.DataFrame(results)
    result_df.to_csv("../test_outputs/cleaning_results.csv", index=False)
    
    # 找出最佳方法
    best_method = result_df.loc[result_df['KS_pvalue'].idxmax()]
    print(f"最佳方法: {best_method['Method']} (KS p值={best_method['KS_pvalue']:.2f})")
    
    return {
        'best_method': best_method['Method'],
        'best_ks': best_method['KS_pvalue']
    }
