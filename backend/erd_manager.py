import sqlite3
import pandas as pd
from backend.utils import *
from collections import defaultdict

class Visualizer:
    def __init__(self, graph_db_path) -> None:
        self._db = graph_db_path

    # def add_table(self, table):
    #     pass

    # def delete_table(self, table):
    #     pass

    # def update_properties(self, table):
    #     pass

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
        for u, v, typ in res:
            adj[u].append((v, typ))
            adj[v].append((u, typ))
        return adj        

class CRUD:
    def __init__(self, db_path) -> None:
        self._db = db_path

#     def create_table(self, table):
#         pass

#     def delete_table(self, table):
#         pass

#     def create_record(self, data):
#         pass

#     def update_record(self, table, data):
#         pass

#     def delete_record(self, table, data):
#         pass

def create_graph_db():
    db_path = "backend/graph.db"
    nodes_data = [
        (1, "Date"), 
        (2, "Week"), 
        (3, "Restriction"), 
        (4, "Source"), 
        (5, "DailyRestriction"), 
        (6, "WeeklyRestriction"),
        (7, "SummaryRestriction") 
    ]

    edge_types_data = [
        (1, "zero-one"), (2, "zero-n"), (3, "one-only"), (4, "one-n")
    ]

    edges_data = [
        (1, 1, 5, 4), # date - daily restriction
        (2, 5, 1, 4),
        (3, 1, 7, 4), # date - summary restriction
        (4, 7, 1, 4),
        (5, 5, 3, 4), # daily restriction - restriction
        (6, 3, 5, 4), 
        (7, 7, 3, 4), # summary restriction - restriction
        (8, 3, 7, 4),
        (9, 7, 4, 4), # summary restriction - source
        (10, 4, 7, 4),
        (11, 3, 6, 4), # restriction - weekly restriction
        (12, 6, 3, 4),
        (13, 6, 2, 4), # weekly restriction - week
        (14, 2, 6, 4)
    ]

    edge = pd.DataFrame(edges_data)

    def create_nodes():
        cols = {
            "node_id": "INTEGER PRIMARY KEY",
            "node_name": "TEXT NOT NULL"
        }
        create_table(db_path, "Nodes", cols)
        insert_data(db_path, "Nodes", nodes_data)
    
    def create_edge_types():
        cols = {
            "type_id": "INTEGER PRIMARY KEY",
            "type_name": "TEXT NOT NULL"
        }
        create_table(db_path, "EdgeTypes", cols)
        insert_data(db_path, "EdgeTypes", edge_types_data)

    def create_edges():
        cols = {
            "edge_id": "INTEGER PRIMARY KEY",
            "from_node": "INTEGER NOT NULL",
            "to_node": "INTEGER NOT NULL",
            "type_id": "INTEGER NOT NULL",
        }
        create_table(db_path, "Edges", cols)
        insert_data(db_path, "Edges", edges_data)

    create_nodes()
    create_edge_types()
    create_edges()

if __name__ == "__main__":
    vis = Visualizer("backend/graph.db")
    print(vis.get_adj_list())





