from frames import Frames, Tables, DatabaseManager
class DataServer:
    def __init__(self, db_path) -> None:
        self.manager = DatabaseManager(db_path)

    def serve_erd(self):        
        tables = self.manager.show_tables()


if __name__ == "__main__":
    manager = DatabaseManager("backend/database.db")
    print(manager.show_tables())