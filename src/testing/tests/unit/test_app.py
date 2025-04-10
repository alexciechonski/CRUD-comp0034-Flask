import pytest
from src.frontend.app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test-secret-key'
    app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing
    return app.test_client()

def test_index(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b'COVID-19 Insights' in response.data

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

def test_table_crud(client):
    response = client.get('/crud-view')
    assert response.status_code == 200

def test_audit_log(client):
    response = client.get('/audit-log')
    assert response.status_code == 200
    assert b'Audit Log' in response.data

def test_restr_distr(client):
    response = client.get('/restriction-distribution?end_date=2021-06-15')
    assert response.status_code == 200
    assert b"Global Restriction Patterns" in response.data
    assert b"Most Common Restriction" in response.data
    assert b"As of Date" in response.data

    # # Test with invalid date (should use default)
    response = client.get('/restriction-distribution?end_date=2020-01-15')
    assert response.status_code == 200
    assert b"No data available for the selected date" in response.data
