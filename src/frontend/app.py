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
from flask import request, redirect, flash
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

# Add the parent directory to Python path
sys.path.append(str(Path(__file__).parent.parent.parent))

from flask import Flask, render_template, url_for, jsonify, send_file
from src.backend.data_server import DataServer
from src.config import PATHS
from src.utils import (
    query_db, 
    get_table_info, 
    convert_to_date, 
    show_tables, 
    select_graphable_tables, 
    get_databases, 
    create_table, 
    get_graphable_tables,
    get_resp
)
from src.backend.erd_manager import Visualizer, CRUD
from src.frontend.diagrams import Diagrams
from src.frontend.input_validation import Validator as v
from src.prediction.pred import Model

# Debug: Print the paths
print("Database paths:")
for key, path in PATHS.items():
    print(f"{key}: {path}")
    print(f"File exists: {os.path.exists(path)}")

app = Flask(__name__,
            template_folder='templates',
            static_folder='static')

# Set a secret key for flash messages
app.secret_key = 'your-secret-key-here'  # Replace with a secure secret key in production

# Initialize Diagrams
diagrams = Diagrams(
    db_path=PATHS['covid.db'],
    graph_path=PATHS['graph.db'],
    custom_path=PATHS['custom.db']
)

def get_data_server():
    """Create a new DataServer instance for each request"""
    return DataServer(
        db_path=PATHS['covid.db'],
        graph_path=PATHS['graph.db'],
        custom_path=PATHS['custom.db']
    )

# Add caching for time series data
@lru_cache(maxsize=32)
def get_cached_time_series(database, table, restrictions_key):
    """Cache time series data to improve performance"""
    restrictions = () if restrictions_key == 'all' else tuple(restrictions_key.split(','))
    data_server = get_data_server()
    try:
        return data_server.serve_time_series(restrictions, database=database, table=table)
    finally:
        data_server._db_session.close()
        data_server._graph_session.close()
        data_server._custom_session.close()

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/databases')
def fetch_databases():
    """Get list of available databases excluding graph.db"""
    return get_databases()

@app.route('/dataset')
def dataset():
    # Get selected database from query parameters, default to covid.db
    selected_db = request.args.get('database', 'covid.db')
    
    try:
        # Get list of available databases using get_databases() function
        databases = get_databases()
        
        # Get all tables for the selected database
        tables = show_tables(selected_db)
        
        # Get table info and format it properly
        table_info = {}
        for table in tables:
            try:
                # Get table schema information using get_table_info
                schema_info = get_table_info(table, PATHS[selected_db])
                if schema_info:
                    # Format schema info into a list of dictionaries
                    formatted_info = [{
                        'Column Name': col[1],  # name
                        'Type': col[2],         # type
                        'Constraints': ' '.join(filter(None, [
                            'NOT NULL' if col[3] else '',  # notnull
                            'PRIMARY KEY' if col[5] else '' # pk
                        ]))
                    } for col in schema_info]
                    table_info[table] = formatted_info
                else:
                    table_info[table] = []
            except Exception as table_error:
                print(f"Error getting schema for table {table}: {str(table_error)}")
                table_info[table] = []

        # Get ERD visualization
        try:
            # Create a NetworkX graph from the database structure
            G = nx.DiGraph()
            
            # Create a case-insensitive mapping of table names
            table_map = {table.lower(): table for table in tables}
            
            # Add nodes (tables)
            for table in tables:
                G.add_node(table)
            
            # Get foreign key relationships
            with sqlite3.connect(PATHS[selected_db]) as conn:
                cursor = conn.cursor()
                
                # Enable foreign keys and set to full foreign key checks
                cursor.execute("PRAGMA foreign_keys = ON")
                
                # Debug: Print database being analyzed
                print(f"\nAnalyzing database: {selected_db}")
                print(f"Tables found: {tables}")
                
                # Add edges based on foreign key relationships
                for table in tables:
                    print(f"\nChecking foreign keys for table: {table}")
                    
                    # Get foreign key information
                    cursor.execute(f"PRAGMA foreign_key_list('{table}')")
                    foreign_keys = cursor.fetchall()
                    
                    if foreign_keys:
                        print(f"Found {len(foreign_keys)} foreign key(s) in {table}")
                        for fk in foreign_keys:
                            # fk[0] is id, fk[1] is seq, fk[2] is table, fk[3] is from, fk[4] is to
                            referenced_table = fk[2]
                            from_col = fk[3]
                            to_col = fk[4]
                            print(f"Found relationship: {table}.{to_col} -> {referenced_table}.{from_col}")
                            
                            # Look up the actual table name using case-insensitive comparison
                            referenced_table_actual = table_map.get(referenced_table.lower())
                            if referenced_table_actual:
                                G.add_edge(table, referenced_table_actual)
                                print(f"Added edge: {table} -> {referenced_table_actual}")
                            else:
                                print(f"Warning: Referenced table {referenced_table} not found in table list")
            
            edge_count = len(G.edges())
            print(f"\nTotal edges found: {edge_count}")
            print(f"Graph edges: {list(G.edges())}")
            
            # Always create visualization, even if there are no edges
            # Create the plot with a more appropriate figure size
            plt.figure(figsize=(10, 8))
            
            # Use spring layout with optimized parameters for better distribution
            # If there are no edges, arrange nodes in a circle
            if edge_count > 0:
                pos = nx.spring_layout(G, k=1.5, iterations=50)
            else:
                pos = nx.circular_layout(G)
            
            # Draw edges with arrows (if any exist)
            if edge_count > 0:
                nx.draw_networkx_edges(G, pos, edge_color='gray', arrows=True, 
                                     arrowsize=20, width=1.5)
            
            # Draw nodes with better visibility
            nx.draw_networkx_nodes(G, pos, node_color='lightblue', 
                                 node_size=3000, alpha=0.7)
            
            # Draw labels with better font size
            nx.draw_networkx_labels(G, pos, font_size=10, font_weight='bold')
            
            # Add padding around the graph
            plt.margins(0.2)
            
            # Convert plot to image with higher DPI for better quality
            img = io.BytesIO()
            plt.savefig(img, format='png', bbox_inches='tight', dpi=200)
            img.seek(0)
            plt.close()
            
            # Convert to base64 for embedding in HTML
            if edge_count > 0:
                title = "Entity Relationship Diagram"
                desc = "Showing tables and their relationships"
            else:
                title = "Database Tables Overview"
                desc = ""
                
            erd_html = f'''
                <div class="erd-container">
                    <h4 class="text-center mb-3">{title}</h4>
                    <p class="text-muted text-center mb-3">{desc}</p>
                    <img src="data:image/png;base64,{base64.b64encode(img.getvalue()).decode()}" 
                         class="img-fluid" 
                         style="max-width: 100%; height: auto; border: 1px solid #ddd; border-radius: 4px; padding: 5px;">
                </div>
            '''
            
            if edge_count == 0:
                print("No relationships between tables")
        except Exception as e:
            print(f"Error generating ERD: {str(e)}")
            erd_html = f'''
                <div class="alert alert-danger">
                    <h4 class="alert-heading">Error Generating ERD</h4>
                    <p>{str(e)}</p>
                    <hr>
                    <p class="mb-0">Please check the database connection and schema.</p>
                </div>
            '''

        return render_template('dataset.html', 
                             table_info=table_info,
                             selected_db=selected_db,
                             databases=databases,
                             erd_html=erd_html)
    except Exception as e:
        return render_template('dataset.html', 
                             error=str(e),
                             selected_db=selected_db,
                             databases=databases)

@app.route('/time-series', methods=['GET', 'POST'])
def time_series():
    # Get data server instance
    data_server = get_data_server()
    try:
        # Get available tables and restrictions
        print("Fetching graphable tables...")
        tables = get_graphable_tables()
        print(f"Found tables: {tables}")
        
        # Define restrictions list
        restrictions = [
            "curfew",
            "eat_out_to_help_out",
            "eating_places_closed",
            "household_mixing_indoors_banned",
            "pubs_closed",
            "rule_of_6_indoors",
            "schools_closed",
            "shops_closed",
            "stay_at_home",
            "wfh"
        ]
        
        # Initialize variables
        selected_table = None
        selected_restrictions = []
        prompt = ""
        time_series_plot = None
        regression_plot = None
        analysis_result = None
        
        if request.method == 'POST':
            print("Processing POST request...")
            selected_table = request.form.get('table')
            selected_restrictions = request.form.getlist('restrictions[]')
            prompt = request.form.get('prompt', '')
            
            print(f"Selected table: {selected_table}")
            print(f"Selected restrictions: {selected_restrictions}")
            
            if selected_table:
                try:
                    # 1. Generate time series plot
                    print("Fetching time series data...")
                    time_series_data = data_server.serve_time_series(selected_restrictions, 'custom.db', selected_table)
                    
                    if time_series_data:
                        print("Processing time series data...")
                        # Get restrictions data first
                        print("Fetching restrictions data...")
                        restrictions_data = data_server.serve_time_series(selected_restrictions, 'covid.db', None)
                        
                        if restrictions_data and len(restrictions_data) > 0:
                            # Debug: Print date ranges
                            time_series_dates = [row[0] for row in time_series_data if row[0] is not None]
                            restrictions_dates = [row[0] for row in restrictions_data if row[0] is not None]
                            
                            if time_series_dates and restrictions_dates:
                                print(f"Time series date range: {min(time_series_dates)} to {max(time_series_dates)}")
                                print(f"Restrictions date range: {min(restrictions_dates)} to {max(restrictions_dates)}")
                            else:
                                print("Warning: One or both datasets have no valid dates")
                                print(f"Time series dates available: {len(time_series_dates)}")
                                print(f"Restrictions dates available: {len(restrictions_dates)}")
                            
                            # Convert data to pandas DataFrames for easier manipulation
                            df_values = pd.DataFrame([
                                {'date': row[0], 'value': row[1]} 
                                for row in time_series_data if row[0] is not None and row[1] is not None
                            ])
                            
                            df_restrictions = pd.DataFrame([
                                {'date': row[0], 'restrictions': row[1]} 
                                for row in restrictions_data if row[0] is not None and row[1] is not None
                            ])
                            
                            # Debug: Print DataFrame info
                            print("\nTime series DataFrame info:")
                            print(df_values.info())
                            print("\nRestrictions DataFrame info:")
                            print(df_restrictions.info())
                            
                            # Check if we have valid data
                            if df_values.empty or df_restrictions.empty:
                                raise ValueError("No valid data points found in one or both datasets")
                            
                            # Convert dates to datetime if they aren't already
                            df_values['date'] = pd.to_datetime(df_values['date'])
                            df_restrictions['date'] = pd.to_datetime(df_restrictions['date'])
                            
                            # Set date as index after conversion
                            df_values.set_index('date', inplace=True)
                            df_restrictions.set_index('date', inplace=True)
                            
                            # Debug: Print date ranges after conversion
                            print(f"\nTime series date range after conversion: {df_values.index.min()} to {df_values.index.max()}")
                            print(f"Restrictions date range after conversion: {df_restrictions.index.min()} to {df_restrictions.index.max()}")
                            
                            # Align the dates by using only dates present in both datasets
                            common_dates = df_values.index.intersection(df_restrictions.index)
                            print(f"\nNumber of common dates: {len(common_dates)}")
                            if len(common_dates) == 0:
                                error_msg = (
                                    f"No overlapping dates found between the datasets.\n"
                                    f"Time series data range: {df_values.index.min()} to {df_values.index.max()}\n"
                                    f"Restrictions data range: {df_restrictions.index.min()} to {df_restrictions.index.max()}"
                                )
                                raise ValueError(error_msg)
                                
                            df_values = df_values.loc[common_dates]
                            df_restrictions = df_restrictions.loc[common_dates]
                            
                            print(f"Common data points: {len(common_dates)}")
                            
                            # Create a combined DataFrame for plotting
                            plot_df = pd.DataFrame({
                                'value': df_values['value'],
                                'restrictions': df_restrictions['restrictions']
                            }, index=common_dates)
                            
                            # Sort by date
                            plot_df = plot_df.sort_index()
                            
                            print("\nFirst few rows of sorted data:")
                            print(plot_df.head())
                            print("\nLast few rows of sorted data:")
                            print(plot_df.tail())
                            
                            # Verify we have valid data for plotting
                            if plot_df['value'].isna().all() or plot_df['restrictions'].isna().all():
                                raise ValueError("One or both datasets contain only null values")
                            
                            # Create figure with secondary y-axis using Plotly Express
                            # Reset index to get date as a column for plotting
                            plot_df_reset = plot_df.reset_index()
                            fig = px.line(plot_df_reset, x='date', y='value',
                                        title=f'Time Series Analysis: {selected_table} and Active Restrictions')
                            
                            # Format the main data line
                            fig.update_traces(
                                name=selected_table.replace('_', ' ').title(),
                                line=dict(color='rgb(75, 192, 192)', width=2),
                                mode='lines+markers',
                                marker=dict(size=6)
                            )
                            
                            # Add restrictions as a second y-axis
                            fig.add_scatter(
                                x=plot_df_reset['date'],
                                y=plot_df_reset['restrictions'],
                                name='Active Restrictions',
                                yaxis='y2',
                                line=dict(
                                    color='rgba(255, 99, 132, 0.8)', 
                                    width=2, 
                                    dash='dot'
                                ),
                                marker=dict(size=6)
                            )
                            
                            # Get max value for y2 axis with safety check
                            max_restrictions = plot_df['restrictions'].max()
                            if pd.isna(max_restrictions):
                                max_restrictions = 1  # Default to 1 if no valid max found
                            
                            # Update layout for dual axes with improved formatting
                            fig.update_layout(
                                yaxis=dict(
                                    title=dict(
                                        text=selected_table.replace('_', ' ').title(),
                                        font=dict(color='rgb(75, 192, 192)')
                                    ),
                                    tickfont=dict(color='rgb(75, 192, 192)'),
                                    showgrid=True,
                                    gridcolor='rgba(75, 192, 192, 0.1)',
                                    tickformat=',d'  # Add thousand separators
                                ),
                                yaxis2=dict(
                                    title=dict(
                                        text='Number of Active Restrictions',
                                        font=dict(color='rgba(255, 99, 132, 0.8)')
                                    ),
                                    tickfont=dict(color='rgba(255, 99, 132, 0.8)'),
                                    overlaying='y',
                                    side='right',
                                    showgrid=False,
                                    range=[0, max_restrictions + 1]  # Ensure y2 axis starts at 0
                                ),
                                xaxis=dict(
                                    title=dict(text='Date'),
                                    tickangle=45,
                                    nticks=20,  # Reduce number of x-axis labels
                                    showgrid=True,
                                    gridcolor='rgba(128, 128, 128, 0.1)',
                                ),
                                height=600,  # Increase height for better visibility
                                showlegend=True,
                                legend=dict(
                                    yanchor="top",
                                    y=0.99,
                                    xanchor="left",
                                    x=0.01
                                ),
                                margin=dict(t=30, b=50),  # Adjust margins
                                plot_bgcolor='white'  # White background
                            )
                        
                            time_series_plot = fig.to_html(full_html=False, include_plotlyjs=True)
                            print("Time series plot generated successfully")
                        else:
                            raise ValueError("No restrictions data available for the selected time period")
                    else:
                        raise ValueError("No time series data found for the selected table")
                
                except Exception as plot_error:
                    print(f"Error generating time series plot: {plot_error}")
                    raise
                
                try:
                    # 2. Generate regression plot using Model class
                    print("Creating regression plot...")
                    model = Model(selected_restrictions, 'custom.db', selected_table)
                    df = model.prepare()
                    
                    if not df.empty and len(df) >= 2:
                        print(f"Regression data points: {len(df)}")
                        x = df['restr_value'].values
                        y = df['custom_value'].values
                        correlation = model.get_correlation()
                        print(f"Correlation coefficient: {correlation}")
                        
                        # Calculate regression line parameters
                        slope, intercept = np.polyfit(x, y, 1)
                        
                        # Create regression plot using Plotly Express
                        fig = px.scatter(x=x, y=y,
                                       title=f'Correlation Analysis (r = {correlation:.3f})')
                        
                        # Add regression line
                        line_x = [min(x), max(x)]
                        line_y = [slope * min(x) + intercept, slope * max(x) + intercept]
                        
                        fig.add_scatter(x=line_x, y=line_y,
                                      mode='lines',
                                      name='Regression Line',
                                      line=dict(color='rgba(255, 99, 132, 0.8)', width=2))
                        
                        # Update layout
                        fig.update_traces(
                            marker=dict(size=10, color='rgb(75, 192, 192)', opacity=0.7),
                            selector=dict(mode='markers')
                        )
                        fig.update_layout(
                            xaxis_title='Number of Active Restrictions',
                            yaxis_title=selected_table.replace('_', ' ').title(),
                            height=500,
                            showlegend=True,
                            annotations=[
                                dict(
                                    x=0.05,
                                    y=0.95,
                                    xref='paper',
                                    yref='paper',
                                    text=f'Correlation: {correlation:.3f}',
                                    showarrow=False,
                                    bgcolor='rgba(255, 255, 255, 0.8)',
                                    borderpad=4
                                )
                            ]
                        )
                        
                        regression_plot = fig.to_html(full_html=False)
                        print("Regression plot generated successfully")
                    else:
                        print("Insufficient data for regression analysis")
                
                except Exception as reg_error:
                    print(f"Error generating regression plot: {reg_error}")
                    raise
                
                try:
                    # 3. Generate LLM analysis if prompt is provided
                    if prompt:
                        print("Generating LLM analysis...")
                        correlation = model.get_correlation()
                        meta = f"""The correlation coefficient between the number of lockdown restrictions and {selected_table.replace('_', ' ')} 
                        is {correlation:.3f}. The analysis is based on data from {min(common_dates)} to {max(common_dates)}."""
                        analysis_result = get_resp(meta + "\n\n" + prompt)
                        print("LLM analysis generated successfully")
                
                except Exception as llm_error:
                    print(f"Error generating LLM analysis: {llm_error}")
                    raise
        
        return render_template('time_series.html',
                             tables=tables,
                             restrictions=restrictions,
                             selected_table=selected_table,
                             selected_restrictions=selected_restrictions,
                             prompt=prompt,
                             time_series_plot=time_series_plot,
                             regression_plot=regression_plot,
                             analysis_result=analysis_result)
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        print(f"Error in time_series route: {e}")
        print(f"Traceback: {error_traceback}")
        return render_template('time_series.html',
                             tables=[],
                             restrictions=restrictions,
                             error=f"An error occurred while loading the data: {str(e)}")

@app.route('/api/time-series')
def time_series_data():
    try:
        # Get parameters
        selected_restrictions = request.args.getlist('restrictions[]')
        database = request.args.get('database', 'covid.db')
        table = request.args.get('table')

        print(f"Received request with: database={database}, table={table}, restrictions={selected_restrictions}")

        if not database:
            return jsonify({'error': 'Missing database parameter'}), 400
            
        # Only require table parameter for non-COVID database
        if database != 'covid.db' and not table:
            return jsonify({'error': 'Missing table parameter'}), 400

        # Get a new data server instance
        data_server = get_data_server()
        try:
            print(f"Fetching time series data...")
            # For COVID database, table parameter should be None
            if database == 'covid.db':
                table = None
            data = data_server.serve_time_series(selected_restrictions, database, table)
            
            # Convert SQLAlchemy objects to JSON-serializable format
            formatted_data = []
            for row in data:
                if row[0] is not None:  # Skip null dates
                    formatted_data.append([
                        row[0].isoformat() if hasattr(row[0], 'isoformat') else str(row[0]),
                        float(row[1]) if row[1] is not None else 0
                    ])
            
            print(f"Returning {len(formatted_data)} data points")
            return jsonify(formatted_data)
        finally:
            data_server._db_session.close()
            data_server._graph_session.close()
            data_server._custom_session.close()
    except Exception as e:
        print(f"Error in time_series_data: {str(e)}")
        return jsonify({
            'error': str(e),
            'params': {
                'database': database,
                'table': table,
                'restrictions': selected_restrictions
            }
        }), 500

@app.route('/restriction-distribution')
def restriction_distribution():
    # Get the date range from the database
    data_server = get_data_server()
    start_date, end_date = data_server.get_date_range()
    return render_template('restriction_distribution.html', start_date=start_date, end_date=end_date)

@app.route('/api/restriction-distribution')
def restriction_distribution_data():
    try:
        # Get end date from query parameters
        end_date = request.args.get('end_date', None)
        # Get restriction distribution data
        data_server = get_data_server()
        try:
            restr_distr = data_server.serve_restr_distr(end_date=end_date)
            
            # Convert SQLAlchemy Row objects to JSON-serializable format
            formatted_data = []
            for row in restr_distr:
                formatted_data.append([
                    str(row[0]),  # restriction name
                    float(row[1]) if row[1] is not None else 0  # count
                ])
            
            return jsonify(formatted_data)
        finally:
            data_server._db_session.close()
            data_server._graph_session.close()
            data_server._custom_session.close()
    except Exception as e:
        print(f"Error in restriction_distribution_data: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/timeline')
def timeline():
    # Render the timeline template
    return render_template('timeline.html')

@app.route('/api/timeline')
def timeline_data():
    # Get timeline data as JSON
    data_server = get_data_server()
    timeline_data = data_server.serve_timeline()
    return jsonify(timeline_data)

@app.route('/api/restrictions')
def get_restrictions():
    """Get list of all available restrictions"""
    data_server = get_data_server()
    try:
        restrictions = data_server.get_restrictions()
        # Convert restriction names to strings to ensure JSON serialization
        formatted_restrictions = [str(r) for r in restrictions]
        return jsonify(formatted_restrictions)
    except Exception as e:
        print(f"Error in get_restrictions: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        data_server._db_session.close()
        data_server._graph_session.close()
        data_server._custom_session.close()

@app.route('/api/tables/<database>')
def get_tables(database):
    """Get list of available tables for a given database"""
    try:
        data_server = get_data_server()
        tables = show_tables(database)
        return jsonify(tables)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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

        # Create a CRUD instance with the database name (not path)
        data_server = get_data_server()
        crud = CRUD(database)

        # Generate a unique graph_id based on the number of databases
        graph_id = len(show_tables(database)) + 1

        # Create the table using the CRUD add_table method
        crud.add_table(table_name, graph_id)

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
            flash('Database and table name are required', 'error')
            return redirect(url_for('dataset', database=database))

        # Validate table deletion
        if not v.val_delete_table(database, table_name):
            flash(f'Table {table_name} cannot be deleted as it is immutable', 'error')
            return redirect(url_for('dataset', database=database))

        # Create a CRUD instance with the database name
        data_server = get_data_server()
        crud = CRUD(database)

        # Delete the table using the CRUD remove_table method
        crud.remove_table(database, table_name)

        flash(f'Table {table_name} deleted successfully', 'success')
        return redirect(url_for('dataset', database=database))

    except Exception as e:
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

        # Validate if data can be inserted into this table
        if not v.val_insert(database, table_name):
            flash(f'Cannot insert data into table {table_name} as it is immutable', 'error')
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
        db_path = PATHS.get(database)
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

@app.route('/api/regression')
def regression_data():
    try:
        # Get parameters
        selected_restrictions = request.args.getlist('restrictions[]')
        database = request.args.get('database', 'covid.db')
        table = request.args.get('table')

        print(f"Regression request with: database={database}, table={table}, restrictions={selected_restrictions}")

        if not database:
            return jsonify({'error': 'Missing database parameter'}), 400
            
        # Only require table parameter for non-COVID database
        if database != 'covid.db' and not table:
            return jsonify({'error': 'Missing table parameter'}), 400

        # Create Model instance and get regression data
        try:
            model = Model(selected_restrictions, database, table)
            df = model.prepare()
            
            if df.empty:
                return jsonify({
                    'error': 'No data available for regression analysis',
                    'details': 'Could not find matching data points between restrictions and custom data'
                }), 404

            # Calculate regression line
            x = df['restr_value'].values
            y = df['custom_value'].values / 1000  # Convert to thousands
            
            if len(x) < 2:
                return jsonify({
                    'error': 'Insufficient data for regression analysis',
                    'details': 'Need at least 2 data points to calculate regression'
                }), 400
            
            # Calculate correlation coefficient
            correlation = np.corrcoef(x, y)[0, 1]
            
            # Calculate regression line parameters
            slope, intercept = np.polyfit(x, y, 1)
            
            return jsonify({
                'points': list(zip(x.tolist(), y.tolist())),
                'slope': float(slope),
                'intercept': float(intercept),
                'correlation': float(correlation)
            })

        except Exception as model_error:
            print(f"Model error: {str(model_error)}")
            return jsonify({
                'error': 'Failed to calculate regression',
                'details': str(model_error)
            }), 500

    except Exception as e:
        print(f"Error in regression_data: {str(e)}")
        return jsonify({
            'error': 'Failed to process regression request',
            'details': str(e),
            'params': {
                'database': database,
                'table': table,
                'restrictions': selected_restrictions
            }
        }), 500

@app.route('/api/analyze')
def analyze_data():
    try:
        # Get parameters
        prompt = request.args.get('prompt')
        selected_restrictions = request.args.getlist('restrictions[]')
        database = request.args.get('database', 'covid.db')
        table = request.args.get('table')

        if not prompt:
            return jsonify({'error': 'Missing prompt parameter'}), 400
        if not database:
            return jsonify({'error': 'Missing database parameter'}), 400
        if database != 'covid.db' and not table:
            return jsonify({'error': 'Missing table parameter'}), 400

        # Create Model instance and get correlation
        try:
            model = Model(selected_restrictions, database, table)
            correlation = model.get_correlation()
            
            # Create system prompt with correlation information
            variable = table if table else "restrictions"
            system_prompt = f"The correlation between number of restrictions and {variable} is {correlation:.3f}. "
            
            # Get AI response
            response = get_resp(system_prompt + prompt)
            
            return jsonify({
                'analysis': response,
                'correlation': correlation
            })

        except Exception as model_error:
            print(f"Model error: {str(model_error)}")
            return jsonify({
                'error': 'Failed to analyze data',
                'details': str(model_error)
            }), 500

    except Exception as e:
        print(f"Error in analyze_data: {str(e)}")
        return jsonify({
            'error': 'Failed to process analysis request',
            'details': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True)
