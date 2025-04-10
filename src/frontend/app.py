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
import traceback
import tempfile
import sqlite3
from sqlite3 import OperationalError
from flask import request, redirect, flash
from flask import Flask, render_template, url_for
import pandas as pd
from src.frontend.diagrams import ERD, TimeSeries, RevertChange
from src.utils import create_database, delete_database
from src.config import load_config
from src.forms.time_series_form import TimeSeriesForm
from src.backend.data_server import DataServer
from src.utils import get_table_info, get_databases, get_db_path
from src.backend.erd_manager import CRUD
from src.backend.validation import Validator as v
from src.backend.routes import bp as restriction_bp
from src.frontend.dash_app import create_dash_app
from src.backend.log.log_manager import LogManager

# Add the parent directory to Python path
sys.path.append(str(Path(__file__).parent.parent.parent))

ROUTE_CREATE_DB = '/api/create-database'
ROUTE_DELETE_DB = '/api/delete-database'
ROUTE_DATASET = '/dataset'
ROUTE_TIME_SERIES = '/time-series'
ROUTE_TIMELINE = '/timeline'
ROUTE_INSERT_DATA = '/api/insert-data'
ROUTE_CRUD_VIEW = '/crud-view'
ROUTE_AUDIT_LOG = '/audit-log'
ROUTE_REVERT_CHANGE = '/revert-change'
ROUTE_CREATE_TABLE = '/api/create-table'
ROUTE_DELETE_TABLE = '/api/delete-table'

app = Flask(__name__,
            template_folder='templates',
            static_folder='static')

app.config['SECRET_KEY'] = 'your-secret-key-here'

# Initialize Dash app
dash_app = create_dash_app(app)

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

@app.route(ROUTE_DATASET)
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
    except (FileNotFoundError, OperationalError, AttributeError, TypeError) as e:
        db_names = get_databases()
        databases = [{'label': db, 'value': db} for db in db_names]
        return render_template(
            'dataset.html',
            error=str(e),
            selected_db=selected_db,
            databases=databases
        )

@app.route(ROUTE_TIME_SERIES, methods=['GET', 'POST'])
def time_series():
    selected_db = request.args.get('database', 'covid.db')
    service = TimeSeries(selected_db)
    form = TimeSeriesForm()

    # Populate form choices
    form.table.choices = [(table['name'], table['name'].replace('_', ' ').title()) for table in service.tables]
    form.restrictions.choices = [(restriction, restriction.replace('_', ' ').title()) for restriction in service.restrictions]

    if request.method == 'POST' and form.validate():
        try:
            # Get validated data directly from the form
            db_name, table, selected_restrictions, prompt = service.validate_form_data(form)
            result = service.analyze(db_name, table, selected_restrictions, prompt)

            return render_template('time_series.html',
                                form=form,
                                databases=service.databases,
                                selected_db=selected_db,
                                time_series_plot=result['time_series_plot'],
                                regression_plot=result['regression_plot'],
                                analysis_result=result['analysis_result'])

        except (ValueError, OperationalError) as e:
            return render_template('time_series.html',
                                form=form,
                                databases=service.databases,
                                selected_db=selected_db,
                                error=str(e))
    else:
        return render_template('time_series.html',
                            form=form,
                            databases=service.databases,
                            selected_db=selected_db)


@app.route(ROUTE_TIMELINE)
def timeline():
    return render_template('timeline.html')

@app.route(ROUTE_CREATE_DB, methods=['POST'])
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

    except ValueError as val_err:
        flash(str(val_err), 'error')
        return redirect(url_for('dataset'))
    except OperationalError as e:
        flash(f'Error creating database: {str(e)}', 'error')
        return redirect(url_for('dataset'))

@app.route(ROUTE_CREATE_TABLE, methods=['POST'])
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

    except OperationalError as e:
        flash(str(e), 'error')
        return redirect(url_for('dataset', database=database))

@app.route(ROUTE_DELETE_TABLE, methods=['POST'])
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
        
        except OperationalError as e:
            print(f"Error in CRUD operations: {str(e)}")
            raise
        
        finally:
            if hasattr(crud, 'engine') and crud.engine:
                crud.engine.dispose()

        return redirect(url_for('dataset', database=database))

    except OperationalError as e:
        print(f"Traceback: {traceback.format_exc()}")
        flash(str(e), 'error')
        return redirect(url_for('dataset', database=database))

@app.route(ROUTE_INSERT_DATA, methods=['POST'])
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

            except (ValueError, FileNotFoundError) as e:
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

                cursor = conn.cursor()
                rows_inserted = 0
                for row in data_to_insert:
                    values = [row[col] for col in columns]
                    try:
                        cursor.execute(query, values)
                        rows_inserted += 1
                    except OperationalError as e:
                        print(f"Error inserting row {values}: {str(e)}")
                        raise

                conn.commit()

                flash(f'Successfully inserted {rows_inserted} records into {table_name}', 'success')
                return redirect(url_for('dataset', database=database))

        except OperationalError as e:
            flash(f'Error inserting data: {str(e)}', 'error')
            return redirect(url_for('dataset', database=database))

        finally:
            os.unlink(temp_file.name)

    except ValueError as e:
        flash(str(e), 'error')
        return redirect(url_for('dataset', database=database))

@app.route(ROUTE_DELETE_DB, methods=['POST'])
def delete_database_endpoint():
    try:
        database = request.form.get('database', '')

        if not database:
            flash('No database selected for deletion', 'error')
            return redirect(url_for('dataset'))

        if not v.val_delete_database(database):
            flash('This database cannot be deleted as it is protected', 'error')
            return redirect(url_for('dataset'))

        success = delete_database(database)

        if success:
            load_config()
            flash(f'Database {database} deleted successfully', 'success')
        else:
            flash(f'Failed to delete database {database}', 'error')

        return redirect(url_for('dataset'))

    except OperationalError as e:
        flash(f'Error deleting database: {str(e)}', 'error')
        return redirect(url_for('dataset'))

@app.route(ROUTE_CRUD_VIEW)
def table_crud():
    """Render the Table CRUD page with the embedded Dash app."""
    return render_template('table_crud.html')

@app.route(ROUTE_AUDIT_LOG)
def audit_log():
    log_manager = LogManager()
    changes_df = log_manager.to_tables()
    return render_template('audit_log.html', changes_df=changes_df)

@app.route(ROUTE_REVERT_CHANGE, methods=['POST'])
def revert_change():
    try:
        database = request.form.get('database')
        table = request.form.get('table')
        change_type = request.form.get('change_type')

        reverter = RevertChange(database, table, change_type)
        change_data = reverter.find_change()

        if not change_data:
            return redirect(url_for('audit_log'))

        reverter.revert(change_data)
        return redirect(url_for('audit_log', _external=True))

    except ValueError as e:
        print(f"Error type: {type(e)}")
        return redirect(url_for('audit_log'))

    finally:
        try:
            reverter.cleanup()
        except OperationalError as err:
            print(err)

if __name__ == '__main__':
    app.run(debug=True)
