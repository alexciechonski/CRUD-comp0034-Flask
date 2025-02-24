"""
Module for validating database operations.

This module provides the `Validator` class, which includes static methods
to validate table creation, deletion, data insertion, and schema compliance
based on predefined database constraints.

Dependencies:
- `IMMUTABLE` (from `src.config`): A dictionary defining tables that cannot be modified.
- `SCHEMA` (from `src.config`): The expected schema structure for data validation.
- `show_tables` (from `src.utils`): A function to list available tables in a database.

Example Usage:
    is_valid = Validator.val_create_table("covid.db", "NewTable")
    can_delete = Validator.val_delete_table("covid.db", "Date")
    is_schema_valid = Validator.val_schema(dataframe)
"""
import pandas as pd
from src.config import IMMUTABLE, SCHEMA
from src.utils import show_tables

class Validator:
    """
    A static class for validating database operations, such as table creation, deletion,
    data insertion, and schema compliance.
    """
    @staticmethod
    def val_create_table(database: str, table: str) -> bool:
        """
        Validates if a table can be created in the database.

        Args:
            db (str): The name of the database.
            table (str): The name of the table to be created.

        Returns:
            bool: True if the table does not already exist, otherwise False.
        """
        tables = show_tables(database)
        if table in tables:
            return False
        return True

    @staticmethod
    def val_delete_table(db_name: str, table: str) -> bool:
        """
        Validates if a table can be deleted.

        Args:
            db_name (str): The name of the database.
            table (str): The name of the table to be deleted.

        Returns:
            bool: False if the table is immutable, otherwise True.
        """
        if table in IMMUTABLE[db_name]:
            return False
        return True

    @staticmethod
    def val_insert(db_name: str, table: str) -> bool:
        """
        Validates if data can be inserted into a table.

        Args:
            db_name (str): The name of the database.
            table (str): The name of the table to insert data into.

        Returns:
            bool: False if the table is immutable, otherwise True.
        """
        if table in IMMUTABLE[db_name]:
            return False
        return True

    @staticmethod
    def val_schema(contents_df: pd.DataFrame):
        """
        Validates if a DataFrame's schema matches the expected schema.

        Args:
            contents_df (pd.DataFrame): The DataFrame containing the data.

        Returns:
            bool: True if the schema matches the expected structure, otherwise False.
        """
        return SCHEMA == list(contents_df.columns)
