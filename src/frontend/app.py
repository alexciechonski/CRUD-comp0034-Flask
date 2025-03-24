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

# Add the parent directory to Python path
sys.path.append(str(Path(__file__).parent.parent.parent))

from flask import Flask, render_template, url_for, jsonify
from src.backend.data_server import DataServer
from src.config import PATHS
from src.utils import query_db, get_table_info, convert_to_date, show_tables, select_graphable_tables, get_databases, create_table
from src.backend.erd_manager import Visualizer, CRUD
from src.frontend.diagrams import Diagrams
from src.frontend.input_validation import Validator as v

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

if __name__ == '__main__':
    app.run(debug=True)
