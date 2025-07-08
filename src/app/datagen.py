import pandas as pd
import numpy as np

def generate_mortality_data(years=20, age_groups=100):
    data = []
    for year in range(2020, 2020+years):
        for age in range(1, age_groups+1):
            base_rate = 0.001 * np.exp(0.05*age)
            data.append({
                'year': year,
                'age': age,
                'mortality': base_rate * (1 + np.random.normal(0, 0.1))
            })
    return pd.DataFrame(data)

if __name__ == "__main__":
    df = generate_mortality_data()
    df.to_csv("backend/datasets/simulated_mortality.csv", index=False)
