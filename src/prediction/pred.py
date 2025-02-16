from sklearn.linear_model import LinearRegression
import numpy as np
import pandas as pd
from datetime import datetime
from src.backend.data_server import DataServer
import matplotlib.pyplot as plt

class Model:
    def __init__(self, restrs, db_name, table_name) -> None:
        self.restrs = restrs 
        self.db_name = db_name
        self.table_name = table_name

    def prepare(self):
        server = DataServer("src/backend/data/covid.db", "src/backend/data/graph.db", "src/backend/data/mental_health.db")
        time_series_data = server.serve_time_series(self.restrs)
        second_series_data = server.serve_second_series(self.db_name, self.table_name)
        time_series_df = pd.DataFrame(time_series_data, columns=["date", "restr_value"])
        second_series_df = pd.DataFrame(second_series_data, columns=["date", "mental_health_value"])
        time_series_df['date'] = pd.to_datetime(time_series_df['date'])
        second_series_df['date'] = pd.to_datetime(second_series_df['date'])
        merged_df = pd.merge_asof(
            time_series_df.sort_values('date'),
            second_series_df.sort_values('date'),
            on='date',
            direction='nearest'
        )
        merged_df.interpolate(method='linear', inplace=True)
        aggregated_df = merged_df.groupby('restr_value')['mental_health_value'].mean().reset_index()
        return aggregated_df

    def train_linear(self):
        df = self.prepare()
        X_train = df[['restr_value']]
        y_train = df['mental_health_value']
        model = LinearRegression().fit(X_train, y_train)
        df['predicted_mental'] = model.predict(df[['restr_value']])
        return df

    def get_correlation(self):
        data = self.prepare()
        x = np.array(data['restr_value'].tolist())
        y = np.array(data['mental_health_value'].tolist())
        correlation = np.corrcoef(x, y)[0, 1]
        return correlation

if __name__ == "__main__":
    m = Model([], "mental_health.db", "Deaths")
    print(m.get_correlation())

