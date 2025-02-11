import sqlite3
import pandas as pd
from src.utils import *
from collections import defaultdict
import io
import base64
import json

class Visualizer:
    def __init__(self, graph_db_path) -> None:
        self._db = graph_db_path

    def get_adj_list(self, graph_id):
        sql = """
            SELECT 
                fn.node_name AS from_node_name, 
                tn.node_name AS to_node_name, 
                et.type_name AS edge_type
            FROM 
                Nodes fn
            LEFT JOIN 
                Edges e ON e.from_node = fn.node_id
            LEFT JOIN 
                Nodes tn ON e.to_node = tn.node_id
            LEFT JOIN 
                EdgeTypes et ON e.type_id = et.type_id
            WHERE 
                fn.graph_id = ?;
            """
        res = query_db(sql, self._db, (graph_id,))
        adj = defaultdict(list)
        for start, end, typ in res:
            adj[start].append([end, typ])
        return adj

    def add_graph(self, graph_id, graph_name):
        with sqlite3.connect(self._db) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO Graphs (graph_id, graph_name) VALUES (?, ?)", (graph_id, graph_name))
            conn.commit()

    def delete_graph(self, name):
        pass

    def add_edge():
        pass     

class CRUD:
    def __init__(self, db_name) -> None:
        self.db_name = db_name
        self._db = f"src/backend/data/{self.db_name}"
        self.tables_path = 'src/backend/tables.json'
        with open(self.tables_path, 'r') as file:
            self.table_map = json.load(file)
        self._graph = "src/backend/data/graph.db"
        self.last_node_id = query_db("SELECT node_id FROM Nodes", self._graph)[-1][0]
        # self.last_graph_id = len(get_databases())

    def add_table(self, table_name: str, cols_dict: dict[str, str], graph_id) -> None:
        create_table(self._db, table_name, cols_dict)
        # add node to graph db
        self.last_node_id += 1
        with sqlite3.connect(self._graph) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO Nodes (node_id, node_name, graph_id) VALUES (?, ?, ?)", (self.last_node_id, table_name, graph_id))
            conn.commit()

    def insert_data(self, table_name: str, data: list[tuple[Any, ...]]) -> None:
        """
        Inserts data into an SQLite table.

        Parameters:
        - table_name (str): Name of the table to insert data into.
        - data (list of tuples): List of tuples, each tuple represents a row of data.
                                Example: [(1, '2023-01-01'), (2, '2023-01-02')]
        """
        with sqlite3.connect(self._db) as conn:
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

    def delete_table(self, db_name, table_name: str) -> None:
        """
        Deletes a specified table from the database.

        Parameters:
            table_name (str): The name of the table to delete.
        """
        if table_name in self.table_map[table_name]:
            raise ValueError
        with sqlite3.connect(self._db) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(f"DROP TABLE IF EXISTS {table_name};")
                conn.commit()
                print(f"Table '{table_name}' has been deleted from the database '{self._db}'.")
                self.table_map['added_by_user'][db_name].remove(table_name)
            except sqlite3.DatabaseError as db_err:
                print(f"Database error occurred: {db_err}")

    def import_data_from_csv(self, table, data):
        if data is None:
            return None
        _, content_string = data.split(',')
        decoded = base64.b64decode(content_string)
        try:
            df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
            if DataValidator.validate_df(df, self.db_name, table):
                CRUD.insert_data(self._db, table, list(df.itertuples(index=False, name=None)))
        except Exception as e:
            return f"Error processing file: {str(e)}"

    def export_to_csv(self, table):
        pass

    @staticmethod
    def create_new_db(db_name):
        directory = "src/backend/data"
        os.makedirs(directory, exist_ok=True)
        path = os.path.join(directory, db_name)
        with open(path, 'w') as file:
            pass 
        num_db = len(get_databases())
        vis = Visualizer("src/backend/data/graph.db")
        vis.add_graph(num_db, db_name)

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
    # vis = Visualizer("src/backend/data/graph.db")
    # print(vis.get_adj_list(2))
    crud = CRUD("covid.db")
    print(crud.last_node_id)