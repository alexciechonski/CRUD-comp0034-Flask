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
from src.frontend.diagrams import ERD, TimeSeries

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
    # Render the timeline template
    return render_template('timeline.html')

@app.route('/api/create-database', methods=['POST'])
def create_database_endpoint():
    try:
        # Get database name from form
        database_name = request.form.get('database_name')
        
        if not database_name:
            flash('Database name is required', 'error')
            return redirect(url_for('dataset'))

        # Ensure database name ends with .db
        if not database_name.endswith('.db'):
            database_name += '.db'

        # Create the database using the utility function
        from src.utils import create_database
        from src.config import load_config
        success = create_database(database_name)

        if success:
            # Reload configuration to get the new database path
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
        # Get data from form instead of JSON
        database = request.form.get('database')
        table_name = request.form.get('table_name')

        if not database or not table_name:
            flash('Database and table name are required', 'error')
            return redirect(url_for('dataset', database=database))

        # Validate table creation
        if not v.val_create_table(database, table_name):
            flash(f'Table {table_name} already exists', 'error')
            return redirect(url_for('dataset', database=database))

        # Create a CRUD instance with the database name
        crud = CRUD(database)

        # Create the table using the CRUD add_table method
        crud.add_table(table_name)

        # Log the change
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
        # Get data from form instead of JSON
        database = request.form.get('database')
        table_name = request.form.get('table_name')
        if not database or not table_name:
            print("Error: Missing database or table name")
            flash('Database and table name are required', 'error')
            return redirect(url_for('dataset', database=database))

        # Validate table deletion
        print(f"Validating table deletion...")
        if not v.val_delete_table(database, table_name):
            print(f"Error: Table {table_name} is immutable")
            flash(f'Table {table_name} cannot be deleted as it is immutable', 'error')
            return redirect(url_for('dataset', database=database))

        print(f"Creating CRUD instance for database: {database}")
        # Create a CRUD instance with the database name
        crud = CRUD(database)
        try:
            # Get table info before deletion for logging
            db_path = get_db_path(database)
            print(f"Getting table info from: {db_path}")
            table_info = get_table_info(table_name, db_path)
            
            print(f"Attempting to remove table {table_name} from {database}")
            # Delete the table using the CRUD remove_table method
            crud.remove_table(database, table_name)
            
            print("Creating log entry...")
            # Log the change
            log_manager = LogManager()
            log_manager.delete_change(database, table_name, {"table_name": table_name, "schema": table_info})
            log_manager.save_log()
            
            flash(f'Table {table_name} deleted successfully', 'success')
        except Exception as e:
            print(f"Error in CRUD operations: {str(e)}")
            raise
        finally:
            # Clean up the CRUD instance
            print("Cleaning up CRUD instance...")
            if hasattr(crud, 'engine') and crud.engine:
                crud.engine.dispose()

        return redirect(url_for('dataset', database=database))

    except Exception as e:
        print(f"\nError in delete_table_endpoint: {str(e)}")
        print(f"Error type: {type(e)}")
        import traceback
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

        # Create a temporary file to store the uploaded CSV
        import tempfile
        import pandas as pd
        
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as temp_file:
            file.save(temp_file.name)
            # Read CSV file using pandas
            try:
                df = pd.read_csv(temp_file.name)
                print(f"Successfully read CSV with {len(df)} rows")
                print(f"Columns: {df.columns.tolist()}")
                print(f"First row: {df.iloc[0].to_dict()}")

                # Validate schema
                if not v.val_schema(df):
                    flash('CSV schema does not match the required schema', 'error')
                    return redirect(url_for('dataset', database=database))

            except Exception as e:
                flash(f'Error reading CSV file: {str(e)}', 'error')
                return redirect(url_for('dataset', database=database))

        # Get the correct database path
        data_server = get_data_server()
        db_path = get_db_path(database)
        if not db_path:
            flash(f'Database {database} not found', 'error')
            return redirect(url_for('dataset', database=database))

        print(f"Using database path: {db_path}")
        
        try:
            # Connect directly to the database for insertion
            with sqlite3.connect(db_path) as conn:
                # Convert DataFrame to list of dictionaries
                data_to_insert = df.to_dict('records')
                
                # Get column names from the first row
                if not data_to_insert:
                    flash('No data to insert', 'error')
                    return redirect(url_for('dataset', database=database))
                    
                columns = list(data_to_insert[0].keys())
                placeholders = ','.join(['?' for _ in columns])
                columns_str = ','.join(columns)
                
                # Prepare the insert query
                query = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
                print(f"Insert query: {query}")
                
                # Insert the data
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
                
                # Commit the transaction
                conn.commit()
                print(f"Committed {rows_inserted} rows to database")
                
                flash(f'Successfully inserted {rows_inserted} records into {table_name}', 'success')
                return redirect(url_for('dataset', database=database))
            
        except Exception as e:
            print(f"Error during database operation: {str(e)}")
            flash(f'Error inserting data: {str(e)}', 'error')
            return redirect(url_for('dataset', database=database))
            
        finally:
            # Clean up the temporary file
            import os
            os.unlink(temp_file.name)
            
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        flash(str(e), 'error')
        return redirect(url_for('dataset', database=database))

@app.route('/api/delete-database', methods=['POST'])
def delete_database_endpoint():
    try:
        # Get the currently selected database from form data
        database = request.form.get('database', '')
        print(f"Attempting to delete database: {database}")
        
        if not database:
            print("No database name provided")
            flash('No database selected for deletion', 'error')
            return redirect(url_for('dataset'))
            
        # Validate if database can be deleted
        if not v.val_delete_database(database):
            print(f"Attempted to delete non-deletable database: {database}")
            flash('This database cannot be deleted as it is protected', 'error')
            return redirect(url_for('dataset'))
            
        # Import necessary functions
        from src.utils import delete_database
        from src.config import load_config
        
        print(f"Current database path before deletion: {get_db_path(database)}")
        
        # Delete the database
        success = delete_database(database)
        print(f"Delete operation result: {success}")
        
        if success:
            # Reload configuration after deletion
            print("Reloading configuration...")
            load_config()
            print(f"Database path after reload: {get_db_path(database)}")
            flash(f'Database {database} deleted successfully', 'success')
        else:
            print("Delete operation failed")
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
    # Initialize LogManager
    log_manager = LogManager()
    
    # Get the changes as a DataFrame
    changes_df = log_manager.to_tables()
    
    return render_template('audit_log.html', changes_df=changes_df)

@app.route('/revert-change', methods=['POST'])
def revert_change():
    """Handle reverting a change from the audit log"""
    try:
        database = request.form.get('database')
        table = request.form.get('table')
        change_type = request.form.get('change_type')
        
        print(f"Received form data: database={database}, table={table}, change_type={change_type}")
        
        # Initialize managers
        revert_manager = RevertManager(database)
        log_manager = LogManager()
        
        print("Initialized managers")
        
        # Get the change to revert
        changes = log_manager.to_tables()
        print(f"Found {len(changes)} changes in log")
        
        # Find the specific change to revert
        change_to_revert = changes[
            (changes['database'] == database) & 
            (changes['table'] == table) & 
            (changes['change_type'] == change_type)
        ]
        
        print(f"Found change to revert: {change_to_revert.to_dict('records')}")
        
        if change_to_revert.empty:
            print("No matching change found in log")
            return redirect(url_for('audit_log'))
            
        # Store current state before making changes
        print("Storing current state...")
        revert_manager.store_state()

        # Get the change data
        change_data = change_to_revert.iloc[0].to_dict()
        print(f"Change data: {change_data}")
        
        # Use RevertManager's engine and session
        engine = revert_manager.engine
        session = revert_manager.Session()
        
        try:
            if change_type == 'create':
                # For create operations, we need to delete the created record
                print("Reverting create operation...")
                # Get primary keys for the table
                primary_keys = get_primary_keys(table, database)
                if not primary_keys:
                    print("No primary keys found, using 'id' as fallback")
                    primary_keys = ['id']
                
                # Construct WHERE clause using primary keys
                where_clause = []
                for key in primary_keys:
                    if key in change_data:
                        where_clause.append(f"{key} = {change_data[key]}")
                
                if where_clause:
                    delete_query = f"DELETE FROM {table} WHERE {' AND '.join(where_clause)}"
                    print(f"Executing delete query: {delete_query}")
                    result = session.execute(text(delete_query))
                    print(f"Delete affected {result.rowcount} rows")
                else:
                    print("No primary keys found in change data")
                
            elif change_type == 'delete':
                # For delete operations, we need to insert the deleted record
                print("Reverting delete operation...")
                # Get the previous data from the change data
                prev_data = {}
                for key, value in change_data.items():
                    if key.startswith('prev_'):
                        # Remove the 'prev_' prefix
                        clean_key = key[5:]  # Remove 'prev_' prefix
                        prev_data[clean_key] = value
                
                if prev_data:
                    # Get column names from the table
                    inspector = inspect(engine)
                    columns = [col['name'] for col in inspector.get_columns(table)]
                    
                    # Filter out columns that don't exist in the table
                    filtered_prev_data = {k: v for k, v in prev_data.items() if k in columns}
                    
                    # Ensure all required columns are present
                    missing_columns = [col for col in columns if col not in filtered_prev_data]
                    if missing_columns:
                        print(f"Warning: Missing columns in previous data: {missing_columns}")
                    
                    if filtered_prev_data:
                        # Construct the insert query
                        insert_query = f"INSERT INTO {table} ({', '.join(filtered_prev_data.keys())}) VALUES ({', '.join([':' + k for k in filtered_prev_data.keys()])})"
                        print(f"Executing insert query: {insert_query}")
                        print(f"With data: {filtered_prev_data}")
                        
                        result = session.execute(text(insert_query), filtered_prev_data)
                        print(f"Insert affected {result.rowcount} rows")
                    else:
                        print("No valid columns found in previous data")
                else:
                    print("No previous data found in change data")
                    # Try to use the non-prefixed data as fallback
                    prev_data = {k: v for k, v in change_data.items() 
                               if k not in ['change_type', 'database', 'table']}
                    
                    # Get column names from the table
                    inspector = inspect(engine)
                    columns = [col['name'] for col in inspector.get_columns(table)]
                    
                    # Filter out columns that don't exist in the table
                    filtered_prev_data = {k: v for k, v in prev_data.items() if k in columns}
                    
                    if filtered_prev_data:
                        insert_query = f"INSERT INTO {table} ({', '.join(filtered_prev_data.keys())}) VALUES ({', '.join([':' + k for k in filtered_prev_data.keys()])})"
                        print(f"Executing insert query with fallback data: {insert_query}")
                        print(f"With data: {filtered_prev_data}")
                        result = session.execute(text(insert_query), filtered_prev_data)
                        print(f"Insert affected {result.rowcount} rows")
                    else:
                        print("No valid columns found in fallback data")
                
            elif change_type == 'update':
                # For update operations, we need to restore the previous values
                print("Reverting update operation...")
                prev_data = {k.replace('prev_', ''): v for k, v in change_data.items() if k.startswith('prev_')}
                
                if prev_data:
                    # Get column names from the table
                    inspector = inspect(engine)
                    columns = [col['name'] for col in inspector.get_columns(table)]
                    
                    # Filter out columns that don't exist in the table
                    filtered_prev_data = {k: v for k, v in prev_data.items() if k in columns}
                    
                    # Get primary keys for the table
                    primary_keys = get_primary_keys(table, database)
                    if not primary_keys:
                        print("No primary keys found, using 'id' as fallback")
                        primary_keys = ['id']

                    # Construct WHERE clause using primary keys
                    where_clause = []
                    for key in primary_keys:
                        if key in change_data:
                            where_clause.append(f"{key} = {change_data[key]}")
                    
                    if where_clause and filtered_prev_data:
                        # Construct SET clause
                        set_clause = ', '.join([f"{k} = :{k}" for k in filtered_prev_data.keys()])
                        update_query = f"UPDATE {table} SET {set_clause} WHERE {' AND '.join(where_clause)}"
                        print(f"Executing update query: {update_query}")
                        result = session.execute(text(update_query), filtered_prev_data)
                        print(f"Update affected {result.rowcount} rows")
                    else:
                        if not where_clause:
                            print("No primary keys found in change data")
                        if not filtered_prev_data:
                            print("No valid columns found in previous data")
                    log_manager.update_length()
                else:
                    print("No previous data found")

            
            # Commit the transaction
            session.commit()
            print("Transaction committed successfully")
            
            # Only remove the change from the log after successful reversion
            print(f"Removing change from log: database={database}, table={table}, change_type={change_type}")
            log_manager.remove_change(database, table, change_type)
            print("Change removed from log")
            
            # Force a refresh of the audit log page
            return redirect(url_for('audit_log', _external=True))
            
        finally:
            session.close()
            engine.dispose()
            
    except Exception as e:
        print(f"\n=== Error in revert_change: {str(e)} ===")
        print(f"Error type: {type(e)}")
        print(13, os.path.exists("/Users/alexanderciechonski/Desktop/comp0034cw2/deaths.db"))
        return redirect(url_for('audit_log'))

if __name__ == '__main__':
    app.run(debug=True)

