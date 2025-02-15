from typing import Optional, Any
import sqlite3
from src.utils import query_db, get_table_info, convert_to_date
from src.backend.erd_manager import Visualizer

class DataServer:
    def __init__(self, db_path, graph_path, mental_path) -> None:
        self._db = db_path
        self._graph = graph_path
        self._mental = mental_path

    def serve_erd(self, graph_id):        
        erd = Visualizer(self._graph)
        return erd.get_adj_list(graph_id)

    def serve_table(self, db_name, table):
        db_path = f"src/backend/data/{db_name}"
        return get_table_info(table, db_path)

    def serve_time_series(self, restrs = []):
        if not restrs:
            query = """
                    SELECT Date.date, SUM(DailyRestriction.in_place) AS total_restrictions
                    FROM DailyRestriction
                    JOIN Date ON DailyRestriction.date_id = Date.date_id
                    GROUP BY Date.date;
                    """
            return query_db(query, self._db, restrs)
        else:
            placeholders = ', '.join(['?'] * len(restrs))
            query = f"""
                SELECT Date.date, SUM(DailyRestriction.in_place) AS total_restrictions
                FROM DailyRestriction
                JOIN Date ON DailyRestriction.date_id = Date.date_id
                JOIN Restriction ON DailyRestriction.restriction_id = Restriction.restriction_id
                WHERE Restriction.restriction IN ({placeholders})
                GROUP BY Date.date;
            """
            with sqlite3.connect(self._db) as conn:
                cursor = conn.cursor()
                cursor.execute(query, restrs)
                return cursor.fetchall()
        # return query_db(query, self._db, restrs)

    def serve_restr_distr(self, end_date = None):
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

    def serve_timeline(self):
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
    def serve_second_series(db_name, table_name):
        query = f"SELECT time, measured_value FROM {table_name};"
        raw_data = query_db(query, f"src/backend/data/{db_name}")
        processed_data = [(convert_to_date(row[0]), row[1]) for row in raw_data]
        return processed_data

if __name__ == "__main__":
    server = DataServer("src/backend/data/covid.db", "src/backend/data/graph.db", 'src/backend/data/mental_health.db')
    print(server.serve_second_series("mental_health.db", "MHCareCluster"))

