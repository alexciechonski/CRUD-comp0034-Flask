import sqlite3
from typing import Optional, Any
import math
from datetime import datetime
import os
import json

def query_db(query: str, db_path: str, param: tuple = ()) -> Optional[list[tuple[Any, ...]]]:
    """
    Executes a query against the main database.

    Returns:
        list[tuple[Any, ...]]: Results of the query if it is a SELECT query.
    """
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        try:
            if param is not None:
                cursor.execute(query, param)
            else:
                cursor.execute(query)
            if query.strip().upper().startswith("SELECT"):
                results = cursor.fetchall()
                print("SELECT query executed successfully.")
                return results
            else:
                conn.commit()
                print("Query executed successfully")
        except sqlite3.IntegrityError as int_err:
            raise sqlite3.IntegrityError("Database query failed") from int_err
        except sqlite3.DatabaseError as db_err:
            raise sqlite3.DatabaseError("Database query failed") from db_err

def create_table(db_path: str, table_name: str, cols_dict: dict[str, str], foreign_keys: list[str] = None) -> None:
    """
    Creates a table in the database with specified columns.

    Parameters:
        table_name (str): Name of the table to create.
        cols_dict (dict): Column names as keys and data types as values.
    """
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON;")
        cols_str = f"({', '.join([f'{col_name} {constraint.upper()}' for col_name, constraint in cols_dict.items()])})"
        if foreign_keys:
            fk_str = ", " + ", ".join(foreign_keys)
        else:
            fk_str = ""
        query = f"CREATE TABLE {table_name} {cols_str}{fk_str}"
        try:
            cursor.execute(query)
            print(f"Table '{table_name}' created successfully.")
        except sqlite3.Error as err:
            print(f"An error occurred: {err}")
        finally:
            conn.commit()

def insert_data(db_path: str, table_name: str, data: list[tuple[Any, ...]]) -> None:
    """
    Inserts data into an SQLite table.

    Parameters:
    - table_name (str): Name of the table to insert data into.
    - data (list of tuples): List of tuples, each tuple represents a row of data.
                            Example: [(1, '2023-01-01'), (2, '2023-01-02')]
    """
    with sqlite3.connect(db_path) as conn:
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

def delete_table(db_name, table_name: str) -> None:
        """
        Deletes a specified table from the database.

        Parameters:
            table_name (str): The name of the table to delete.
        """
        with sqlite3.connect(f"src/backend/data/{db_name}") as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(f"DROP TABLE IF EXISTS {table_name};")
                conn.commit()
                print(f"Table '{table_name}' has been deleted from the database.")
            except sqlite3.DatabaseError as db_err:
                print(f"Database error occurred: {db_err}")

def get_table_info(table, db_path):
    with sqlite3.connect(db_path) as conn:
        try:
            cursor = conn.cursor()
            cursor.execute(f"PRAGMA table_info('{table}');")
            res = cursor.fetchall()
            return res
        except sqlite3.IntegrityError as int_err:
            raise sqlite3.IntegrityError("Database query failed") from int_err
        except sqlite3.DatabaseError as db_err:
            raise sqlite3.DatabaseError("Database query failed") from db_err

def show_tables(db_name) -> None:
    """
    Connects to an SQLite database and prints all table names.
    """
    with sqlite3.connect(f"src/backend/data/{db_name}") as conn:
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

def process_multiselect(selections):
    return [sel.replace(" ", "_").lower() for sel in selections]

def convert_to_date(date_str):
    return datetime.strptime(date_str, '%m/%Y').strftime('%Y-%m-%d')

def get_databases():
    data_folder = 'src/backend/data'
    files = [file for file in os.listdir(data_folder) if os.path.isfile(os.path.join(data_folder, file))]
    
    if "graph.db" in files:
        files.remove("graph.db")  # Avoid KeyError if "graph.db" is missing

    # Convert list of strings into list of dictionaries for Dash dropdown
    return [{'label': db, 'value': db} for db in files]


def save_to_json(path, data):
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

if __name__ == "__main__":
    print(show_tables("covid.db"))