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
    html.Div(
        id='add-records-form',  # fixed typo in id
        children=[]
    )
])

# Load table columns and data + generate form
@app.callback(
    Output('data-table', 'columns'),
    Output('data-table', 'data'),
    Output('add-records-form', 'children'),
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

    # Generate input form for adding new records
    form = html.Div([
        html.H4(f"Add Record to {table_name}"),
        html.Div([
            html.Div([
                html.Label(col_id),
                dcc.Input(id=f'input-{col_id}', type='text', debounce=True)
            ], style={'margin-bottom': '10px'}) for col_id in col_ids
        ]),
        html.Button('Submit', id='submit-button', n_clicks=0)
    ])

    return cols, table_data, form

if __name__ == '__main__':
    app.run(debug=True)
