from dash import Dash, dcc, html, Input, Output, ALL, Patch, callback, State, no_update

app = Dash()

app.layout = [
    dcc.Dropdown(
        id='select-db',
        options=['1','2','3']
    ),
    html.Button(
        "Create Databse",
        id='create-new-db',
        n_clicks = 0
    ),
    html.Div(
        id='create-db-menu',
        children=[
            dcc.Input(
                id='new-db',
                placeholder="Create a New Database",
                style=dict(display='none') # made invisible
            ),
            html.Button(
                "SUBMIT",
                id='submit-new-db',
                n_clicks=0,
                style=dict(display='none') # made invisible
            )
        ]
    )
]

@callback(
    [
        Output('new-db', 'style'),
        Output('submit-new-db', 'style')
    ],
    Input('create-new-db', 'n_clicks'),
    prevent_initial_call=True

)
def new_db_menu(n_clicks):
    if n_clicks > 0:
        return dict(), dict()
    else:
        return dict(display='none'), dict(display='none')


@callback(
    Output('select-db', 'options'),  # Just a placeholder output for now
    Input('submit-new-db', 'n_clicks'),  # Button click triggers the callback
    State('new-db', 'value'),  # Read input value
)
def test_callback(n_clicks, value):
    if n_clicks > 0:
        print("Callback triggered!")  # Check if the function runs
        print(f"n_clicks: {n_clicks}, value: {value}")  # Check input values
    return no_update  # No changes to dropdown, just testing

    
if __name__ == '__main__':
    app.run(debug=True)

