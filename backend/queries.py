"""
This module facilitates interaction with a SQLite database using the `TestQueries` class.

Classes:
    - TestQueries: Provides methods to execute predefined SQL queries,
      including SELECT, INSERT, UPDATE,
      and DELETE operations.

Functions:
    - main(): Demonstrates the usage of the `TestQueries` class.

Usage:
    Initialize `TestQueries` with a database path and a list of SQL queries
    to perform database operations.
"""
import sqlite3
from typing import Optional, Any
from utils import get_queries

class Queries:
    """Base class for test queries"""
    def __init__(self, db_path: str, queries_path: str) -> None:
        """
        Initializes the Queries with database paths and queries as a child of TestQueries.

        Parameters:
            db_path (str): Path to the main database file.
            queries (list[str]): List of SQL queries to test.
        """
        self._db = db_path
        self.queries = get_queries(queries_path)

    def query_db(self, query: str) -> Optional[list[tuple[Any, ...]]]:
        """
        Executes a query against the main database.

        Parameters:
            query (str): The SQL query to execute.

        Returns:
            list[tuple[Any, ...]]: Results of the query if it is a SELECT query.
        """
        with sqlite3.connect(self._db) as conn:
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

    def sum_restrictions_for_date(self) -> list[tuple[int, int]]:
        """Queries the database and finds the sum of all restrictions for each date"""
        return self.query_db(self.queries[0])

    def insert(self):
        """Inserts a record into the database"""
        return self.query_db(self.queries[1])

    def update(self):
        """Updates a record in the database"""
        return self.query_db(self.queries[2])

    def delete(self):
        """Deletes a record from the database"""
        return self.query_db(self.queries[3])

    def group_restrictions_until_date(self) -> list[tuple[int, int]]:
        """Finds the number of individual restrictions up to the date specified"""
        return self.query_db(self.queries[4])

    def get_timeline_data(self) -> list[tuple[str, str]]:
        """Obtains all policy changes dates, names and urls"""
        return self.query_db(self.queries[5])

def main():
    """
    The main function demonstrates the usage of the `TestQueries` class by executing
    a series of predefined SQL queries.

    It initializes the `TestQueries` instance with the database path and queries
    loaded from a file, then sequentially executes the following operations:
    1. Summing restrictions for each date.
    2. Inserting a record.
    3. Updating a record.
    4. Deleting a record.
    5. Grouping restrictions up to a specific date.
    6. Retrieving timeline data (policy change dates, names, and URLs).

    Ensure the database path and queries file are correctly specified before running the function.
    """
    # setup
    queries_path = "coursework2/queries.txt"
    db_path = "courswork2/covid_copy.db"
    test_queries = Queries(db_path, queries_path)

    # Query 1
    test_queries.sum_restrictions_for_date()

    # Query 2
    test_queries.insert()

    # Query 3
    test_queries.update()

    # Query 4
    test_queries.delete()

    # Query 5
    test_queries.group_restrictions_until_date()

    # Query 6
    test_queries.get_timeline_data()

if __name__ == "__main__":
    main()
    