"""
Module for managing graph visualizations and database operations.

This module provides two classes:
1. `Visualizer`: Handles graph-related operations such as retrieving adjacency lists
   and managing graph entities in an SQLite database.
2. `CRUD`: Provides basic database operations, including table creation, data insertion,
   and table deletion, with integration into a graph database.
"""
import sqlite3
from typing import Any
from collections import defaultdict
from src.utils import create_table, delete_table, query_db
from src.config import PATHS
from src.frontend.input_validation import Validator as v

class Visualizer:
    """
    A class for managing graph structures and retrieving adjacency lists.

    Attributes:
        _db (str): Path to the graph database.
    """
    def __init__(self, graph_db_path: str) -> None:
        """
        Initializes the Visualizer with the given graph database path.

        Args:
            graph_db_path (str): Path to the SQLite database containing graph data.
        """
        self._db = graph_db_path

    def get_adj_list(self, graph_id: int) -> None:
        """
        Retrieves the adjacency list representation of a graph.

        Args:
            graph_id (int): The ID of the graph to retrieve.

        Returns:
            dict: A dictionary where each key is a node, and the value is a list
                  of connected nodes along with their edge types.
        """
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

    def add_graph(self, graph_id: int, graph_name: str) -> None:
        """
        Adds a new graph entry to the database.

        Args:
            graph_id (int): Unique identifier for the graph.
            graph_name (str): Name of the graph.
        """
        with sqlite3.connect(self._db) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO Graphs (graph_id, graph_name) VALUES (?, ?)",
                (graph_id, graph_name)
                )
            conn.commit()

    def delete_graph(self, graph_id: int) -> None:
        """
        Deletes a graph and its associated nodes from the database.

        Args:
            graph_id (int): Unique identifier for the graph to be deleted.
        """
        with sqlite3.connect(self._db) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM Graphs WHERE graph_id = ?;", (graph_id,))
            cursor.execute("DELETE FROM Nodes WHERE graph_id = ?;", (graph_id,))
            conn.commit()

class CRUD:
    """
    A class for performing Create, Read, Update, and Delete (CRUD) operations
    on an SQLite database while maintaining a graph-based representation.

    Attributes:
        db_name (str): The name of the database.
        _db (str): Path to the main database.
        _graph (str): Path to the graph database.
        last_node_id (int): The last node ID used in the graph.
    """
    def __init__(self, db_name: str) -> None:
        """
        Initializes the CRUD operations for a specific database.

        Args:
            db_name (str): The name of the database being managed.
        """
        self.db_name = db_name
        self._db = PATHS[self.db_name]
        self._graph = PATHS["graph.db"]
        self.last_node_id = query_db("SELECT node_id FROM Nodes", self._graph)[-1][0]

    def add_table(self, table_name: str, graph_id: int) -> None:
        """
        Creates a new table in the database and registers it as a node in the graph database.

        Args:
            table_name (str): The name of the table to create.
            graph_id (int): The graph ID to associate with the table.

        Raises:
            ValueError: If table already exists or validation fails.
        """
        # Validate table creation
        if not v.val_create_table(self.db_name, table_name):
            raise ValueError(f"Table {table_name} already exists")

        cols = {
            "id": "INTEGER PRIMARY KEY",
            "time": "TEXT NOT NULL",
            "measured_value": "INTEGER NOT NULL"
        }
        create_table(self._db, table_name, cols)
        # add node to graph db
        self.last_node_id += 1
        with sqlite3.connect(self._graph) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO Nodes (node_id, node_name, graph_id) VALUES (?, ?, ?)",
                (self.last_node_id, table_name, graph_id)
            )
            conn.commit()

    def insert_data(self, table_name: str, data: list[dict]) -> None:
        """
        Inserts data into an SQLite table.

        Args:
            table_name (str): Name of the table to insert data into.
            data (list[dict]): List of dictionaries, each representing a row of data.

        Raises:
            ValueError: If table is immutable or schema validation fails.
        """
        # Validate if data can be inserted into this table
        if not v.val_insert(self.db_name, table_name):
            raise ValueError(f"Cannot insert data into table {table_name} as it is immutable")

        # Convert data to DataFrame for schema validation
        import pandas as pd
        df = pd.DataFrame(data)
        
        # Validate schema
        if not v.val_schema(df):
            raise ValueError("Data schema does not match the required schema")

        with sqlite3.connect(self._db) as conn:
            cursor = conn.cursor()
            if not data:
                return

            # Get column names from the first row
            columns = list(data[0].keys())
            placeholders = ','.join(['?' for _ in columns])
            columns_str = ','.join(columns)
            
            # Prepare the insert query
            insert_sql = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
            
            try:
                for row in data:
                    values = [row[col] for col in columns]
                    cursor.execute(insert_sql, values)
                print(f"Inserted {len(data)} rows into '{table_name}' successfully.")
            except sqlite3.Error as err:
                print(f"An error occurred: {err}")
                raise
            finally:
                conn.commit()

    @staticmethod
    def remove_table(db_name: str, table: str) -> None:
        """
        Removes a table from the database and deletes its corresponding node
        from the graph database.

        Args:
            db_name (str): The name of the database.
            table (str): The name of the table to be removed.

        Raises:
            ValueError: If table is immutable or validation fails.
        """
        # Validate table deletion
        if not v.val_delete_table(db_name, table):
            raise ValueError(f"Table {table} cannot be deleted as it is immutable")

        delete_table(db_name, table)
        with sqlite3.connect(PATHS["graph.db"]) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM Nodes WHERE node_name = ?;", (table,))
            conn.commit()

if __name__ == "__main__":
    pass
