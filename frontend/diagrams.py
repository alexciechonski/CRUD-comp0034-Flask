import pandas as pd
from backend.data_server import DataServer
import plotly.graph_objs as go
import plotly.express as px
import networkx as nx
import matplotlib.pyplot as plt
import scipy
from networkx.drawing.nx_pydot import graphviz_layout
from backend.utils import calculate_perpendicular
import plotly.tools as tls
# import pygraphviz as pgv
from networkx.drawing.nx_agraph import to_agraph
import matplotlib.image as mpimg
import io


class Diagrams:
    def __init__(self, db_path, graph_path) -> None:
        self.server = DataServer(db_path, graph_path)

    def erd(self):
        adj = self.server.serve_erd()
        adj_list = {node: [lst[0] for lst in nei] for node, nei in adj.items()}
        G = nx.DiGraph(adj_list)
        pos = nx.nx_pydot.graphviz_layout(G, prog='neato')  # You can use 'neato', 'dot', 'twopi', 'circo', etc

        edge_x = []
        edge_y = []
        arrow_x = []
        arrow_y = []
        for edge in G.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
            arrow_x.append(x1 * 0.9 + x0 * 0.1)  # Move arrow slightly back from the end
            arrow_y.append(y1 * 0.9 + y0 * 0.1)

        node_x = []
        node_y = []
        for node in G.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)

        # Step 5: Create edge trace
        edge_trace = go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=1, color='#888'),
            hoverinfo='none',
            mode='lines'
        )

        arrow_trace = go.Scatter(
        x=arrow_x, y=arrow_y,
        mode='markers',
        marker=dict(
            size=10,
            color='black',
            symbol='triangle-up'  # Arrowhead marker
        ),
        hoverinfo='none'
    )

        # Step 6: Create node trace
        node_trace = go.Scatter(
            x=node_x, y=node_y,
            mode='markers+text',
            marker=dict(
                size=10,
                color='lightblue',
                line=dict(width=2)
            ),
            text=[str(node) for node in G.nodes()],
            textposition='top center',
            hoverinfo='text'
        )

        # Step 7: Create the Plotly figure
        fig = go.Figure(data=[edge_trace, arrow_trace, node_trace],
                        layout=go.Layout(
                            title='Directed Graph Visualization',
                            showlegend=False,
                            hovermode='closest',
                            margin=dict(b=0, l=0, r=0, t=40),
                            xaxis=dict(showgrid=False, zeroline=False),
                            yaxis=dict(showgrid=False, zeroline=False)
                        ))

        return fig



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

        return fig
        # fig.show()


if __name__ == "__main__":
    dgms = Diagrams(
    "backend/covid.db",
    "backend/graph.db"
    )

    dgms.erd()
