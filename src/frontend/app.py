"""
Main entry point for the Dash web application.

This module initializes and configures a Dash app, setting up its layout
and server instance. It also enables page-based navigation and suppresses
callback exceptions for dynamic callbacks.

Dependencies:
- Dash: Web framework for building interactive dashboards.
- frontend.index: Contains the main application layout.
"""
from dash import Dash
import frontend.index

app = Dash(__name__, use_pages=True, suppress_callback_exceptions=True)

app.layout = frontend.index.layout

server = app.server

if __name__ == '__main__':
    app.run(debug=True)
