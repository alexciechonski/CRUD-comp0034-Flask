from dash import Dash
import frontend.index 

app = Dash(__name__, use_pages=True, suppress_callback_exceptions=True)

app.layout = frontend.index.layout

server = app.server

if __name__ == '__main__':
    app.run(debug=True)


"""
TODO:
- name_to_id dictionary non sustainable for delete db and not scalable
- need proper foreign and primary keys for delete db (graphs and graphid) can be done using shell

Adding:
- new table stopped showing
- last node id does not go down for removing graphs and tables

- matplotlib bug
- graphviz warning
"""