import sqlite3
import pandas as pd
from src.utils import *
from collections import defaultdict
import io
import base64

class Visualizer:
    def __init__(self, graph_db_path) -> None:
        self._db = graph_db_path

    def get_adj_list(self):
        sql = """
            SELECT 
                n1.node_name AS from_node_name,
                n2.node_name AS to_node_name,
                et.type_name AS connection_type_name
            FROM Edges e
            JOIN Nodes n1 ON e.from_node = n1.node_id
            JOIN Nodes n2 ON e.to_node = n2.node_id
            JOIN EdgeTypes et ON e.type_id = et.type_id;
            """
        res = query_db(sql, self._db)
        adj = defaultdict(list)
        for start, end, typ in res:
            adj[start].append([end, typ])
        return adj     

class CRUD:
    def __init__(self, db_path) -> None:
        self._db = db_path

    @staticmethod
    def create_table(db_name: str, table_name: str, cols_dict: dict[str, str], foreign_keys: list[str] = None) -> None:
        """
        Creates a table in the database with specified columns.

        Parameters:
            table_name (str): Name of the table to create.
            cols_dict (dict): Column names as keys and data types as values.
        """
        with sqlite3.connect(f"src/backend/data/{db_name}") as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA foreign_keys = ON;")
            cols_str = f"({', '.join([f'{col_name} {constraint.upper()}' for col_name, constraint in cols_dict.items()])})"
            if foreign_keys:
                fk_str = ", " + ", ".join(foreign_keys)
            else:
                fk_str = ""
            query = f"CREATE TABLE {table_name} {cols_str}{fk_str}"
            try:
                cursor.execute(query)
                print(f"Table '{table_name}' created successfully.")
            except sqlite3.Error as err:
                print(f"An error occurred: {err}")
            finally:
                conn.commit()

    @staticmethod
    def insert_data(db_path: str, table_name: str, data: list[tuple[Any, ...]]) -> None:
        """
        Inserts data into an SQLite table.

        Parameters:
        - table_name (str): Name of the table to insert data into.
        - data (list of tuples): List of tuples, each tuple represents a row of data.
                                Example: [(1, '2023-01-01'), (2, '2023-01-02')]
        """
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            placeholders = ', '.join(['?' for _ in data[0]])
            insert_sql = f"INSERT INTO {table_name} VALUES ({placeholders})"

            try:
                for row in data:
                    cursor.execute(insert_sql, row)
                print(f"Inserted {len(data)} rows into '{table_name}' successfully.")
            except sqlite3.Error as e:
                print(f"An error occurred: {e}")
            finally:
                conn.commit()

    @staticmethod
    def delete_table(self, db_name, table_name: str) -> None:
        """
        Deletes a specified table from the database.

        Parameters:
            table_name (str): The name of the table to delete.
        """
        with sqlite3.connect(f"src/backend/data/{db_name}") as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(f"DROP TABLE IF EXISTS {table_name};")
                conn.commit()
                print(f"Table '{table_name}' has been deleted from the database '{self._db}'.")
            except sqlite3.DatabaseError as db_err:
                print(f"Database error occurred: {db_err}")

    def import_data_from_csv(self, db_name, table, data):
        if data is None:
            return None
        _, content_string = data.split(',')
        decoded = base64.b64decode(content_string)
        try:
            df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
            if DataValidator.validate_df(df, db_name, table):
                db_path = f"src/backend/data/{db_name}"
                self.insert_data(db_path, table, list(df.itertuples(index=False, name=None)))
        except Exception as e:
            return f"Error processing file: {str(e)}"

    def export_to_csv(self, table):
        pass


class DataValidator:

    @staticmethod
    def get_table_fields(db_name, table):
        db_path = f"src/backend/data/{db_name}"
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(f"PRAGMA table_info('{table}');")
            res = cursor.fetchall()
            return res

    @staticmethod
    def validate_df(df, db_name, table):
        table_fields = DataValidator.get_table_fields(db_name, table)
        if len(table_fields) != len(df.columns):
            return False
        field_names = [field[1] for field in table_fields]
        for col in df.columns:
            if col not in field_names:
                return False
        return True


if __name__ == "__main__":
    data = [
        (1, 'date_id'),
        (2, 'date'),
    ]
    df = pd.DataFrame(data, columns=['date_id', 'date'])
    print(DataValidator.validate_df(df, "covid.db", "Date"))




