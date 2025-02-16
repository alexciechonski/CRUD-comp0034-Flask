from dash import Dash
import frontend.index 

app = Dash(__name__, use_pages=True, suppress_callback_exceptions=True)

app.layout = frontend.index.layout

server = app.server

if __name__ == '__main__':
    app.run(debug=True)


"""
TODO:
- name_to_id declaration
- dgms declaration
- server injection serve second series
- one function for handling queries
- separate module for sql utils

- matplotlib bug
- graphviz warning
"""