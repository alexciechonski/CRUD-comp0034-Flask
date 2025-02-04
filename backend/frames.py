"""
This script provides the Frames class, which loads and preprocesses COVID-19 restriction
datasets for further database operations. The class converts CSV data into DataFrames
structured for efficient database insertion.

Classes:
    - Frames: Loads daily, weekly, and summary datasets and provides methods to
      retrieve processed DataFrames for dates, weeks, restrictions, sources, and
      various restriction summaries.
"""
import pandas as pd
import sqlite3
from typing import Any
from collections import OrderedDict
import json
class Frames:
    """
    Loads and processes COVID-19 restriction data from daily, weekly, and summary CSV files.

    Attributes:
        daily (pd.DataFrame): DataFrame containing daily restriction data.
        weekly (pd.DataFrame): DataFrame containing weekly restriction data.
        summary (pd.DataFrame): DataFrame containing summary restriction data.
        dates_map (dict): Maps dates to unique IDs for the daily dataset.
        weeks_map (dict): Maps week start dates to unique IDs for the weekly dataset.
        restrs_map (dict): Maps restriction types to unique IDs.
        sources_map (dict): Maps source names to unique IDs.
    """
    def __init__(self, daily_path: str, weekly_path: str, summary_path: str) -> None:
        """
        Initializes the Frames class by loading and processing the daily, weekly,
        and summary CSV datasets.

        Parameters:
            daily_path (str): Path to the daily dataset CSV file.
            weekly_path (str): Path to the weekly dataset CSV file.
            summary_path (str): Path to the summary dataset CSV file.
        """
        self.daily = pd.read_csv(daily_path)
        self.weekly = pd.read_csv(weekly_path)
        self.summary =  pd.read_csv(summary_path).dropna()
        self.dates_map = {date: idx for idx, date in enumerate(self.daily['date'].tolist())}
        self.weeks_map = {
            week_start: idx for idx, week_start in enumerate(self.weekly['week_start'].tolist())
            }
        self.restrs_map = {restr: i for i, restr in enumerate(self.summary.columns.tolist()[3:])}
        self.sources_map = {src: i for i, src in enumerate(OrderedDict.fromkeys(self.summary['source']))}

    def get_date_df(self) -> pd.DataFrame:
        """
        Retrieves a DataFrame mapping each unique date to a date ID.

        Returns:
            pd.DataFrame: DataFrame with columns 'date_id' and 'date'.
        """
        return pd.DataFrame(list(self.dates_map.items()), columns=["date", "date_id"])

    def get_week_df(self)-> pd.DataFrame:
        """
        Retrieves a DataFrame mapping each unique week start date to a week ID.

        Returns:
            pd.DataFrame: DataFrame with columns 'week_id' and 'week_start'.
        """
        return pd.DataFrame(list(self.weeks_map.items()), columns=["week_start", "week_id"])

    def get_restriction_df(self) -> pd.DataFrame:
        """
        Retrieves a DataFrame mapping each restriction type to a unique ID.

        Returns:
            pd.DataFrame: DataFrame with columns 'restriction' and 'id'.
        """
        return pd.DataFrame(list(self.restrs_map.items()), columns=['restriction', 'restriction_id'])

    def get_source_df(self) -> pd.DataFrame:
        """
        Retrieves a DataFrame mapping each source name to a unique ID.

        Returns:
            pd.DataFrame: DataFrame with columns 'source', 'name', and 'id'.
        """
        df = pd.DataFrame(list(self.sources_map.items()), columns=['source', 'source_id'])
        df['name'] = self.summary['restriction']
        return df

    def get_summary_restriction_df(self) -> pd.DataFrame:
        """
        Retrieves a DataFrame summarizing restrictions with date, source, and restriction IDs.

        Returns:
            pd.DataFrame: DataFrame with columns:
                'date_id',
                'source_id',
                'restriction_id',
                'in_place'.
        """
        dates_lst = self.summary['date'].tolist()
        sources_lst = self.summary['source'].tolist()
        source_ids = [self.sources_map[src] for src in sources_lst]
        res = []
        for i, date in enumerate(dates_lst):
            for restr in sorted(self.restrs_map.keys()):
                res.append(
                    {
                        'date_id':self.dates_map[date],
                        'source_id':source_ids[i],
                        'restriction_id':self.restrs_map[restr],
                        'in_place': int(self.summary[restr][i])
                    }
                )
        return pd.DataFrame(res)

    def get_daily_restriction_df(self) -> pd.DataFrame:
        """
        Retrieves a DataFrame of daily restrictions with date and restriction IDs.

        Returns:
            pd.DataFrame: DataFrame with columns 'date_id', 'restriction_id', and 'in_place'.
        """
        dates_lst = self.daily['date'].tolist()
        res = []
        for i, date in enumerate(dates_lst):
            for restr in self.restrs_map.keys():
                res.append(
                    {
                        'date_id':self.dates_map[date],
                        'restriction_id':self.restrs_map[restr],
                        'in_place': int(self.daily[restr][i])
                    }
                    )
        return pd.DataFrame(res)

    def get_weekly_restriction_df(self) -> pd.DataFrame:
        """
        Retrieves a DataFrame of weekly restrictions with week start date and restriction IDs.

        Returns:
            pd.DataFrame: DataFrame with columns 'week_id', 'restriction_id', and 'in_place'.
        """
        weeks_lst = self.weekly['week_start'].tolist()
        res = []
        for i, week in enumerate(weeks_lst):
            for restr in self.restrs_map.keys():
                res.append(
                    {
                        'week_id':self.weeks_map[week],
                        'restriction_id':self.restrs_map[restr],
                        'in_place': int(self.weekly[restr][i])
                    }
                )
        return pd.DataFrame(res)

class DatabaseManager:
    """
    Manages database operations such as creating tables, inserting data,
    and retrieving information about tables and fields.

    Attributes:
        _db (str): Path to the SQLite database.
    """
    def __init__(self, db_path: str) -> None:
        """
        Initializes the DatabaseManager with the path to the database.

        Parameters:
            db_path (str): Path to the SQLite database file.
        """
        self._db = db_path

    def show_tables(self) -> None:
        """
        Connects to an SQLite database and prints all table names.
        """
        with sqlite3.connect(self._db) as conn:
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = cursor.fetchall()
                if tables:
                    return [t[0] for t in tables]
                else:
                    print("No tables found in the database.")
            except sqlite3.Error as err:
                print(f"An error occurred: {err}")

    def read_table_fields(self, table: str) -> None:
        """
        Connects to an SQLite database and prints all column names for a given table.

        Parameters:
            table: The name of the table to retrieve the fields from.
        """
        with sqlite3.connect(self._db) as conn:
            try:
                cursor = conn.cursor()
                cursor.execute(f"PRAGMA table_info({table});")
                columns = cursor.fetchall()
                if columns:
                    print(f"Fields in the table '{table}':")
                    for column in columns:
                        print(f"- {column[1]} ({column[2]})")  # column[1] name, column[2] type
                else:
                    print(f"No fields found or table '{table}' does not exist.")
            except sqlite3.Error as err:
                print(f"An error occurred: {err}")

    def read_table_vals(self, table: str) -> None:
        """
        Connects to an SQLite database and prints all the values in a given table.

        Parameters:
            table: The name of the table to retrieve the values from.
        """
        with sqlite3.connect(self._db) as conn:
            try:
                cursor = conn.cursor()
                cursor.execute(f"SELECT * FROM {table}")
                rows = cursor.fetchall()
                column_names = [description[0] for description in cursor.description]
                if rows:
                    print(f"Values in the table '{table}':")
                    print(f"{' | '.join(column_names)}")
                    for row in rows:
                        print(row)
                else:
                    print(f"The table '{table}' is empty or does not exist.")
            except sqlite3.Error as err:
                print(f"An error occurred: {err}")

    def delete_table(self, table_name: str) -> None:
        """
        Deletes a specified table from the database.

        Parameters:
            table_name (str): The name of the table to delete.
        """
        with sqlite3.connect(self._db) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(f"DROP TABLE IF EXISTS {table_name};")
                conn.commit()
                print(f"Table '{table_name}' has been deleted from the database '{self._db}'.")
            except sqlite3.DatabaseError as db_err:
                print(f"Database error occurred: {db_err}")

    def insert_data(self, table_name: str, data: list[tuple[Any, ...]]) -> None:
        """
        Inserts data into an SQLite table.

        Parameters:
        - table_name (str): Name of the table to insert data into.
        - data (list of tuples): List of tuples, each tuple represents a row of data.
                                Example: [(1, '2023-01-01'), (2, '2023-01-02')]
        """
        with sqlite3.connect(self._db) as conn:
            cursor = conn.cursor()
            placeholders = ', '.join(['?' for _ in data[0]])
            insert_sql = f"INSERT INTO {table_name} VALUES ({placeholders})"

            try:
                for row in data:
                    cursor.execute(insert_sql, row)
                print(f"Inserted {len(data)} rows into '{table_name}' successfully.")
            except sqlite3.Error as e:
                print(f"An error occurred: {e}")
            finally:
                conn.commit()

    def create_table(self, table_name: str, cols_dict: dict[str, str]) -> None:
        """
        Creates a table in the database with specified columns.

        Parameters:
            table_name (str): Name of the table to create.
            cols_dict (dict): Column names as keys and data types as values.
        """
        with sqlite3.connect(self._db) as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA foreign_keys = ON;")
            cols_str = f"({', '.join([f'{col_name} {constraint.upper()}' for col_name, constraint in cols_dict.items()])})"
            query = f"CREATE TABLE {table_name} {cols_str}"
            try:
                cursor.execute(query)
                print(f"Table '{table_name}' created successfully.")
            except sqlite3.Error as err:
                print(f"An error occurred: {err}")
            finally:
                conn.commit()

class Tables(Frames):
    """
    A subclass of Frames that manages creation of specific tables in the database
    and inserts data from various DataFrames.

    Attributes:
        db_path (str): Path to the SQLite database.
        daily_path (str): Path to the daily dataset CSV file.
        weekly_path (str): Path to the weekly dataset CSV file.
        summary_path (str): Path to the summary dataset CSV file.
    """
    def __init__(self, db_path: str, daily_path: str, weekly_path: str, summary_path: str) -> None:
        """
        Initializes the Tables class with database path and dataset paths.

        Parameters:
            db_path (str): Path to the SQLite database.
            daily_path (str): Path to the daily dataset CSV file.
            weekly_path (str): Path to the weekly dataset CSV file.
            summary_path (str): Path to the summary dataset CSV file.
        """
        super().__init__(daily_path=daily_path, weekly_path=weekly_path, summary_path=summary_path)
        self._db = db_path
        self.date_df = self.get_date_df()
        self.week_df = self.get_week_df()
        self.source_df = self.get_source_df()
        self.restriction_df = self.get_restriction_df()
        self.summary_restriction_df = self.get_summary_restriction_df()
        self.daily_restriction_df = self.get_daily_restriction_df()
        self.weekly_restriction_df = self.get_weekly_restriction_df()

    def t_date(self) -> None:
        """Creates and populates the 'Date' table with data from date_df."""
        manager = DatabaseManager(self._db)
        cols = {
            "date": "TEXT NOT NULL",
            "date_id":"INTEGER PRIMARY KEY",
        }
        manager.create_table("Date", cols)
        data = list(self.date_df.itertuples(index=False, name=None))
        manager.insert_data("Date", data)

    def t_week(self) -> None:
        """Creates and populates the 'Week' table with data from week_df."""
        manager = DatabaseManager(self._db)
        cols = {
            "week_start": "TEXT NOT NULL",
            "week_id":"INTEGER PRIMARY KEY",
        }
        manager.create_table("Week", cols)
        data = list(self.week_df.itertuples(index=False, name=None))
        manager.insert_data("Week", data)

    def t_restriction(self) -> None:
        """Creates and populates the 'Restriction' table with data from restriction_df."""
        manager = DatabaseManager(self._db)
        cols = {
            "restriction": "TEXT NOT NULL",
            "restriction_id":"INTEGER PRIMARY KEY",
        }
        manager.create_table("Restriction", cols)
        data = list(self.restriction_df.itertuples(index=False, name=None))
        manager.insert_data("Restriction", data)

    def t_source(self) -> None:
        """Creates and populates the 'Source' table with data from source_df."""
        manager = DatabaseManager(self._db)
        cols = {
            "source": "TEXT NOT NULL",
            "source_id":"INTEGER PRIMARY KEY",
            "name": "TEXT NOT NULL",
        }
        manager.create_table("Source", cols)
        data = list(self.source_df.itertuples(index=False, name=None))
        manager.insert_data("Source", data)

    def t_daily_restriction(self) -> None:
        """
        Creates and populates the 'DailyRestriction' table with data
        from daily_restriction_df.
        """
        manager = DatabaseManager(self._db)
        cols = {
            "date_id": "INTEGER NOT NULL REFERENCES Date(date_id)",
            "restriction_id": "INTEGER NOT NULL REFERENCES Restriction(restriction_id)",
            "in_place": "INTEGER NOT NULL CHECK (in_place <= 1 AND in_place >= 0)"
        }
        manager.create_table("DailyRestriction", cols)
        data = list(self.daily_restriction_df.itertuples(index=False, name=None))
        manager.insert_data("DailyRestriction", data)

    def t_weekly_restriction(self) -> None:
        """
        Creates and populates the 'WeeklyRestriction' table with data
        from weekly_restriction_df.
        """
        manager = DatabaseManager(self._db)
        cols = {
            "week_id": "INTEGER NOT NULL REFERENCES Week(week_id)",
            "restriction_id": "INTEGER NOT NULL REFERENCES Restriction(restriction_id)",
            "in_place": "INTEGER NOT NULL CHECK (in_place <= 1 AND in_place >= 0)"
        }
        manager.create_table("WeeklyRestriction", cols)
        data = list(self.weekly_restriction_df.itertuples(index=False, name=None))
        manager.insert_data("WeeklyRestriction", data)

    def t_summary_restriction(self) -> None:
        """
        Creates and populates the 'SummaryRestriction' table with data
        from summary_restriction_df.
        """
        manager = DatabaseManager(self._db)
        cols = {
            "date_id": "INTEGER NOT NULL REFERENCES Date(date_id)",
            "source_id": "INTEGER NOT NULL REFERENCES Source(source_id)",
            "restriction_id": "INTEGER NOT NULL REFERENCES Restriction(restriction_id)",
            "in_place": "INTEGER NOT NULL CHECK (in_place <= 1 AND in_place >= 0)"
        }
        manager.create_table("SummaryRestriction", cols)
        data = list(self.summary_restriction_df.itertuples(index=False, name=None))
        manager.insert_data("SummaryRestriction", data)

    def generate(self) -> None:
        """
        Calls methods to create and populate all tables in the database
        based on the data provided in the DataFrames.
        """
        self.t_date()
        self.t_week()
        self.t_restriction()
        self.t_source()
        self.t_daily_restriction()
        self.t_weekly_restriction()
        self.t_summary_restriction()

if __name__ == "__main__":
    daily_path = "coursework1/datasets/restrictions_daily.csv"
    weekly_path = "coursework1/datasets/restrictions_weekly.csv"
    summary_path = "coursework1/datasets/restrictions_summary.csv"
    frames = Frames(
        daily_path=daily_path,
        weekly_path=weekly_path,
        summary_path=summary_path
    )
    tables = Tables(
        db_path="coursework2/covid_copy.db",
        daily_path=daily_path,
        weekly_path=weekly_path,
        summary_path=summary_path
    )
    manager = DatabaseManager("coursework2/covid_copy.db")
    print(json.dumps(frames.sources_map, indent=2))
