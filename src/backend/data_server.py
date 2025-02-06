from typing import Optional, Any
import sqlite3
from src.utils import query_db, get_table_info
from html_parser import Parser
from src.backend.erd_manager import Visualizer

class DataServer:
    def __init__(self, db_path, graph_path) -> None:
        self._db = db_path
        self._graph = graph_path

    def serve_erd(self):        
        erd = Visualizer(self._graph)
        return erd.get_adj_list()

    def serve_table(self, table):
        return get_table_info(table, self._db)

    def serve_time_series(self):
        query = """
                SELECT Date.date, SUM(DailyRestriction.in_place) AS total_restrictions
                FROM DailyRestriction
                JOIN Date ON DailyRestriction.date_id = Date.date_id
                GROUP BY Date.date;
                """
        return query_db(query, self._db)

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

if __name__ == "__main__":
    server = DataServer("backend/covid.db", "backend/graph.db")
    print(server.serve_timeline())

    # with sqlite3.connect("backend/covid.db") as conn:
    #     cursor = conn.cursor()
    #     cursor.execute("PRAGMA table_info('Source');")
    #     res = cursor.fetchall()
    #     print(res)

    # print(query_db("SELECT source FROM Source", "backend/covid.db"))
