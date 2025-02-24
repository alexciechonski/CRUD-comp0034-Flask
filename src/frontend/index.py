"""
Dash Layout Module for COVID-19 Insights Dashboard.

This module defines the main layout for a multi-page Dash application.
It includes navigation links to different pages such as dataset visualization,
time series analysis, restriction distribution, and event timelines.

Dependencies:
- Dash: Used for creating interactive web applications.
- `dcc.Location`: Enables URL-based navigation without refreshing the page.
- `dcc.Link`: Creates navigation links between different pages.

Example Usage:
    Import this module in the main Dash app file:

    ```python
    import frontend.index
    app.layout = frontend.index.layout
    ```

Layout Components:
- `html.H1`: Displays the dashboard title.
- `dcc.Location`: Tracks the current page URL.
- `dcc.Link`: Navigation links to different sections.
- `dash.page_container`: Dynamically loads pages based on URL.
"""
from dash import html, dcc
import dash

layout = html.Div([
    html.H1("COVID-19 Insights", className='centered-item'),
    dcc.Location(id='url', refresh=False),
    html.Div(
        children=[
            dcc.Link('Dataset', href='/dataset'),
            html.Br(),
            dcc.Link('Time Series', href='/time-series'),
            html.Br(),
            dcc.Link('Restriction Distribution', href='/restriction-distribution'),
            html.Br(),
            dcc.Link('Timeline ', href='/timeline'),
        ],
        style={
            'display': 'flex',
            'justify-content': 'center',
            'gap': '20px',
            'padding': '20px'
        }
    ),
    dash.page_container
])
