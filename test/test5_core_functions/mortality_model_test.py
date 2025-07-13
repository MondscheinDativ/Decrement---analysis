import numpy as np
import pandas as pd

def test_mortality(seed):
    np.random.seed(seed)
    
    # 生成简化死亡率数据
    age_groups = ['20-39', '40-59', '60-79', '80+']
    data = []
    
    # 生成2000-2019年数据
    for year in range(2000, 2020):
        for age in age_groups:
            # 基础死亡率 + 年龄因子 + 随机波动
            base_qx = 0.01 if age == '20-39' else 0.02 if age == '40-59' else 0.05 if age == '60-79' else 0.1
            age_factor = 0.1 if age == '80+' else 0.05
            qx = base_qx + (year - 2000) * 0.001 + age_factor + np.random.normal(0, 0.002)
            
            data.append({
                'year': year,
                'age_group': age,
                'qx': max(qx, 0.001)  # 确保正值
            })
    
    df = pd.DataFrame(data)
    
    # 划分训练集(2000-2014)和测试集(2015-2019)
    train = df[df['year'] <= 2014]
    test = df[df['year'] >= 2015]
    
    # 简化预测模型：按年龄组和时间趋势预测
    predictions = []
    for age in age_groups:
        age_data = train[train['age_group'] == age]
        slope = (age_data['qx'].iloc[-1] - age_data['qx'].iloc[0]) / len(age_data)
        
        # 预测2015-2019
        for year in range(2015, 2020):
            last_value = age_data[age_data['year'] == 2014]['qx'].values[0]
            pred = last_value + slope * (year - 2014)
            actual = test[(test['year'] == year) & (test['age_group'] == age)]['qx'].values[0]
            
            predictions.append({
                'Age Group': age,
                'Year': year,
                'Predicted': pred,
                'Actual': actual,
                'Error': abs(pred - actual),
                'MAPE': abs(pred - actual) / actual * 100
            })
    
    # 计算各年龄组MAPE
    pred_df = pd.DataFrame(predictions)
    mape_results = pred_df.groupby('Age Group')['MAPE'].mean().reset_index()
    mape_results.to_csv("../test_outputs/mortality_mape.csv", index=False)
    
    # 高龄组结果
    elderly_mape = mape_results[mape_results['Age Group'] == '80+']['MAPE'].values[0]
    print(f"80+岁组MAPE: {elderly_mape:.1f}%")
    
    return {'elderly_mape': elderly_mape}
