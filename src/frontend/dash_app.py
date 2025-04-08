from typing import List
from dash import Dash, html, dcc, dash_table, Input, Output, State, no_update, callback_context
import dash.exceptions
from sqlalchemy import create_engine, text
from src.utils import get_all_tables, get_table_info, get_db_path, query_db
from src.backend.log.log_manager import LogManager

def create_dash_app(server):
    dash_app = Dash(__name__, server=server, url_base_pathname='/table-crud/')
    dash_app.config.suppress_callback_exceptions = True
    dash_app.config.external_stylesheets = [
        'https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css'
    ]

    try:
        all_tables = get_all_tables()
    except Exception:
        all_tables = []

    dash_app.layout = build_layout(all_tables)
    register_callbacks(dash_app)
    return dash_app


def build_layout(all_tables):
    dropdown_options = [f"{table['name']} {table['database']}" for table in all_tables]
    return html.Div([
        html.Div(className="container-fluid p-3", children=[
            html.Div(className="row mb-4", children=[
                html.Div(className="col-12", children=[
                    dcc.Dropdown(dropdown_options, id='table-select', className='dash-dropdown')
                ])
            ]),
            html.Div(className="row", children=[
                html.Div(className="col-12", children=[
                    html.Div(className="table-container", children=[
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
                                {'if': {'row_index': 'odd'}, 'backgroundColor': '#f8f9fa'}
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
                    ]),
                    html.Div(className="form-container", children=[
                        html.H4("Add New Record", className="mb-3"),
                        html.Div(id="input-fields", className="mb-3"),
                        html.Button("Save Record", id="save-record-button",
                                    className="btn btn-primary", n_clicks=0)
                    ])
                ])
            ])
        ])
    ])


def register_callbacks(app):
    @app.callback(
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
        columns = generate_table_columns(cols_info)
        col_ids = [field[1] for field in cols_info]
        rows = query_db(f"SELECT * FROM {table_name}", db_path)
        table_data = [dict(zip(col_ids, row)) for row in rows]
        input_fields = generate_input_fields(cols_info)

        return columns, table_data, table_data, input_fields

    @app.callback(
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
        ctx = callback_context
        trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
        engine = create_engine(f'sqlite:///{db_path}')
        log_manager = LogManager()

        try:
            if trigger_id == 'data-table':
                current_data = handle_edits_and_deletions(engine, log_manager,
                    table_name, db_name, db_path, previous, current_data)
            elif trigger_id == 'save-record-button' and n_clicks > 0:
                current_data = insert_new_record(engine, log_manager, input_fields,
                    table_name, db_name, db_path)
            log_manager.save_log()
            return current_data
        except Exception as e:
            print(f"Error in handle_table_updates: {str(e)}")
            raise


def generate_table_columns(cols_info):
    columns = []
    for field in cols_info:
        field_name = field[1]
        field_type = field[2]
        input_type = "text"
        if field_type.upper() in ['INTEGER', 'FLOAT', 'REAL']:
            input_type = "numeric"
        elif field_type.upper() in ['DATE', 'DATETIME']:
            input_type = "datetime"

        columns.append({
            "name": field_name,
            "id": field_name,
            "editable": True,
            "type": input_type,
            "presentation": "markdown" if input_type == "text" else None,
            "filterable": True,
            "sortable": True,
            "clearable": True
        })
    return columns


def generate_input_fields(cols_info):
    fields = []
    for field in cols_info:
        field_name = field[1]
        field_type = field[2]
        is_pk = field[5]

        fields.append(html.Div(className="form-group mb-2", children=[
            html.Label(f"{field_name}{' *' if is_pk else ''}", className="form-label"),
            dcc.Input(
                type="text" if field_type.upper() not in ['INTEGER', 'FLOAT', 'REAL'] else "number",
                id=f"input-{field_name}",
                className="form-control",
                required=is_pk
            )
        ]))
    return fields


def handle_edits_and_deletions(engine, log_manager, table, database, db_path, prev, curr):
    pk_columns = get_primary_keys(table, db_path)
    cols_info = get_table_info(table, db_path)
    col_names = [f[1] for f in cols_info]

    prev_dict = {tuple(row[pk] for pk in pk_columns): row for row in prev}
    curr_dict = {tuple(row[pk] for pk in pk_columns): row for row in curr}

    with engine.connect() as connection:
        # Handle deletions
        deleted = set(prev_dict.keys()) - set(curr_dict.keys())
        for pk_tuple in deleted:
            conditions = " AND ".join([f"{pk} = :{pk}" for pk in pk_columns])
            delete_query = f"DELETE FROM {table} WHERE {conditions}"
            connection.execute(text(delete_query), dict(zip(pk_columns, pk_tuple)))
            log_manager.delete_change(database, table, prev_dict[pk_tuple])

        # Handle edits
        for pk_tuple in set(prev_dict.keys()) & set(curr_dict.keys()):
            prev_row, curr_row = prev_dict[pk_tuple], curr_dict[pk_tuple]
            changed = [col for col in col_names if col not in pk_columns and prev_row[col] != curr_row[col]]
            if changed:
                set_clause = ", ".join([f"{col} = :{col}" for col in changed])
                conditions = " AND ".join([f"{pk} = :{pk}" for pk in pk_columns])
                connection.execute(text(f"UPDATE {table} SET {set_clause} WHERE {conditions}"), curr_row)
                log_manager.update_change(database, table, curr_row, prev_row)

    return curr


def insert_new_record(engine, log_manager, input_fields, table, database, db_path):
    cols_info = get_table_info(table, db_path)
    required = [field[1] for field in cols_info if field[5] or field[3] == 'NOT NULL']
    new_record = {}

    for field in input_fields:
        field_name = field['props']['children'][0]['props']['children'].replace(' *', '')
        value = field['props']['children'][1]['props']['value']
        if value:
            new_record[field_name] = value

    missing = [f for f in required if f not in new_record]
    if missing:
        raise ValueError(f"Missing required fields: {', '.join(missing)}")

    if new_record:
        cols = list(new_record.keys())
        placeholders = ",".join([f":{col}" for col in cols])
        insert_query = f"INSERT INTO {table} ({','.join(cols)}) VALUES ({placeholders})"
        with engine.connect() as conn:
            conn.execute(text(insert_query), new_record)
            log_manager.create_change(database, table, new_record)

            col_ids = [field[1] for field in cols_info]
            rows = conn.execute(text(f"SELECT * FROM {table}")).fetchall()
            return [dict(zip(col_ids, row)) for row in rows]

    return []


def get_primary_keys(table_name: str, db_path: str) -> List[str]:
    return [field[1] for field in get_table_info(table_name, db_path) if field[5]]
