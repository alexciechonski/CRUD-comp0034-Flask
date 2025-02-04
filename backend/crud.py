from frames import DatabaseManager
import sqlite3
class CRUDManager:
    def __init__(self, db_path) -> None:
        self._db = db_path
        self.adj = self.get_adj_list()

    def get_adj_list(self):
        with sqlite3.connect(self._db) as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA foreign_key_list(Date);")
            res = cursor.fetchall()
            print(res)

    def create_table(self, table):
        pass

    def delete_table(self, table):
        pass

    def create_record(self, data):
        pass

    def update_record(self, table, data):
        pass

    def delete_record(self, table, data):
        pass


if __name__ == "__main__":
    # manager = DatabaseManager("backend/graph.db")
    # # create the two tables
    # node_cols = {
    #     "node_id": "INTEGER PRIMARY KEY AUTOINCREMENT",
    #     "node_name": "TEXT UNIQUE NOT NULL",
    # }
    # manager.create_table("Nodes", node_cols)

    # edge_cols = {
    #     "edge_id": "INTEGER PRIMARY KEY AUTOINCREMENT",
    #     "from_node": "INTEGER NOT NULL FOREIGN KEY REFERENCES nodes(node_id)",
    #     "to_node": "INTEGER NOT NULL FOREIGN KEY REFERENCES nodes(node_id)",
    #     "edge_type": "INTEGER NOT NULL FOREIGN KEY REFERENCES edge_types(type_id)",
    #     }

    with sqlite3.connect("backend/covid.db") as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_key_list(Week);")
        res = cursor.fetchall()
        print(res)