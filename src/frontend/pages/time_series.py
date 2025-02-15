from dash import dcc, html, Dash, Input, Output, no_update, register_page, callback
from src.frontend.diagrams import Diagrams
from src.utils import process_multiselect, show_tables, get_databases

dgms = Diagrams(
    "src/backend/data/covid.db",
    "src/backend/data/graph.db",
    "src/backend/data/mental_health.db"
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
                    dcc.Dropdown(
                        id='select-db',
                        options = get_databases()
                    ),
                    dcc.Dropdown(
                        id='select-table',
                        style = dict(display='none')
                    )
                ]
            ),
            dcc.Graph(
                id='time-series-chart',
                figure=dgms.time_series([])
            ),
            html.Div(
                id ='restr_multiselect',
                children = [
                    dcc.Dropdown(
                    ["Curfew", 'Eat Out to Help Out', "Eating Places Closed", "Household Mixing Indoors Banned",  "Pubs Closed", "Rule of 6 Indoors", "Shools Closed", "Shops Closed", "Stay at Home", "WFH"],
                    multi=True,
                    placeholder = "All",
                    id = 'dropdown'
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
                                figure=dgms.overlayed_series([], "mental_health.db", "MHCareCluster")
                            )
                        ]
                    ),
                ]
            )
        ]
    )
]

@callback(
    Output('time-series-chart', 'figure'),
    Input('dropdown', 'value')
)
def update_time_series(value):
    if not value:
        return dgms.time_series(restrs=[])
    elif isinstance(value, str): 
        value = process_multiselect(value)
        return dgms.time_series(restrs=[value])
    else:  
        value = process_multiselect(value)
        return dgms.time_series(restrs=value)

@callback(
    Output('corr-chart', 'figure'),
    Input('dropdown', 'value')
)
def update_correlation(value):
    if not value:
        return dgms.overlayed_series([], "mental_health.db", "MHCareCluster")
    elif isinstance(value, str):
        value = process_multiselect(value)
        return dgms.overlayed_series([value], "mental_health.db", "MHCareCluster")
    else:  
        value = process_multiselect(value)
        return dgms.overlayed_series(value, "mental_health.db", "MHCareCluster")
