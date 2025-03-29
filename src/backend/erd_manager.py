"""
Module for managing graph visualizations and database operations.

This module provides two classes:
1. `Visualizer`: Handles graph-related operations such as retrieving adjacency lists
   and managing graph entities in an SQLite database.
2. `CRUD`: Provides basic database operations, including table creation, data insertion,
   and table deletion, with integration into a graph database.
"""
import sqlite3
from typing import Any, Dict, List
from collections import defaultdict
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, inspect, Date
from sqlalchemy.orm import sessionmaker
from src.utils import create_table, delete_table, query_db, get_db_path
from src.backend.validation import Validator as v
from src.backend.models import Base, create_custom_table

class Visualizer:
    """Class for visualizing database relationships"""
    def __init__(self, session):
        """Initialize the Visualizer with a database session
        
        Args:
            session: SQLAlchemy session for database access
        """
        self._session = session
        self._engine = session.get_bind()
        
    def get_adj_list(self, db_name: str) -> Dict[str, List[List[str]]]:
        """Get adjacency list representation of database relationships
        
        Args:
            db_name (str): Name of the database to analyze
            
        Returns:
            Dict[str, List[List[str]]]: Adjacency list where each key is a table name and 
            each value is a list of [target_table, relationship_type] pairs
        """
        inspector = inspect(self._engine)
        adj_list = {}
        
        try:
            # Get all tables in the database
            tables = inspector.get_table_names()
            
            # Initialize empty lists for all tables
            for table in tables:
                adj_list[table] = []
            
            # For each table, analyze its relationships
            for table in tables:
                # Get foreign key information
                fks = inspector.get_foreign_keys(table)
                
                # Get unique constraints and primary key info
                unique_constraints = inspector.get_unique_constraints(table)
                pk_constraint = inspector.get_pk_constraint(table)
                unique_columns = set()
                
                # Collect all unique columns
                for constraint in unique_constraints:
                    unique_columns.update(constraint['column_names'])
                if pk_constraint:
                    unique_columns.update(pk_constraint['constrained_columns'])
                
                # For each foreign key, determine the relationship type
                for fk in fks:
                    referred_table = fk['referred_table']
                    constrained_columns = fk['constrained_columns']
                    referred_columns = fk['referred_columns']
                    
                    # Check if the foreign key columns are part of a unique constraint
                    is_unique = all(col in unique_columns for col in constrained_columns)
                    
                    # Determine relationship type
                    relationship_type = self._determine_relationship_type(
                        inspector, table, referred_table,
                        constrained_columns, referred_columns,
                        is_unique
                    )
                    
                    # Add relationship to adjacency list as [to_node, relationship_type]
                    adj_list[table].append([referred_table, relationship_type])
                    
                # Sort the list of references by table name for consistency
                adj_list[table].sort(key=lambda x: x[0])
            
            return adj_list
            
        except Exception as e:
            print(f"Error creating adjacency list for {db_name}: {str(e)}")
            return {}
            
        finally:
            if hasattr(self, '_engine'):
                self._engine.dispose()

    def _determine_relationship_type(
        self, 
        inspector: Any,
        source_table: str,
        target_table: str,
        source_columns: List[str],
        target_columns: List[str],
        is_unique: bool
    ) -> str:
        """
        Determines the type of relationship between two tables.

        Args:
            inspector: SQLAlchemy inspector instance
            source_table: Name of the table containing the foreign key
            target_table: Name of the referenced table
            source_columns: Columns in the source table (foreign key columns)
            target_columns: Referenced columns in the target table
            is_unique: Whether the foreign key columns are unique

        Returns:
            str: Relationship type ('1:1', '1:N', or 'N:M')
        """
        # Check for many-to-many relationship
        # This is a heuristic: if a table has exactly two foreign keys and no other columns
        # (except perhaps an id), it's likely a junction table
        source_columns_all = [col['name'] for col in inspector.get_columns(source_table)]
        if len(inspector.get_foreign_keys(source_table)) == 2 and \
           len(source_columns_all) <= len(source_columns) + 1:  # +1 for possible id column
            return 'N:M'
        
        # If the foreign key columns are unique, it's a one-to-one relationship
        if is_unique:
            return '1:1'
        
        # Otherwise, it's a one-to-many relationship
        return '1:N'

class CRUD:
    """
    Handles Create, Read, Update, and Delete operations for database tables.

    Attributes:
        db_name (str): Name of the database to operate on.
        engine: SQLAlchemy engine instance.
        Session: SQLAlchemy session factory.
    """
    def __init__(self, db_name: str) -> None:
        """
        Initializes CRUD with a database name.

        Args:
            db_name (str): Name of the database to operate on.
        """
        print(f"\n=== Initializing CRUD ===")
        print(f"Input database name: '{db_name}'")
        
        # Ensure database name ends with .db
        if not db_name.endswith('.db'):
            db_name += '.db'
            print(f"Added .db extension: '{db_name}'")
            
        self.db_name = db_name
        self.engine = None
        self.Session = None
        print(f"Calling _initialize_engine...")
        self._initialize_engine()

    def _initialize_engine(self) -> None:
        """Initialize SQLAlchemy engine and session factory."""
        try:
            if self.engine:
                print("Disposing existing engine...")
                self.engine.dispose()
            
            db_path = get_db_path(self.db_name)
            print(f"Database path: '{db_path}'")
            
            # Check if database file exists
            import os
            if not os.path.exists(db_path):
                print(f"Database file not found!")
                print(f"Current working directory: {os.getcwd()}")
                print(f"Directory contents: {os.listdir(os.path.dirname(db_path))}")
                raise ValueError(f"Database file not found at: {db_path}")
            
            print(f"Creating engine with URI: sqlite:///{db_path}")
            self.engine = create_engine(f'sqlite:///{db_path}')
            self.Session = sessionmaker(bind=self.engine)
            
            # Test connection
            with self.engine.connect() as conn:
                print("Successfully connected to database")
                
        except Exception as e:
            print(f"Error in _initialize_engine: {str(e)}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            raise

    def add_table(self, table_name: str) -> None:
        """
        Creates a new table in the database.

        Args:
            table_name (str): Name of the table to create.

        Raises:
            ValueError: If table already exists.
        """
        if not v.val_create_table(self.db_name, table_name):
            raise ValueError(f"Table {table_name} already exists")

        # Create a basic table model with id, time, and measured_value columns
        columns = [
            ('time', 'date', 'NOT NULL'),
            ('measured_value', 'float', 'NOT NULL')
        ]
        
        # Create the table model
        table_model = create_custom_table(table_name, columns)
        
        # Create the table in the database
        table_model.__table__.create(self.engine)

    def remove_table(self, database: str, table_name: str) -> None:
        """
        Removes a table from the database.

        Args:
            database (str): Name of the database.
            table_name (str): Name of the table to remove.

        Raises:
            ValueError: If table is immutable or doesn't exist.
        """
        print(f"\n=== Removing Table ===")
        print(f"Database: '{database}'")
        print(f"Table: '{table_name}'")
        print(f"Current db_name: '{self.db_name}'")
        
        try:
            # Ensure database name ends with .db
            if not database.endswith('.db'):
                database += '.db'
                print(f"Added .db extension to database: '{database}'")
                
            # Update engine if database is different from current one
            if database != self.db_name:
                print(f"Switching database from '{self.db_name}' to '{database}'")
                self.db_name = database
                self._initialize_engine()

            print("Validating table deletion...")
            if not v.val_delete_table(database, table_name):
                raise ValueError(f"Table {table_name} cannot be deleted as it is immutable")

            # Check if table exists
            print("Checking if table exists...")
            inspector = inspect(self.engine)
            tables = inspector.get_table_names()
            print(f"Available tables: {tables}")
            
            if table_name not in tables:
                raise ValueError(f"Table {table_name} does not exist in database {database}")

            print(f"Attempting to drop table {table_name}...")
            # Drop the table using SQLAlchemy
            metadata = MetaData()
            table = Table(table_name, metadata)
            table.drop(self.engine, checkfirst=True)
            print(f"Successfully dropped table {table_name} from {database}")
                
        except Exception as e:
            print(f"Error in remove_table: {str(e)}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            raise

    def insert_data(self, table_name: str, data: List[Dict]) -> None:
        """
        Inserts data into a table using SQLAlchemy.

        Args:
            table_name (str): Name of the table to insert data into.
            data (List[Dict]): List of dictionaries containing the data to insert.

        Raises:
            ValueError: If table is immutable or schema validation fails.
        """
        print(f"\n=== Inserting Data ===")
        print(f"Table: '{table_name}'")
        print(f"Number of rows to insert: {len(data)}")
        print(f"Sample data: {data[0] if data else 'No data'}")

        if not v.val_insert(self.db_name, table_name):
            raise ValueError(f"Cannot insert data into table {table_name} as it is immutable")

        # Convert data to DataFrame for schema validation
        import pandas as pd
        df = pd.DataFrame(data)
        print(f"DataFrame columns: {df.columns.tolist()}")
        
        # Convert date format from DD/MM/YYYY to YYYY-MM-DD
        if 'time' in df.columns:
            print("Converting date format...")
            df['time'] = pd.to_datetime(df['time'], format='%d/%m/%Y').dt.strftime('%Y-%m-%d')
            print(f"Sample converted date: {df['time'].iloc[0] if not df.empty else 'No data'}")
        
        # Validate schema
        if not v.val_schema(df):
            raise ValueError("Data schema does not match the required schema")

        session = self.Session()
        try:
            # Get table model
            metadata = MetaData()
            table = Table(table_name, metadata, autoload_with=self.engine)
            print(f"Table columns: {[c.name for c in table.columns]}")
            
            # Convert DataFrame back to list of dictionaries
            data_to_insert = df.to_dict('records')
            
            # Insert data
            print("Executing insert...")
            session.execute(table.insert(), data_to_insert)
            session.commit()
            print(f"Successfully inserted {len(data_to_insert)} rows into '{table_name}'")
        except Exception as e:
            print(f"Error during insert: {str(e)}")
            session.rollback()
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            raise e
        finally:
            session.close()

    def get_tables(self) -> List[str]:
        """
        Gets a list of all tables in the database.

        Returns:
            List[str]: List of table names.
        """
        inspector = inspect(self.engine)
        return inspector.get_table_names()

    def __del__(self):
        """Clean up database connections."""
        if hasattr(self, 'engine') and self.engine:
            print("Disposing engine in destructor")
            self.engine.dispose()

if __name__ == "__main__":
    path = get_db_path('covid.db')
    v = Visualizer(path)
    print(v.get_adj_list('covid.db'))