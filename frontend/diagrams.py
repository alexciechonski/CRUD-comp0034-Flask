import pandas as pd
from backend.data_server import DataServer
import plotly.graph_objs as go
import plotly.express as px
import networkx as nx
import matplotlib.pyplot as plt

class Diagrams:
    def __init__(self, db_path, graph_path) -> None:
        self.server = DataServer(db_path, graph_path)

    def erd(self):
        adj = self.server.serve_erd()
        G = nx.Graph()
        visited_edges = set()  # To keep track of visited edges

        for node, neighbors in adj.items():
            for neighbor, _ in neighbors:
                # Ensure each edge is only added once (account for both directions)
                if (node, neighbor) not in visited_edges and (neighbor, node) not in visited_edges:
                    G.add_edge(node, neighbor)
                    visited_edges.add((node, neighbor))

        # Step 2: Use NetworkX to generate node positions
        positions = nx.spring_layout(G)

        # Step 3: Extract node and edge coordinates for Plotly visualization
        node_x = [positions[node][0] for node in G.nodes()]
        node_y = [positions[node][1] for node in G.nodes()]

        edge_x = []
        edge_y = []
        for edge in G.edges():
            x0, y0 = positions[edge[0]]
            x1, y1 = positions[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])

        # Step 4: Create traces for the graph visualization
        edge_trace = go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=1, color='#888'),
            hoverinfo='none',
            mode='lines'
        )

        node_trace = go.Scatter(
            x=node_x, y=node_y,
            mode='markers+text',
            text=[node for node in G.nodes()],
            hoverinfo='text',
            marker=dict(
                color='lightblue',
                size=20,
                line_width=2
            )
        )

        # Step 5: Create the Plotly figure
        fig = go.Figure(
            data=[edge_trace, node_trace],
            layout=go.Layout(
                title='Graph Visualization from Bidirectional Adjacency List',
                showlegend=False,
                margin=dict(b=0, l=0, r=0, t=0),
                xaxis=dict(showgrid=False, zeroline=False),
                yaxis=dict(showgrid=False, zeroline=False)
            )
        )

        fig.show()

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
