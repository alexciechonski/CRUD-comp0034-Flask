"""
Home Page for Dash Application.

This module defines and registers the home page for the Dash web application.

Dependencies:
- `dash.html`: Provides HTML components for Dash layouts.
- `register_page`: Registers the home page within the multi-page Dash application.
"""
from dash import html, register_page

# Register this page for the root URL
register_page(__name__, path='/', name='Home')

layout = html.Div([])
