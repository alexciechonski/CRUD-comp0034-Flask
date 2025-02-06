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
import base64


class Diagrams:
    def __init__(self, db_path, graph_path) -> None:
        self.server = DataServer(db_path, graph_path)

    @staticmethod
    def create_legend_base64(legend):
        # Step 1: Create a Matplotlib figure and draw the legend
        fig, ax = plt.subplots(figsize=(2, 1))
        ax.axis('off')  # Hide the axes

        # Step 2: Create custom legend handles
        legend_handles = [plt.Line2D([0], [0], color=color, lw=4, label=key) for key, color in legend.items()]

        # Step 3: Add the legend to the plot
        ax.legend(handles=legend_handles, loc='center', frameon=True, framealpha=0.9, edgecolor='black')

        # Step 4: Save the image to an in-memory buffer
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight', transparent=True)
        plt.close(fig)

        # Step 5: Encode the image as base64
        buffer.seek(0)
        base64_image = base64.b64encode(buffer.read()).decode('utf-8')
        buffer.close()

        return f"data:image/png;base64,{base64_image}"


    def erd(self):
        adj = self.server.serve_erd()  # Your modified adjacency list
        legend = {
            "one-n": "salmon",
            "zero-one": "black",
            "zero-n": "darkblue",
            "one-only": "lime"
        }
        legend_image_base64 = self.create_legend_base64(legend)

        # Step 2: Create a directed graph using NetworkX
        G = nx.DiGraph()

        # Step 3: Add edges to the graph with connection type as an attribute
        for node, neighbors in adj.items():
            for neighbor, connection_type in neighbors:
                G.add_edge(node, neighbor, connection_type=connection_type)

        # Step 4: Generate layout (e.g., spring layout)
        pos = nx.nx_pydot.graphviz_layout(G, prog='neato')

        # Step 5: Extract node and edge data for Plotly
        edge_traces = []  # Separate traces for edges based on color
        arrow_traces = []  # Separate traces for arrows based on color

        for connection_type, color in legend.items():
            # Prepare edge and arrow coordinates for this connection type
            edge_x, edge_y = [], []
            arrow_x, arrow_y = [], []

            for edge in G.edges(data=True):
                if edge[2]['connection_type'] == connection_type:
                    x0, y0 = pos[edge[0]]
                    x1, y1 = pos[edge[1]]

                    # Add edge line coordinates
                    edge_x.extend([x0, x1, None])
                    edge_y.extend([y0, y1, None])

                    # Calculate arrow coordinates (slightly back from the node to avoid overlap)
                    arrow_x.append(x1 * 0.9 + x0 * 0.1)
                    arrow_y.append(y1 * 0.9 + y0 * 0.1)

            # Create edge trace for this connection type
            edge_trace = go.Scatter(
                x=edge_x, y=edge_y,
                line=dict(width=2, color=color),
                hoverinfo='none',
                mode='lines'
            )
            edge_traces.append(edge_trace)

            # Create arrow trace for this connection type
            arrow_trace = go.Scatter(
                x=arrow_x, y=arrow_y,
                mode='markers',
                marker=dict(
                    size=10,
                    color=color,
                    symbol='triangle-up'
                ),
                hoverinfo='none'
            )
            arrow_traces.append(arrow_trace)

        # Step 6: Extract node positions
        node_x = []
        node_y = []
        for node in G.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)

        # Step 7: Create node trace
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
        # Step 8: Create the Plotly figure
        fig = go.Figure(data=edge_traces + arrow_traces + [node_trace],
                    layout=go.Layout(
                        title='Directed Graph Visualization',
                        showlegend=False,  # Disable Plotly legend
                        images=[
                            dict(
                                source=legend_image_base64,  # Embed the base64 image
                                x=0, y=0,  # Position the image at the top-right corner
                                xref='paper', yref='paper',
                                xanchor='left', yanchor='bottom',
                                sizex=0.15, sizey=0.15,  # Half the previous size
                                opacity=1
                            )
                        ],
                        hovermode='closest',
                        margin=dict(b=0, l=0, r=0, t=40),
                        xaxis=dict(showgrid=False, zeroline=False),
                        yaxis=dict(showgrid=False, zeroline=False)
                    ))
        # return fig
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