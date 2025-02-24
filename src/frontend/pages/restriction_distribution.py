from sqlite3 import DatabaseError
from datetime import date
from dash import dcc, html, Input, Output, callback, register_page
import dash_daq as daq
import plotly.graph_objects as go
from src.config import PATHS
from src.frontend.diagrams import Diagrams


dgms = Diagrams(
    PATHS["covid.db"],
    PATHS["graph.db"],
    PATHS["custom.db"]
)

register_page(__name__, path='/restriction-distribution')


layout = [
    html.Div(
        id='restriction-distribution-page',
        children=[
            html.H1("RESTRICTION DISTRIBUTION", className='centered-item'),
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
        ]
    ),
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
    except ValueError as _:
        pass
    except DatabaseError as _:
        pass
    return go.Figure(
        data=[],
        layout=go.Layout(
            title='Error: Could not generate the graph',
            xaxis=dict(title='Date'),
            yaxis=dict(title='Distribution')
        )
    )
