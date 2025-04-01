import pytest
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import json
from datetime import datetime
import datetime as dt

# Add the project root to Python path
project_root = str(Path(__file__).resolve().parents[3])
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import the app module
from src.frontend.app import app

@pytest.fixture(scope="session")
def test_client():
    """Create a test client with mocked dependencies."""
    # Mock all dependencies
    with patch('src.frontend.app.DataServer') as mock_data_server, \
         patch('src.frontend.app.Diagrams') as mock_diagrams, \
         patch('src.frontend.app.create_dash_app') as mock_dash_app, \
         patch('src.frontend.app.get_db_path') as mock_get_db_path, \
         patch('src.frontend.app.Session') as mock_session, \
         patch('src.frontend.app.CRUD') as mock_crud, \
         patch('src.frontend.app.Model') as mock_model, \
         patch('src.frontend.app.RevertManager') as mock_revert_manager, \
         patch('src.frontend.app.get_data_server') as mock_get_data_server, \
         patch('src.frontend.app.get_databases') as mock_get_databases, \
         patch('src.frontend.app.show_tables') as mock_show_tables, \
         patch('src.frontend.app.create_database') as mock_create_database:
        
        # Configure mocks
        mock_data_server.return_value = MagicMock()
        mock_diagrams.return_value = MagicMock()
        mock_dash_app.return_value = MagicMock()
        mock_get_db_path.return_value = 'test_covid.db'
        mock_session.return_value = MagicMock()
        mock_crud.return_value = MagicMock()
        mock_model.return_value = MagicMock()
        mock_revert_manager.return_value = MagicMock()
        mock_get_data_server.return_value = MagicMock()
        mock_get_databases.return_value = ['covid.db']
        mock_show_tables.return_value = ['table1', 'table2']
        mock_create_database.return_value = True
        
        # Configure the app for testing
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        
        yield app.test_client()

def test_index_route(test_client):
    """Test the index route."""
    response = test_client.get('/')
    assert response.status_code == 200
    assert b"COVID-19 Insights" in response.data

def test_dataset_route(test_client):
    """Test the dataset route."""
    response = test_client.get('/dataset')
    assert response.status_code == 200
    assert b"Dataset Management" in response.data

def test_time_series_route(test_client):
    """Test the time series route."""
    response = test_client.get('/time-series')
    assert response.status_code == 200
    assert b"Time Series Analysis" in response.data

def test_timeline_route(test_client):
    """Test the timeline route."""
    response = test_client.get('/timeline')
    assert response.status_code == 200
    assert b"COVID-19 Event Timeline" in response.data

def test_table_crud_route(test_client):
    """Test the table CRUD route."""
    response = test_client.get('/crud-view')
    assert response.status_code == 200
    assert b"Table CRUD Operations" in response.data

def test_audit_log_route(test_client):
    """Test the audit log route."""
    response = test_client.get('/audit-log')
    assert response.status_code == 200
    assert b"Audit Log" in response.data

def test_fetch_databases_api(test_client):
    """Test the fetch databases API endpoint."""
    response = test_client.get('/api/databases')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert isinstance(data, list)
    assert 'covid.db' in data

def test_get_tables_api(test_client):
    """Test the get tables API endpoint."""
    response = test_client.get('/api/tables/covid.db')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert isinstance(data, list)

def test_get_restrictions_api(test_client):
    """Test the get restrictions API endpoint."""
    response = test_client.get('/api/restrictions?database=covid.db')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert isinstance(data, list)

def test_create_database_api(test_client):
    """Test the create database API endpoint."""
    test_db_name = "test_db.db"
    response = test_client.post('/api/create-database', 
                               json={'database_name': test_db_name})
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True

    # Clean up
    response = test_client.post('/api/delete-database',
                               json={'database_name': test_db_name})
    assert response.status_code == 200

def test_create_table_api(test_client):
    """Test the create table API endpoint."""
    test_db_name = "test_db.db"
    test_table_name = "test_table"
    
    # Create database first
    test_client.post('/api/create-database', 
                     json={'database_name': test_db_name})
    
    # Create table
    response = test_client.post('/api/create-table',
                               json={
                                   'database_name': test_db_name,
                                   'table_name': test_table_name,
                                   'columns': [
                                       {'name': 'id', 'type': 'INTEGER', 'primary_key': True},
                                       {'name': 'name', 'type': 'TEXT'}
                                   ]
                               })
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True

    # Clean up
    test_client.post('/api/delete-table',
                     json={'database_name': test_db_name, 'table_name': test_table_name})
    test_client.post('/api/delete-database',
                     json={'database_name': test_db_name})

def test_delete_table_api(test_client):
    """Test the delete table API endpoint."""
    test_db_name = "test_db.db"
    test_table_name = "test_table"
    
    # Setup: create database and table
    test_client.post('/api/create-database', 
                     json={'database_name': test_db_name})
    test_client.post('/api/create-table',
                     json={
                         'database_name': test_db_name,
                         'table_name': test_table_name,
                         'columns': [
                             {'name': 'id', 'type': 'INTEGER', 'primary_key': True},
                             {'name': 'name', 'type': 'TEXT'}
                         ]
                     })
    
    # Delete table
    response = test_client.post('/api/delete-table',
                               json={'database_name': test_db_name, 'table_name': test_table_name})
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True

    # Clean up
    test_client.post('/api/delete-database',
                     json={'database_name': test_db_name})

def test_insert_data_api(test_client):
    """Test the insert data API endpoint."""
    test_db_name = "test_db.db"
    test_table_name = "test_table"
    
    # Setup: create database and table
    test_client.post('/api/create-database', 
                     json={'database_name': test_db_name})
    test_client.post('/api/create-table',
                     json={
                         'database_name': test_db_name,
                         'table_name': test_table_name,
                         'columns': [
                             {'name': 'id', 'type': 'INTEGER', 'primary_key': True},
                             {'name': 'name', 'type': 'TEXT'}
                         ]
                     })
    
    # Insert data
    response = test_client.post('/api/insert-data',
                               json={
                                   'database_name': test_db_name,
                                   'table_name': test_table_name,
                                   'data': [
                                       {'id': 1, 'name': 'Test 1'},
                                       {'id': 2, 'name': 'Test 2'}
                                   ]
                               })
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True

    # Clean up
    test_client.post('/api/delete-table',
                     json={'database_name': test_db_name, 'table_name': test_table_name})
    test_client.post('/api/delete-database',
                     json={'database_name': test_db_name})

def test_regression_api(test_client):
    """Test the regression API endpoint."""
    response = test_client.get('/api/regression')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert isinstance(data, dict)
    assert 'success' in data

def test_analyze_data_api(test_client):
    """Test the analyze data API endpoint."""
    response = test_client.get('/api/analyze')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert isinstance(data, dict)
    assert 'success' in data

def test_revert_change_api(test_client):
    """Test the revert change API endpoint."""
    response = test_client.post('/revert-change',
                               json={'change_id': 1})
    assert response.status_code == 200
    data = json.loads(response.data)
    assert isinstance(data, dict)
    assert 'success' in data
