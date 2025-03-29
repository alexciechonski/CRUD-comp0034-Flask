"""
Module for serving database queries and ERD visualizations.

This module defines the `DataServer` class, which acts as a backend service
to fetch ERD structures, table information, time series data, restriction distributions,
timelines, and other relevant data using SQLAlchemy.
"""
from typing import List, Dict, Tuple
from sqlalchemy import func, desc, create_engine
from sqlalchemy.orm import Session, sessionmaker
from src.backend.models import init_db, Date, Restriction, DailyRestriction, Source, SummaryRestriction
from src.backend.erd_manager import Visualizer
import pandas as pd
from src.utils import get_table_info, get_db_path
from sqlalchemy import Table, MetaData

class DataServer:
    """Class for serving data from the database"""
    @staticmethod
    def get_session(db_name):
        """Get a SQLAlchemy session for a database
        
        Args:
            db_name (str): Name of the database to connect to
            
        Returns:
            Session: SQLAlchemy session
        """
        engine = create_engine(f'sqlite:///{get_db_path(db_name)}')
        Session = sessionmaker(bind=engine)
        return Session()

    def __init__(self, db_name: str):
        """Initialize the DataServer with database paths
        
        Args:
            db_name (str): Name of the database to connect to
        """
        self._db_session = self.get_session('covid.db')
        self._graph_session = self.get_session('graph.db')
        self._custom_session = self.get_session('custom.db')

    def serve_erd(self, graph_id: int) -> Dict:
        """
        Retrieves the adjacency list for a given graph from the ERD manager.

        Args:
            graph_id (int): The ID of the graph to retrieve.

        Returns:
            dict: Adjacency list of the graph.
        """
        erd = Visualizer(self._db_session)
        return erd.get_adj_list(graph_id)

    def serve_table(self, db_name: str, table: str) ->List[tuple]:
        """
        Fetches schema details for a specified table.

        Args:
            db_name (str): Name of the database.
            table (str): Name of the table.
        """
        db_path = get_db_path(db_name)
        return get_table_info(table, db_path)

    def serve_time_series(self, restrs: List[str], database: str, table: str) -> List[tuple]:
        """
        Retrieves time-series data using SQLAlchemy.

        Args:
            restrs (list[str]): List of specific restrictions to filter by.
            database (str): Name of the database to query. Defaults to 'covid.db'.
            table (str): Name of the table to query. If None, uses default COVID tables.

        Returns:
            list[tuple]: List of tuples containing date and total restrictions applied.
        """
        print(f"serve_time_series called with: database={database}, table={table}, restrictions={restrs}")
        if not restrs:
            restrs = []
        
        if database == 'covid.db':
            try:
                # Base query joining Date and DailyRestriction
                query = self._db_session.query(
                    Date.date,
                    func.count(DailyRestriction.restriction_id).filter(DailyRestriction.in_place == 1).label('total_restrictions')
                ).join(
                    DailyRestriction,
                    Date.date_id == DailyRestriction.date_id
                )

                # Add restriction filter if restrictions are specified
                if restrs:
                    print(f"Filtering for restrictions: {restrs}")
                    query = query.join(
                        Restriction,
                        DailyRestriction.restriction_id == Restriction.restriction_id
                    ).filter(
                        Restriction.restriction.in_(restrs)
                    )

                # Group by date and order by date
                query = query.group_by(Date.date).order_by(Date.date)
                
                print("Executing query...")
                result = query.all()
                print(f"Query returned {len(result)} rows")
                
                if not result:
                    print("No results found, returning default value")
                    return [(None, 0)]
                return result
                
            except Exception as e:
                print(f"Error in serve_time_series (covid.db): {str(e)}")
                raise
        
        session = None
        try:
            session = init_db(f'sqlite:///{get_db_path(database)}')()
            # For custom tables, we need to use the table object dynamically
            metadata = MetaData()
            table_obj = Table(table, metadata, autoload_with=session.bind)
            
            result = session.query(
                table_obj.c.time,
                table_obj.c.measured_value
            ).order_by(table_obj.c.time).all()
            
            if not result:
                return [(None, 0)]
            return result
        except Exception as e:
            print(f"Error in serve_time_series (custom db): {str(e)}")
            raise
        finally:
            if session:
                session.close()
    

    def serve_restr_distr(self, end_date: str = None) -> List[tuple]:
        """
        Fetches the distribution of restrictions using SQLAlchemy.

        Args:
            end_date (str): The latest date to include in the distribution.

        Returns:
            list[tuple]: List of tuples containing restriction types and their frequency.
        """
        query = self._db_session.query(
            Restriction.restriction,
            func.sum(DailyRestriction.in_place).label('total_restrictions')
        ).join(DailyRestriction)

        if end_date:
            date_id = self._db_session.query(Date.date_id).filter(Date.date == end_date).scalar()
            if date_id:
                query = query.join(DailyRestriction.date).filter(Date.date_id <= date_id)

        return query.group_by(Restriction.restriction).all()

    def serve_timeline(self) -> List[tuple]:
        """
        Retrieves a timeline of restrictions using SQLAlchemy.

        Returns:
            List[tuple]: List of tuples with (date, source name, source URL).
        """
        return self._db_session.query(
            Date.date.label('date_value'),
            Source.name.label('source_name'),
            Source.source.label('source_url')
        ).join(
            SummaryRestriction, Date.date_id == SummaryRestriction.date_id
        ).join(
            Source, SummaryRestriction.source_id == Source.source_id
        ).distinct().all()

    def serve_second_series(self, db_name: str, table_name: str) -> List[tuple]:
        """
        Fetches time series data from a specific table and converts time values.

        Args:
            db_name (str): Name of the database.
            table_name (str): Name of the table containing time series data.

        Returns:
            List[tuple]: Processed time series data as (converted_date, measured_value).
        """
        if not db_name or not table_name:
            print("Missing database name or table name")
            return []

        session = None
        try:
            # Use the appropriate session based on the database
            if db_name == 'covid.db':
                session = self._db_session
            elif db_name == 'custom.db':
                session = self._custom_session
            else:
                # Create a new session for other databases
                engine = create_engine(f'sqlite:///{get_db_path(db_name)}')
                Session = sessionmaker(bind=engine)
                session = Session()

            from sqlalchemy import Table, MetaData
            metadata = MetaData()
            table_obj = Table(table_name, metadata, autoload_with=session.bind)
            
            result = session.query(
                table_obj.c.time,
                table_obj.c.measured_value
            ).order_by(table_obj.c.time).all()
            
            if not result:
                print(f"No data found in table {table_name}")
                return []

            processed_data = []
            for row in result:
                try:
                    # Handle different date formats
                    date_str = str(row[0])
                    if '/' in date_str:
                        # M/YYYY format
                        month, year = date_str.split('/')
                        from datetime import datetime
                        date = datetime(int(year), int(month), 1)
                    else:
                        # Try parsing as ISO format
                        date = pd.to_datetime(date_str)
                    
                    value = float(row[1]) if row[1] is not None else 0
                    processed_data.append((date, value))
                except Exception as e:
                    print(f"Error processing row {row}: {str(e)}")
                    continue
            
            return sorted(processed_data, key=lambda x: x[0])
            
        except Exception as e:
            print(f"Error in serve_second_series: {str(e)}")
            return []
        finally:
            # Only close the session if we created it
            if db_name not in ['covid.db', 'custom.db'] and session:
                session.close()

    def get_restrictions(self, database: str = 'covid.db') -> List[str]:
        """
        Gets a list of available restrictions for a specific database.

        Args:
            database (str): Name of the database to get restrictions from. Defaults to 'covid.db'.

        Returns:
            List[str]: List of restriction names.
        """
        if database == 'covid.db':
            return [r.restriction for r in self._db_session.query(Restriction).all()]
        else:
            # For custom databases, return empty list as they don't have restrictions
            return []

    def get_date_range(self) -> Tuple[str, str]:
        """
        Retrieves the earliest and latest dates using SQLAlchemy.

        Returns:
            Tuple[str, str]: A tuple containing (earliest_date, latest_date).
        """
        result = self._db_session.query(
            func.min(Date.date),
            func.max(Date.date)
        ).first()
        
        if result and result[0]:
            return result
        return ('', '')

    def __del__(self):
        """Clean up database connections"""
        if hasattr(self, '_db_session'):
            self._db_session.close()
        if hasattr(self, '_custom_session'):
            self._custom_session.close()
        if hasattr(self, '_db_engine'):
            self._db_engine.dispose()
        if hasattr(self, '_custom_engine'):
            self._custom_engine.dispose()

# if __name__ == "__main__":
#     data_server = DataServer("covid.db")
#     time_series_data = data_server.serve_time_series(selected_restrictions, database=selected_db, table=table)

