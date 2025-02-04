from frames import Frames, Tables, DatabaseManager
from typing import Optional, Any
import sqlite3

def query_db(query: str, db_path: str) -> Optional[list[tuple[Any, ...]]]:
    """
    Executes a query against the main database.

    Returns:
        list[tuple[Any, ...]]: Results of the query if it is a SELECT query.
    """
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(query)
            if query.strip().upper().startswith("SELECT"):
                results = cursor.fetchall()
                print("SELECT query executed successfully.")
                return results
            else:
                conn.commit()
                print("Query executed successfully")
        except sqlite3.IntegrityError as int_err:
            raise sqlite3.IntegrityError("Database query failed") from int_err
        except sqlite3.DatabaseError as db_err:
            raise sqlite3.DatabaseError("Database query failed") from db_err

class DataServer:
    def __init__(self, db_path) -> None:
        self._db = db_path

    def serve_erd(self):        
        pass

    def serve_time_series(self):
        query = """
                SELECT Date.date, SUM(DailyRestriction.in_place) AS total_restrictions
                FROM DailyRestriction
                JOIN Date ON DailyRestriction.date_id = Date.date_id
                GROUP BY Date.date;
                """
        return query_db(query, self._db)


if __name__ == "__main__":
    server = DataServer("backend/covid.db")
    print(server.serve_time_series())