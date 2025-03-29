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
from src.config import NON_GRAPHABLE, BASE_PATH
from src.backend.models import init_db, Base
import glob
from pathlib import Path
import logging

def get_db_path(db_name):
    return BASE_PATH + db_name

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
        db_name (str): Name of the database.
        table_name (str): Name of the table to delete.
    """
    with sqlite3.connect(get_db_path(db_name)) as conn:
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
    logger = logging.getLogger(__name__)
    
    db_path = get_db_path(database)
    logger.info(f"Connecting to database at: {db_path}")
    
    engine = create_engine(f'sqlite:///{db_path}')
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    logger.info(f"Found tables in {database}: {tables}")
    
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
    engine = create_engine(f'sqlite:///{get_db_path(db_name)}')
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
    with sqlite3.connect(get_db_path("graph.db")) as conn:
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
    engine = create_engine(f'sqlite:///{get_db_path(database)}')
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

def graphable_tables():
    db_files = os.listdir(BASE_PATH)
    graphable = []
    for db in db_files:
        tables = show_tables(db)
        for table in tables:
            if table not in NON_GRAPHABLE:
                graphable.append(f"{db.replace('.db', '')}.{table}")
    return graphable

def get_all_tables():
    """Get list of all tables with their associated databases
    
    Returns:
        List[Dict[str, str]]: List of dictionaries containing table name and database name
    """
    logger = logging.getLogger(__name__)
    
    logger.info(f"Looking for database files in: {BASE_PATH}")
    db_files = [f for f in os.listdir(BASE_PATH) if f.endswith('.db')]
    logger.info(f"Found database files: {db_files}")
    
    tables = []
    for db in db_files:
        logger.info(f"Getting tables for database: {db}")
        db_tables = show_tables(db)
        logger.info(f"Found tables in {db}: {db_tables}")
        for table in db_tables:
            tables.append({
                'name': table,
                'database': db
            })
    
    logger.info(f"Total tables found: {len(tables)}")
    return tables

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

def create_database(db_name: str) -> bool:
    """
    Creates a new empty SQLite database file in the data directory.
    
    Args:
        db_name (str): Name of the database to create (should end with .db)
        
    Returns:
        bool: True if database was created successfully, False otherwise
        
    Raises:
        ValueError: If db_name doesn't end with .db or database already exists
    """
    from pathlib import Path
    from sqlalchemy import create_engine
    
    # Validate database name
    if not db_name.endswith('.db'):
        raise ValueError("Database name must end with .db")
    
    # Construct the full path
    db_path = Path(BASE_PATH) / db_name
    
    # Check if database already exists
    if db_path.exists():
        raise ValueError(f"Database {db_name} already exists at {db_path}")
    
    try:
        # Create the data directory if it doesn't exist
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create an empty database file
        engine = create_engine(f'sqlite:///{db_path}')
        # Just connect and disconnect to create the empty file
        engine.connect().close()
        
        return True
        
    except Exception as e:
        print(f"Error creating database: {str(e)}")
        # Clean up if file was created but there was an error
        if db_path.exists():
            db_path.unlink()
        return False
        
    finally:
        if 'engine' in locals():
            engine.dispose()

def delete_database(db_name: str) -> bool:
    """
    Deletes a SQLite database file and updates the configuration.
    
    Args:
        db_name (str): Name of the database to delete
        
    Returns:
        bool: True if database was deleted successfully, False otherwise
        
    Raises:
        ValueError: If db_name is covid.db or database doesn't exist
    """
    from pathlib import Path
    
    print(f"delete_database called with db_name: {db_name}")
    print(f"BASE_PATH: {BASE_PATH}")
    
    # Don't allow deletion of covid.db
    if db_name == 'covid.db':
        print("Attempted to delete covid.db")
        raise ValueError("Cannot delete the main COVID-19 database")
    
    # Construct the full path
    db_path = Path(BASE_PATH) / db_name
    print(f"Full database path: {db_path}")
    print(f"Database exists: {db_path.exists()}")
    
    # Check if database exists
    if not db_path.exists():
        print(f"Database not found at {db_path}")
        raise ValueError(f"Database {db_name} does not exist at {db_path}")
    
    try:
        # Delete the database file
        print(f"Attempting to delete file at {db_path}")
        db_path.unlink()
        print(f"File deleted successfully. Still exists: {db_path.exists()}")
        
        return True
        
    except Exception as e:
        print(f"Error in delete_database: {str(e)}")
        return False

def get_primary_keys(table: str, db_path: str) -> List[str]:
    """
    Get primary key columns for a table.
    
    Args:
        table (str): Name of the table
        db_path (str): Path to the database file
        
    Returns:
        List[str]: List of primary key column names
    """
    engine = create_engine(f'sqlite:///{db_path}')
    inspector = inspect(engine)
    
    try:
        pk_columns = inspector.get_pk_constraint(table)['constrained_columns']
        return pk_columns
    except Exception as e:
        print(f"Error getting primary keys for table {table}: {str(e)}")
        return []
    finally:
        engine.dispose()

if __name__ == "__main__":
    print(get_table_info("deaths", "src/backend/data/custom.db"))