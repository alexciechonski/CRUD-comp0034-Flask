import sqlite3
from typing import Optional, Any

def query_db(query: str, db_path: str, param: tuple = ()) -> Optional[list[tuple[Any, ...]]]:
    """
    Executes a query against the main database.

    Returns:
        list[tuple[Any, ...]]: Results of the query if it is a SELECT query.
    """
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        try:
            if param is not None:
                cursor.execute(query, param)
            else:
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

def fit_slider(db_path):
    data = query_db("SELECT date_id FROM Date;", db_path)
    first, last = data[0][0], data[-1][0]
    return first, last

if __name__ == "__main__":
    fit_slider("backend/covid.db")