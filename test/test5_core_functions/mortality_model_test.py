import pandas as pd
import numpy as np
from lifelines import LeeCarterFitter

def test_lee_carter_accuracy():
    """测试Lee-Carter模型预测精度"""
    # 生成模拟数据 (2000-2019)
    years = np.arange(2000, 2020)
    age_groups = ['20-39', '40-59', '60-79', '80+']
    data = pd.DataFrame({
        'year': np.tile(years, len(age_groups)),
        'age_group': np.repeat(age_groups, len(years)),
        'qx': np.random.exponential(0.01, len(years)*len(age_groups))
    })
    
    # 训练模型 (2000-2014)
    train = data[data['year'] <= 2014]
    lcf = LeeCarterFitter()
    lcf.fit(train, 'year', 'age_group', 'qx')
    
    # 预测 (2015-2019)
    forecast = lcf.predict(np.arange(2015, 2020))
    
    # 计算误差
    actual = data[data['year'] >= 2015].set_index(['year', 'age_group'])['qx']
    errors = (forecast - actual).abs()
    mape = (errors / actual).groupby('age_group').mean() * 100
    
    # 保存结果
    results = pd.DataFrame({
        'Age Group': age_groups,
        'MAPE': mape.values
    })
    results.to_csv('../test_outputs/mortality_mape.csv', index=False)
    return results
