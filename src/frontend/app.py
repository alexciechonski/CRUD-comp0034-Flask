import pandas as pd
from dash import Dash, html, dcc, callback, Output, Input
from frontend.diagrams import Diagrams
from backend.data_server import DataServer
import dash_daq as daq
from datetime import date
from sqlite3 import DatabaseError
from dash_extensions.javascript import assign, Namespace
import dash

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
                    dcc.Graph(id='erd-chart', figure=dgms.erd())
                ]
            ),

            html.Div(
                id='time-series-page',
                className="section",
                children=[
                    html.H1("TIME SERIES"),
                    dcc.Graph(
                        figure=dgms.time_series()
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
    final_date = date(year, month, day)
    if final_date < date(2024, 1, 15):
        return dgms.restr_distr(final_date)
    else:
        raise DatabaseError

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

# @callback(
#     Output('datatset-page', 'children'),
#     Input('erd-chart', 'clickData')
# )
# def show_table():
#     pass

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