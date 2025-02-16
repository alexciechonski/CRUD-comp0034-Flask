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

    def delete_graph(self, graph_id):
        with sqlite3.connect(self._db) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM Graphs WHERE graph_id = ?;", (graph_id,))
            cursor.execute("DELETE FROM Nodes WHERE graph_id = ?;", (graph_id,))
            conn.commit()


class CRUD:
    def __init__(self, db_name) -> None:
        self.db_name = db_name
        self._db = PATHS[self.db_name]
        self._graph = PATHS["graph.db"]
        self.last_node_id = query_db("SELECT node_id FROM Nodes", self._graph)[-1][0]
        # self.last_graph_id = len(get_databases())

    def add_table(self, table_name: str, graph_id) -> None:
        cols = {"id": "INTEGER PRIMARY KEY", "time":"TEXT NOT NULL", "measured_value":"INTEGER NOT NULL"}
        create_table(self._db, table_name, cols)
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

    @staticmethod
    def remove_table(db_name, table):
        delete_table(db_name, table)
        with sqlite3.connect(PATHS["graph.db"]) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM Nodes WHERE node_name = ?;", (table,))
            conn.commit()

if __name__ == "__main__":
    pass
