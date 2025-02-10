from dash import Dash
import dash
import frontend.index 

app = Dash(__name__, use_pages=True, suppress_callback_exceptions=True)

app.layout = frontend.index.layout

server = app.server

if __name__ == '__main__':
    app.run(debug=True)


"""
TODO:
- make graphs look nicer and give better labels
- raise db err ???
- foreign keys db creation
- too long functions
- bug with redirection?
- rename html vars
"""