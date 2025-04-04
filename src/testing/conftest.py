EXP_OUTPUTS = "src/testing/exp_outputs.json"
DEATHS_FILEPATH = "src/testing/resources/deaths.csv"
BAD_SCHEMA_PATH = "src/testing/resources/bad_schema.csv"

import pytest
import os
import sys
from pathlib import Path
import sqlite3
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.backend.data_server import DataServer
from src.backend.erd_manager import CRUD
from src.backend.log.log_manager import LogManager
from src.backend.revert_manager import RevertManager
from src.backend.validation import Validator as v
from src.utils import get_db_path, get_table_info, show_tables
from src.backend.erd_manager import Visualizer
from src.frontend.app import app
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String
from sqlalchemy.orm import declarative_base
from src.backend.log.log_manager import LogManager
import src.backend.log.log_manager as log_module  # to patch get_db_path + LOG_PATH
import tempfile

# Add the project root to Python path
project_root = str(Path(__file__).parent.parent.parent.parent)
sys.path.append(project_root)

@pytest.fixture
def test_db_path():
    """Fixture to get the path to the test database."""
    return get_db_path('test.db')

@pytest.fixture
def test_db_engine(test_db_path):
    """Fixture to create a SQLAlchemy engine for the test database."""
    return create_engine(f'sqlite:///{test_db_path}')

@pytest.fixture
def covid_server():
    return DataServer("covid.db")

# @pytest.fixture
# def test_db_session(test_db_engine):
#     """Fixture to create a SQLAlchemy session for the test database."""
#     Session = sessionmaker(bind=test_db_engine)
#     session = Session()
#     yield session
#     session.close()

@pytest.fixture
def test_data_server():
    """Fixture to create a DataServer instance for testing."""
    return DataServer('test.db')

# @pytest.fixture
# def test_crud():
#     """Fixture to create a CRUD instance for testing."""
#     return CRUD('test.db')

# @pytest.fixture
# def test_log_manager():
#     """Fixture to create a LogManager instance for testing."""
#     return LogManager()

# @pytest.fixture
# def test_revert_manager():
#     """Fixture to create a RevertManager instance for testing."""
#     return RevertManager('test.db')

@pytest.fixture
def test_validator():
    """Fixture to create a Validator instance for testing."""
    return v()

# @pytest.fixture
# def sample_data():
#     """Fixture to provide sample data for testing."""
#     return {
#         'date': ['2020-01-01', '2020-01-02', '2020-01-03'],
#         'cases': [100, 200, 300],
#         'deaths': [10, 20, 30]
#     }

# @pytest.fixture
# def sample_dataframe(sample_data):
#     """Fixture to create a pandas DataFrame from sample data."""
#     return pd.DataFrame(sample_data)

# @pytest.fixture
# def test_table_name():
#     """Fixture to provide a test table name."""
#     return 'test_table'

# @pytest.fixture
# def setup_test_database(test_db_path, test_table_name, sample_dataframe):
#     """Fixture to set up a test database with sample data."""
#     # Create the database if it doesn't exist
#     if not os.path.exists(test_db_path):
#         conn = sqlite3.connect(test_db_path)
#         conn.close()
    
#     # Create the test table and insert sample data
#     engine = create_engine(f'sqlite:///{test_db_path}')
#     sample_dataframe.to_sql(test_table_name, engine, if_exists='replace', index=False)
    
#     yield
    
#     # Clean up after tests
#     if os.path.exists(test_db_path):
#         os.remove(test_db_path)

# @pytest.fixture
# def mock_flask_app():
#     """Fixture to create a mock Flask app for testing."""
#     from flask import Flask
#     app = Flask(__name__)
#     app.config['TESTING'] = True
#     return app

# @pytest.fixture
# def mock_flask_client(mock_flask_app):
#     """Fixture to create a Flask test client."""
#     return mock_flask_app.test_client()

@pytest.fixture
def client():
    with app.test_client() as client:
        yield client

# @pytest.fixture
# def mock_request_context(mock_flask_app):
#     """Fixture to create a Flask request context."""
#     return mock_flask_app.test_request_context()

# @pytest.fixture
# def mock_session():
#     """Fixture to create a mock session object."""
#     from flask import session
#     session['user_id'] = 1
#     return session

# @pytest.fixture
# def mock_db_connection():
#     """Fixture to create a mock database connection."""
#     class MockConnection:
#         def __init__(self):
#             self.cursor = self.MockCursor()
        
#         class MockCursor:
#             def execute(self, query, params=None):
#                 pass
            
#             def fetchall(self):
#                 return []
            
#             def fetchone(self):
#                 return None
            
#             def close(self):
#                 pass
        
#         def close(self):
#             pass
    
#     return MockConnection()

# @pytest.fixture
# def mock_sqlalchemy_session():
#     """Fixture to create a mock SQLAlchemy session."""
#     class MockSession:
#         def query(self, *args):
#             return self
        
#         def filter(self, *args):
#             return self
        
#         def first(self):
#             return None
        
#         def all(self):
#             return []
        
#         def add(self, obj):
#             pass
        
#         def commit(self):
#             pass
        
#         def rollback(self):
#             pass
        
#         def close(self):
#             pass
    
#     return MockSession()

# @pytest.fixture
# def mock_plotly_figure():
#     """Fixture to create a mock Plotly figure."""
#     class MockFigure:
#         def to_html(self, *args, **kwargs):
#             return "<div>Mock Plotly Figure</div>"
    
#     return MockFigure()

# @pytest.fixture
# def mock_networkx_graph():
#     """Fixture to create a mock NetworkX graph."""
#     import networkx as nx
#     G = nx.Graph()
#     G.add_node('test_node')
#     return G

# @pytest.fixture
# def mock_matplotlib_figure():
#     """Fixture to create a mock Matplotlib figure."""
#     import matplotlib.pyplot as plt
#     fig = plt.figure()
#     plt.plot([1, 2, 3], [1, 2, 3])
#     return fig

# @pytest.fixture
# def mock_pandas_dataframe():
#     """Fixture to create a mock pandas DataFrame."""
#     return pd.DataFrame({
#         'column1': [1, 2, 3],
#         'column2': ['a', 'b', 'c']
#     })

# @pytest.fixture
# def mock_numpy_array():
#     """Fixture to create a mock NumPy array."""
#     import numpy as np
#     return np.array([1, 2, 3, 4, 5])

# @pytest.fixture
# def mock_file_object():
#     """Fixture to create a mock file object."""
#     class MockFile:
#         def __init__(self):
#             self.content = b"test content"
#             self.position = 0
        
#         def read(self, size=-1):
#             if size == -1:
#                 return self.content
#             data = self.content[self.position:self.position + size]
#             self.position += size
#             return data
        
#         def seek(self, offset, whence=0):
#             if whence == 0:
#                 self.position = offset
#             elif whence == 1:
#                 self.position += offset
#             elif whence == 2:
#                 self.position = len(self.content) + offset
        
#         def tell(self):
#             return self.position
        
#         def close(self):
#             pass
    
#     return MockFile()

# @pytest.fixture
# def mock_csv_file():
#     """Fixture to create a mock CSV file."""
#     return "date,cases,deaths\n2020-01-01,100,10\n2020-01-02,200,20\n2020-01-03,300,30"

# @pytest.fixture
# def mock_json_data():
#     """Fixture to create mock JSON data."""
#     return {
#         "key1": "value1",
#         "key2": ["item1", "item2"],
#         "key3": {"nested": "value"}
#     }

# @pytest.fixture
# def mock_datetime():
#     """Fixture to create mock datetime objects."""
#     from datetime import datetime
#     return datetime(2020, 1, 1, 12, 0, 0)

# @pytest.fixture
# def mock_time_series_data():
#     """Fixture to create mock time series data."""
#     return {
#         'dates': pd.date_range(start='2020-01-01', periods=5),
#         'values': [100, 200, 300, 400, 500]
#     }

# @pytest.fixture
# def mock_correlation_data():
#     """Fixture to create mock correlation data."""
#     return {
#         'x': [1, 2, 3, 4, 5],
#         'y': [2, 4, 6, 8, 10],
#         'correlation': 1.0
#     }

# @pytest.fixture
# def mock_prediction_data():
#     """Fixture to create mock prediction data."""
#     return {
#         'actual': [100, 200, 300],
#         'predicted': [110, 210, 310],
#         'error': [10, 10, 10]
#     }

# @pytest.fixture
# def mock_validation_result():
#     """Fixture to create mock validation results."""
#     return {
#         'is_valid': True,
#         'errors': [],
#         'warnings': []
#     }

# @pytest.fixture
# def mock_audit_log_entry():
#     """Fixture to create mock audit log entries."""
#     return {
#         'timestamp': '2020-01-01 12:00:00',
#         'user': 'test_user',
#         'action': 'create',
#         'table': 'test_table',
#         'details': {'column': 'value'}
#     }

# @pytest.fixture
# def mock_revert_data():
#     """Fixture to create mock revert data."""
#     return {
#         'table': 'test_table',
#         'operation': 'delete',
#         'data': {'id': 1, 'value': 'test'}
#     }

# @pytest.fixture
# def mock_graph_data():
#     """Fixture to create mock graph data."""
#     return {
#         'nodes': [
#             {'id': 1, 'label': 'Node 1'},
#             {'id': 2, 'label': 'Node 2'}
#         ],
#         'edges': [
#             {'from': 1, 'to': 2, 'label': 'relation'}
#         ]
#     }

# @pytest.fixture
# def mock_erd_data():
#     """Fixture to create mock ERD data."""
#     return {
#         'tables': [
#             {
#                 'name': 'table1',
#                 'columns': [
#                     {'name': 'id', 'type': 'INTEGER', 'primary_key': True},
#                     {'name': 'value', 'type': 'TEXT'}
#                 ]
#             }
#         ],
#         'relationships': [
#             {
#                 'from': 'table1',
#                 'to': 'table2',
#                 'type': 'one-to-many'
#             }
#         ]
#     } 

@pytest.fixture
def temp_log_file(monkeypatch):
    with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8') as tmp:
        tmp.write("[]")  # write an empty JSON array to initialize the log
        tmp.flush()      # make sure it's written to disk
        monkeypatch.setattr(log_module, "LOG_PATH", tmp.name)
        yield tmp.name
        os.remove(tmp.name)

@pytest.fixture
def in_memory_db(monkeypatch):
    monkeypatch.setattr(log_module, "get_db_path", lambda name: ":memory:")
    engine = create_engine("sqlite:///:memory:")
    metadata = MetaData()
    test_table = Table("test_table", metadata,
        Column("id", Integer, primary_key=True),
        Column("name", String),
    )
    metadata.create_all(engine)
    return engine