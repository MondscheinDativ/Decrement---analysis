import os
import pandas as pd
import requests
import io
from datetime import datetime

# CDC数据API端点
CDC_URL = "https://data.cdc.gov/resource/9bhg-hcku.csv"

def fetch_cdc_data():
    # 尝试获取API令牌（如果有）
    api_token = os.getenv("CDC_API_TOKEN", "")
    params = {"$limit": 5000}
    
    if api_token:
        params["$$app_token"] = api_token

    # 获取数据
    try:
        print("正在请求CDC数据...")
        response = requests.get(CDC_URL, params=params, timeout=30)
        response.raise_for_status()  # 检查HTTP状态码
        
        # 验证响应内容类型
        if 'csv' not in response.headers.get('Content-Type', ''):
            raise ValueError(f"Unexpected response type: {response.headers.get('Content-Type')}")
            
        df = pd.read_csv(io.StringIO(response.text))
        print(f"成功获取 {len(df)} 条记录")
        
    except requests.exceptions.RequestException as e:
        print(f"网络请求失败: {str(e)}")
        raise
    except Exception as e:
        print(f"数据处理失败: {str(e)}")
        raise

    # 确保日期列是datetime类型
    if 'start_date' in df.columns:
        df['start_date'] = pd.to_datetime(df['start_date'])
    else:
        raise ValueError("数据中缺少 start_date 列")

    # 筛选核心数据
    filtered_df = df[
        (df['start_date'] >= '2020-01-01') &
        (df['start_date'] <= '2023-12-31') &
        (df['age_group'].isin(['20-24 years', '25-29 years', '30-34 years', 
                              '60-64 years', '80-84 years']))
    ]

    # 检查筛选后是否有数据
    if filtered_df.empty:
        print("警告: 筛选后没有匹配的数据!")
    
    # 创建数据目录（使用绝对路径）
    data_dir = os.path.join(os.getcwd(), 'data')
    os.makedirs(data_dir, exist_ok=True)
    
    # 保存为CSV
    csv_path = os.path.join(data_dir, 'cdc_excess_mortality_2020-2023.csv')
    filtered_df.to_csv(csv_path, index=False)
    print(f"数据已保存至: {csv_path}")

    # 生成摘要
    if not filtered_df.empty:
        summary = filtered_df.groupby('age_group').agg({
            'covid_19_deaths': 'sum',
            'total_deaths': 'sum',
            'pneumonia_deaths': 'sum'
        }).reset_index()
        
        summary_path = os.path.join(data_dir, 'cdc_summary.csv')
        summary.to_csv(summary_path, index=False)
        print(f"摘要已保存至: {summary_path}")
    else:
        print("由于没有数据，跳过摘要生成")

    print("CDC数据获取流程完成")

if __name__ == "__main__":
    fetch_cdc_data()
