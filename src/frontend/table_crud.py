import random
import pandas as pd
from dash import dcc, html, Dash, dash_table, Output, Input, no_update, State
import dash.exceptions
from src.utils import get_all_tables, get_table_info, get_db_path, query_db

app = Dash(__name__)

all_tables = get_all_tables()

app.layout = html.Div([
    html.H1("TABLE CRUD"),
    html.Div(
        dcc.Dropdown(
            [f"{table['name']} {table['database']}" for table in all_tables],
            id='table-select',
            className='dash-dropdown'
        )
    ),
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
                active_cell=None
            )
        ]
    ),
])

# Load table columns and data
@app.callback(
    Output('data-table', 'columns'),
    Output('data-table', 'data'),
    Output('data-table', 'data_previous'),
    Input('table-select', 'value')
)
def show_table(selection):
    if not selection:
        return no_update, no_update, no_update

    table_name, db_name = selection.split(" ")
    db_path = get_db_path(db_name)

    cols_info = get_table_info(table_name, db_path)
    cols = [{"name": field[1], "id": field[1]} for field in cols_info]
    col_ids = [field[1] for field in cols_info]

    data = query_db(f"SELECT * FROM {table_name}", db_path)
    table_data = [dict(zip(col_ids, row)) for row in data]

    return cols, table_data, table_data  # set both data and data_previous

# Detect edits or deletions
@app.callback(
    Output('data-table', 'data_previous', allow_duplicate=True),
    Input('data-table', 'data'),
    State('data-table', 'data_previous'),
    prevent_initial_call=True
)
def detect_change(data, previous):
    if not previous:
        raise dash.exceptions.PreventUpdate

    # Detect deleted rows
    deleted_rows = [row for row in previous if row not in data]
    if deleted_rows:
        for row in deleted_rows:
            print(row)

    # Detect edited values
    for new_row in data:
        for old_row in previous:
            if old_row.get('id') == new_row.get('id'):  # assuming each row has an 'id' field
                for key in new_row:
                    if new_row[key] != old_row[key]:
                        print(f"Edited row id={new_row['id']} column '{key}': '{old_row[key]}' → '{new_row[key]}'")

    return data  # update previous state

if __name__ == '__main__':
    app.run(debug=True)
