from dash import dcc, html, Dash, Input, Output, no_update, register_page, callback
from src.frontend.diagrams import Diagrams


dgms = Diagrams(
    "src/backend/data/covid.db",
    "src/backend/data/graph.db",
    "src/backend/data/mental_health.db"
)

register_page(__name__, path='/dataset')

layout = [
    html.Div(
        className='container',
        children=[
            html.Div(
                id="dataset-page",
                className="section",
                children=[
                    html.H1("DATASET"),
                    dcc.Graph(
                        id='erd-chart', 
                        figure=dgms.erd(),
                        ),
                    html.Div(
                        id='back-button',
                        children=[
                            html.Button(
                                "Back",
                                id='back-btn',
                                n_clicks=0,
                                className='back-button',
                                style=dict(display='none')
                            )
                        ]
                    )
                ]
            ),
        ]
    )
]

@callback(
    [Output('erd-chart', 'figure'),
    Output('back-btn', 'style'),
    Output('back-btn', 'n_clicks')],
    [Input('erd-chart', 'clickData'),
    Input('back-btn', 'n_clicks')]
)
def display_table_info(clickData, n_clicks):
    if not clickData:
        return dgms.erd(), dict(display='none'), 0
    else:
        if n_clicks > 0:
            return dgms.erd(), dict(display='none'), 0
        else:
            return dgms.get_table(clickData['points'][0]['customdata']), dict(), no_update