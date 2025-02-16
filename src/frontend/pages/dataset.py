from dash import dcc, html, Input, Output, no_update, register_page, callback, State, ctx
from src.frontend.diagrams import Diagrams
from src.utils import get_databases, show_tables, parse_csv_contents, dynamic_name_id
from src.backend.erd_manager import CRUD
import os
import json
from src.frontend.input_validation import Validator as v

dgms = Diagrams(
    "src/backend/data/covid.db",
    "src/backend/data/graph.db",
    "src/backend/data/mental_health.db"
)
name_to_id = dynamic_name_id()

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
                    # html.Br(),
                    # html.H3("Create Database"),
                    # html.Div(
                    #     id='create-db-menu',
                    #     children=[
                    #         dcc.Input(
                    #             id='new-db',
                    #             placeholder="Create a New Database",
                    #         ),
                    #         html.Button(
                    #             "SUBMIT",
                    #             id='submit-new-db',
                    #             n_clicks=0,
                    #         )
                    #     ]
                    # ),
                    html.Br(),
                    html.H3("Add Table"),
                    html.Div(
                        id='add-menu',
                        children=[
                            dcc.Input(
                                id='table-name-input',
                                placeholder="Enter the Table Name",
                            ),
                            # dcc.Textarea(
                            #     id='columns-input',
                            #     placeholder="""Enter the columns in a json format: column_name:type, nullable, primary, foreign_keys
                            #                 example:
                            #                 {
                            #                     "id": "INTEGER PRIMARY KEY",
                            #                     "name": "INTEGER NOT NULL"
                            #                 }
                            #                 """,
                            # ),
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
                                placeholder="Enter a database to be deleted"
                            ),
                            html.Button(
                                "SUBMIT",
                                id='submit-delete-button',
                                n_clicks=0
                            )
                        ]
                    ),
                    html.Br(),
                    html.Div(
                        [
                            dcc.ConfirmDialog(
                                id='add-val',
                                message="You cannot add this table"
                            ),
                            dcc.ConfirmDialog(
                                id='delete-val',
                                message="You cannot delete this Table"
                            ),
                            dcc.ConfirmDialog(
                                id='insert-val',
                                message="You cannot insert into this Table"
                            ),
                            dcc.ConfirmDialog(
                                id='schema-val',
                                message="Schema of table does not match"
                            )
                        ]
                    )
                ]
            ),
        ]
    )
]

@callback(
    [
        Output('erd-chart', 'figure'),
        Output('back-btn', 'style'),
        Output('back-btn', 'n_clicks'), # this can be deleted
        Output('erd-chart', 'clickData'),

        Output('select_db', 'value'),

        Output('delete-input', 'options'),

        #delete input for add
        Output('table-name-input', 'value'),
        # Output('columns-input', 'value'),

        # warnings
        Output('add-val', 'displayed'),
        Output('delete-val', 'displayed'),
    ],
    [
        Input('select_db', 'value'), # select db

        Input('erd-chart', 'clickData'), # check if table clicked
        Input('back-btn', 'n_clicks'), # check if back button clicked

        Input('submit-create-button', 'n_clicks'), # check if add table new
        Input('submit-delete-button', 'n_clicks'), # check if wants to delete
        # State('columns-input', 'value'),
        State('table-name-input', 'value'),
        State('delete-input', 'value')
    ]
)
def update_erd_chart(select_db, clickData, back_btn, create_btn, delete_btn, new_table, delete_input):
    id = ctx.triggered_id

    # go back
    if id == 'back-btn':
        return dgms.erd(1), dict(display='none'), 0, None, 'covid.db', no_update, "", False, False

    # show table
    elif id == 'erd-chart': 
        table_name = clickData['points'][0].get('text')
        return dgms.get_table(select_db, table_name), dict(), no_update, no_update, no_update, show_tables(select_db), "", False, False
    
    # create table
    elif id == 'submit-create-button':
        if not v.val_create_table(select_db, new_table):
            return no_update, no_update, no_update, no_update, no_update, no_update, "", True, False,

        crud = CRUD(select_db)
        graph_id = len(get_databases())
        crud.add_table(new_table, graph_id)
        return dgms.erd(name_to_id[select_db]), no_update, 0, no_update, no_update, show_tables(select_db), "", False, False

    # delete table
    elif id == 'submit-delete-button':
        if not v.val_delete_table(select_db, delete_input):
            return no_update, no_update, no_update, no_update, no_update, no_update, "", False, True,

        crud = CRUD(select_db)
        crud.remove_table(select_db, delete_input)
        return dgms.erd(name_to_id[select_db]), no_update, 0, no_update, no_update, show_tables(select_db), "", False, False
        
    return dgms.erd(name_to_id[select_db]), dict(display='none'), 0, no_update, no_update, show_tables(select_db), "", False, False

"""
{"new":"INTEGER PRIMARY KEY"}
{"id": "INTEGER PRIMARY KEY", "time":"TEXT NOT NULL", "measured_value":"INTEGER NOT NULL"}
"""

@callback(
    Output('csv-dummy', 'data'),
    Output('upload-data', 'contents'),
    Output('insert-to-table', 'value'),
    Output('insert-val', 'displayed'),
    Output('schema-val', 'displayed'),

    Input('upload-data', 'contents'),
    Input("select_db", 'value'),
    Input('submit-insert', 'n_clicks'),
    State('insert-to-table', 'value')
)
def insert_df(contents, db_name, submit, table):
    if contents and submit:
        data, df = parse_csv_contents(contents)
        if not v.val_insert(db_name, table):
            return no_update, None, "", True, False
        if not v.val_schema(db_name, table, df):
            return no_update, None, "", False, True
        crud = CRUD(db_name)
        crud.insert_data(table, data)
        return no_update, None, "", False, False
    return no_update, no_update, no_update, False, False



