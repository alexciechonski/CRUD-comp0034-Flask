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

def calculate_edge_point(x0, y0, x1, y1, node_size):
    """Calculate where the edge should end on the node's boundary."""
    dx, dy = x1 - x0, y1 - y0
    distance = math.sqrt(dx**2 + dy**2)
    
    # Scale the vector to stop at the node's edge
    scale = (distance - node_size / 2) / distance
    return x0 + dx * scale, y0 + dy * scale

def calculate_perpendicular(mid_x, mid_y, x0, y0, x1, y1, length=20):
    """Calculate points for a perpendicular T-style decorator."""
    dx, dy = x1 - x0, y1 - y0
    # Normalize to get perpendicular direction
    distance = math.sqrt(dx ** 2 + dy ** 2)
    if distance == 0:
        return mid_x, mid_y, mid_x, mid_y

    # Perpendicular direction vector
    perp_dx, perp_dy = -dy / distance, dx / distance

    # Points for the T-line (perpendicular to the edge)
    t_x1 = mid_x + perp_dx * length
    t_y1 = mid_y + perp_dy * length
    t_x2 = mid_x - perp_dx * length
    t_y2 = mid_y - perp_dy * length

    return t_x1, t_y1, t_x2, t_y2

if __name__ == "__main__":
    pass