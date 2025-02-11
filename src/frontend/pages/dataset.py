from dash import dcc, html, Dash, Input, Output, no_update, register_page, callback, State
from src.frontend.diagrams import Diagrams
from src.utils import get_databases
from src.backend.erd_manager import CRUD
import os

dgms = Diagrams(
    "src/backend/data/covid.db",
    "src/backend/data/graph.db",
    "src/backend/data/mental_health.db"
)

name_to_id = {
    'covid.db': 1,
    'mental_health.db': 2
}

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
                    html.Div(
                        id='insert-menu',
                        children = [
                            html.Button(
                            "Insert Data From CSV",
                            id='update',
                            style=dict(display='none') # made invisible
                           )
                        ]
                    ),
                    html.Div(
                        id='crud-menu',
                        children=[
                            html.Button(
                                "Create Databse",
                                id='create-new-db',
                                n_clicks = 0
                            ),
                            html.Button(
                                "Add Table",
                                id='create-button',
                                n_clicks=0
                            ),
                            html.Button(
                                "Delete Table",
                                id='delete-button',
                                n_clicks=0
                            ) 
                        ]
                    ),
                    html.Div(
                        id='create-db-menu',
                        children=[
                            dcc.Input(
                                id='new-db',
                                placeholder="Create a New Database",
                                style=dict(display='none') # made invisible
                            ),
                            html.Button(
                                "SUBMIT",
                                id='submit-new-db',
                                n_clicks=0,
                                style=dict(display='none') # made invisible
                            )
                        ]
                    ),
                    html.Div(
                        id='add-menu',
                        children=[
                            dcc.Input(
                                id='table-name-input',
                                placeholder="Enter the Table Name",
                                style=dict(display='none') # made invisible
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
                                style=dict(display='none') # made invisible
                            ),
                            html.Button(
                                "SUBMIT",
                                id='submit-create-button',
                                style=dict(display='none') # made invisible
                            )
                        ]
                    ),
                    html.Div(
                        id='delete-form',
                        children=[
                            dcc.Dropdown(
                                id='delete-input',
                                options=get_databases(),
                                style=dict(display='none')
                            ),
                            html.Button(
                                "SUBMIT",
                                id='submit-delete-button',
                                style=dict(display='none')
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
        Input('select_db', 'value'),
        Input('erd-chart', 'clickData'),
        Input('back-btn', 'n_clicks')
    ]
)
def update_erd_chart(select_db, clickData, n_clicks):
    if n_clicks > 0:
        return dgms.erd(1), dict(display='none'), 0, None, 'covid.db'

    if not clickData:
        return dgms.erd(name_to_id[select_db]), dict(display='none'), 0, no_update, no_update 
    else: 
        table_name = clickData['points'][0].get('text')
        print(dgms.get_table(select_db, table_name))
        return dgms.get_table(select_db, table_name), dict(), no_update, no_update, no_update 

# ------- create db callbacks ------

@callback(
    [
        Output('new-db', 'style'),
        Output('submit-new-db', 'style')
    ],
    Input('create-new-db', 'n_clicks')
)
def new_db_menu(n_clicks):
    if n_clicks > 0:
        return dict(), dict()
    else:
        return dict(display='none'), dict(display='none')

@callback(
    Output('select_db', 'options'),
    [
        Input('submit-new-db', 'n_clicks')
    ],
    [
        State('new-db', 'value'),
    ]
)
def create_new_db(n_clicks, value):
    if n_clicks > 0 and value:
        CRUD.create_new_db(value)
    return get_databases()

# ------- create table callbacks -------

@callback(
    [
        Output('table-name-input', 'style'),
        Output('columns-input', 'style'),
        Output('submit-create-button','style')
    ],
    Input('create-button', 'n_clicks')
)
def create_form(n_clicks):
    if n_clicks > 0:
        return dict(), dict(), dict()
    else:
        return dict(display='none'), dict(display='none'), dict(display='none')

# ---------- delete table callbacks ----------

@callback(
    [
        Output('delete-input', 'style'),
        Output('submit-delete-button', 'style')
    ],
    Input('delete-button', 'n_clicks')
)
def delete_form(n_clicks):
    if n_clicks > 0:
        return dict(), dict()
    else:
        return dict(display='none'), dict(display='none'),


