"""
Home Page for Dash Application.

This module defines and registers the home page for the Dash web application.
"""
from dash import html, register_page

register_page(__name__, path='/', name='Home')

layout = html.Div([])
