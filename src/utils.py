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
"""
import io
import os
import base64
import sqlite3
from typing import Optional, Any, List, Dict, Tuple
from datetime import datetime
import pandas as pd
import ollama # ollama has not been covered in the couse: https://github.com/ollama/ollama
from sqlalchemy import create_engine, inspect, MetaData, Table
from sqlalchemy.orm import sessionmaker
from src.config import PATHS, NON_GRAPHABLE, BASE_PATH
from src.backend.models import init_db, Base
import glob

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
                return results
            else:
                conn.commit()
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

def delete_table(db_name: str, table_name: str) -> None:
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

def get_table_info(table: str, db_path: str) -> List[Tuple]:
    """
    Get table schema information using SQLAlchemy.

    Args:
        table (str): Name of the table.
        db_path (str): Path to the database.

    Returns:
        List[Tuple]: List of column information tuples.
    """
    engine = create_engine(f'sqlite:///{db_path}')
    inspector = inspect(engine)
    
    try:
        columns = inspector.get_columns(table)
        result = []
        for i, col in enumerate(columns):
            result.append((
                i,  # cid
                col['name'],  # name
                col['type'].__str__(),  # type
                not col.get('nullable', True),  # notnull
                col.get('default', None),  # dflt_value
                col.get('primary_key', False)  # pk
            ))
        return result
    finally:
        engine.dispose()

def show_tables(database: str) -> List[str]:
    """
    Get list of tables in a database using SQLAlchemy.

    Args:
        database (str): Name of the database.

    Returns:
        List[str]: List of table names.
    """
    engine = create_engine(f'sqlite:///{PATHS[database]}')
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    engine.dispose()
    return tables

def table_not_empty(db_name: str, table: str) -> bool:
    """
    Check if a table has any rows using SQLAlchemy.

    Args:
        db_name (str): Name of the database.
        table (str): Name of the table.

    Returns:
        bool: True if table has rows, False otherwise.
    """
    engine = create_engine(f'sqlite:///{PATHS[db_name]}')
    metadata = MetaData()
    table_obj = Table(table, metadata, autoload_with=engine)
    
    session = sessionmaker(bind=engine)()
    try:
        result = session.query(table_obj).first() is not None
        return result
    finally:
        session.close()
        engine.dispose()

def process_multiselect(selections: List[str]) -> List[str]:
    """
    Converts a list of user-selected restriction names into lowercase with underscores.

    Args:
        selections (list[str]): List of selected restriction names.

    Returns:
        list[str]: Processed names in lowercase with underscores.
    """
    return [sel.replace(" ", "_").lower() for sel in selections]

def convert_to_date(date_str: str) -> str:
    """
    Convert various date formats to a standardized format.

    Args:
        date_str (str): Date string to convert.

    Returns:
        str: Standardized date string.
    """
    try:
        # Try parsing with various formats
        for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%Y/%m/%d']:
            try:
                return datetime.strptime(date_str, fmt).strftime('%Y-%m-%d')
            except ValueError:
                continue
        raise ValueError(f"Unable to parse date: {date_str}")
    except:
        return date_str

def get_databases() -> List[str]:
    """Get list of available databases
    
    Returns:
        List[str]: List of database names
    """
    db_files = glob.glob(os.path.join(BASE_PATH, '*.db'))
    return [os.path.basename(db) for db in db_files]

def get_database_path(database: str) -> str:
    """Get full path for a database
    
    Args:
        database (str): Name of the database
        
    Returns:
        str: Full path to the database file
    """
    return os.path.join(BASE_PATH, database)

def parse_csv_contents(contents) -> tuple[List[tuple], pd.DataFrame]:
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

def dynamic_name_id() -> List[tuple]:
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

def select_graphable_tables(database: str) -> List[str]:
    """
    Get list of tables that can be graphed using SQLAlchemy.

    Args:
        database (str): Name of the database.

    Returns:
        List[str]: List of table names that can be graphed.
    """
    tables = show_tables(database)
    engine = create_engine(f'sqlite:///{PATHS[database]}')
    inspector = inspect(engine)
    
    graphable = []
    for table in tables:
        columns = {col['name'] for col in inspector.get_columns(table)}
        if 'time' in columns and 'measured_value' in columns:
            graphable.append(table)
    
    engine.dispose()
    return graphable

def get_graphable_tables(database: str = None):
    """
    Get list of tables that can be graphed using SQLAlchemy.
    Excludes tables from graph.db and includes debug prints.

    Args:
        database (str, optional): Specific database to get graphable tables from.
                                If None, returns graphable tables from all databases.

    Returns:
        List[str]: List of table names that can be graphed.
    """
    res = []
    
    if database:
        # If a specific database is provided, only check that one
        if database != 'graph.db':
            try:
                tables = select_graphable_tables(database)
                res.extend(tables)
            except Exception as e:
                print(f"Error processing {database}: {str(e)}")  # Debug print
    else:
        # If no database specified, check all databases
        databases = get_databases()
        for db in databases:
            if db not in ['graph.db']:  # Check the 'value' key and exclude graph.db
                try:
                    tables = select_graphable_tables(db)
                    res.extend(tables)
                except Exception as e:
                    print(f"Error processing {db}: {str(e)}")  # Debug print
    
    res.sort()
    return res

def get_resp(prompt: str) -> str:
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
    print(get_graphable_tables())