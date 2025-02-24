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
def redirect_on_click(click_data):
    if click_data is None:
        raise dash.exceptions.PreventUpdate
    else:
        clicked_point = click_data['points'][0]
        redirect_url = clicked_point['customdata']
        return redirect_url
