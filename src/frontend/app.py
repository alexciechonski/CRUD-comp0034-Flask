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
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

# Add the parent directory to Python path
sys.path.append(str(Path(__file__).parent.parent.parent))

from flask import Flask, render_template, url_for, jsonify, send_file
from src.backend.data_server import DataServer
from src.utils import (
    query_db, 
    get_table_info, 
    convert_to_date, 
    show_tables, 
    select_graphable_tables, 
    get_databases, 
    create_table, 
    get_graphable_tables,
    get_resp,
    get_db_path,
    graphable_tables,
    get_all_tables
)
from src.backend.erd_manager import Visualizer, CRUD
from src.frontend.diagrams import Diagrams
from src.backend.validation import Validator as v
from src.prediction.pred import Model
from src.backend.routes import bp as restriction_bp

app = Flask(__name__,
            template_folder='templates',
            static_folder='static')

# Set a secret key for flash messages
app.secret_key = 'your-secret-key-here'  # Replace with a secure secret key in production

# Register blueprints
app.register_blueprint(restriction_bp, url_prefix='')

# Initialize SQLAlchemy session
engine = create_engine(f'sqlite:///{get_db_path("covid.db")}')
Session = sessionmaker(bind=engine)

# Initialize Diagrams
diagrams = Diagrams(
    db_name='covid.db'
)

def get_data_server():
    """Create a new DataServer instance for each request"""
    return DataServer(
        db_name='covid.db'
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
        db_names = get_databases()
        # Format database names as objects with label and value attributes
        databases = [{'label': db, 'value': db} for db in db_names]
        
        # Get all tables for the selected database
        tables = show_tables(selected_db)
        
        # Get table info and format it properly
        table_info = {}
        for table in tables:
            try:
                # Get table schema information using get_table_info
                schema_info = get_table_info(table, get_db_path(selected_db))
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

        # Get ERD visualization using Visualizer
        try:
            # If there are no tables, show a message instead of trying to create a graph
            if not tables:
                erd_html = '''
                    <div class="erd-container">
                        <div class="alert alert-info">
                            <h4 class="alert-heading">Empty Database</h4>
                            <p>This database has no tables yet. Create a table to get started!</p>
                        </div>
                    </div>
                '''
            else:
                # Create engine and session for the selected database
                db_engine = create_engine(f'sqlite:///{get_db_path(selected_db)}')
                DbSession = sessionmaker(bind=db_engine)
                
                # Create Visualizer instance with the correct session
                visualizer = Visualizer(DbSession())
                
                # Get adjacency list with relationship types
                adj_list = visualizer.get_adj_list(selected_db)
                
                # Check if there are any relationships
                has_relationships = any(relationships for relationships in adj_list.values())
                
                # Create a NetworkX graph
                G = nx.DiGraph()
                
                # Create a case mapping dictionary to ensure consistent case
                case_mapping = {}
                
                # Add all tables as nodes, regardless of relationships
                for table in tables:
                    G.add_node(table)
                
                if has_relationships:
                    # First pass: collect all table names and determine canonical case
                    all_tables = set()
                    for source_table, relationships in adj_list.items():
                        all_tables.add(source_table.lower())
                        for target_table, _ in relationships:
                            all_tables.add(target_table.lower())
                    
                    # Create case mapping using actual table names from database
                    actual_tables = {table.lower(): table for table in tables}
                    
                    # Update case mapping for tables with relationships
                    for table_lower in all_tables:
                        if table_lower in actual_tables:
                            canonical_name = actual_tables[table_lower]
                            case_mapping[table_lower] = canonical_name
                    
                    # Add edges with relationship types using correct case
                    for source_table, relationships in adj_list.items():
                        source_lower = source_table.lower()
                        if source_lower in case_mapping:
                            source_canonical = case_mapping[source_lower]
                            for target_table, rel_type in relationships:
                                target_lower = target_table.lower()
                                if target_lower in case_mapping:
                                    target_canonical = case_mapping[target_lower]
                                    G.add_edge(source_canonical, target_canonical, relationship=rel_type)
                
                edge_count = len(G.edges())
                print(f"\nTotal edges found: {edge_count}")
                if edge_count > 0:
                    print(f"Graph edges with relationships: {list(G.edges(data=True))}")
                
                # Create visualization
                plt.figure(figsize=(12, 10))
                
                # Use spring layout with optimized parameters for connected graphs
                # Use circular layout for disconnected nodes
                pos = nx.spring_layout(G, k=2, iterations=50) if edge_count > 0 else nx.circular_layout(G)
                
                # Draw nodes
                nx.draw_networkx_nodes(G, pos, node_color='lightblue', 
                                     node_size=3000, alpha=0.7)
                
                # Draw node labels
                nx.draw_networkx_labels(G, pos, font_size=10, font_weight='bold')
                
                if edge_count > 0:
                    # Draw edges with arrows and relationship labels
                    nx.draw_networkx_edges(G, pos, edge_color='gray', arrows=True, 
                                         arrowsize=20, width=1.5)
                    
                    # Add edge labels (relationship types)
                    edge_labels = nx.get_edge_attributes(G, 'relationship')
                    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels,
                                               font_size=8, font_color='red')
                
                # Add padding around the graph
                plt.margins(0.2)
                
                # Convert plot to image
                img = io.BytesIO()
                plt.savefig(img, format='png', bbox_inches='tight', dpi=200)
                img.seek(0)
                plt.close()
                
                # Convert to base64 for embedding in HTML
                title = "Entity Relationship Diagram"
                desc = "Showing tables" + (" and their relationships (1:1, 1:N, N:M)" if edge_count > 0 else " (no relationships)")
                    
                erd_html = f'''
                    <div class="erd-container">
                        <h4 class="text-center mb-3">{title}</h4>
                        <p class="text-muted text-center mb-3">{desc}</p>
                        <img src="data:image/png;base64,{base64.b64encode(img.getvalue()).decode()}" 
                             class="img-fluid" 
                             style="max-width: 100%; height: auto; border: 1px solid #ddd; border-radius: 4px; padding: 5px;">
                    </div>
                '''
            
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
        finally:
            # Clean up database resources
            if 'db_engine' in locals():
                db_engine.dispose()

        return render_template('dataset.html', 
                             table_info=table_info,
                             selected_db=selected_db,
                             databases=databases,
                             erd_html=erd_html)
    except Exception as e:
        # Format database names as objects with label and value attributes
        db_names = get_databases()
        databases = [{'label': db, 'value': db} for db in db_names]
        return render_template('dataset.html', 
                             error=str(e),
                             selected_db=selected_db,
                             databases=databases)

@app.route('/time-series', methods=['GET', 'POST'])
def time_series():
    # Get selected database from query parameters, default to covid.db
    selected_db = request.args.get('database', 'covid.db')
    
    # Get data server instance with the selected database
    data_server = get_data_server()
    try:
        # Get list of available databases
        databases = get_databases()
        
        # Get graphable tables for the selected database
        tables = graphable_tables()
        
        # Get restrictions for the selected database
        restrictions = data_server.get_restrictions(selected_db)
        
        # Handle POST request for analysis
        if request.method == 'POST':
            # Get form data
            table = request.form.get('table')
            selected_restrictions = request.form.getlist('restrictions[]')
            prompt = request.form.get('prompt')
            
            if not table or not selected_restrictions or not prompt:
                return render_template('time_series.html',
                                     databases=databases,
                                     selected_db=selected_db,
                                     tables=tables,
                                     restrictions=restrictions,
                                     error="Please fill in all required fields")
            
            try:
                # Extract database and table names from the combined string
                db_name, table_name = table.split('.')
                db_name = f"{db_name}.db"  # Add back the .db extension
                
                # Create Model instance and get correlation
                model = Model(selected_restrictions, db_name, table_name)
                correlation = model.get_correlation()
                
                # Create system prompt with correlation information
                system_prompt = f"The correlation between number of restrictions and {table_name} is {correlation:.3f}. "
                
                # Get AI response
                analysis_result = get_resp(system_prompt + prompt)
                
                # Get time series data for plotting
                time_series_data = data_server.serve_time_series(selected_restrictions, database='covid.db', table=None)  # Get restrictions data
                custom_series_data = data_server.serve_time_series(selected_restrictions, database=db_name, table=table_name)  # Get custom variable data
                
                # Create time series plot
                # Create DataFrame for restrictions
                restrictions_df = pd.DataFrame(time_series_data, columns=['date', 'total_restrictions'])
                restrictions_df['date'] = pd.to_datetime(restrictions_df['date'])
                
                # Create DataFrame for custom variable
                custom_df = pd.DataFrame(custom_series_data, columns=['date', 'measured_value'])
                custom_df['date'] = pd.to_datetime(custom_df['date'])
                
                # Merge the dataframes
                merged_df = pd.merge_asof(restrictions_df, custom_df, on='date', direction='nearest')
                
                # Create figure with secondary y-axis
                fig = px.line(merged_df, x='date', y='total_restrictions',
                            title='Time Series Analysis')
                
                # Add second trace on secondary y-axis
                fig.add_scatter(x=merged_df['date'], y=merged_df['measured_value'],
                              name=f'{table_name}',
                              yaxis='y2')
                
                # Update layout for dual axes
                fig.update_layout(
                    yaxis=dict(
                        title=dict(
                            text='Number of Restrictions',
                            font=dict(color='blue')
                        ),
                        tickfont=dict(color='blue')
                    ),
                    yaxis2=dict(
                        title=dict(
                            text=f'{table_name} Value',
                            font=dict(color='red')
                        ),
                        tickfont=dict(color='red'),
                        overlaying='y',
                        side='right'
                    ),
                    xaxis=dict(
                        title=dict(
                            text='Date'
                        )
                    ),
                    showlegend=True
                )
                
                # Update first trace name and color
                fig.data[0].name = 'Restrictions'
                fig.data[0].line.color = 'blue'
                fig.data[1].line.color = 'red'
                
                time_series_plot = pio.to_html(fig, full_html=False)
                
                # Create regression plot
                regression_data = model.prepare()
                if not regression_data.empty:
                    fig = px.scatter(regression_data, x='restr_value', y='custom_value',
                                   title='Correlation Analysis',
                                   labels={'restr_value': 'Number of Restrictions',
                                          'custom_value': f'{table_name} Value'})
                    regression_plot = pio.to_html(fig, full_html=False)
                else:
                    regression_plot = None
                
                return render_template('time_series.html',
                                   databases=databases,
                                   selected_db=selected_db,
                                   tables=tables,
                                   restrictions=restrictions,
                                   selected_table=table,
                                   selected_restrictions=selected_restrictions,
                                   prompt=prompt,
                                   time_series_plot=time_series_plot,
                                   regression_plot=regression_plot,
                                   analysis_result=analysis_result)
                
            except Exception as e:
                print(f"Error in time series analysis: {str(e)}")  # Add debug print
                return render_template('time_series.html',
                                     databases=databases,
                                     selected_db=selected_db,
                                     tables=tables,
                                     restrictions=restrictions,
                                     error=str(e))
        
        # Handle GET request
        return render_template('time_series.html',
                             databases=databases,
                             selected_db=selected_db,
                             tables=tables,
                             restrictions=restrictions)
    finally:
        data_server._db_session.close()
        data_server._custom_session.close()

@app.route('/api/time-series')
def time_series_data():
    # Get data server instance
    data_server = get_data_server()
    try:
        # Get parameters from request
        database = request.args.get('database', 'covid.db')
        table = request.args.get('table')
        restrictions = request.args.getlist('restrictions[]')
        
        # Get time series data
        data = data_server.serve_time_series(restrictions, database=database, table=table)
        
        return jsonify(data)
    finally:
        data_server._db_session.close()
        data_server._custom_session.close()

@app.route('/timeline')
def timeline():
    # Render the timeline template
    return render_template('timeline.html')

@app.route('/api/timeline')
def timeline_data():
    # Get timeline data as JSON
    data_server = get_data_server()
    try:
        data = data_server.serve_timeline()
        return jsonify(data)
    finally:
        data_server._db_session.close()
        data_server._custom_session.close()

@app.route('/api/restrictions')
def get_restrictions():
    # Get restrictions for a specific database
    database = request.args.get('database', 'covid.db')
    data_server = get_data_server()
    try:
        restrictions = data_server.get_restrictions(database)
        return jsonify(restrictions)
    finally:
        data_server._db_session.close()
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
        crud = CRUD(database)
        try:
            # Delete the table using the CRUD remove_table method
            crud.remove_table(database, table_name)
            flash(f'Table {table_name} deleted successfully', 'success')
        finally:
            # Clean up the CRUD instance
            crud.engine.dispose()

        return redirect(url_for('dataset', database=database))

    except Exception as e:
        print(f"Error in delete_table_endpoint: {str(e)}")
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

@app.route('/table-crud', methods=['GET', 'POST'])
def table_crud():
    """Render the Table CRUD page with available tables."""
    try:
        # Handle POST request for adding/updating/deleting records
        if request.method == 'POST':
            action = request.form.get('action')
            selected_db = request.form.get('database')
            selected_table = request.form.get('table')
            
            print(f"POST request received - Action: {action}, DB: {selected_db}, Table: {selected_table}")
            print(f"Form data: {request.form}")
            
            if action == 'add':
                try:
                    if not selected_table or not selected_db:
                        flash('No table or database selected', 'error')
                        return redirect(url_for('table_crud'))
                    
                    # Create a dictionary of column values from form data
                    record_data = {
                        key: value for key, value in request.form.items()
                        if key not in ['action', 'database', 'table']
                    }
                    
                    print(f"Record data to insert: {record_data}")
                    
                    # Create a CRUD instance
                    crud = CRUD(selected_db)
                    try:
                        # Insert the data
                        crud.insert_data(selected_table, [record_data])
                        flash('Record added successfully!', 'success')
                    except Exception as e:
                        print(f"Error in crud.insert_data: {str(e)}")
                        flash(f'Error adding record: {str(e)}', 'error')
                    finally:
                        crud.engine.dispose()
                        
                except Exception as e:
                    print(f"Error in add record handling: {str(e)}")
                    flash(f'Error adding record: {str(e)}', 'error')
                
                return redirect(url_for('table_crud', table=selected_table))
                
            elif action == 'delete':
                try:
                    if not selected_table or not selected_db:
                        flash('No table or database selected', 'error')
                        return redirect(url_for('table_crud'))
                    
                    # Create a dictionary of column values from form data
                    record_data = {
                        key: value for key, value in request.form.items()
                        if key not in ['action', 'database', 'table']
                    }
                    
                    print(f"Record data to delete: {record_data}")
                    
                    # Create SQLAlchemy engine
                    db_path = get_db_path(selected_db)
                    engine = create_engine(f'sqlite:///{db_path}')
                    
                    try:
                        # First check if the record exists
                        conditions = " AND ".join([f"{k} = :{k}" for k in record_data.keys()])
                        check_query = f"SELECT COUNT(*) FROM {selected_table} WHERE {conditions}"
                        
                        with engine.connect() as connection:
                            result = connection.execute(text(check_query), record_data)
                            count = result.scalar()
                            
                            if count == 0:
                                flash('Record not found. Please check the values and try again.', 'error')
                            else:
                                # Delete the record
                                delete_query = f"DELETE FROM {selected_table} WHERE {conditions}"
                                connection.execute(text(delete_query), record_data)
                                connection.commit()
                                flash('Record deleted successfully!', 'success')
                    finally:
                        engine.dispose()
                        
                except Exception as e:
                    print(f"Error in delete record handling: {str(e)}")
                    flash(f'Error deleting record: {str(e)}', 'error')
                
                return redirect(url_for('table_crud', table=selected_table))
                
        # Handle GET request
        selected_table = request.args.get('table')
        
        print(f"GET request - Selected Table: {selected_table}")
        
        # Get list of all available tables across all databases
        tables = get_all_tables()
        print(f"Available tables: {tables}")
        
        # Initialize variables for table data
        table_data = None
        table_columns = None
        selected_db = None
        
        # If a table is selected, fetch its data
        if selected_table:
            try:
                # Find the table info from the list of tables
                table_info = next((table for table in tables if table['name'].lower() == selected_table.lower()), None)
                
                if not table_info:
                    raise ValueError(f"Could not find table '{selected_table}'")
                
                # Get the correct case for the table name and its database
                selected_table = table_info['name']
                selected_db = table_info['database']
                
                # Get the database path
                db_path = get_db_path(selected_db)
                if not db_path:
                    raise ValueError(f"Could not find database path for {selected_db}")
                
                print(f"Using database path: {db_path} for table: {selected_table}")
                
                # Create SQLAlchemy engine
                engine = create_engine(f'sqlite:///{db_path}')
                
                try:
                    # Create a connection
                    with engine.connect() as connection:
                        # Get table columns
                        inspector = inspect(engine)
                        columns = inspector.get_columns(selected_table)
                        table_columns = [col['name'] for col in columns]
                        print(f"Found columns: {table_columns}")
                        
                        # Query table data
                        result = connection.execute(text(f"SELECT * FROM {selected_table} LIMIT 100"))
                        table_data = result.fetchall()
                        print(f"Retrieved {len(table_data) if table_data else 0} rows")
                        
                finally:
                    engine.dispose()
                
            except SQLAlchemyError as e:
                error_msg = f"Database error: {str(e)}"
                print(error_msg)
                flash(error_msg, "error")
            except ValueError as e:
                error_msg = str(e)
                print(error_msg)
                flash(error_msg, "error")
            except Exception as e:
                error_msg = f"Error fetching table data: {str(e)}"
                print(error_msg)
                flash(error_msg, "error")
        
        return render_template('table_crud.html', 
                             tables=tables,
                             selected_db=selected_db,
                             selected_table=selected_table,
                             table_data=table_data,
                             table_columns=table_columns)
                             
    except Exception as e:
        error_msg = f"Unexpected error in table_crud: {str(e)}"
        print(error_msg)
        flash(error_msg, "error")
        return render_template('table_crud.html', 
                             tables=get_all_tables(),
                             selected_db=None)

if __name__ == '__main__':
    app.run(debug=True)
