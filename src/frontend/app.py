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
from flask import request, redirect, flash, jsonify
from functools import lru_cache
import networkx as nx
import matplotlib.pyplot as plt
import io
import base64
import sqlite3
import plotly.express as px
import plotly.io as pio
import numpy as np
import pandas as pd
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from src.frontend.diagrams import ERD, TimeSeries, RevertChange
from src.utils import create_database, delete_database
from src.config import load_config
import traceback
import tempfile
import pandas as pd

# Add the parent directory to Python path
sys.path.append(str(Path(__file__).parent.parent.parent))

from flask import Flask, render_template, url_for, jsonify, send_file
from src.backend.data_server import DataServer
from src.utils import (
    get_table_info, 
    show_tables, 
    get_databases, 
    get_resp,
    get_db_path,
    get_all_tables,
    get_primary_keys,
    get_graphable_tables
)
from src.backend.erd_manager import Visualizer, CRUD
from src.backend.validation import Validator as v
from src.prediction.pred import Model
from src.backend.routes import bp as restriction_bp
from src.frontend.dash_app import create_dash_app
from src.backend.log.log_manager import LogManager
from src.backend.revert_manager import RevertManager

app = Flask(__name__,
            template_folder='templates',
            static_folder='static')

# Initialize Dash app
dash_app = create_dash_app(app)

app.secret_key = 'your-secret-key-here'

# Register blueprints
app.register_blueprint(restriction_bp, url_prefix='')

def get_data_server():
    """Create a new DataServer instance for each request"""
    return DataServer(
        db_name='covid.db'
    )

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dataset')
def dataset():
    selected_db = request.args.get('database', 'covid.db')

    try:
        db_names = get_databases()
        databases = [{'label': db, 'value': db} for db in db_names]

        erd = ERD(selected_db)
        erd_html = erd.render_erd_html()

        return render_template(
            'dataset.html',
            table_info=erd.table_info,
            selected_db=selected_db,
            databases=databases,
            erd_html=erd_html
        )
    except Exception as e:
        db_names = get_databases()
        databases = [{'label': db, 'value': db} for db in db_names]
        return render_template(
            'dataset.html',
            error=str(e),
            selected_db=selected_db,
            databases=databases
        )
@app.route('/time-series', methods=['GET', 'POST'])
def time_series():
    selected_db = request.args.get('database', 'covid.db')
    service = TimeSeries(selected_db)

    if request.method == 'POST':
        try:
            db_name, table, selected_restrictions, prompt = service.validate_form_data(request.form)
            result = service.analyze(db_name, table, selected_restrictions, prompt)

            return render_template('time_series.html',
                                   databases=service.databases,
                                   selected_db=selected_db,
                                   tables=service.tables,
                                   restrictions=service.restrictions,
                                   selected_table=table,
                                   selected_restrictions=selected_restrictions,
                                   prompt=prompt,
                                   time_series_plot=result['time_series_plot'],
                                   regression_plot=result['regression_plot'],
                                   analysis_result=result['analysis_result'])

        except Exception as e:
            print(f"Error in time series analysis: {str(e)}")
            return render_template('time_series.html',
                                   databases=service.databases,
                                   selected_db=selected_db,
                                   tables=service.tables,
                                   restrictions=service.restrictions,
                                   error=str(e))
    else:
        return render_template('time_series.html',
                               databases=service.databases,
                               selected_db=selected_db,
                               tables=service.tables,
                               restrictions=service.restrictions)


@app.route('/timeline')
def timeline():
    return render_template('timeline.html')

@app.route('/api/create-database', methods=['POST'])
def create_database_endpoint():
    try:
        database_name = request.form.get('database_name')
        
        if not database_name:
            flash('Database name is required', 'error')
            return redirect(url_for('dataset'))

        if not database_name.endswith('.db'):
            database_name += '.db'

        success = create_database(database_name)

        if success:
            load_config()
            flash(f'Database {database_name} created successfully', 'success')
        else:
            flash(f'Failed to create database {database_name}', 'error')

        return redirect(url_for('dataset'))

    except ValueError as ve:
        flash(str(ve), 'error')
        return redirect(url_for('dataset'))
    except Exception as e:
        flash(f'Error creating database: {str(e)}', 'error')
        return redirect(url_for('dataset'))

@app.route('/api/create-table', methods=['POST'])
def create_table_endpoint():
    try:
        database = request.form.get('database')
        table_name = request.form.get('table_name')

        if not database or not table_name:
            flash('Database and table name are required', 'error')
            return redirect(url_for('dataset', database=database))

        if not v.val_create_table(database, table_name):
            flash(f'Table {table_name} already exists', 'error')
            return redirect(url_for('dataset', database=database))

        crud = CRUD(database)

        crud.add_table(table_name)

        log_manager = LogManager()
        log_manager.create_change(database, table_name, {"table_name": table_name})
        log_manager.save_log()

        flash(f'Table {table_name} created successfully', 'success')
        return redirect(url_for('dataset', database=database))

    except Exception as e:
        flash(str(e), 'error')
        return redirect(url_for('dataset', database=database))

@app.route('/api/delete-table', methods=['POST'])
def delete_table_endpoint():
    try:
        database = request.form.get('database')
        table_name = request.form.get('table_name')
        if not database or not table_name:
            flash('Database and table name are required', 'error')
            return redirect(url_for('dataset', database=database))

        if not v.val_delete_table(database, table_name):
            flash(f'Table {table_name} cannot be deleted as it is immutable', 'error')
            return redirect(url_for('dataset', database=database))

        crud = CRUD(database)
        try:
            db_path = get_db_path(database)
            table_info = get_table_info(table_name, db_path)
            
            crud.remove_table(database, table_name)
            
            # Log the change
            log_manager = LogManager()
            log_manager.delete_change(database, table_name, {"table_name": table_name, "schema": table_info})
            log_manager.save_log()
            
            flash(f'Table {table_name} deleted successfully', 'success')
        except Exception as e:
            print(f"Error in CRUD operations: {str(e)}")
            raise
        finally:
            if hasattr(crud, 'engine') and crud.engine:
                crud.engine.dispose()

        return redirect(url_for('dataset', database=database))

    except Exception as e:
        print(f"\nError in delete_table_endpoint: {str(e)}")
        print(f"Error type: {type(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        flash(str(e), 'error')
        return redirect(url_for('dataset', database=database))

@app.route('/api/insert-data', methods=['POST'])
def insert_data_endpoint():
    try:
        if 'csv_file' not in request.files:
            flash('No file uploaded', 'error')
            return redirect(url_for('dataset', database=request.form.get('database')))
            
        file = request.files['csv_file']
        database = request.form.get('database')
        table_name = request.form.get('table_name')
        
        if not file or not database or not table_name:
            flash('Missing required parameters', 'error')
            return redirect(url_for('dataset', database=database))
            
        if not file.filename.endswith('.csv'):
            flash('File must be a CSV', 'error')
            return redirect(url_for('dataset', database=database))
        
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as temp_file:
            file.save(temp_file.name)
            try:
                df = pd.read_csv(temp_file.name)

                if not v.val_schema(df):
                    flash('CSV schema does not match the required schema', 'error')
                    return redirect(url_for('dataset', database=database))

            except Exception as e:
                flash(f'Error reading CSV file: {str(e)}', 'error')
                return redirect(url_for('dataset', database=database))

        # Get the correct database path
        db_path = get_db_path(database)
        if not db_path:
            flash(f'Database {database} not found', 'error')
            return redirect(url_for('dataset', database=database))
        
        try:
            with sqlite3.connect(db_path) as conn:
                data_to_insert = df.to_dict('records')
                
                if not data_to_insert:
                    flash('No data to insert', 'error')
                    return redirect(url_for('dataset', database=database))
                    
                columns = list(data_to_insert[0].keys())
                placeholders = ','.join(['?' for _ in columns])
                columns_str = ','.join(columns)
                
                query = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
                print(f"Insert query: {query}")
                
                cursor = conn.cursor()
                rows_inserted = 0
                for row in data_to_insert:
                    values = [row[col] for col in columns]
                    try:
                        cursor.execute(query, values)
                        rows_inserted += 1
                        print(f"Inserted row: {values}")
                    except Exception as e:
                        print(f"Error inserting row {values}: {str(e)}")
                        raise
                
                conn.commit()
                print(f"Committed {rows_inserted} rows to database")
                
                flash(f'Successfully inserted {rows_inserted} records into {table_name}', 'success')
                return redirect(url_for('dataset', database=database))
            
        except Exception as e:
            print(f"Error during database operation: {str(e)}")
            flash(f'Error inserting data: {str(e)}', 'error')
            return redirect(url_for('dataset', database=database))
            
        finally:
            os.unlink(temp_file.name)
            
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        flash(str(e), 'error')
        return redirect(url_for('dataset', database=database))

@app.route('/api/delete-database', methods=['POST'])
def delete_database_endpoint():
    try:
        database = request.form.get('database', '')
        print(f"Attempting to delete database: {database}")
        
        if not database:
            print("No database name provided")
            flash('No database selected for deletion', 'error')
            return redirect(url_for('dataset'))
            
        if not v.val_delete_database(database):
            print(f"Attempted to delete non-deletable database: {database}")
            flash('This database cannot be deleted as it is protected', 'error')
            return redirect(url_for('dataset'))
        
        print(f"Current database path before deletion: {get_db_path(database)}")
        
        success = delete_database(database)
        print(f"Delete operation result: {success}")
        
        if success:
            load_config()
            flash(f'Database {database} deleted successfully', 'success')
        else:
            flash(f'Failed to delete database {database}', 'error')
            
        return redirect(url_for('dataset'))
        
    except Exception as e:
        print(f"Error in delete_database_endpoint: {str(e)}")
        flash(f'Error deleting database: {str(e)}', 'error')
        return redirect(url_for('dataset'))

@app.route('/crud-view')
def table_crud():
    """Render the Table CRUD page with the embedded Dash app."""
    return render_template('table_crud.html')

@app.route('/audit-log')
def audit_log():
    log_manager = LogManager()    
    changes_df = log_manager.to_tables()
    return render_template('audit_log.html', changes_df=changes_df)
    
@app.route('/revert-change', methods=['POST'])
def revert_change():
    try:
        database = request.form.get('database')
        table = request.form.get('table')
        change_type = request.form.get('change_type')

        reverter = RevertChange(database, table, change_type)
        change_data = reverter.find_change()

        if not change_data:
            print("No matching change found in log")
            return redirect(url_for('audit_log'))

        reverter.revert(change_data)
        return redirect(url_for('audit_log', _external=True))

    except Exception as e:
        print(f"\n=== Error in revert_change: {str(e)} ===")
        print(f"Error type: {type(e)}")
        return redirect(url_for('audit_log'))

    finally:
        try:
            reverter.cleanup()
        except Exception as err:
            print(err)

if __name__ == '__main__':
    app.run(debug=True)

