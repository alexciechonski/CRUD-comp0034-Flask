"""
Module for managing audit logs.

This module provides functionality to track and manage changes to the database
using a JSON-based audit log.
"""
import json
import os
from typing import Dict, Any, List
from collections import deque
import pandas as pd
from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.orm import sessionmaker
from src.config import LOG_PATH
from src.utils import get_db_path

class LogManager:
    """Class for managing audit logs"""
    
    def __init__(self) -> None:
        # Create the log directory if it doesn't exist
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
        
        # Create the log file with empty list if it doesn't exist
        if not os.path.exists(LOG_PATH):
            with open(LOG_PATH, 'w') as f:
                json.dump([], f, indent=2)
        
        # Read the log file
        with open(LOG_PATH, 'r') as f:
            log_data = json.load(f)
        self.log = deque(log_data)
        self.length = len(self.log)

    def update_length(self):
        """Remove oldest entry if log exceeds 10 entries"""
        if self.length > 10:
            self.log.popleft()

    def _get_orm_instances(self, database: str, table_name: str, data: Dict) -> Dict:
        """
        Get ORM instances for a table.
        
        Args:
            database (str): Name of the database
            table_name (str): Name of the table
            data (Dict): Data to create instances from
            
        Returns:
            Dict: Serialized ORM instances
        """
        try:
            # Create engine and session
            engine = create_engine(f'sqlite:///{get_db_path(database)}')
            Session = sessionmaker(bind=engine)
            session = Session()
            
            # Get table metadata
            metadata = MetaData()
            metadata.reflect(bind=engine)
            table = metadata.tables[table_name]
            
            # Create ORM instances
            instances = []
            if isinstance(data, list):
                for row in data:
                    instance = table._class()
                    for column in table.columns:
                        setattr(instance, column.name, row.get(column.name))
                    instances.append(instance)
            else:
                instance = table._class()
                for column in table.columns:
                    setattr(instance, column.name, data.get(column.name))
                instances.append(instance)
            
            # Convert instances to serializable format
            serializable_instances = []
            for instance in instances:
                instance_dict = {}
                for column in instance.__table__.columns:
                    value = getattr(instance, column.name)
                    # Handle special types (e.g., datetime)
                    if hasattr(value, 'isoformat'):
                        value = value.isoformat()
                    instance_dict[column.name] = value
                serializable_instances.append(instance_dict)
            
            return serializable_instances
            
        except Exception as e:
            print(f"Error getting ORM instances: {str(e)}")
            return []
        finally:
            if 'session' in locals():
                session.close()
            if 'engine' in locals():
                engine.dispose()

    def create_change(self, database: str, table_name: str, new_data_dict: Dict) -> None:
        """
        Log a create operation.
        
        Args:
            database (str): Name of the database
            table_name (str): Name of the table
            new_data_dict (Dict): New data being created
        """
        # Get ORM instances for the new data
        orm_instances = self._get_orm_instances(database, table_name, new_data_dict)
        
        self.log.append({
            "change": "create",
            "database": database,
            "table": table_name,
            "new_data": new_data_dict,
            "orm_instances": orm_instances
        })
        self.update_length()
        self.save_log()

    def update_change(self, database: str, table_name: str, new_data_dict: Dict, old_data_dict: Dict) -> None:
        """
        Log an update operation.
        
        Args:
            database (str): Name of the database
            table_name (str): Name of the table
            new_data_dict (Dict): New data after update
            old_data_dict (Dict): Previous data before update
        """
        # Get ORM instances for both new and old data
        new_orm_instances = self._get_orm_instances(database, table_name, new_data_dict)
        old_orm_instances = self._get_orm_instances(database, table_name, old_data_dict)
        
        self.log.append({
            "change": "update",
            "database": database,
            "table": table_name,
            "new_data": new_data_dict,
            "prev_data": old_data_dict,
            "new_orm_instances": new_orm_instances,
            "prev_orm_instances": old_orm_instances
        })
        self.update_length()
        self.save_log()

    def delete_change(self, database: str, table_name: str, old_data_dict: Dict) -> None:
        """
        Log a delete operation.
        
        Args:
            database (str): Name of the database
            table_name (str): Name of the table
            old_data_dict (Dict): Data being deleted
        """
        # Get ORM instances for the deleted data
        orm_instances = self._get_orm_instances(database, table_name, old_data_dict)
        
        self.log.append({
            "change": "delete",
            "database": database,
            "table": table_name,
            "prev_data": old_data_dict,
            "orm_instances": orm_instances
        })
        self.update_length()
        self.save_log()

    def remove_change(self, database: str, table_name: str, change_type: str) -> None:
        """
        Remove a specific change from the log.
        
        Args:
            database (str): Name of the database
            table_name (str): Name of the table
            change_type (str): Type of change to remove
        """
        print(f"Attempting to remove change: database={database}, table={table_name}, change_type={change_type}")
        
        # Convert deque to list for easier manipulation
        log_list = list(self.log)
        print(f"Current log has {len(log_list)} entries")
        
        # Find and remove the specific change
        found = False
        for i, entry in enumerate(log_list):
            print(f"Checking entry: database={entry.get('database')}, table={entry.get('table')}, change={entry.get('change')}")
            if (entry.get('database') == database and 
                entry.get('table') == table_name and 
                entry.get('change') == change_type):
                # Remove only this specific change
                log_list.pop(i)
                found = True
                print(f"Found and removed change at index {i}")
                break
        
        if not found:
            print(f"Warning: No matching change found to remove")
        
        # Update the log with the modified list
        self.log = deque(log_list)
        
        # Update the log length and save the changes
        self.update_length()
        self.save_log()
        
        print(f"Removed {change_type} change for {table_name} in {database}")

    def save_log(self) -> None:
        """Save the current log to file"""
        with open(LOG_PATH, 'w') as f:
            json.dump(list(self.log), f, indent=2)

    def to_tables(self) -> pd.DataFrame:
        """
        Convert log entries to a pandas DataFrame.
        
        Returns:
            pd.DataFrame: DataFrame containing log entries
        """
        res = []
        # Convert deque to list and reverse it to show newest changes first
        for change in reversed(list(self.log)):
            if change['change'] == "create":
                df = pd.DataFrame([{
                    'change_type': change['change'],
                    'database': change['database'],
                    'table': change['table'],
                    **change['new_data']
                }])
                res.append(df)
            elif change['change'] == 'delete':
                # For delete operations, include both the deleted data and previous data
                df = pd.DataFrame([{
                    'change_type': change['change'],
                    'database': change['database'],
                    'table': change['table'],
                    **change['prev_data'],
                    **{f'prev_{k}': v for k, v in change['prev_data'].items()}  # Add prev_ prefix for reversion
                }])
                res.append(df)
            elif change['change'] == 'update':
                # Create a dictionary with previous data prefixed with 'prev_'
                prev_data_dict = {f'prev_{k}': v for k, v in change['prev_data'].items()}
                df = pd.DataFrame([{
                    'change_type': change['change'],
                    'database': change['database'],
                    'table': change['table'],
                    **change['new_data'],
                    **prev_data_dict
                }])
                res.append(df)
        return pd.concat(res, ignore_index=True) if res else pd.DataFrame()

