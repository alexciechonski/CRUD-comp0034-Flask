from src.utils import *
def create_graph_db():
    db_path = "src/backend/data/graph.db"
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
        # (2, 5, 1, 4),
        (3, 1, 7, 4), # date - summary restriction
        # (4, 7, 1, 4),
        # (5, 5, 3, 4), # daily restriction - restriction
        (6, 3, 5, 4), 
        # (7, 7, 3, 4), # summary restriction - restriction
        (8, 3, 7, 4),
        # (9, 7, 4, 4), # summary restriction - source
        (10, 4, 7, 4),
        (11, 3, 6, 4), # restriction - weekly restriction
        # (12, 6, 3, 4),
        # (13, 6, 2, 4), # weekly restriction - week
        (14, 2, 6, 4)
    ]

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

def create_mental_db():
    db_path = "src/backend/data/mental_health.db"
    data = [
        (1, "3/2020", 1139242),
        (2, "4/2020", 1145537),
        (3, "5/2020", 1142144),
        (4, "6/2020", 1148158),
        (5, "7/2020", 1119842),
        (6, "8/2020", 1148703),
        (7, "9/2020", 1180163),
        (8, "10/2020", 1140157),
        (9, "11/2020", 1085628),
        (10, "12/2020", 1114316),
        (11, "1/2021", 1142849),
        (12, "2/2021", 1124193),
        (13, "3/2021", 1115858),
        (14, "4/2021", 1107582),
        (15, "5/2021", 1096063),
        (16, "6/2021", 1122513),
        (17, "7/2021", 1082603),
        (18, "8/2021", 1148874),
        (19, "9/2021", 1124816),
        (20, "10/2021", 1121761)
    ]
    cols = {
        "id": "INTEGER PRIMARY KEY",
        "reporting_period": "INTEGER NOT NULL",
        "measured_value": "INTEGER NOT NULL"
    }
    create_table(db_path, "MHCareCluster", cols)
    insert_data(db_path, "MHCareCluster", data)


if __name__ == "__main__":
    create_mental_db()