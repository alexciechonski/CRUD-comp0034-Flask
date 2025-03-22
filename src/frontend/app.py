"""
Main entry point for the Flask web application.

This module initializes and configures a Flask app, setting up its routes
and template rendering. It handles page-based navigation and serves
static assets.

Dependencies:
- Flask: Web framework for building web applications
- Jinja2: Template engine for rendering HTML
"""
import os
import sys
from pathlib import Path
from flask import request
from functools import lru_cache

# Add the parent directory to Python path
sys.path.append(str(Path(__file__).parent.parent.parent))

from flask import Flask, render_template, url_for, jsonify
from src.backend.data_server import DataServer
from src.config import PATHS
from src.utils import query_db, get_table_info, convert_to_date, show_tables, select_graphable_tables

# Debug: Print the paths
print("Database paths:")
for key, path in PATHS.items():
    print(f"{key}: {path}")
    print(f"File exists: {os.path.exists(path)}")

app = Flask(__name__,
            template_folder='templates',
            static_folder='static')

# Initialize DataServer
data_server = DataServer(
    db_path=PATHS['covid.db'],
    graph_path=PATHS['graph.db'],
    custom_path=PATHS['custom.db']
)

# Add caching for time series data
@lru_cache(maxsize=32)
def get_cached_time_series(database, table, restrictions_key):
    """Cache time series data to improve performance"""
    restrictions = () if restrictions_key == 'all' else tuple(restrictions_key.split(','))
    return data_server.serve_time_series(restrictions, database=database, table=table)

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dataset')
def dataset():
    # Get table information for the dataset overview
    tables = ['Date', 'Restriction', 'DailyRestriction', 'Source']
    table_info = {table: data_server.serve_table('covid.db', table) for table in tables}
    return render_template('dataset.html', table_info=table_info)

@app.route('/time-series')
def time_series():
    # Render the time series template
    return render_template('time_series.html')

@app.route('/api/time-series')
def time_series_data():
    try:
        # Get parameters
        selected_restrictions = request.args.getlist('restrictions[]')
        database = request.args.get('database', 'covid.db')
        table = request.args.get('table')

        if not database or not table:
            return jsonify({'error': 'Missing database or table parameter'}), 400

        # Create a cache key for the restrictions
        restrictions_key = 'all' if not selected_restrictions else ','.join(sorted(selected_restrictions))
        
        # Get data from cache or compute new
        time_series_data = get_cached_time_series(database, table, restrictions_key)
        
        if not time_series_data:
            return jsonify({'error': 'No data available'}), 404
            
        return jsonify(time_series_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/restriction-distribution')
def restriction_distribution():
    # Get the date range from the database
    start_date, end_date = data_server.get_date_range()
    return render_template('restriction_distribution.html', start_date=start_date, end_date=end_date)

@app.route('/api/restriction-distribution')
def restriction_distribution_data():
    # Get end date from query parameters
    end_date = request.args.get('end_date', None)
    # Get restriction distribution data as JSON with end date filter
    restr_distr = data_server.serve_restr_distr(end_date=end_date)
    
    # Return empty list as valid response when no data is found
    if restr_distr is None:
        return jsonify([])
        
    return jsonify(restr_distr)

@app.route('/timeline')
def timeline():
    # Render the timeline template
    return render_template('timeline.html')

@app.route('/api/timeline')
def timeline_data():
    # Get timeline data as JSON
    timeline_data = data_server.serve_timeline()
    return jsonify(timeline_data)

@app.route('/api/restrictions')
def get_restrictions():
    """Get list of all available restrictions"""
    restrictions = data_server.get_restrictions()
    return jsonify(restrictions)

@app.route('/api/tables/<database>')
def get_tables(database):
    """Get list of available tables for a given database"""
    try:
        tables = show_tables(database)
        return jsonify(tables)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
