from dash import dcc, html, Dash, Input, Output, no_update, callback, register_page
from src.frontend.diagrams import Diagrams
import dash_daq as daq
from sqlite3 import DatabaseError
from datetime import date
import plotly.graph_objects as go


dgms = Diagrams(
    "src/backend/data/covid.db",
    "src/backend/data/graph.db",
    "src/backend/data/custom.db"
)

register_page(__name__, path='/restriction-distribution')


layout = [
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