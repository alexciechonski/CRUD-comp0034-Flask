import pandas as pd
from dash import Dash, html, dcc, callback, Output, Input, State, no_update
from frontend.diagrams import Diagrams
from backend.data_server import DataServer
import dash_daq as daq
from datetime import date
from sqlite3 import DatabaseError
import dash
import plotly.graph_objects as go
from src.utils import process_multiselect

dgms = Diagrams(
    "src/backend/covid.db",
    "src/backend/graph.db"
)
server = DataServer(
    "src/backend/covid.db",
    "src/backend/graph.db"
)

app = Dash(__name__)

app.layout = [
    html.Div(
        className='container',
        children=[
            html.Div(
                id="dataset-page",
                className="section",
                children=[
                    html.H1("DATASET"),
                    dcc.Graph(
                        id='erd-chart', 
                        figure=dgms.erd(),
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
                    )
                ]
            ),

            html.Div(
                id='time-series-page',
                className="section",
                children=[
                    html.H1("TIME SERIES"),
                    dcc.Graph(
                        id='time-series-chart',
                        figure=dgms.time_series([])
                    ),
                    html.Div(
                        id = 'restr_multiselect',
                        children = [
                            dcc.Dropdown(
                            ["Curfew", 'Eat Out to Help Out', "Eating Places Closed", "Household Mixing Indoors Banned",  "Pubs Closed", "Rule of 6 Indoors", "Shools Closed", "Shops Closed", "Stay at Home", "WFH"],
                            multi=True,
                            placeholder = "All",
                            id = 'dropdown'
                            ),
                            html.Div(
                                id='show-res'
                            )
                        ]
                    )
                ]
            ),

            html.Div(
                id='restriction-distribution-page',
                className="section",
                children=[
                    html.H1("RESTRICTION DISTRIBUTION"),
                    dcc.Graph(
                        id='restriction_distribution_graph',
                        figure=dgms.restr_distr()
                        ),
                    html.Div(
                        className='text-input',
                        children = [
                            html.H3("ENTER A DATE:")
                        ]
                    ),
                    html.Div(
                        className='text-input',
                        children=[
                            daq.NumericInput(
                                id="input-day",
                                value=14,    
                            ),
                            html.Span(" / ", className="slash"),
                            daq.NumericInput(
                                id="input-month",
                                value=1,
                                max=12
                            ),
                            html.Span(" / ", className="slash"),
                            daq.NumericInput(
                                id="input-year",
                                value=2024,
                                max=2024
                            ),
                        ]
                    ),
                    html.Div(id='test'),
                ]
            ),

            html.Div(
                id='timeline-page',
                className="section",
                children=[
                    html.H1("TIMELINE"),
                    dcc.Location(id='url', refresh=True),
                    dcc.Graph(id="timeline-graph", figure=dgms.timeline()),
                ]
            )
        ]
    )
]

@callback(
    Output(component_id='restriction_distribution_graph', component_property='figure'),
    [
        Input(component_id='input-day', component_property='value'),
        Input(component_id='input-month', component_property='value'),
        Input(component_id='input-year', component_property='value')
    ]
)
def query_date(day, month, year):
    try:
        final_date = date(year, month, day)
        if final_date < date(2024, 1, 15):
            return dgms.restr_distr(final_date)
        else:
            return go.Figure()
    except ValueError as val_err:
        pass
    except DatabaseError as db_err:
        pass
    return go.Figure(
        data=[],
        layout=go.Layout(
            title='Error: Could not generate the graph',
            xaxis=dict(title='Date'),
            yaxis=dict(title='Distribution')
        )
    )

@app.callback(
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

@app.callback(
    Output('url', 'href'),
    Input('timeline-graph', 'clickData')
)
def redirect_on_click(clickData):
    if clickData is None:
        raise dash.exceptions.PreventUpdate
    else:
        clicked_point = clickData['points'][0]
        redirect_url = clicked_point['customdata']
        return redirect_url 

@app.callback(
    [Output('erd-chart', 'figure'),
    Output('back-btn', 'style'),
    Output('back-btn', 'n_clicks')],
    [Input('erd-chart', 'clickData'),
    Input('back-btn', 'n_clicks')]
)
def display_table_info(clickData, n_clicks):
    if not clickData:
        return dgms.erd(), dict(display='none'), 0
    else:
        if n_clicks > 0:
            return dgms.erd(), dict(display='none'), 0
        else:
            return dgms.get_table("Date"), dict(), no_update

if __name__ == '__main__':
    app.run(debug=True)

"""
TODO:
- make graphs look nicer and give better labels
- raise db err ???
- foreign keys db creation
- too long functions
- bug in bar chart input
- graphviz warning

- add erd database
- graph erd
"""