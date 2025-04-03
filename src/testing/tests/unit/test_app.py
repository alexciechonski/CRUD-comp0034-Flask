import pytest
from src.frontend.app import app

@pytest.fixture
def client():
    with app.test_client() as client:
        yield client

def test_index(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b'COVID-19 Insights' in response.data

def test_fetch_databases(client):
    response = client.get('/api/databases')
    assert response.status_code == 200
    assert isinstance(response.json, list)

def test_dataset(client):
    response = client.get('/dataset')
    assert response.status_code == 200
    assert b'Dataset Overview' in response.data

def test_time_series_get(client):
    response = client.get('/time-series')
    assert response.status_code == 200
    assert b'Time Series' in response.data

def test_timeline(client):
    response = client.get('/timeline')
    assert response.status_code == 200

def test_get_restrictions(client):
    response = client.get('/api/restrictions')
    assert response.status_code == 200
    assert isinstance(response.json, list)

def test_get_tables(client):
    response = client.get('/api/tables/covid.db')
    assert response.status_code == 200
    assert isinstance(response.json, list)

def test_analyze_data_invalid(client):
    response = client.get('/api/analyze')
    assert response.status_code == 400

def test_table_crud(client):
    response = client.get('/crud-view')
    assert response.status_code == 200

def test_audit_log(client):
    response = client.get('/audit-log')
    assert response.status_code == 200
    assert b'Audit Log' in response.data
