from dash import dcc, html, Dash, Input, Output, no_update, register_page, callback, State
from src.frontend.diagrams import Diagrams
from src.utils import process_multiselect, show_tables, get_databases, select_graphable_tables, get_resp
from src.prediction.pred import Model

dgms = Diagrams(
    "src/backend/data/covid.db",
    "src/backend/data/graph.db",
    "src/backend/data/custom.db"
)

register_page(__name__, path='/time-series')


layout = [
    html.Div(
        id='time-series-page',
        className="section",
        children=[
            html.H1("TIME SERIES"),
            html.Div(
                id='select-data',
                children=[
                    html.H3("Plot against a custom dataset"),
                    dcc.RadioItems(
                        id='plot-against',
                        options=[
                            {'label': 'Yes', 'value': True},
                            {'label': 'No', 'value': False},
                        ],
                        value=False,
                    ),
                    dcc.Dropdown(
                        id='select-db',
                        options = get_databases(),
                        style = dict(display='none')
                    ),
                    html.Br(),
                    dcc.Dropdown(
                        id='select-table',
                        style = dict(display='none')
                    )
                ]
            ),
            dcc.Graph(
                id='time-series-chart',
                figure=dgms.time_series()
            ),
            html.Div(
                id ='restr_multiselect',
                children = [
                    dcc.Dropdown(
                    ["Curfew", 'Eat Out to Help Out', "Eating Places Closed", "Household Mixing Indoors Banned",  "Pubs Closed", "Rule of 6 Indoors", "Shools Closed", "Shops Closed", "Stay at Home", "WFH"],
                    multi=True,
                    placeholder = "All",
                    id = 'restr-select'
                    ),
                ]
            ),
            html.Div(
                id='correlation',
                children = [
                    html.Div(
                        id='corr-graph',
                        children = [
                            dcc.Graph(
                                id='corr-chart',
                                figure=dgms.correlation(),
                                style=dict(display='none')
                            )
                        ]
                    ),
                ]
            ),
            html.Br(),
            html.Div(
                id='generate-resp',
                children=[
                    html.H3("What would you like to know about the data correlation"),
                    dcc.Textarea(
                        id='user-prompt',
                        value="Explain the correlation.",
                        style=dict(display='none')
                    ),
                    html.Button(
                        "SUBMIT",
                        id='submit-prompt',
                        n_clicks=0,
                        style=dict(display='none')
                    ),
                    dcc.Loading(
                        id="loading",
                        type="circle",
                        children = [
                            dcc.Markdown(id='llm-response', style=dict(display='none'))
                        ]
                    ),
                ]
            )
        ]
    )
]

@callback(
    Output('time-series-chart', 'figure'),
    Input('plot-against', 'value'),
    Input('restr-select', 'value'),
    Input('select-db', 'value'),
    Input('select-table', 'value')
)
def update_time_series(plot_against, restrs, db_name, table):
    if plot_against and db_name and table:
        if not restrs:
            return dgms.time_series(db_name=db_name, table=table)
        else:
            if db_name and table:
                return dgms.time_series(restrs=process_multiselect(restrs), db_name=db_name, table=table)
    else:
        if restrs:
            return dgms.time_series(restrs=process_multiselect(restrs), custom=False)
        else:
            return dgms.time_series(custom=False)

@callback(
    Output('corr-chart', 'figure'),
    Input('restr-select', 'value'),
    Input('select-db', 'value'),
    Input('select-table', 'value')
)
def update_correlation(restrs, db_name, table_name):
    if db_name and table_name:
        if not restrs:
            return dgms.correlation(db_name=db_name, table_name=table_name)
        else:
            return dgms.correlation(restrs=process_multiselect(restrs), db_name=db_name, table_name=table_name)
    else:
        return no_update

@callback(
    Output('select-db', 'style'),
    Input('plot-against', 'value')
)
def show_menu(value):
    if value:
        return dict()
    else:
        return dict(display='none')

@callback(
    Output('corr-chart', 'style'),
    Output('user-prompt', 'style'),
    Output('submit-prompt', 'style'),
    Output('llm-response', 'style'),
    Input('select-table', 'value')
)
def show_corr_graph(value):
    if value:
        return dict(), dict(), dict(), dict()
    else:
        return dict(display='none'), dict(display='none'), dict(display='none'), dict(display='none')

@callback(
    Output('select-table', 'style'),
    Output('select-table', 'options'),
    Input('select-db', 'value')
)
def show_table_select(value):
    if value:
        return dict(), select_graphable_tables(show_tables(value))
    return no_update, no_update

@callback(
    Output('llm-response', 'children'),
    State('user-prompt', 'value'),
    Input('submit-prompt', 'n_clicks'),
    Input('restr-select', 'value'),
    State('select-db', 'value'),
    State('select-table', 'value'),
    prevent_initial_call=True
)
def show_llm_resp(prompt, click, restrs, db_name, table_name):
    if click > 0:
        restrs = restrs or []
        m = Model(restrs, db_name, table_name)
        meta=f"The correlation coefficient between the number of lockdown restriction and {table_name} is {m.get_correlation()}."
        resp = get_resp(meta + prompt)
        return resp
    return no_update
    
