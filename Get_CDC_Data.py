import pandas as pd
import requests
from io import StringIO
import os

def fetch_cdc_data(country, start_year=2015, end_year=2023):
    if country == 'USA':
        base_url = "https://data.cdc.gov/api/views/xkkf-xrst/rows.csv?accessType=DOWNLOAD"
    elif country == 'UK':
        base_url = "https://api.ons.gov.uk/dataset/vsob/editions/time-series/versions/1.csv"
    else:
        raise ValueError("Only supports USA and UK")

    all_data = []
    for year in range(start_year, end_year + 1):
        try:
            response = requests.get(base_url)
            if response.status_code == 200:
                data = pd.read_csv(StringIO(response.text))
                data['year'] = year
                data['country'] = country
                all_data.append(data)
            else:
                print(f"Failed to get {country} {year} data, status code: {response.status_code}")
        except Exception as e:
            print(f"Error getting {country} {year} data: {str(e)}")

    if all_data:
        combined_data = pd.concat(all_data, ignore_index=True)
        return combined_data
    else:
        return None

usa_data = fetch_cdc_data('USA')
uk_data = fetch_cdc_data('UK')

if usa_data is not None:
    usa_data.to_csv('cdc_usa_excess_mortality.csv', index=False)
if uk_data is not None:
    uk_data.to_csv('cdc_uk_excess_mortality.csv', index=False)
