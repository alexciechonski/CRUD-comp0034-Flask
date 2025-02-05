import pandas as pd
from backend.data_server import DataServer
import plotly.graph_objs as go
import plotly.express as px

class Diagrams:
    def __init__(self, db_path, graph_path) -> None:
        self.server = DataServer(db_path, graph_path)

    def time_series(self):
        sql = self.server.serve_time_series()
        x, y = zip(*sql)
        return {
                "data": [
                    {
                        "x": x,                # Dates as the x-axis
                        "y": y,                # Values as the y-axis
                        "type": "line",        # You can change this to "bar", "scatter", etc.
                        "name": "Time Series"  # Optional trace name
                    }
                ],
                "layout": {
                    "title": "Time Series Plot"
                }
            }

    def restr_distr(self, final_date = None):
        sql = self.server.serve_restr_distr(final_date)
        restr, val = zip(*sql)

        fig = px.bar(
            x=restr,
            y=val,
            labels={'x': 'Restriction', 'y': 'Total Restrictions'},
            title='Restrictions and Total Count'
        )
        return fig

        # Show the plot
        # fig.show()

    def timeline(self):
        sql = self.server.serve_timeline()
        date, event, url = zip(*sql)

        pattern = list(range(1, 10, 2)) + list(range(5, -10, -2))
        level = [pattern[i % len(pattern)] for i in range(len(sql))]

        fig = go.Figure()

        # Add markers and text annotations
        fig.add_trace(
            go.Scatter(
                x=date,
                y=level,
                mode="markers+text",
                marker=dict(size=10, color="black"),
                text=event,
                textposition="top center",
                textfont=dict(
                    color="black",
                    size=12
                ),
                customdata=url, 
                name="Events"
            )
        )

        fig.add_trace(
            go.Scatter(
                x=date,  
                y=[0] * len(date),  
                mode="lines",
                line=dict(color="black", width=2),
                showlegend=False  # Hide from legend
            )
        )

        # Add thin vertical lines
        for date, level in zip(date, level):
            fig.add_trace(
                go.Scatter(
                    x=[date, date],
                    y=[0, level],  # Line goes from y=0 to the point's level
                    mode="lines",
                    line=dict(color="black", width=1, dash="dot"),
                    opacity=0.3,
                    showlegend=False  # Hide from legend
                )
            )

        # Customize the layout
        fig.update_layout(
            title="Event Timeline",
            xaxis=dict(title="Date"),
            yaxis=dict(visible=False),  # Hide the y-axis
            showlegend=False,
            height=600,
            margin=dict(l=40, r=40, t=40, b=40)
        )

        # # Generate a click handler using Plotly's events
        # fig.update_layout(
        #     clickmode='event+select',
        # )

        # # Use JavaScript to handle clicks (you can include this part in your front-end code)
        # fig.add_html(
        #     """
        #     <script>
        #         document.addEventListener('plotly_click', function(event) {
        #             var point = event.points[0];
        #             var url = point.customdata;

        #             if (url) {
        #                 window.open(url, '_blank');
        #             }
        #         });
        #     </script>
        #     """
        # )

        # fig.show()
        return fig


if __name__ == "__main__":
    dgms = Diagrams(
    "backend/covid.db",
    "backend/graph.db"
    )

    dgms.restr_distr()
