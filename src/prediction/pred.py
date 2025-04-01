"""
Module for predictive modeling using linear regression.

This module defines the `Model` class, which processes time series data,
trains a linear regression model, and calculates correlations between
restrictions and custom data.
"""
from sklearn.linear_model import LinearRegression
import numpy as np
import pandas as pd
from src.backend.data_server import DataServer
from src.utils import get_db_path

class Model:
    """
    A class for training predictive models based on restrictions and
    custom time series data.

    Attributes:
        restrs (list[str]): List of restrictions to include in the analysis.
        db_name (str): Name of the database containing custom data.
        table_name (str): Name of the table storing custom data.
    """
    def __init__(self, restrs: str, db_name: str, table_name: str) -> None:
        """
        Initializes the Model with restrictions, database name, and table name.

        Args:
            restrs (list[str]): List of restrictions to analyze.
            db_name (str): Database name containing custom data.
            table_name (str): Table name storing custom time series data.
        """
        self.restrs = restrs
        self.db_name = db_name
        self.table_name = table_name  # Preserve case sensitivity

    def prepare(self) -> pd.DataFrame:
        """
        Prepares and merges restriction and custom time series data.

        - Retrieves time series data from the DataServer.
        - Converts dates to datetime format.
        - Merges datasets based on the nearest date match.
        - Interpolates missing values and calculates mean per restriction level.

        Returns:
            pd.DataFrame: A DataFrame containing `restr_value` and `custom_value`.
        """
        server = DataServer('covid.db')
        try:
            # Always get restriction data from covid.db
            restriction_data = server.serve_time_series(self.restrs)
            print(f"Restriction data: {restriction_data[:5]}")  # Debug print
            
            # Get custom data from the specified database
            custom_data = server.serve_second_series(self.db_name, self.table_name)
            print(f"Custom data: {custom_data[:5]}")  # Debug print

            # Create DataFrame for restrictions
            time_series_df = pd.DataFrame(
                restriction_data, columns=["date", "total_restrictions"]
            ).rename(columns={"total_restrictions": "restr_value"}
            ).sort_values('date')

            # Create DataFrame for custom data
            second_series_df = pd.DataFrame(
                custom_data, columns=["date", "custom_value"]
            ).sort_values('date')

            time_series_df['date'] = pd.to_datetime(time_series_df['date'])
            second_series_df['date'] = pd.to_datetime(second_series_df['date'])
            
            # Merge the datasets based on nearest date match
            merged_df = pd.merge_asof(
                time_series_df, second_series_df, on='date', direction='nearest'
            ).interpolate(method='pad')

            # Group by restriction value and calculate mean of custom values
            return merged_df.groupby('restr_value', as_index=False)['custom_value'].mean()
        finally:
            server._db_session.close()

    def train_linear(self) -> pd.DataFrame:
        """
        Trains a linear regression model to predict custom values based on restriction values.

        Returns:
            pd.DataFrame: The DataFrame with predicted values added under the column `predicted`.
        """
        train_df = self.prepare()
        if train_df.empty:
            return train_df

        x_train = train_df[['restr_value']]
        y_train = train_df['custom_value']
        model = LinearRegression().fit(x_train, y_train)
        train_df['predicted'] = model.predict(train_df[['restr_value']])
        return train_df

    def get_correlation(self) -> float:
        """
        Computes the Pearson correlation coefficient between restriction values
        and custom values.

        Returns:
            float: Correlation coefficient (between -1 and 1).
        """
        data = self.prepare()
        x_vals = np.array(data['restr_value'].tolist())
        y_vals = np.array(data['custom_value'].tolist())
        correlation = np.corrcoef(x_vals, y_vals)[0, 1]
        return correlation

if __name__ == "__main__":
    m = Model([], "custom.db", "Deaths")
    print(m.get_correlation())
    print(m.prepare())
