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

def get_databases() -> List[str]:
    """Get list of available databases
    
    Returns:
        List[str]: List of database names
    """
    db_files = glob.glob(os.path.join(BASE_PATH, '*.db'))
    return [os.path.basename(db) for db in db_files]

def get_all_tables():
    """Get list of all tables with their associated databases
    
    Returns:
        List[Dict[str, str]]: List of dictionaries containing table name and database name
    """
    
    db_files = [f for f in os.listdir(BASE_PATH) if f.endswith('.db')]
    
    tables = []
    for db in db_files:
        db_tables = show_tables(db)
        for table in db_tables:
            tables.append({
                'name': table,
                'database': db
            })
    
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

def get_primary_keys(table: str, db_name: str) -> List[str]:
    """
    Get primary key columns for a table.
    
    Args:
        table (str): Name of the table
        db_path (str): Path to the database file
        
    Returns:
        List[str]: List of primary key column names
    """
    engine = create_engine(f'sqlite:///{get_db_path(db_name)}')
    inspector = inspect(engine)
    
    try:
        pk_columns = inspector.get_pk_constraint(table)['constrained_columns']
        return pk_columns
    except Exception as e:
        print(f"Error getting primary keys for table {table}: {str(e)}")
        return []
    finally:
        engine.dispose()

def get_graphable_tables():
    """
    Get list of tables that can be used for graphing, including their database information.
    
    Returns:
        list: List of dictionaries containing table information with 'name' and 'database' keys.
    """
    res = []
    all_tables = get_all_tables()
    for table in all_tables:
        if table['name'] not in NON_GRAPHABLE:
            res.append({
                'name': table['name'],
                'database': table['database']
            })
    return res



if __name__ == "__main__":
    from pathlib import Path
    print(os.path.exists('/Users/alexanderciechonski/Desktop/comp0034cw2/deaths.db'))
