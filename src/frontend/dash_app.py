from flask import Flask
from dash import Dash, html, dcc, dash_table, Input, Output, State, no_update, callback_context
import dash.exceptions
from src.utils import get_all_tables, get_table_info, get_db_path, query_db
from sqlalchemy import create_engine, text
from src.backend.erd_manager import CRUD
import logging
import sys
from typing import List

# Set up logging with more detailed configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def create_dash_app(server):
    """Create a Dash app and integrate it with Flask."""
    print("Starting Dash app creation...")  # Direct print for immediate visibility
    logger.info("Creating Dash app...")
    dash_app = Dash(__name__, server=server, url_base_pathname='/table-crud/')
    
    # Configure the app to work in an iframe
    dash_app.config.suppress_callback_exceptions = True
    dash_app.config.external_stylesheets = [
        'https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css'
    ]
    
    # Get all available tables
    print("Getting all tables...")  # Direct print for immediate visibility
    logger.info("Getting all tables...")
    try:
        all_tables = get_all_tables()
        print(f"Found tables: {all_tables}")  # Direct print for immediate visibility
        logger.info(f"Found tables: {all_tables}")
    except Exception as e:
        print(f"Error getting tables: {str(e)}")  # Direct print for immediate visibility
        logger.error(f"Error getting tables: {str(e)}")
        all_tables = []
    
    # Define the layout
    logger.info("Creating layout...")
    try:
        dash_app.layout = html.Div([
            html.Div(
                className="container-fluid p-3",
                children=[
                    html.Div(
                        className="row mb-4",
                        children=[
                            html.Div(
                                className="col-12",
                                children=[
                                    dcc.Dropdown(
                                        [f"{table['name']} {table['database']}" for table in all_tables],
                                        id='table-select',
                                        className='dash-dropdown'
                                    )
                                ]
                            )
                        ]
                    ),
                    html.Div(
                        className="row",
                        children=[
                            html.Div(
                                className="col-12",
                                children=[
                                    html.Div(
                                        className="table-container",
                                        children=[
                                            dash_table.DataTable(
                                                id="data-table",
                                                columns=[],
                                                data=[],
                                                editable=True,
                                                row_deletable=True,
                                                data_previous=[],
                                                active_cell=None,
                                                row_selectable='single',
                                                style_table={'overflowX': 'auto'},
                                                style_cell={
                                                    'textAlign': 'left',
                                                    'padding': '8px',
                                                    'whiteSpace': 'normal',
                                                    'height': 'auto'
                                                },
                                                style_header={
                                                    'backgroundColor': '#f8f9fa',
                                                    'fontWeight': 'bold'
                                                },
                                                style_data_conditional=[
                                                    {
                                                        'if': {'row_index': 'odd'},
                                                        'backgroundColor': '#f8f9fa'
                                                    }
                                                ]
                                            )
                                        ]
                                    ),
                                    html.Div(
                                        className="form-container",
                                        children=[
                                            html.H4("Add New Record", className="mb-3"),
                                            html.Div(id="input-fields", className="mb-3"),
                                            html.Button(
                                                "Save Record",
                                                id="save-record-button",
                                                className="btn btn-primary",
                                                n_clicks=0
                                            )
                                        ]
                                    )
                                ]
                            )
                        ]
                    )
                ]
            )
        ])
        logger.info("Layout created successfully")
    except Exception as e:
        logger.error(f"Error creating layout: {str(e)}")
        raise
    
    # Initialize callbacks
    logger.info("Initializing callbacks...")
    try:
        # Load table columns and data
        @dash_app.callback(
            Output('data-table', 'columns'),
            Output('data-table', 'data'),
            Output('data-table', 'data_previous'),
            Output('input-fields', 'children'),
            Input('table-select', 'value')
        )
        def show_table(selection):
            logger.info(f"show_table callback triggered with selection: {selection}")
            if not selection:
                logger.info("No selection, returning no_update")
                return no_update, no_update, no_update, no_update
                
            table_name, db_name = selection.split(" ")
            db_path = get_db_path(db_name)
            logger.info(f"Loading table {table_name} from database {db_name}")
            
            cols_info = get_table_info(table_name, db_path)
            logger.info(f"Column info: {cols_info}")
            cols = [{"name": field[1], "id": field[1], "editable": True} for field in cols_info]
            col_ids = [field[1] for field in cols_info]
            
            data = query_db(f"SELECT * FROM {table_name}", db_path)
            logger.info(f"Found {len(data)} rows of data")
            table_data = [dict(zip(col_ids, row)) for row in data]
            
            # Generate input fields for the form
            input_fields = []
            for field in cols_info:
                field_name = field[1]
                field_type = field[2]
                is_pk = field[5]
                
                input_fields.append(
                    html.Div(
                        className="form-group mb-2",
                        children=[
                            html.Label(f"{field_name}{' *' if is_pk else ''}", className="form-label"),
                            dcc.Input(
                                type="text" if field_type.upper() not in ['INTEGER', 'FLOAT', 'REAL'] else "number",
                                id=f"input-{field_name}",
                                className="form-control",
                                required=is_pk
                            )
                        ]
                    )
                )
            
            logger.info("Returning table data and form fields")
            return cols, table_data, table_data, input_fields

        # Handle record deletion
        @dash_app.callback(
            Output('data-table', 'data', allow_duplicate=True),
            Input('data-table', 'data'),
            State('data-table', 'data_previous'),
            State('table-select', 'value'),
            prevent_initial_call=True
        )
        def handle_deletion(data, previous, selection):
            if not selection or not previous:
                raise dash.exceptions.PreventUpdate
                
            table_name, db_name = selection.split(" ")
            db_path = get_db_path(db_name)
            
            # Find deleted rows by comparing previous and current data
            deleted_rows = [row for row in previous if row not in data]
            
            if deleted_rows:
                logger.info(f"Deleting rows from {table_name}: {deleted_rows}")
                engine = create_engine(f'sqlite:///{db_path}')
                
                try:
                    # Get primary key columns
                    cols_info = get_table_info(table_name, db_path)
                    pk_columns = [field[1] for field in cols_info if field[5]]
                    
                    if not pk_columns:
                        logger.error(f"No primary key found for table {table_name}")
                        return data
                    
                    # Delete each row
                    with engine.connect() as connection:
                        for row in deleted_rows:
                            conditions = " AND ".join([f"{pk} = :{pk}" for pk in pk_columns])
                            delete_query = f"DELETE FROM {table_name} WHERE {conditions}"
                            params = {pk: row[pk] for pk in pk_columns}
                            connection.execute(text(delete_query), params)
                        connection.commit()
                    
                    logger.info("Rows deleted successfully")
                finally:
                    engine.dispose()
            
            return data

        # Handle record updates
        @dash_app.callback(
            Output('data-table', 'data_previous', allow_duplicate=True),
            Input('data-table', 'data'),
            State('data-table', 'data_previous'),
            State('table-select', 'value'),
            prevent_initial_call=True
        )
        def handle_updates(data, previous, selection):
            if not selection or not previous:
                raise dash.exceptions.PreventUpdate
                
            table_name, db_name = selection.split(" ")
            db_path = get_db_path(db_name)
            
            # Find updated rows by comparing previous and current data
            updated_rows = []
            for current_row in data:
                for prev_row in previous:
                    if all(current_row.get(pk) == prev_row.get(pk) for pk in get_primary_keys(table_name, db_path)):
                        if current_row != prev_row:
                            updated_rows.append((prev_row, current_row))
                            break
            
            if updated_rows:
                logger.info(f"Updating rows in {table_name}: {updated_rows}")
                engine = create_engine(f'sqlite:///{db_path}')
                
                try:
                    with engine.connect() as connection:
                        for old_row, new_row in updated_rows:
                            # Create WHERE clause using primary key
                            pk_columns = get_primary_keys(table_name, db_path)
                            conditions = " AND ".join([f"{pk} = :{pk}" for pk in pk_columns])
                            
                            # Create SET clause for changed values
                            updates = ", ".join([f"{k} = :new_{k}" for k in new_row.keys()])
                            
                            # Combine parameters
                            params = {f"new_{k}": v for k, v in new_row.items()}
                            params.update({pk: new_row[pk] for pk in pk_columns})
                            
                            update_query = f"UPDATE {table_name} SET {updates} WHERE {conditions}"
                            connection.execute(text(update_query), params)
                        connection.commit()
                    
                    logger.info("Rows updated successfully")
                finally:
                    engine.dispose()
            
            return data

        # Handle new record addition
        @dash_app.callback(
            Output('data-table', 'data', allow_duplicate=True),
            Input('save-record-button', 'n_clicks'),
            [State('table-select', 'value'),
             State('data-table', 'columns'),
             State('data-table', 'data')],
            prevent_initial_call=True
        )
        def handle_addition(n_clicks, selection, columns, current_data):
            if not selection or not columns:
                raise dash.exceptions.PreventUpdate
                
            table_name, db_name = selection.split(" ")
            db_path = get_db_path(db_name)
            
            # Get values from all input fields
            new_record = {}
            has_required_fields = True
            
            # Get column info to check for required fields
            cols_info = get_table_info(table_name, db_path)
            required_fields = {field[1] for field in cols_info if field[5]}  # field[5] is pk flag
            
            for col in columns:
                field_name = col['id']
                input_value = callback_context.inputs.get(f"input-{field_name}.value")
                
                # Check if required field is empty
                if field_name in required_fields and (input_value is None or input_value == ""):
                    has_required_fields = False
                    break
                    
                new_record[field_name] = input_value if input_value != "" else None
            
            if has_required_fields:
                try:
                    # Insert the record into the database
                    engine = create_engine(f'sqlite:///{db_path}')
                    with engine.connect() as connection:
                        columns = list(new_record.keys())
                        placeholders = ",".join([f":{col}" for col in columns])
                        columns_str = ",".join(columns)
                        
                        insert_query = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
                        connection.execute(text(insert_query), new_record)
                        connection.commit()
                    
                    # Refresh the table data
                    col_ids = [field[1] for field in cols_info]
                    data = query_db(f"SELECT * FROM {table_name}", db_path)
                    current_data = [dict(zip(col_ids, row)) for row in data]
                except Exception as e:
                    logger.error(f"Error adding record: {str(e)}")
                    return current_data
                finally:
                    if 'engine' in locals():
                        engine.dispose()
            
            return current_data

        # Helper function to get primary keys
        def get_primary_keys(table_name: str, db_path: str) -> List[str]:
            cols_info = get_table_info(table_name, db_path)
            return [field[1] for field in cols_info if field[5]]

    except Exception as e:
        logger.error(f"Error initializing callbacks: {str(e)}")
        raise
    
    logger.info("Dash app creation completed successfully")
    return dash_app 