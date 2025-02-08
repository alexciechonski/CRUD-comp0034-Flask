import sqlite3
from typing import Optional, Any
import math

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

def create_table(db_path: str, table_name: str, cols_dict: dict[str, str], foreign_keys: list[str] = None) -> None:
    """
    Creates a table in the database with specified columns.

    Parameters:
        table_name (str): Name of the table to create.
        cols_dict (dict): Column names as keys and data types as values.
    """
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON;")
        cols_str = f"({', '.join([f'{col_name} {constraint.upper()}' for col_name, constraint in cols_dict.items()])})"
        if foreign_keys:
            fk_str = ", " + ", ".join(foreign_keys)
        else:
            fk_str = ""
        query = f"CREATE TABLE {table_name} {cols_str}{fk_str}"
        try:
            cursor.execute(query)
            print(f"Table '{table_name}' created successfully.")
        except sqlite3.Error as err:
            print(f"An error occurred: {err}")
        finally:
            conn.commit()

def insert_data(db_path: str, table_name: str, data: list[tuple[Any, ...]]) -> None:
    """
    Inserts data into an SQLite table.

    Parameters:
    - table_name (str): Name of the table to insert data into.
    - data (list of tuples): List of tuples, each tuple represents a row of data.
                            Example: [(1, '2023-01-01'), (2, '2023-01-02')]
    """
    with sqlite3.connect(db_path) as conn:
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

def get_table_info(table, db_path):
    with sqlite3.connect(db_path) as conn:
        try:
            cursor = conn.cursor()
            cursor.execute(f"PRAGMA table_info('{table}');")
            res = cursor.fetchall()
            return res
        except sqlite3.IntegrityError as int_err:
            raise sqlite3.IntegrityError("Database query failed") from int_err
        except sqlite3.DatabaseError as db_err:
            raise sqlite3.DatabaseError("Database query failed") from db_err

def process_multiselect(selections):
    return [sel.replace(" ", "_").lower() for sel in selections]

if __name__ == "__main__":
    print(process_multiselect(['Pubs Closed']))