import pandas as pd
from dash import Dash, html, dcc
import dash


app = Dash(__name__)

app.layout = [
    html.Div(
        className='container',
        children=[
            html.Div(
                id="dataset-page",
                className="section",
                children=[
                    html.H1("DATASET"),
                    dcc.Graph()
                ]
            ),

            html.Div(
                id='time-series-page',
                className="section",
                children=[
                    html.H1("TIME SERIES"),
                    dcc.Graph()
                ]
            ),

            html.Div(
                id='restriction-distribution-page',
                className="section",
                children=[
                    html.H1("RESTRICTION DISTRIBUTION"),
                    dcc.Graph(),
                    html.Div(
                        className='user-input',
                        children=[
                            dcc.Slider(
                                0, 20, 5,
                                value=10,
                                id='my-slider'
                            ),
                        ]
                    ),
                    html.P("or"),
                    html.Div(
                        className='text-input',
                        children=[
                            dcc.DatePickerSingle(
                                id='date-input',
                                date=None,
                                placeholder='Date'
                            )
                        ]
                    )
                ]
            ),

            html.Div(
                id='timeline-page',
                className="section",
                children=[
                    html.H1("TIMELINE"),
                    dcc.Graph()
                ]
            )
        ]
    )
]


if __name__ == '__main__':
    app.run(debug=True)