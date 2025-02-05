import pandas as pd
from dash import Dash, html, dcc
from frontend.diagrams import Diagrams
from backend.utils import fit_slider

dgms = Diagrams(
    "backend/covid.db",
    "backend/graph.db"
)
first, last = fit_slider("backend/covid.db")


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
                    dcc.Graph(
                        figure=dgms.time_series()
                    )
                ]
            ),

            html.Div(
                id='restriction-distribution-page',
                className="section",
                children=[
                    html.H1("RESTRICTION DISTRIBUTION"),
                    dcc.Graph(figure=dgms.restr_distr()),
                    html.Div("Enter a date", className='text-input'),
                    html.Div(), # for extra space
                    html.Div(
                        className='text-input',
                        children=[
                            dcc.DatePickerSingle(
                                id='date-input',
                                date=None,
                                placeholder=''
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
                    dcc.Graph(figure=dgms.timeline())
                ]
            )
        ]
    )
]


if __name__ == '__main__':
    app.run(debug=True)

"""
TODO:
- make user input look nice
- callbacks for bar
- callbacks for timeline
- make graphs look nicer and give better labels
- make utils work

- add erd database
- graph erd
"""