import pandas as pd
from dash import Dash, html, dcc


app = Dash(__name__)

with open("index2.html", "r", encoding="utf-8") as file:
    app.index_string = file.read()

app.layout = [
    html.Div(children='My First App with Data and a Graph')
]

if __name__ == '__main__':
    app.run(debug=True)