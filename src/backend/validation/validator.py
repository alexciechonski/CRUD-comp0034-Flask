"""
Module for validating database operations.

This module provides the `Validator` class, which includes static methods
to validate table creation, deletion, data insertion, and schema compliance
based on predefined database constraints.
"""
import pandas as pd
from src.config import IMMUTABLE, SCHEMA, NON_DELETEABLE
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
    def val_schema(contents_df: pd.DataFrame) -> bool:
        """
        Validates if a DataFrame's schema matches the expected schema.
        For now, we accept any schema since we're working with dynamic tables.

        Args:
            contents_df (pd.DataFrame): The DataFrame containing the data.

        Returns:
            bool: Always returns True for now.
        """
        return True

    @staticmethod
    def val_delete_database(db_name: str) -> bool:
        """
        Validates if a database can be deleted.

        Args:
            db_name (str): The name of the database.

        Returns:
            bool: False if the database is non-deletable, otherwise True.
        """
        return db_name not in NON_DELETEABLE
