import os
import pandas as pd
import requests
import io

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
        response = requests.get(CDC_URL, params=params, timeout=30)
        response.raise_for_status()
        df = pd.read_csv(io.StringIO(response.text))
    except Exception as e:
        print(f"CDC数据获取失败: {str(e)}")
        raise

    # 筛选核心数据
    # 确保日期列转为 datetime 类型再筛选
    df['start_date'] = pd.to_datetime(df['start_date'])
    filtered_df = df[
        (df['start_date'] >= '2020-01-01') &
        (df['start_date'] <= '2023-12-31') &
        (df['age_group'].isin(['20-24 years', '25-29 years', '30-34 years', 
                              '60-64 years', '80-84 years']))
    ]

    # 创建数据目录（根目录的data文件夹）
    data_dir = "data"
    os.makedirs(data_dir, exist_ok=True)
    
    # 保存为CSV
    data_file = os.path.join(data_dir, "cdc_excess_mortality_2020-2023.csv")
    filtered_df.to_csv(data_file, index=False)
    
    # 生成摘要
    summary = filtered_df.groupby('age_group').agg({
        'covid_19_deaths': 'sum',
        'total_deaths': 'sum',
        'pneumonia_deaths': 'sum'
    }).reset_index()
    
    summary_file = os.path.join(data_dir, "cdc_summary.csv")
    summary.to_csv(summary_file, index=False)
    
    # 打印文件路径
    print("\n===== 数据文件已生成 =====")
    print(f"1. 详细数据文件路径: {os.path.abspath(data_file)}")
    print(f"2. 摘要数据文件路径: {os.path.abspath(summary_file)}")
    print("==========================")

if __name__ == "__main__":
    fetch_cdc_data()
