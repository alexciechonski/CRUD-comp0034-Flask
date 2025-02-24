from src.config import IMMUTABLE, SCHEMA
from src.utils import show_tables

class Validator:

    @staticmethod
    def val_create_table(db, table):
        tables = show_tables(db)
        if table in tables:
            return False
        return True

    @staticmethod
    def val_delete_table(db_name, table):
        if table in IMMUTABLE[db_name]:
            return False
        return True

    @staticmethod
    def val_insert(db_name, table):
        if table in IMMUTABLE[db_name]:
            return False
        return True

    @staticmethod
    def val_schema(contents_df):
        return SCHEMA == list(contents_df.columns)
