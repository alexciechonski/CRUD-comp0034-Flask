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