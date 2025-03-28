from flask import Flask
from dash import Dash, html, dcc, dash_table, Input, Output, State, no_update
import dash.exceptions
from src.utils import get_all_tables, get_table_info, get_db_path, query_db
from sqlalchemy import create_engine, text
from src.backend.erd_manager import CRUD

def create_dash_app(server):
    """Create a Dash app and integrate it with Flask."""
    dash_app = Dash(__name__, server=server, url_base_pathname='/table-crud/')
    
    # Get all available tables
    all_tables = get_all_tables()
    
    # Define the layout
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
        cols = [{"name": field[1], "id": field[1], "editable": True} for field in cols_info]
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
    
    # Save new record callback
    @dash_app.callback(
        Output('data-table', 'data', allow_duplicate=True),
        Input('save-record-button', 'n_clicks'),
        [State('table-select', 'value'),
         State('data-table', 'columns'),
         State('data-table', 'data')],
        prevent_initial_call=True
    )
    def save_record(n_clicks, selection, columns, current_data):
        print(f"Save record callback triggered with n_clicks: {n_clicks}")
        if not selection or not columns:
            print("No selection or columns, preventing update")
            raise dash.exceptions.PreventUpdate
            
        table_name, db_name = selection.split(" ")
        db_path = get_db_path(db_name)
        print(f"Processing save for table: {table_name} in database: {db_name}")
        
        # Get values from all input fields
        new_record = {}
        has_required_fields = True
        
        # Get column info to check for required fields
        cols_info = get_table_info(table_name, db_path)
        required_fields = {field[1] for field in cols_info if field[5]}  # field[5] is pk flag
        print(f"Required fields: {required_fields}")
        
        for col in columns:
            field_name = col['id']
            input_value = dash.callback_context.inputs.get(f"input-{field_name}.value")
            print(f"Field {field_name}: {input_value}")
            
            # Check if required field is empty
            if field_name in required_fields and (input_value is None or input_value == ""):
                print(f"Required field {field_name} is empty")
                has_required_fields = False
                break
                
            new_record[field_name] = input_value if input_value != "" else None
        
        print(f"New record to insert: {new_record}")
        
        # Only add the record if all required fields are filled
        if has_required_fields:
            try:
                # Insert the record into the database
                engine = create_engine(f'sqlite:///{db_path}')
                with engine.connect() as connection:
                    columns = list(new_record.keys())
                    placeholders = ",".join([f":{col}" for col in columns])
                    columns_str = ",".join(columns)
                    
                    insert_query = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
                    print(f"Executing query: {insert_query}")
                    print(f"With parameters: {new_record}")
                    connection.execute(text(insert_query), new_record)
                    connection.commit()
                    print("Record inserted successfully")
                
                # Refresh the table data
                col_ids = [field[1] for field in cols_info]
                data = query_db(f"SELECT * FROM {table_name}", db_path)
                current_data = [dict(zip(col_ids, row)) for row in data]
                print(f"Table refreshed with {len(current_data)} rows")
            except Exception as e:
                print(f"Error saving record: {str(e)}")
                return current_data
        
        return current_data
    
    # Clear form fields callback
    @dash_app.callback(
        Output('input-fields', 'children'),
        Input('save-record-button', 'n_clicks'),
        [State('table-select', 'value')],
        prevent_initial_call=True
    )
    def clear_form(n_clicks, selection):
        if not selection:
            raise dash.exceptions.PreventUpdate
            
        table_name, db_name = selection.split(" ")
        db_path = get_db_path(db_name)
        
        # Regenerate empty input fields
        cols_info = get_table_info(table_name, db_path)
        new_input_fields = []
        for field in cols_info:
            field_name = field[1]
            field_type = field[2]
            is_pk = field[5]
            
            new_input_fields.append(
                html.Div(
                    className="form-group mb-2",
                    children=[
                        html.Label(f"{field_name}{' *' if is_pk else ''}", className="form-label"),
                        dcc.Input(
                            type="text" if field_type.upper() not in ['INTEGER', 'FLOAT', 'REAL'] else "number",
                            id=f"input-{field_name}",
                            className="form-control",
                            required=is_pk,
                            value=""  # Set empty value to clear the field
                        )
                    ]
                )
            )
        
        return new_input_fields
    
    # Detect edits or deletions
    @dash_app.callback(
        Output('data-table', 'data_previous', allow_duplicate=True),
        Input('data-table', 'data'),
        State('data-table', 'data_previous'),
        State('table-select', 'value'),
        prevent_initial_call=True
    )
    def detect_change(data, previous, selection):
        if not previous or not selection:
            raise dash.exceptions.PreventUpdate
            
        table_name, db_name = selection.split(" ")
        db_path = get_db_path(db_name)
        engine = create_engine(f'sqlite:///{db_path}')
        
        try:
            # Get primary key columns for the table
            cols_info = get_table_info(table_name, db_path)
            pk_columns = [field[1] for field in cols_info if field[5]]  # field[5] is pk flag
            
            if not pk_columns:
                print(f"No primary key found for table {table_name}")
                return data
            
            # Create a mapping of primary key values to full rows for previous data
            previous_map = {}
            for row in previous:
                pk_values = tuple(row[pk] for pk in pk_columns)
                previous_map[pk_values] = row
            
            # Process current data
            for current_row in data:
                pk_values = tuple(current_row[pk] for pk in pk_columns)
                
                if pk_values in previous_map:
                    # This is an edit - compare and update if changed
                    old_row = previous_map[pk_values]
                    if current_row != old_row:
                        print(f"Edited row: {old_row} -> {current_row}")
                        # Create WHERE clause using primary key
                        conditions = " AND ".join([f"{pk} = :{pk}" for pk in pk_columns])
                        # Create SET clause for changed values
                        updates = ", ".join([f"{k} = :new_{k}" for k in current_row.keys()])
                        # Combine parameters
                        params = {f"new_{k}": v for k, v in current_row.items()}
                        params.update({pk: current_row[pk] for pk in pk_columns})
                        
                        update_query = f"UPDATE {table_name} SET {updates} WHERE {conditions}"
                        
                        with engine.connect() as connection:
                            connection.execute(text(update_query), params)
                            connection.commit()
                else:
                    # This is a new row
                    print(f"New row: {current_row}")
                    columns = list(current_row.keys())
                    placeholders = ",".join([f":{col}" for col in columns])
                    columns_str = ",".join(columns)
                    
                    insert_query = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
                    
                    with engine.connect() as connection:
                        connection.execute(text(insert_query), current_row)
                        connection.commit()
            
            # Check for deleted rows
            current_pks = {tuple(row[pk] for pk in pk_columns) for row in data}
            for pk_values, old_row in previous_map.items():
                if pk_values not in current_pks:
                    print(f"Deleted row: {old_row}")
                    conditions = " AND ".join([f"{pk} = :{pk}" for pk in pk_columns])
                    delete_query = f"DELETE FROM {table_name} WHERE {conditions}"
                    
                    with engine.connect() as connection:
                        connection.execute(text(delete_query), {pk: old_row[pk] for pk in pk_columns})
                        connection.commit()
                        
        finally:
            engine.dispose()
                            
        return data  # update previous state
    
    return dash_app 