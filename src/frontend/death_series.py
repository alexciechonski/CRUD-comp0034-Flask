from dash import Dash, dcc, html
from src.frontend.diagrams import Diagrams

dgms = Diagrams(
    "src/backend/data/covid.db",
    "src/backend/data/graph.db",
    "src/backend/data/mental_health.db"
)

app = Dash(__name__)

app.layout = html.Div(
        id='my-div',
        children = [
            dcc.Graph(
                id='time-series-chart',
                figure=dgms.time_series(db_name="mental_health.db", table="Deaths")
            )
        ]
    )    

if __name__ == '__main__':
    app.run(debug=True)