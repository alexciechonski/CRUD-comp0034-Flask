from flask import Flask
from dash import Dash, html, dcc, dash_table, Input, Output, State, no_update, callback_context
import dash.exceptions
from src.utils import get_all_tables, get_table_info, get_db_path, query_db
from sqlalchemy import create_engine, text
from src.backend.erd_manager import CRUD
import logging
import sys

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
    except Exception as e:
        logger.error(f"Error initializing callbacks: {str(e)}")
        raise
    
    logger.info("Dash app creation completed successfully")
    return dash_app 