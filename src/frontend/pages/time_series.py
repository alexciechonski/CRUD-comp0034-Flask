"""
Time Series Analysis Page for Dash Application.

This module defines the layout and callbacks for the time series analysis page
in the Dash web application.

It allows users to:
- Select restrictions and view their impact over time.
- Compare restrictions against a custom dataset.
- Generate correlation graphs and analyze data relationships.
- Use an AI model to generate insights on correlations.

Dependencies:
- `dash`: Used for layout components, callbacks, and UI interactions.
- `plotly.graph_objects`: Generates interactive graphs.
- `Diagrams`: Handles time series visualization and correlation analysis.
- `Model`: Computes statistical correlations between datasets.
- `process_multiselect`, `show_tables`, `get_databases`, `select_graphable_tables`:
    Utility functions for data processing.
- `get_resp`: Calls an AI model to generate insights.
- `PATHS`: Stores database file paths.
"""
from dash import dcc, html, Input, Output, no_update, register_page, callback, State
from src.frontend.diagrams import Diagrams
from src.utils import process_multiselect, show_tables
from src.utils import get_databases, select_graphable_tables, get_resp
from src.prediction.pred import Model
from src.config import PATHS

dgms = Diagrams(
    PATHS["covid.db"],
    PATHS["graph.db"],
    PATHS["custom.db"]
)

register_page(__name__, path='/time-series')


layout = [
    html.Div(
        id='time-series-page',
        className="section",
        children=[
            html.H1("TIME SERIES", className='centered-item'),
            html.Div(
                id='select-data',
                children=[
                    html.H3("Plot against a custom dataset", className='centered-item'),
                    dcc.Checklist(
                        id='plot-against',
                        className='centered-item',
                        options=[
                            {'label': 'Show Plot', 'value': True},
                        ],
                        value=[],
                    ),
                    html.Br(),
                    dcc.Dropdown(
                        id='select-db',
                        options = get_databases(),
                        style = dict(display='none')
                    ),
                    html.Br(),
                    dcc.Dropdown(
                        id='select-table',
                        style = dict(display='none')
                    )
                ]
            ),
            dcc.Graph(
                id='time-series-chart',
                figure=dgms.time_series()
            ),
            html.H3("Select Restrictions", className='centered-item'),
            html.Div(
                id ='restr_multiselect',
                children = [
                    dcc.Dropdown(
                    [
                        "Curfew",
                        'Eat Out to Help Out',
                        "Eating Places Closed",
                        "Household Mixing Indoors Banned",
                        "Pubs Closed",
                        "Rule of 6 Indoors",
                        "Shools Closed",
                        "Shops Closed",
                        "Stay at Home",
                        "WFH"
                        ],
                    multi=True,
                    placeholder = "All",
                    id = 'restr-select',
                    className='user-input',
                    ),
                ]
            ),
            html.Br(),
            html.Div(
                id='correlation',
                children = [
                    html.Div(
                        id='corr-graph',
                        children = [
                            html.H3("Correlation Graph", className='centered-item'),
                            dcc.Graph(
                                id='corr-chart',
                                figure=dgms.correlation(),
                            )
                        ],
                        style=dict(display='none')
                    ),
                ]
            ),
            html.Br(),
            html.Div(
                id='generate-resp',
                children=[
                    html.H3(
                        "Data Correlation Insights",
                        id='corr-title',
                        className='centered-item',
                        style=dict(display='none')
                    ),
                    html.Div(
                        style={
                            "display":"flex",
                            'justify-content':'center',
                            "alignItems": "center"
                            },
                        children = [
                            dcc.Textarea(
                                id='user-prompt',
                                className='prompt',
                                value="Explain the correlation.",
                            ),
                        ],
                    ),
                    html.Br(),
                    html.Div(
                        className='centered-item',
                        children=[
                            html.Button(
                                "SUBMIT",
                                id='submit-prompt',
                                n_clicks=0,
                                className='button',
                                style=dict(display='none')
                            ),
                        ]
                    ),
                    dcc.Loading(
                        id="loading",
                        type="circle",
                        children = [
                            dcc.Markdown(id='llm-response', style=dict(display='none'))
                        ]
                    ),
                ]
            )
        ]
    )
]

@callback(
    Output('time-series-chart', 'figure'),
    Input('plot-against', 'value'),
    Input('restr-select', 'value'),
    Input('select-db', 'value'),
    Input('select-table', 'value')
)
def update_time_series(plot_against, restrs, db_name, table):
    """
    Updates the time series graph based on selected restrictions and optional custom datasets.

    Steps:
    - If a custom dataset is selected, plots it against the restrictions.
    - If no dataset is selected, only plots the restrictions.
    - Calls the `Diagrams` module to generate the appropriate figure.

    Args:
        plot_against (list[bool]): Whether to plot against a custom dataset.
        restrs (list[str]): Selected restrictions.
        db_name (str): Name of the selected database.
        table (str): Name of the selected table.

    Returns:
        go.Figure: The updated time series graph.
    """
    if plot_against and db_name and table:
        if not restrs:
            return dgms.time_series(db_name=db_name, table=table)
        else:
            if db_name and table:
                return dgms.time_series(
                    restrs=process_multiselect(restrs),
                    db_name=db_name,
                    table=table
                    )
    else:
        if restrs:
            return dgms.time_series(
                restrs=process_multiselect(restrs),
                custom=False
                )
        else:
            return dgms.time_series(custom=False)

@callback(
    Output('corr-chart', 'figure'),
    Input('restr-select', 'value'),
    Input('select-db', 'value'),
    Input('select-table', 'value')
)
def update_correlation(restrs, db_name, table_name):
    """
    Updates the correlation graph based on the selected restrictions and custom dataset.

    Steps:
    - If a database and table are selected, generates a correlation graph.
    - If restrictions are chosen, filters the correlation graph accordingly.
    - Calls the `Diagrams` module for visualization.

    Args:
        restrs (list[str]): Selected restrictions.
        db_name (str): Name of the selected database.
        table_name (str): Name of the selected table.

    Returns:
        go.Figure | no_update: The updated correlation graph or no update if no input is provided.
    """
    if db_name and table_name:
        if not restrs:
            return dgms.correlation(
                db_name=db_name,
                table_name=table_name
                )
        else:
            return dgms.correlation(
                restrs=process_multiselect(restrs),
                db_name=db_name,
                table_name=table_name
                )
    else:
        return no_update

@callback(
    Output('select-db', 'style'),
    Input('plot-against', 'value')
)
def show_menu(value):
    """
    Displays the database selection dropdown when plotting against a custom dataset.

    Args:
        value (list[bool]): Whether the user has enabled the plot option.

    Returns:
        dict: Style properties for showing or hiding the dropdown.
    """
    if value:
        return dict()
    else:
        return dict(display='none')

@callback(
    Output('corr-graph', 'style'),
    Output('user-prompt', 'style'),
    Output('submit-prompt', 'style'),
    Output('llm-response', 'style'),
    Output('corr-title', 'style'),
    Input('select-table', 'value')
)
def show_corr_graph(value):
    """
    Shows or hides the correlation graph and input fields when a custom dataset is selected.

    Args:
        value (str): Selected table name.

    Returns:
        tuple[dict, dict, dict, dict, dict]: Style properties for different UI elements.
    """
    if value:
        return dict(), dict(), dict(), dict(), dict()
    else:
        return (
            dict(display='none'),
            dict(display='none'),
            dict(display='none'),
            dict(display='none'),
            dict(display='none')
            )

@callback(
    Output('select-table', 'style'),
    Output('select-table', 'options'),
    Input('select-db', 'value')
)
def show_table_select(value):
    """
    Displays the table selection dropdown when a database is selected.

    Args:
        value (str): Selected database name.

    Returns:
        tuple[dict, list[str]]: Style properties and table options.
    """
    if value:
        return dict(), select_graphable_tables(show_tables(value))
    return no_update, no_update

@callback(
    Output('llm-response', 'children'),
    State('user-prompt', 'value'),
    Input('submit-prompt', 'n_clicks'),
    Input('restr-select', 'value'),
    State('select-db', 'value'),
    State('select-table', 'value'),
    prevent_initial_call=True
)
def show_llm_resp(prompt, click, restrs, db_name, table_name):
    """
    Generates an AI response analyzing the correlation between restrictions and a custom dataset.

    Steps:
    - Checks if the submit button was clicked.
    - Retrieves correlation information from the `Model` class.
    - Calls an AI model via `get_resp()` to generate an explanation.

    Args:
        prompt (str): User input for AI analysis.
        click (int): Number of times the submit button was clicked.
        restrs (list[str]): Selected restrictions.
        db_name (str): Name of the selected database.
        table_name (str): Name of the selected table.

    Returns:
        str | no_update: AI-generated response or no update if conditions are not met.
    """
    if click > 0:
        restrs = restrs or []
        model= Model(restrs, db_name, table_name)
        meta=f"""The correlation coefficient between the
            number of lockdown restriction and {table_name}
            is {model.get_correlation()}.
            """
        resp = get_resp(meta + prompt)
        return resp
    return no_update
