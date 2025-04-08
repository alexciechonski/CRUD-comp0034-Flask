"""
Module for validating database operations.

This module provides the `Validator` class, which includes static methods
to validate table creation, deletion, data insertion, and schema compliance
based on predefined database constraints.
"""
from src.config import IMMUTABLE, NON_DELETEABLE
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
        # If database is not in IMMUTABLE, all tables are deletable
        if db_name not in IMMUTABLE:
            return True

        # If database is in IMMUTABLE, check if table is in its immutable list
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
        # If database is not in IMMUTABLE, all tables are insertable
        if db_name not in IMMUTABLE:
            return True

        # If database is in IMMUTABLE, check if table is in its immutable list
        if table in IMMUTABLE[db_name]:
            return False
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
