from src.utils import get_databases, show_tables
import sqlite3
import pandas as pd
class Validator:

    @staticmethod
    def val_create_table(db, table):
        tables = show_tables(db)
        if table in tables:
            return False
        return True

    @staticmethod
    def val_delete_table(db_name, table):
        if db_name == "graph.db":
            return False
        if db_name == "covid.db":
            if table in ['Date', 'Week', 'Source', 'Restriction', 'SummaryRestriction', 'DailyRestriction', 'WeeklyRestriction']:
                return False
        if db_name == 'mental_health.db':
            if table == "MHCareClusters":
                return False
        if table not in show_tables(db_name):
            return False
        return True

    @staticmethod
    def val_insert(db_name, table):
        if db_name == "graph.db":
            return False
        if db_name == "covid.db":
            if table in ['Date', 'Week', 'Source', 'Restriction', 'SummaryRestriction', 'DailyRestriction', 'WeeklyRestriction']:
                return False
        if db_name == 'mental_health.db':
            if table == "MHCareClusters":
                return False
        if table not in show_tables(db_name):
            return False
        return True

    @staticmethod
    def val_schema(db_name, table, df):
        schema = ["id", "time", "measured_value"]
        return schema == list(df.columns)

if __name__ == "__main__":
    df = pd.DataFrame(columns=['a', 'b'])
    print(Validator.val_schema("covid.db", "Date", df))
        
