from dash import html, register_page

# Register this page for the root URL
register_page(__name__, path='/', name='Home')

layout = html.Div([
    html.H1("Welcome to the Dashboard Home Page"),
    html.P("Use the links above to navigate to different sections.")
])