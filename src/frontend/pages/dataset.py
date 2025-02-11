from dash import dcc, html, Dash, Input, Output, no_update, register_page, callback
from src.frontend.diagrams import Diagrams
from src.utils import get_databases


dgms = Diagrams(
    "src/backend/data/covid.db",
    "src/backend/data/graph.db",
    "src/backend/data/mental_health.db"
)

name_to_id = {
    'covid.db': 1,
    'mental_health.db': 2
}

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
                    dcc.Dropdown(
                        id='select_db',
                        options=get_databases()
                    ),
                    dcc.Graph(
                        id='erd-chart', 
                        figure=dgms.erd(1),
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
    Output('erd-char', 'figure'),
    Input('select_db', 'value')
)
def get_erd_graph(value):
    if not value:
        return dgms.erd(1)
    if value and value != 1:
        return dgms.erd(name_to_id[value])

@callback(
    [
        Output('erd-chart', 'figure'),
        Output('back-btn', 'style'),
        Output('back-btn', 'n_clicks')
    ],
    [
        Input('select_db', 'value'),
        Input('erd-chart', 'clickData'),
        Input('back-btn', 'n_clicks')
    ]
)
def update_erd_chart(select_db, clickData, n_clicks):
    # Handle reset on back button click
    if n_clicks > 0:
        return dgms.erd(1), dict(display='none'), 0

    # Handle user clicking on the chart to display table info
    if clickData:
        return dgms.get_table(clickData['points'][0]['customdata']), dict(), no_update

    # Handle select_db input to update the ERD graph
    if select_db and select_db != 'covid.db':
        return dgms.erd(name_to_id[select_db]), dict(display='none'), no_update

    # Default case when no other input applies
    return dgms.erd(1), dict(display='none'), no_update

