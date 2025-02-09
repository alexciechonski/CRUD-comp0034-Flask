from sklearn.linear_model import LinearRegression
import numpy as np
import pandas as pd
from datetime import datetime
from src.backend.data_server import DataServer
import matplotlib.pyplot as plt

class Model:
    def __init__(self, restrs) -> None:
        self.restrs = restrs 
        self.df = self.prepare()

    def prepare(self):
        server = DataServer("src/backend/data/covid.db", "src/backend/data/graph.db", "src/backend/data/mental_health.db")
        time_series_data = server.serve_time_series(self.restrs)
        mental_series_data = server.serve_mental_series()
        time_series_df = pd.DataFrame(time_series_data, columns=["date", "restr_value"])
        mental_series_df = pd.DataFrame(mental_series_data, columns=["date", "mental_value"])
        time_series_df['date'] = pd.to_datetime(time_series_df['date'])
        mental_series_df['date'] = pd.to_datetime(mental_series_df['date'])
        merged_df = pd.merge_asof(
            time_series_df.sort_values('date'),
            mental_series_df.sort_values('date'),
            on='date',
            direction='nearest'
        )
        merged_df.interpolate(method='linear', inplace=True)
        aggregated_df = merged_df.groupby('restr_value')['mental_value'].mean().reset_index()
        return aggregated_df

    def train_linear(self):
        df = self.df
        X_train = df[['restr_value']]
        y_train = df['mental_value']
        model = LinearRegression().fit(X_train, y_train)
        df['predicted_mental'] = model.predict(df[['restr_value']])
        return df

    @staticmethod
    def get_correlation(x, y):
        x = np.array(x)
        y = np.array(y)
        correlation = np.corrcoef(x, y)[0, 1]
        return correlation

if __name__ == "__main__":
    pass

