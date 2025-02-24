"""
Module for serving database queries and ERD visualizations.

This module defines the `DataServer` class, which acts as a backend service
to fetch ERD structures, table information, time series data, restriction distributions,
timelines, and other relevant data from an SQLite database.

Dependencies:
- `query_db`: Executes SQL queries on the database.
- `get_table_info`: Retrieves schema information for a given table.
- `convert_to_date`: Converts time values into date format.
- `Visualizer`: Manages ERD (Entity-Relationship Diagram) data.
- `PATHS`: Stores database file paths.

Example Usage:
    server = DataServer(PATHS["covid.db"], PATHS["graph.db"], PATHS["custom.db"])
    erd_data = server.serve_erd(graph_id=1)
    table_info = server.serve_table("covid", "Date")
    time_series_data = server.serve_time_series(["Lockdown", "Curfew"])
"""
from src.utils import query_db, get_table_info, convert_to_date
from src.backend.erd_manager import Visualizer
from src.config import PATHS

class DataServer:
    """
    Backend service for querying ERD structures, table metadata, and time series data.

    Attributes:
        _db (str): Path to the main database.
        _graph (str): Path to the graph database.
        _custom (str): Path to a custom database (if applicable).
    """
    def __init__(self, db_path: str, graph_path: str, custom_path: str) -> None:
        """
        Initializes the DataServer with database paths.

        Args:
            db_path (str): Path to the main database.
            graph_path (str): Path to the graph database.
            custom_path (str): Path to an additional database.
        """
        self._db = db_path
        self._graph = graph_path
        self._custom = custom_path

    def serve_erd(self, graph_id: int) -> dict:
        """
        Retrieves the adjacency list for a given graph from the ERD manager.

        Args:
            graph_id (int): The ID of the graph to retrieve.

        Returns:
            dict: Adjacency list of the graph.
        """
        erd = Visualizer(self._graph)
        return erd.get_adj_list(graph_id)

    def serve_table(self, db_name: str, table: str) ->list[tuple]:
        """
        Fetches schema details for a specified table.

        Args:
            db_name (str): Name of the database.
            table (str): Name of the table.
        """
        db_path = PATHS[db_name]
        return get_table_info(table, db_path)

    def serve_time_series(self, restrs: list[str] = []) -> list[str]:
        """
        Retrieves time-series data of restrictions applied over time.

        Args:
            restrs (list[str], optional): List of specific restrictions to filter by.
                                          Defaults to an empty list (fetch all restrictions).

        Returns:
            list[tuple]: List of tuples containing date and total restrictions applied.
        """
        if not restrs:
            query = """
                    SELECT Date.date, SUM(DailyRestriction.in_place) AS total_restrictions
                    FROM DailyRestriction
                    JOIN Date ON DailyRestriction.date_id = Date.date_id
                    GROUP BY Date.date;
                    """
            return query_db(query, self._db)

        placeholders = ', '.join(['?'] * len(restrs))
        query = f"""
            SELECT Date.date, SUM(DailyRestriction.in_place) AS total_restrictions
            FROM DailyRestriction
            JOIN Date ON DailyRestriction.date_id = Date.date_id
            JOIN Restriction ON DailyRestriction.restriction_id = Restriction.restriction_id
            WHERE Restriction.restriction IN ({placeholders})
            GROUP BY Date.date;
        """
        return query_db(query, self._db, restrs)

    def serve_restr_distr(self, end_date: str = None) -> list[tuple[str]]:
        """
        Fetches the distribution of restrictions up to a specific date.

        Args:
            end_date (str, optional): The latest date to include in the distribution.
                                      If None, returns the full distribution.

        Returns:
            list[tuple]: List of tuples containing restriction types and their frequency.
        """
        if end_date is not None:
            query = """
                    SELECT Restriction.restriction AS restriction, SUM(DailyRestriction.in_place) AS total_restrictions
                    FROM DailyRestriction
                    JOIN Restriction ON DailyRestriction.restriction_id = Restriction.restriction_id
                    WHERE date_id <= (SELECT date_id FROM Date WHERE date = ?)
                    GROUP BY Restriction.restriction;
                    """
            return query_db(query, self._db, (end_date,))
        else:
            query = """
                    SELECT Restriction.restriction AS restriction, SUM(DailyRestriction.in_place) AS total_restrictions
                    FROM DailyRestriction
                    JOIN Restriction ON DailyRestriction.restriction_id = Restriction.restriction_id
                    GROUP BY Restriction.restriction;
                    """
            return query_db(query, self._db)

    def serve_timeline(self) -> list[tuple[str]]:
        """
        Retrieves a timeline of restrictions along with their data sources.

        Returns:
            list[tuple]: List of tuples with (date, source name, source URL).
        """
        query = """
                SELECT DISTINCT 
                    d.date AS date_value, 
                    s.name AS source_name, 
                    s.source AS source_url
                FROM SummaryRestriction sr
                JOIN Date d ON sr.date_id = d.date_id
                JOIN Source s ON sr.source_id = s.source_id;
                """
        return query_db(query, self._db)

    @staticmethod
    def serve_second_series(db_name: str, table_name: str) -> list[str]:
        """
        Fetches time series data from a specific table and converts time values.

        Args:
            db_name (str): Name of the database.
            table_name (str): Name of the table containing time series data.

        Returns:
            list[tuple]: Processed time series data as (converted_date, measured_value).
        """
        query = f"SELECT time, measured_value FROM {table_name};"
        raw_data = query_db(query, PATHS[db_name])
        try:
            processed_data = [(convert_to_date(row[0]), row[1]) for row in raw_data]
        except ValueError:
            processed_data = [(row[0], row[1]) for row in raw_data]
        return processed_data
