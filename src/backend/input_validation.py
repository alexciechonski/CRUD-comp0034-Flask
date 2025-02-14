from src.utils import get_databases, show_tables
class Validator:

    @staticmethod
    def val_create_db(input):
        dbs = get_databases()
        if input in dbs:
            return False

    @staticmethod
    def val_delete_db(input):
        dbs = get_databases()
        if input not in dbs:
            return False
        if input in ["covid.db", 'graph.db', 'mental_health.db']:
            return False

    @staticmethod
    def val_create_table(db, table):
        tables = show_tables(db)
        if table in tables:
            return False

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

    @staticmethod
    def val_insert(db_name, table, df):
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
        # case for wrong columsn
        
