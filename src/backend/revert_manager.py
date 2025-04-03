"""
Module for managing database state reversions.

This module provides functionality to store and restore database states
using SQLAlchemy's ORM.
"""
import copy
import json
import os
from typing import Dict, Any, List
from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.orm import sessionmaker, Session
from src.utils import get_db_path
from src.config import LOG_PATH

class RevertManager:
    """Class for managing database state reversions"""
    
    def __init__(self, database: str):
        """
        Initialize the RevertManager with a database name.
        
        Args:
            database (str): Name of the database to manage
        """
        self.database = database
        self.engine = create_engine(f'sqlite:///{get_db_path(database)}')
        self.Session = sessionmaker(bind=self.engine)
        self._state_backup = None
        self._orm_instances = {}
        
        # Create the revert directory if it doesn't exist
        self.revert_dir = os.path.dirname(LOG_PATH)
        os.makedirs(self.revert_dir, exist_ok=True)
        
        # Define the path for storing ORM instances
        self.orm_file = os.path.join(self.revert_dir, f'{database}_orm_backup.json')

    def store_state(self) -> None:
        """
        Store a deep copy of the current database state.
        This should be called before making any changes that might need to be reverted.
        """
        session = self.Session()
        try:
            # Get all tables in the database
            metadata = MetaData()
            metadata.reflect(bind=self.engine)
            
            # Create a deep copy of the current state
            state = {}
            
            for table_name, table in metadata.tables.items():
                # Get all data from the table
                result = session.execute(table.select()).fetchall()
                
                # Store the data
                state[table_name] = []
                for row in result:
                    row_dict = {}
                    for i, column in enumerate(table.columns):
                        value = row[i]
                        # Handle special types (e.g., datetime)
                        if hasattr(value, 'isoformat'):
                            value = value.isoformat()
                        row_dict[column.name] = value
                    state[table_name].append(row_dict)
            
            self._state_backup = state
            
            # Save state to file
            self._save_state()
            
            print(f"Stored backup state for database {self.database}")
            
        finally:
            session.close()

    def _save_state(self) -> None:
        """
        Save the current state to a JSON file.
        """
        try:
            # Save to file
            state_file = os.path.join(self.revert_dir, f'{self.database}_state_backup.json')
            with open(state_file, 'w') as f:
                json.dump(self._state_backup, f, indent=2)
            print(f"Saved state to {state_file}")
            
        except Exception as e:
            print(f"Error saving state: {str(e)}")
            raise

    def _load_state(self) -> None:
        """
        Load the state from the JSON file.
        """
        try:
            state_file = os.path.join(self.revert_dir, f'{self.database}_state_backup.json')
            if not os.path.exists(state_file):
                print(f"No state backup file found at {state_file}")
                return
                
            with open(state_file, 'r') as f:
                self._state_backup = json.load(f)
            
            print(f"Loaded state from {state_file}")
            
        except Exception as e:
            print(f"Error loading state: {str(e)}")
            raise

    def restore_state(self) -> bool:
        """
        Restore the database to the previously stored state.
        
        Returns:
            bool: True if restoration was successful, False otherwise
        """
        # Load state from file if not already loaded
        if not self._state_backup:
            self._load_state()
            
        if not self._state_backup:
            print("No state available to restore")
            return False
            
        session = self.Session()
        try:
            # Get all tables in the database
            metadata = MetaData()
            metadata.reflect(bind=self.engine)
            
            # Begin transaction
            session.begin()
            
            # For each table in the backup
            for table_name, rows in self._state_backup.items():
                if table_name not in metadata.tables:
                    print(f"Warning: Table {table_name} not found in database, skipping")
                    continue
                    
                table = metadata.tables[table_name]
                
                # Get current table columns
                current_columns = {col.name for col in table.columns}
                
                # Clear existing data
                session.execute(table.delete())
                
                # Insert backup data
                for row in rows:
                    # Filter out columns that don't exist in the current table
                    filtered_row = {k: v for k, v in row.items() if k in current_columns}
                    if filtered_row:  # Only insert if there are valid columns
                        insert_stmt = table.insert().values(**filtered_row)
                        session.execute(insert_stmt)
            
            # Commit the transaction
            session.commit()
            print(f"Successfully restored database {self.database} to previous state")
            return True
            
        except Exception as e:
            session.rollback()
            print(f"Error restoring database state: {str(e)}")
            return False
            
        finally:
            session.close()

    def __del__(self):
        """Clean up database connection"""
        if hasattr(self, 'engine'):
            self.engine.dispose() 