import numpy as np
import pandas as pd
from scipy import stats

def generate_clinical_trial_data(n=1000):
    """生成符合生物统计特性的临床试验数据"""
    np.random.seed(1751996090)
    data = pd.DataFrame({
        'age': np.random.randint(18, 90, n),
        'gender': np.random.choice(['M', 'F'], n),
        'baseline_score': np.clip(np.random.normal(50, 10, n), 30, 70),
        'final_score': np.clip(np.random.normal(60, 12, n), 40, 80),
    })
    
    # 添加缺失值
    missing_mask = np.random.choice([True, False], n, p=[0.2, 0.8])
    data.loc[missing_mask, 'final_score'] = np.nan
    
    return data

def test_cleaning_methods():
    """测试三种缺失值处理方法"""
    data = generate_clinical_trial_data()
    original = data['final_score'].dropna()
    
    # 删除法
    deleted = data['final_score'].dropna()
    
    # 均值填充
    mean_filled = data['final_score'].fillna(data['final_score'].mean())
    
    # 中位数填充
    median_filled = data['final_score'].fillna(data['final_score'].median())
    
    # KS检验
    ks_deleted = stats.kstest(deleted, original).pvalue
    ks_mean = stats.kstest(mean_filled, original).pvalue
    ks_median = stats.kstest(median_filled, original).pvalue
    
    # 保存结果
    results = pd.DataFrame({
        'Method': ['Deletion', 'Mean Imputation', 'Median Imputation'],
        'Samples': [len(deleted), len(mean_filled), len(median_filled)],
        'KS_pvalue': [ks_deleted, ks_mean, ks_median],
        'Mean_Shift': [
            abs(deleted.mean() - original.mean()),
            abs(mean_filled.mean() - original.mean()),
            abs(median_filled.mean() - original.mean())
        ]
    })
    
    results.to_csv('../test_outputs/cleaning_results.csv', index=False)
    return results
