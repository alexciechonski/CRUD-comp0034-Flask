"""
Restriction Distribution Page for Dash Application.

This module defines the layout and callback for the restriction distribution
page in the Dash web application. It allows users to visualize restriction
distribution data and filter it by a specified date.

Dependencies:
- `dash`: Used for layout components, callbacks, and UI interactions.
- `dash_daq`: Provides numerical input components.
- `plotly.graph_objects`: Generates interactive graphs.
- `date`: Handles date-based filtering.
- `DatabaseError`: Catches potential database errors.
- `Diagrams`: Manages database queries and visualization generation.
"""
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
    """
    Updates the restriction distribution graph based on the selected date.

    Steps:
    - Constructs a `date` object from user input.
    - If the date is before January 15, 2024, queries the database for restriction data.
    - Handles invalid dates and database errors gracefully.
    - Returns an empty graph with an error message if an exception occurs.

    Args:
        day (int): Selected day.
        month (int): Selected month.
        year (int): Selected year.

    Returns:
        go.Figure: The updated restriction distribution graph or an error message.
    """
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
