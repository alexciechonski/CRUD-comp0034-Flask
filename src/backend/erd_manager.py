"""
Module for managing graph visualizations and database operations.

This module provides two classes:
1. `Visualizer`: Handles graph-related operations such as retrieving adjacency lists
   and managing graph entities in an SQLite database.
2. `CRUD`: Provides basic database operations, including table creation, data insertion,
   and table deletion, with integration into a graph database.
"""
import sqlite3
from typing import Any, Dict, List
from collections import defaultdict
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, inspect, Date
from sqlalchemy.orm import sessionmaker
from src.utils import create_table, delete_table, query_db
from src.config import PATHS
from src.frontend.input_validation import Validator as v
from src.backend.models import Base, create_custom_table

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
    Handles Create, Read, Update, and Delete operations for database tables.

    Attributes:
        db_name (str): Name of the database to operate on.
        engine: SQLAlchemy engine instance.
        Session: SQLAlchemy session factory.
    """
    def __init__(self, db_name: str) -> None:
        """
        Initializes CRUD with a database name.

        Args:
            db_name (str): Name of the database to operate on.
        """
        self.db_name = db_name
        self.engine = create_engine(f'sqlite:///{PATHS[db_name]}')
        self.Session = sessionmaker(bind=self.engine)

    def add_table(self, table_name: str, graph_id: int) -> None:
        """
        Creates a new table in the database.

        Args:
            table_name (str): Name of the table to create.
            graph_id (int): ID for the graph representation.

        Raises:
            ValueError: If table already exists.
        """
        if not v.val_create_table(self.db_name, table_name):
            raise ValueError(f"Table {table_name} already exists")

        # Create a basic table model with id, time, and measured_value columns
        columns = [
            ('time', 'date', 'NOT NULL'),
            ('measured_value', 'float', 'NOT NULL')
        ]
        
        # Create the table model
        table_model = create_custom_table(table_name, columns)
        
        # Create the table in the database
        table_model.__table__.create(self.engine)

    def remove_table(self, database: str, table_name: str) -> None:
        """
        Removes a table from the database.

        Args:
            database (str): Name of the database.
            table_name (str): Name of the table to remove.

        Raises:
            ValueError: If table is immutable or doesn't exist.
        """
        if not v.val_delete_table(database, table_name):
            raise ValueError(f"Table {table_name} cannot be deleted as it is immutable")

        metadata = MetaData()
        # Reflect the table
        table = Table(table_name, metadata, autoload_with=self.engine)
        # Drop the table
        table.drop(self.engine)

    def insert_data(self, table_name: str, data: List[Dict]) -> None:
        """
        Inserts data into a table using SQLAlchemy.

        Args:
            table_name (str): Name of the table to insert data into.
            data (List[Dict]): List of dictionaries containing the data to insert.

        Raises:
            ValueError: If table is immutable or schema validation fails.
        """
        if not v.val_insert(self.db_name, table_name):
            raise ValueError(f"Cannot insert data into table {table_name} as it is immutable")

        # Convert data to DataFrame for schema validation
        import pandas as pd
        df = pd.DataFrame(data)
        
        # Validate schema
        if not v.val_schema(df):
            raise ValueError("Data schema does not match the required schema")

        session = self.Session()
        try:
            # Get table model
            metadata = MetaData()
            table = Table(table_name, metadata, autoload_with=self.engine)
            
            # Insert data
            session.execute(table.insert(), data)
            session.commit()
            print(f"Inserted {len(data)} rows into '{table_name}' successfully.")
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get_tables(self) -> List[str]:
        """
        Gets a list of all tables in the database.

        Returns:
            List[str]: List of table names.
        """
        inspector = inspect(self.engine)
        return inspector.get_table_names()

    def __del__(self):
        """Cleanup database connection."""
        self.engine.dispose()

if __name__ == "__main__":
    pass
