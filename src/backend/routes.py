"""
Backend routes for the Flask application.

This module defines routes for handling restriction distribution and timeline views.
"""
from flask import Blueprint, render_template, jsonify, request, redirect, flash, url_for
from datetime import datetime
from sqlalchemy import func, create_engine
from sqlalchemy.orm import sessionmaker
from .models import Date, Restriction, DailyRestriction, init_db
from src.utils import get_db_path, create_database, delete_database, get_table_info, get_databases
from .data_server import DataServer
import os
import plotly.graph_objects as go
import json
from src.forms.end_date_form import RestrictionForm
from src.forms.time_series_form import TimeSeriesForm
from src.frontend.diagrams import ERD, TimeSeries, RevertChange
from src.backend.erd_manager import CRUD
from src.backend.validation import Validator as v
from src.backend.log.log_manager import LogManager
import pandas as pd
import sqlite3
from sqlite3 import OperationalError
import tempfile
import traceback

bp = Blueprint('main', __name__)

# Route constants
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

# Create engine and session factory
db_path = get_db_path("covid.db")
engine = create_engine(f'sqlite:///{db_path}')
Session = sessionmaker(bind=engine)

# Initialize DataServer
data_server = DataServer("covid.db")

def format_restriction_name(name):
    """Format restriction name for display."""
    return name.replace('_', ' ').title()

@bp.route('/')
def index():
    return render_template('index.html')

@bp.route(ROUTE_DATASET)
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

@bp.route(ROUTE_TIME_SERIES, methods=['GET', 'POST'])
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

@bp.route(ROUTE_TIMELINE)
def timeline():
    """Render the timeline page."""
    try:
        # Get timeline data from DataServer
        timeline_data = data_server.serve_timeline()
        
        # Sort events by date
        timeline_data.sort(key=lambda x: x[0])
        
        return render_template('timeline.html', events=timeline_data)
    except Exception as e:
        print(f"Error in timeline: {str(e)}")
        return render_template('timeline.html', events=[], error="An error occurred while loading the timeline data.")

@bp.route(ROUTE_CREATE_DB, methods=['POST'])
def create_database_endpoint():
    try:
        database_name = request.form.get('database_name')

        if not database_name:
            flash('Database name is required', 'error')
            return redirect(url_for('main.dataset'))

        if not database_name.endswith('.db'):
            database_name += '.db'

        success = create_database(database_name)

        if success:
            flash(f'Database {database_name} created successfully', 'success')
        else:
            flash(f'Failed to create database {database_name}', 'error')

        return redirect(url_for('main.dataset'))

    except ValueError as val_err:
        flash(str(val_err), 'error')
        return redirect(url_for('main.dataset'))
    except OperationalError as e:
        flash(f'Error creating database: {str(e)}', 'error')
        return redirect(url_for('main.dataset'))

@bp.route(ROUTE_CREATE_TABLE, methods=['POST'])
def create_table_endpoint():
    try:
        database = request.form.get('database')
        table_name = request.form.get('table_name')

        if not database or not table_name:
            flash('Database and table name are required', 'error')
            return redirect(url_for('main.dataset', database=database))

        if not v.val_create_table(database, table_name):
            flash(f'Table {table_name} already exists', 'error')
            return redirect(url_for('main.dataset', database=database))

        crud = CRUD(database)
        crud.add_table(table_name)

        log_manager = LogManager()
        log_manager.create_change(database, table_name, {"table_name": table_name})
        log_manager.save_log()

        flash(f'Table {table_name} created successfully', 'success')
        return redirect(url_for('main.dataset', database=database))

    except OperationalError as e:
        flash(str(e), 'error')
        return redirect(url_for('main.dataset', database=database))

@bp.route(ROUTE_DELETE_TABLE, methods=['POST'])
def delete_table_endpoint():
    try:
        database = request.form.get('database')
        table_name = request.form.get('table_name')
        if not database or not table_name:
            flash('Database and table name are required', 'error')
            return redirect(url_for('main.dataset', database=database))

        if not v.val_delete_table(database, table_name):
            flash(f'Table {table_name} cannot be deleted as it is immutable', 'error')
            return redirect(url_for('main.dataset', database=database))

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

        return redirect(url_for('main.dataset', database=database))

    except OperationalError as e:
        print(f"Traceback: {traceback.format_exc()}")
        flash(str(e), 'error')
        return redirect(url_for('main.dataset', database=database))

@bp.route(ROUTE_INSERT_DATA, methods=['POST'])
def insert_data_endpoint():
    try:
        if 'csv_file' not in request.files:
            flash('No file uploaded', 'error')
            return redirect(url_for('main.dataset', database=request.form.get('database')))

        file = request.files['csv_file']
        database = request.form.get('database')
        table_name = request.form.get('table_name')

        if not file or not database or not table_name:
            flash('Missing required parameters', 'error')
            return redirect(url_for('main.dataset', database=database))

        if not file.filename.endswith('.csv'):
            flash('File must be a CSV', 'error')
            return redirect(url_for('main.dataset', database=database))

        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as temp_file:
            file.save(temp_file.name)
            try:
                df = pd.read_csv(temp_file.name)

            except (ValueError, FileNotFoundError) as e:
                flash(f'Error reading CSV file: {str(e)}', 'error')
                return redirect(url_for('main.dataset', database=database))

        # Get the correct database path
        db_path = get_db_path(database)
        if not db_path:
            flash(f'Database {database} not found', 'error')
            return redirect(url_for('main.dataset', database=database))

        try:
            with sqlite3.connect(db_path) as conn:
                data_to_insert = df.to_dict('records')

                if not data_to_insert:
                    flash('No data to insert', 'error')
                    return redirect(url_for('main.dataset', database=database))

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
                return redirect(url_for('main.dataset', database=database))

        except OperationalError as e:
            flash(f'Error inserting data: {str(e)}', 'error')
            return redirect(url_for('main.dataset', database=database))

        finally:
            os.unlink(temp_file.name)

    except ValueError as e:
        flash(str(e), 'error')
        return redirect(url_for('main.dataset', database=database))

@bp.route(ROUTE_DELETE_DB, methods=['POST'])
def delete_database_endpoint():
    try:
        database = request.form.get('database', '')

        if not database:
            flash('No database selected for deletion', 'error')
            return redirect(url_for('main.dataset'))

        if not v.val_delete_database(database):
            flash('This database cannot be deleted as it is protected', 'error')
            return redirect(url_for('main.dataset'))

        success = delete_database(database)

        if success:
            flash(f'Database {database} deleted successfully', 'success')
        else:
            flash(f'Failed to delete database {database}', 'error')

        return redirect(url_for('main.dataset'))

    except OperationalError as e:
        flash(f'Error deleting database: {str(e)}', 'error')
        return redirect(url_for('main.dataset'))

@bp.route(ROUTE_CRUD_VIEW)
def table_crud():
    """Render the Table CRUD page with the embedded Dash app."""
    return render_template('table_crud.html')

@bp.route(ROUTE_AUDIT_LOG)
def audit_log():
    log_manager = LogManager()
    changes_df = log_manager.to_tables()
    return render_template('audit_log.html', changes_df=changes_df)

@bp.route(ROUTE_REVERT_CHANGE, methods=['POST'])
def revert_change():
    try:
        database = request.form.get('database')
        table = request.form.get('table')
        change_type = request.form.get('change_type')

        reverter = RevertChange(database, table, change_type)
        change_data = reverter.find_change()

        if not change_data:
            return redirect(url_for('main.audit_log'))

        reverter.revert(change_data)
        return redirect(url_for('main.audit_log', _external=True))

    except ValueError as e:
        print(f"Error type: {type(e)}")
        return redirect(url_for('main.audit_log'))

    finally:
        try:
            reverter.cleanup()
        except OperationalError as err:
            print(err)

@bp.route('/restriction-distribution', methods=['GET', 'POST'])
def restriction_distribution():
    """Render the restriction distribution page."""
    form = RestrictionForm(request.form)
    if request.method == 'POST' and form.validate_on_submit():
        end_date = form.end_date.data
    else:
        # Handle GET with query param or default date
        raw_date = request.args.get('end_date', '2021-06-15')
        try:
            end_date = datetime.strptime(raw_date, '%Y-%m-%d').date()
            form.end_date.data = end_date
        except ValueError:
            end_date = datetime.strptime('2021-06-15', '%Y-%m-%d').date()
            form.end_date.data = end_date

    # Initialize default values for empty chart
    labels = []
    data = []
    total_restrictions = 0
    most_common = "No data available"
    most_common_count = 0
    error = None
    plot_html = None

    session = Session()
    try:
        print(f"Attempting to query database at: {db_path}")
        
        # Get the date_id for the end date
        date_record = session.query(Date).filter(Date.date <= end_date).order_by(Date.date.desc()).first()
        
        if date_record is None:
            print(f"No date record found for date: {end_date}")
            error = "No data available for the selected date"
        else:
            print(f"Found date record: {date_record.date}")
            
            # Get restriction counts up to the end date
            restriction_counts = session.query(
                Restriction.restriction,
                func.count(DailyRestriction.restriction_id).label('count')
            ).join(
                DailyRestriction,
                DailyRestriction.restriction_id == Restriction.restriction_id
            ).join(
                Date,
                DailyRestriction.date_id == Date.date_id
            ).filter(
                Date.date <= end_date,
                DailyRestriction.in_place == True
            ).group_by(
                Restriction.restriction
            ).order_by(
                func.count(DailyRestriction.restriction_id).desc()
            ).all()

            print(f"Query returned {len(restriction_counts)} restrictions")

            if restriction_counts:
                # Prepare data for the template
                labels = [format_restriction_name(r.restriction) for r in restriction_counts]
                data = [r.count for r in restriction_counts]
                
                print(f"Labels: {labels}")
                print(f"Data: {data}")
                
                # Calculate statistics
                total_restrictions = sum(data)
                most_common = labels[0] if labels else "No data available"
                most_common_count = data[0] if data else 0

                # Create Plotly bar chart
                fig = go.Figure(data=[
                    go.Bar(
                        x=labels,
                        y=data,
                        marker_color='rgba(75, 192, 192, 0.6)',
                        marker_line_color='rgb(75, 192, 192)',
                        marker_line_width=1,
                        text=data,
                        textposition='auto',
                    )
                ])

                # Update layout
                fig.update_layout(
                    title='Global Restriction Patterns',
                    xaxis_title='Restriction Type',
                    yaxis_title='Number of Applications',
                    showlegend=False,
                    height=400,
                    margin=dict(l=60, r=20, t=40, b=100),
                    xaxis=dict(
                        tickangle=-45,
                        tickfont=dict(size=10)
                    ),
                    yaxis=dict(
                        tickfont=dict(size=10)
                    ),
                    paper_bgcolor='white',
                    plot_bgcolor='white',
                )

                # Convert to HTML
                plot_html = fig.to_html(full_html=False, include_plotlyjs=True)
                print("Successfully created plot HTML")
            else:
                print("No restrictions found")
                error = "No restriction data found for the selected date"

    except Exception as e:
        print(f"Error in restriction_distribution: {str(e)}")
        error = "An error occurred while processing the data"
    finally:
        session.close()

    
    return render_template('restriction_distribution.html',
                         plot_html=plot_html,
                         total_restrictions=total_restrictions,
                         most_common=most_common,
                         most_common_count=most_common_count,
                         end_date=end_date.strftime('%Y-%m-%d'),
                         error=error) 