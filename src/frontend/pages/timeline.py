from dash import dcc, html, Dash, Input, Output, no_update, register_page, callback
from src.frontend.diagrams import Diagrams
import dash_daq as daq
import dash
from src.config import PATHS


dgms = Diagrams(
    "src/backend/data/covid.db",
    "src/backend/data/graph.db",
    "src/backend/data/custom.db"
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
def redirect_on_click(clickData):
    if clickData is None:
        raise dash.exceptions.PreventUpdate
    else:
        clicked_point = clickData['points'][0]
        redirect_url = clicked_point['customdata']
        return redirect_url 
