"""
Timeline Page for Dash Application.

This module defines the layout and callbacks for the timeline page in the Dash web application.
It allows users to:
- View an interactive timeline of significant events.
- Click on timeline events to be redirected to external sources for further information.
"""
from typing import Any, Dict
from dash import dcc, html, Input, Output, register_page, callback
import dash
from src.frontend.diagrams import Diagrams
from src.config import PATHS

dgms = Diagrams(
    PATHS["covid.db"],
    PATHS["graph.db"],
    PATHS["custom.db"]
)

register_page(__name__, path='/timeline')

layout = [
    html.Div(
        id='timeline-page',
        className="section",
        children=[
            html.H1("TIMELINE", className='centered-item'),
            dcc.Location(id='url', refresh=True),
            dcc.Graph(id="timeline-graph", figure=dgms.timeline()),
        ]
    )
]

@callback(
    Output('url', 'href'),
    Input('timeline-graph', 'clickData')
)
def redirect_on_click(click_data: Dict[Any, Any]):
    """
    Redirects the user to an external URL when clicking on a timeline event.

    Steps:
    - Extracts the `customdata` field from the clicked timeline point.
    - Redirects the user to the corresponding external URL.
    - If no click event occurs, prevents updates.

    Args:
        click_data (dict): Click event data from the timeline graph.

    Returns:
        str | PreventUpdate: The external URL to redirect to or no update if no click event.
    """
    if click_data is None:
        raise dash.exceptions.PreventUpdate
    else:
        clicked_point = click_data['points'][0]
        redirect_url = clicked_point['customdata']
        return redirect_url
