from flask import Flask
from dash import Dash, html, dcc, dash_table, Input, Output, State, no_update, callback_context
import dash.exceptions
from src.utils import get_all_tables, get_table_info, get_db_path, query_db
from sqlalchemy import create_engine, text
from src.backend.erd_manager import CRUD
from typing import List
from src.backend.log.log_manager import LogManager

def create_dash_app(server):
    """Create a Dash app and integrate it with Flask."""
    dash_app = Dash(__name__, server=server, url_base_pathname='/table-crud/')
    
    # Configure the app to work in an iframe
    dash_app.config.suppress_callback_exceptions = True
    dash_app.config.external_stylesheets = [
        'https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css'
    ]
    
    # Get all available tables
    try:
        all_tables = get_all_tables()
    except Exception:
        all_tables = []
    
    # Define the layout
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
    except Exception as e:
        raise
    
    # Initialize callbacks
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
            if not selection:
                return no_update, no_update, no_update, no_update
                
            table_name, db_name = selection.split(" ")
            db_path = get_db_path(db_name)
            
            cols_info = get_table_info(table_name, db_path)
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
            
            return cols, table_data, table_data, input_fields

        # Handle table updates (edits, deletions, additions)
        @dash_app.callback(
            Output('data-table', 'data', allow_duplicate=True),
            [Input('data-table', 'data'),
             Input('save-record-button', 'n_clicks')],
            [State('data-table', 'data_previous'),
             State('table-select', 'value'),
             State('data-table', 'columns'),
             State('input-fields', 'children')],
            prevent_initial_call=True
        )
        def handle_table_updates(current_data, n_clicks, previous, selection, columns, input_fields):
            if not selection:
                raise dash.exceptions.PreventUpdate
                
            table_name, db_name = selection.split(" ")
            db_path = get_db_path(db_name)
            
            # Determine which type of update triggered the callback
            ctx = callback_context
            trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
            
            try:
                engine = create_engine(f'sqlite:///{db_path}')
                log_manager = LogManager()
                
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
                            with engine.connect() as connection:
                                for pk_tuple in deleted_pks:
                                    conditions = " AND ".join([f"{pk} = :{pk}" for pk in pk_columns])
                                    delete_query = f"DELETE FROM {table_name} WHERE {conditions}"
                                    params = dict(zip(pk_columns, pk_tuple))
                                    connection.execute(text(delete_query), params)
                                    
                                    # Log the deletion
                                    deleted_row = previous_dict[pk_tuple]
                                    log_manager.delete_change(db_name, table_name, deleted_row)
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
                                conditions = " AND ".join([f"{pk} = :{pk}" for pk in pk_columns])
                                set_clause = ", ".join([f"{col} = :{col}" for col in changed_cols])
                                update_query = f"UPDATE {table_name} SET {set_clause} WHERE {conditions}"
                                
                                with engine.connect() as connection:
                                    connection.execute(text(update_query), curr_row)
                                    connection.commit()
                                    
                                    # Log the update
                                    log_manager.update_change(db_name, table_name, curr_row, prev_row)
                
                elif trigger_id == 'save-record-button' and n_clicks > 0:
                    # Handle new record insertion
                    new_record = {}
                    for field in input_fields:
                        field_name = field['props']['children'][0]['props']['children'].replace(' *', '')
                        input_value = field['props']['children'][1]['props']['value']
                        if input_value:
                            new_record[field_name] = input_value
                    
                    if new_record:
                        # Insert the new record
                        cols = list(new_record.keys())
                        values = [new_record[col] for col in cols]
                        placeholders = ','.join(['?' for _ in cols])
                        cols_str = ','.join(cols)
                        insert_query = f"INSERT INTO {table_name} ({cols_str}) VALUES ({placeholders})"
                        
                        with engine.connect() as connection:
                            connection.execute(text(insert_query), values)
                            connection.commit()
                            
                            # Log the insertion
                            log_manager.create_change(db_name, table_name, new_record)
                
                log_manager.save_log()
                return current_data
                
            except Exception as e:
                print(f"Error in handle_table_updates: {str(e)}")
                raise

        # Helper function to get primary keys
        def get_primary_keys(table_name: str, db_path: str) -> List[str]:
            cols_info = get_table_info(table_name, db_path)
            return [field[1] for field in cols_info if field[5]]

    except Exception as e:
        raise
    
    return dash_app 