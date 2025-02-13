from dash import dcc, html, Input, Output, no_update, register_page, callback, State, ctx
from src.frontend.diagrams import Diagrams
from src.utils import get_databases, show_tables, parse_csv_contents
from src.backend.erd_manager import CRUD
import os
import json

dgms = Diagrams(
    "src/backend/data/covid.db",
    "src/backend/data/graph.db",
    "src/backend/data/mental_health.db"
)
name_to_id = {"covid.db":1, "mental_health.db":2}

register_page(__name__, path='/dataset')

layout = [
    html.Div(
        className='container',
        children=[
            html.Div(
                id="dataset-page",
                className="section",
                children=[
                    html.H1("DATASET"),
                    dcc.Dropdown(
                        id='select_db',
                        options=get_databases(),
                        value="covid.db"
                    ),
                    dcc.Graph(
                        id='erd-chart', 
                        figure=dgms.erd(1),
                        ),
                    html.Div(
                        id='back-button',
                        children=[
                            html.Button(
                                "Back",
                                id='back-btn',
                                n_clicks=0,
                                className='back-button',
                                style=dict(display='none')
                            )
                        ]
                    ),
                    html.Br(),
                    html.H3("Insert Data from csv"),
                    html.Div(
                        id='insert-menu',
                        children = [
                            dcc.Upload(
                            id='upload-data',
                            children=html.Div([
                                'Drag and Drop or ',
                                html.A('Select Files')
                            ]),
                            style={
                                'width': '100%',
                                'height': '60px',
                                'lineHeight': '60px',
                                'borderWidth': '1px',
                                'borderStyle': 'dashed',
                                'borderRadius': '5px',
                                'textAlign': 'center',
                                'margin': '10px'
                            },
                            # Allow multiple files to be uploaded
                            multiple=False
                            ),
                            html.Button(
                                "SUBMIT",
                                id='submit-insert',
                                n_clicks=0
                            )
                        ]
                    ),
                    html.Div(
                        children = [
                            dcc.Input(
                            id='insert-to-table',
                            placeholder="Enter a table name"
                            ),
                        ]
                    ),
                    dcc.Store(id='csv-dummy'),
                    html.Br(),
                    html.H3("Create Database"),
                    html.Div(
                        id='create-db-menu',
                        children=[
                            dcc.Input(
                                id='new-db',
                                placeholder="Create a New Database",
                            ),
                            html.Button(
                                "SUBMIT",
                                id='submit-new-db',
                                n_clicks=0,
                            )
                        ]
                    ),
                    html.Br(),
                    html.H3("Add Table"),
                    html.Div(
                        id='add-menu',
                        children=[
                            dcc.Input(
                                id='table-name-input',
                                placeholder="Enter the Table Name",
                            ),
                            dcc.Textarea(
                                id='columns-input',
                                placeholder="""Enter the columns in a json format: column_name:type, nullable, primary, foreign_keys
                                            example:
                                            {
                                                "id": "INTEGER PRIMARY KEY",
                                                "name": "INTEGER NOT NULL"
                                            }
                                            """,
                            ),
                            html.Button(
                                "SUBMIT",
                                id='submit-create-button',
                                n_clicks = 0
                            ),
                        ]
                    ),
                    html.Br(),
                    html.H3("Delete Table"),
                    html.Div(
                        id='delete-form',
                        children=[
                            dcc.Dropdown(
                                id='delete-input',
                                options=show_tables("covid.db"),
                            ),
                            html.Button(
                                "SUBMIT",
                                id='submit-delete-button',
                                n_clicks=0
                            )
                        ]
                    )
                ]
            ),
        ]
    )
]

@callback(
    Output('erd-char', 'figure'),
    Input('select_db', 'value')
)
def get_erd_graph(value):
    if not value:
        return dgms.erd(1)
    if value and value != 1:
        return dgms.erd(name_to_id[value])

@callback(
    [
        Output('erd-chart', 'figure'),
        Output('back-btn', 'style'),
        Output('back-btn', 'n_clicks'),
        Output('erd-chart', 'clickData'),
        Output('select_db', 'value')
    ],
    [
        Input('select_db', 'value'), # select db
        Input('erd-chart', 'clickData'), # check if table clicked
        Input('back-btn', 'n_clicks'), # check if back button clicked
        Input('submit-create-button', 'n_clicks'), # check if add table new
        Input('submit-delete-button', 'n_clicks'), # check if wants to delete
        State('columns-input', 'value'),
        State('table-name-input', 'value'),
        State('delete-input', 'value')
    ]
)
def update_erd_chart(select_db, clickData, back_btn, create_btn, delete_btn, cols, new_table, delete_input):
    id = ctx.triggered_id

    # go back
    if id == 'back-btn':
        return dgms.erd(1), dict(display='none'), 0, None, 'covid.db'

    # show table
    elif id == 'erd-chart': 
        table_name = clickData['points'][0].get('text')
        return dgms.get_table(select_db, table_name), dict(), no_update, no_update, no_update 
    
    # create table
    elif id == 'submit-create-button':
        crud = CRUD(select_db)
        graph_id = len(get_databases())
        print("GID", graph_id)
        crud.add_table(new_table, json.loads(cols), graph_id)
        return dgms.erd(name_to_id[select_db]), no_update, 0, no_update, no_update

    # delete table
    elif id == 'submit-delete-button':
        crud = CRUD(select_db)
        crud.remove_table(select_db, delete_input)
        
    return dgms.erd(name_to_id[select_db]), dict(display='none'), 0, no_update, no_update 

@callback(
    Output('select_db', 'options'),
    Input('submit-new-db', 'n_clicks'),
    Input('select_db', 'options'),
    State('new-db', 'value'),
)
def create_database(submit_new, select_db, new_db):
    if submit_new > 0 and new_db:
        CRUD.create_new_db(new_db)
        n = len(get_databases())
        name_to_id[new_db] = n + 1
        select_db.append({'label': new_db, 'value': new_db})
    return get_databases()

"""
{"new":"INTEGER PRIMARY KEY"}
"""

@callback(
    Output('delete-input', 'options'),
    Input('select_db', 'value')
)
def update_delete_options(value):
    if value:
        return show_tables(value)
    else:
        return no_update

@callback(
    Output('csv-dummy', 'data'),
    Input('upload-data', 'contents'),
    Input("select_db", 'value'),
    Input('submit-insert', 'n_clicks'),
    State('insert-to-table', 'value')
)
def insert_df(contents, db_name, submit, table):
    if contents and submit:
        data = parse_csv_contents(contents)
        crud = CRUD(db_name)
        crud.insert_data(table, data)
    return no_update


"""
BUGS:
Add table:
1. named simple all the time
2. does not show up in new db

GENERAL:
1. use foreign keys in database
2. get rid of name_to_id
3. stop using len(get_databases()) for graph id
"""
