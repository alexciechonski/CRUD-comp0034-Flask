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
    "src/backend/data/custom.db"
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
                    html.H1("DATASET", className='centered-item'),
                    dcc.Dropdown(
                        id='select_db',
                        className='user-input',
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
                                className='button',
                                style=dict(display='none')
                            )
                        ]
                    ),
                    html.Br(),
                    html.H3("Insert Data from csv", className='centered-item'),
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
                                'width': '70%',
                                'height': '60px',
                                'lineHeight': '60px',
                                'borderWidth': '1px',
                                'borderStyle': 'dashed',
                                'borderRadius': '5px',
                                'textAlign': 'center',
                                'margin': '10px auto'
                            },
                            multiple=False
                            ),
                            dcc.Dropdown(
                                id='insert-to-table',
                                className='user-input',
                                options=show_tables("covid.db"),
                                placeholder="Enter a table name"
                                ),
                            html.Div(
                                className='centered-item',
                                children=[
                                    html.Button(
                                        "SUBMIT",
                                        id='submit-insert',
                                        className="button",
                                        n_clicks=0,
                                    )
                                ]
                            ),
                        ]
                    ),
                    dcc.Store(id='csv-dummy'),
                    html.Br(),
                    html.H3("Add Table", className='centered-item'),
                    html.Div(
                        id='add-menu',
                        children=[
                            html.Div(
                                style={"width":"100%", "display":"flex"},
                                children=[
                                    dcc.Input(
                                        id='table-name-input',
                                        placeholder="Enter the Table Name",
                                        style={"width": "70%", "margin":"0 auto", "padding": "10px"}
                                    ),
                                ],
                            ),
                            html.Div(
                                className='centered-item',
                                children=[
                                    html.Button(
                                        "SUBMIT",
                                        id='submit-create-button',
                                        className='button',
                                        n_clicks = 0
                                    )
                                ]
                            ),
                        ]
                    ),
                    html.Br(),
                    html.H3("Delete Table", className='centered-item'),
                    html.Div(
                        id='delete-form',
                        children=[
                            html.Div(
                                className='user-input',
                                children=[
                                    dcc.Dropdown(
                                        id='delete-input',
                                        options=show_tables("covid.db"),
                                        placeholder="Enter a database to be deleted"
                                    ),
                                ]
                            ),
                            html.Div(
                                className='centered-item',
                                children=[
                                    html.Button(
                                        "SUBMIT",
                                        id='submit-delete-button',
                                        className='button',
                                        n_clicks=0
                                    )
                                ]
                            ),
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

        # warnings
        Output('add-val', 'displayed'),
        Output('delete-val', 'displayed'),

        Output('insert-to-table', 'options')
    ],
    [
        Input('select_db', 'value'), # select db

        Input('erd-chart', 'clickData'), # check if table clicked
        Input('back-btn', 'n_clicks'), # check if back button clicked

        Input('submit-create-button', 'n_clicks'), # check if add table new
        Input('submit-delete-button', 'n_clicks'), # check if wants to delete
        State('table-name-input', 'value'),
        State('delete-input', 'value')
    ]
)
def update_erd_chart(select_db, clickData, back_btn, create_btn, delete_btn, new_table, delete_input):
    id = ctx.triggered_id

    # go back
    if id == 'back-btn':
        return dgms.erd(1), dict(display='none'), 0, None, 'covid.db', no_update, "", False, False, show_tables(select_db)

    # show table
    elif id == 'erd-chart': 
        table_name = clickData['points'][0].get('text')
        return dgms.get_table(select_db, table_name), dict(), no_update, no_update, no_update, show_tables(select_db), "", False, False, show_tables(select_db)
    
    # create table
    elif id == 'submit-create-button':
        if not v.val_create_table(select_db, new_table):
            return no_update, no_update, no_update, no_update, no_update, no_update, "", True, False, show_tables(select_db)

        crud = CRUD(select_db)
        graph_id = len(get_databases())
        crud.add_table(new_table, graph_id)
        return dgms.erd(name_to_id[select_db]), no_update, 0, no_update, no_update, show_tables(select_db), "", False, False, show_tables(select_db)

    # delete table
    elif id == 'submit-delete-button':
        if not v.val_delete_table(select_db, delete_input):
            return no_update, no_update, no_update, no_update, no_update, no_update, "", False, True, show_tables(select_db)

        crud = CRUD(select_db)
        crud.remove_table(select_db, delete_input)
        return dgms.erd(name_to_id[select_db]), no_update, 0, no_update, no_update, show_tables(select_db), "", False, False, show_tables(select_db)
        
    return dgms.erd(name_to_id[select_db]), dict(display='none'), 0, no_update, no_update, show_tables(select_db), "", False, False, show_tables(select_db)

@callback(
    Output('csv-dummy', 'data'),
    Output('upload-data', 'contents'),
    # Output('insert-to-table', 'options'),
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
            return no_update, None, True, False
        if not v.val_schema(df):
            return no_update, None, False, True
        crud = CRUD(db_name)
        crud.insert_data(table, data)
        return no_update, None, False, False
    return no_update, no_update, False, False



