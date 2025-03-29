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
                                                ],
                                                page_action='none',
                                                sort_action='native',
                                                filter_action='native',
                                                sort_mode='multi',
                                                persistence=True,
                                                persistence_type='memory',
                                                cell_selectable=True,
                                                dropdown_conditional=[],
                                                dropdown={}
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
            cols = []
            for field in cols_info:
                field_name = field[1]
                field_type = field[2]
                is_pk = field[5]
                
                # Determine the appropriate input type based on the field type
                input_type = "text"
                if field_type.upper() in ['INTEGER', 'FLOAT', 'REAL']:
                    input_type = "numeric"
                elif field_type.upper() == 'DATE':
                    input_type = "datetime"
                elif field_type.upper() == 'DATETIME':
                    input_type = "datetime"
                
                cols.append({
                    "name": field_name,
                    "id": field_name,
                    "editable": True,
                    "type": input_type,
                    "presentation": "markdown" if input_type == "text" else None,
                    "filterable": True,
                    "sortable": True,
                    "clearable": True
                })
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

        # Handle table updates (edits, deletions, additions)
        @dash_app.callback(
            Output('data-table', 'data', allow_duplicate=True),
            [Input('data-table', 'data'),
             Input('save-record-button', 'n_clicks')],
            [State('data-table', 'data_previous'),
             State('table-select', 'value'),
             State('data-table', 'columns')],
            prevent_initial_call=True
        )
        def handle_table_updates(current_data, n_clicks, previous, selection, columns):
            logger.info("handle_table_updates callback triggered")
            
            if not selection:
                raise dash.exceptions.PreventUpdate
                
            table_name, db_name = selection.split(" ")
            db_path = get_db_path(db_name)
            
            # Determine which type of update triggered the callback
            ctx = callback_context
            trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
            
            try:
                engine = create_engine(f'sqlite:///{db_path}')
                
                if trigger_id == 'data-table':
                    # Handle cell edits and row deletions
                    if previous and current_data:
                        # Find edited cells by comparing current and previous data
                        pk_columns = get_primary_keys(table_name, db_path)
                        cols_info = get_table_info(table_name, db_path)
                        col_names = [field[1] for field in cols_info]
                        
                        # Create dictionaries for easier comparison
                        previous_dict = {tuple(row[pk] for pk in pk_columns): row for row in previous}
                        current_dict = {tuple(row[pk] for pk in pk_columns): row for row in current_data}
                        
                        # Handle deletions
                        deleted_pks = set(previous_dict.keys()) - set(current_dict.keys())
                        if deleted_pks:
                            logger.info(f"Deleting rows from {table_name} with primary keys: {deleted_pks}")
                            with engine.connect() as connection:
                                for pk_tuple in deleted_pks:
                                    conditions = " AND ".join([f"{pk} = :{pk}" for pk in pk_columns])
                                    delete_query = f"DELETE FROM {table_name} WHERE {conditions}"
                                    params = dict(zip(pk_columns, pk_tuple))
                                    connection.execute(text(delete_query), params)
                                connection.commit()
                        
                        # Handle edits
                        for pk_tuple in set(previous_dict.keys()) & set(current_dict.keys()):
                            prev_row = previous_dict[pk_tuple]
                            curr_row = current_dict[pk_tuple]
                            
                            # Find changed columns
                            changed_cols = []
                            for col in col_names:
                                if col not in pk_columns and prev_row[col] != curr_row[col]:
                                    changed_cols.append(col)
                            
                            if changed_cols:
                                logger.info(f"Updating row {pk_tuple} with changes in columns: {changed_cols}")
                                conditions = " AND ".join([f"{pk} = :{pk}" for pk in pk_columns])
                                set_clause = ", ".join([f"{col} = :{col}" for col in changed_cols])
                                update_query = f"UPDATE {table_name} SET {set_clause} WHERE {conditions}"
                                
                                params = {pk: curr_row[pk] for pk in pk_columns}
                                params.update({col: curr_row[col] for col in changed_cols})
                                
                                with engine.connect() as connection:
                                    connection.execute(text(update_query), params)
                                    connection.commit()
                
                elif trigger_id == 'save-record-button':
                    # Handle new record addition
                    if columns:
                        new_record = {}
                        has_required_fields = True
                        cols_info = get_table_info(table_name, db_path)
                        required_fields = {field[1] for field in cols_info if field[5]}
                        
                        for col in columns:
                            field_name = col['id']
                            input_value = ctx.inputs.get(f"input-{field_name}.value")
                            
                            if field_name in required_fields and (input_value is None or input_value == ""):
                                has_required_fields = False
                                break
                                
                            new_record[field_name] = input_value if input_value != "" else None
                        
                        if has_required_fields:
                            with engine.connect() as connection:
                                columns = list(new_record.keys())
                                placeholders = ",".join([f":{col}" for col in columns])
                                columns_str = ",".join(columns)
                                
                                insert_query = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
                                connection.execute(text(insert_query), new_record)
                                connection.commit()
                
                # Refresh the data from the database
                cols_info = get_table_info(table_name, db_path)
                col_ids = [field[1] for field in cols_info]
                new_data = query_db(f"SELECT * FROM {table_name}", db_path)
                current_data = [dict(zip(col_ids, row)) for row in new_data]
                
            except Exception as e:
                logger.error(f"Error handling table update: {str(e)}")
                raise
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