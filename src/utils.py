"""
Utility Functions for Database Operations and Data Processing.

This module provides various utility functions for interacting with SQLite databases,
processing CSV files, formatting data, and handling AI-based responses.

Functions include:
- Querying and modifying databases.
- Creating and deleting tables.
- Fetching database metadata (e.g., table information, existing databases).
- Processing user inputs (e.g., formatting multiselect values, parsing CSV content).
- Interacting with AI models for generating responses.

Dependencies:
- `sqlite3`: For database operations.
- `pandas`: For CSV processing.
- `ollama`: AI model interaction (not covered in course material).
- `base64`, `io`, `os`: For file handling.
- `datetime`: For date formatting.
- `PATHS`, `NON_GRAPHABLE`, `BASE_PATH`: Configuration constants.
"""
import io
import os
import base64
import sqlite3
from typing import Optional, Any
from datetime import datetime
import pandas as pd
import ollama # ollama has not been covered in the couse: https://github.com/ollama/ollama
from src.config import PATHS, NON_GRAPHABLE, BASE_PATH

def query_db(query: str, db_path: str, param: tuple = ()) -> Optional[list[tuple[Any, ...]]]:
    """
    Executes a SQL query on a specified SQLite database.

    Args:
        query (str): The SQL query to execute.
        db_path (str): Path to the SQLite database.
        param (tuple, optional): Parameters for parameterized queries. Defaults to ().

    Returns:
        Optional[list[tuple[Any, ...]]]: Query results as a list of tuples (if applicable).
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
                # print("SELECT query executed successfully.")
                return results
            else:
                conn.commit()
                # print("Query executed successfully")
        except sqlite3.IntegrityError as int_err:
            raise sqlite3.IntegrityError("Database query failed") from int_err
        except sqlite3.DatabaseError as db_err:
            raise sqlite3.DatabaseError("Database query failed") from db_err

def create_table(
    db_path: str,
    table_name: str,
    cols_dict: dict[str, str],
    foreign_keys: list[str] = None
    ) -> None:
    """
    Creates a new table in the specified SQLite database.

    Args:
        db_path (str): Path to the SQLite database.
        table_name (str): Name of the table to create.
        cols_dict (dict[str, str]): Column names and their data types.
        foreign_keys (list[str], optional): Foreign key constraints. Defaults to None.
    """
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON;")
        cols_str = f"""
                    ({', '.join([f'{col_name} {constraint.upper()}' for col_name, constraint in cols_dict.items()])})
                    """
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

def delete_table(db_name, table_name: str) -> None:
    """
    Deletes a table from the specified SQLite database.

    Args:
        db_name (str): Name of the database (key from PATHS).
        table_name (str): Name of the table to delete.
    """
    with sqlite3.connect(PATHS[db_name]) as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(f"DROP TABLE IF EXISTS {table_name};")
            conn.commit()
            print(f"Table '{table_name}' has been deleted from the database.")
        except sqlite3.DatabaseError as db_err:
            print(f"Database error occurred: {db_err}")

def get_table_info(table, db_path):
    """
    Retrieves metadata about a table in the database.

    Args:
        table (str): Name of the table.
        db_path (str): Path to the SQLite database.

    Returns:
        list[tuple]: Table metadata (column names, data types, constraints).
    """
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
    Retrieves a list of tables in the specified database.

    Args:
        db_name (str): Name of the database (key from PATHS).

    Returns:
        list[str]: List of table names.
    """
    tables = query_db("SELECT name FROM sqlite_master WHERE type='table';", PATHS[db_name])
    return [row[0] for row in tables or []]

def table_not_empty(db_name: str, table_name: str) -> bool:
    """
    Checks whether a table contains any data.

    Args:
        db_name (str): Name of the database.
        table_name (str): Name of the table.

    Returns:
        bool: True if the table has data, False otherwise.
    """
    query = f"SELECT COUNT(*) FROM {table_name};"
    with sqlite3.connect(PATHS[db_name]) as conn:
        cursor = conn.cursor()
        cursor.execute(query)
        row_count = cursor.fetchone()[0]
    return row_count > 0

def process_multiselect(selections):
    """
    Converts a list of user-selected restriction names into lowercase with underscores.

    Args:
        selections (list[str]): List of selected restriction names.

    Returns:
        list[str]: Processed names in lowercase with underscores.
    """
    return [sel.replace(" ", "_").lower() for sel in selections]

def convert_to_date(date_str):
    """
    Converts a date string from "MM/YYYY" format to "YYYY-MM-DD".

    Args:
        date_str (str): Date string in "MM/YYYY" format.

    Returns:
        str: Reformatted date string in "YYYY-MM-DD" format.
    """
    return datetime.strptime(date_str, '%m/%Y').strftime('%Y-%m-%d')

def get_databases():
    """
    Retrieves all available database files except `graph.db`.

    Returns:
        list[dict[str, str]]: List of dictionaries containing database labels and values.
    """
    data_folder = BASE_PATH
    files = [
        file for file in os.listdir(data_folder) if os.path.isfile(os.path.join(data_folder, file))
        ]

    if "graph.db" in files:
        files.remove("graph.db")  # Avoid KeyError if "graph.db" is missing

    return [{'label': db, 'value': db} for db in files]

def parse_csv_contents(contents):
    """
    Parses and decodes a CSV file from Base64 format.

    Args:
        contents (str): Base64-encoded CSV file contents.

    Returns:
        tuple[list[tuple], pd.DataFrame]: Parsed data as a list of tuples and a DataFrame.
    """
    _, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    try:
        contents_df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
        return [tuple(row) for row in contents_df.itertuples(index=False)], contents_df
    except ValueError as val_err:
        print('THERE WAS AN ERROR PROCESSING THE CSV', val_err)
        return

def dynamic_name_id():
    """
    Retrieves a mapping of graph names to their corresponding IDs.

    Returns:
        dict[str, int]: Dictionary mapping graph names to their IDs.
    """
    with sqlite3.connect(PATHS["graph.db"]) as conn:
        res = {}
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Graphs;")
        data = cursor.fetchall()
        for graph_id, name in data:
            res[name] = graph_id
        return res

def select_graphable_tables(tables):
    """
    Filters out non-graphable tables from a given list.

    Args:
        tables (list[str]): List of table names.

    Returns:
        list[str]: List of graphable table names.
    """
    non_graphable = set(NON_GRAPHABLE)
    return [table for table in tables if table not in non_graphable]

def get_resp(prompt):
    """
    Generates a response from an AI model using the `ollama` library.

    Args:
        prompt (str): Input prompt for the AI model.

    Returns:
        str: AI-generated response.
    """
    response = ollama.chat(model="tinyllama", messages=[{"role": "user", "content": prompt}])
    return response['message']['content'] if 'message' in response else "No response"

if __name__ == "__main__":
    # print(select_graphable_tables(show_tables("covid.db")))
    print(show_tables("custom.db"))
