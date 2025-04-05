import pytest
from flask import Flask, render_template
from src.backend.routes import bp
import os
from datetime import datetime

@pytest.fixture
def test_client():
    # Use absolute path for templates
    template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../frontend/templates"))
    app = Flask(__name__, template_folder=template_dir)
    
    # Add secret key for CSRF protection
    app.config['SECRET_KEY'] = 'test-secret-key'
    app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing

    # Dummy routes for other dependencies used in templates
    @app.route('/', endpoint='index')
    def dummy_index():
        return 'Dummy index page'

    @app.route('/dataset', endpoint='dataset')
    def dummy_dataset():
        return 'Dummy dataset'

    @app.route('/table-crud', endpoint='table_crud')
    def dummy_table_crud():
        return 'Dummy table crud'

    @app.route('/time-series', endpoint='time_series')
    def dummy_time_series():
        return 'Dummy time series'

    @app.route('/audit-log', endpoint='audit_log')
    def dummy_audit_log():
        return 'Dummy audit_log'

    # Add dummy timeline route that uses the template
    @app.route('/timeline', endpoint='timeline')
    def dummy_timeline():
        try:
            events = app.config.get('TIMELINE_EVENTS', [])
            if events is None:
                raise Exception("Test error")
            return render_template('timeline.html', events=events, error=None)
        except Exception as e:
            return render_template('timeline.html', events=[], error=str(e))

    # Register blueprint
    app.register_blueprint(bp)
    app.config['TESTING'] = True
    return app.test_client()

class DummySession:
    def __init__(self):
        self.restriction_data = [
            type("RestrictionRecord", (), {"restriction": "stay_home", "count": 5}),
            type("RestrictionRecord", (), {"restriction": "mask_mandatory", "count": 3}),
            type("RestrictionRecord", (), {"restriction": "social_distancing", "count": 2})
        ]
        self.date_record = type("DateRecord", (), {"date": "2021-06-15"})()
    
    def query(self, *args, **kwargs): return self
    def filter(self, *args, **kwargs): return self
    def order_by(self, *args, **kwargs): return self
    def first(self): return self.date_record
    def close(self): pass
    def __enter__(self): return self
    def __exit__(self, *args): pass
    def all(self): return self.restriction_data
    def join(self, *args, **kwargs): return self
    def group_by(self, *args, **kwargs): return self

def test_restriction_distribution_route(test_client, monkeypatch):
    # Patch the DB session and query logic
    monkeypatch.setattr("src.backend.routes.Session", lambda: DummySession())
    
    # Test with valid date
    response = test_client.get('/restriction-distribution?end_date=2021-06-15')
    assert response.status_code == 200
    assert b"Global Restriction Patterns" in response.data
    assert b"Stay Home" in response.data
    assert b"Mask Mandatory" in response.data
    
    # Test with invalid date (should use default)
    response = test_client.get('/restriction-distribution?end_date=invalid-date')
    assert response.status_code == 200
    assert b"Global Restriction Patterns" in response.data

def test_timeline_route(test_client, monkeypatch):
    # Test data with datetime objects
    test_events = [
        (datetime(2020, 1, 1), "First Lockdown", "url1"),
        (datetime(2020, 3, 15), "Mask Mandate", "url2"),
        (datetime(2020, 6, 1), "Reopening", "url3")
    ]
    
    # Set the test events in the app config
    test_client.application.config['TIMELINE_EVENTS'] = test_events
    
    response = test_client.get('/timeline')
    assert response.status_code == 200
    
    # Check if all test events are present
    for date, event, url in test_events:
        assert date.strftime('%d %B %Y').encode() in response.data
        assert event.encode() in response.data
        assert url.encode() in response.data

def test_timeline_route_error_handling(test_client, monkeypatch):
    # Test error handling by setting an invalid event format
    test_client.application.config['TIMELINE_EVENTS'] = None
    
    response = test_client.get('/timeline')
    assert response.status_code == 200
    assert b"Test error" in response.data
