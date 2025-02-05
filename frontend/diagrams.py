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
import pygraphviz as pgv
from networkx.drawing.nx_agraph import to_agraph


class Diagrams:
    def __init__(self, db_path, graph_path) -> None:
        self.server = DataServer(db_path, graph_path)

    def erd(self):
        adj = self.server.serve_erd()
        G = nx.DiGraph()
        visited_edges = set()  

        for node, neighbors in adj.items():
            for neighbor, _ in neighbors:
                # Ensure each edge is only added once (account for both directions)
                if (node, neighbor) not in visited_edges and (neighbor, node) not in visited_edges:
                    G.add_edge(node, neighbor)
                    visited_edges.add((node, neighbor))

        A = to_agraph(G)
        A.draw('networkx_with_custom_arrows.png')

        # Step 2: Use NetworkX to generate node positions
        positions = nx.nx_pydot.graphviz_layout(G, prog='neato')

        # Step 3: Extract node and edge coordinates for Plotly visualization
        node_x = [positions[node][0] for node in G.nodes()]
        node_y = [positions[node][1] for node in G.nodes()]

        edge_x = []
        edge_y = []
        decorator_x = []
        decorator_y = []
        # arrow_x = []
        # arrow_y = []
        annotations = []
        for edge in G.edges():
            x0, y0 = positions[edge[0]]
            x1, y1 = positions[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])

            mid_x, mid_y = (x0 + x1) / 2, (y0 + y1) / 2
            t_x1, t_y1, t_x2, t_y2 = calculate_perpendicular(mid_x, mid_y, x0, y0, x1, y1)
            decorator_x.extend([t_x1, t_x2, None])
            decorator_y.extend([t_y1, t_y2, None])

            # arrow_x.append((x0 + x1) / 2)
            # arrow_y.append((y0 + y1) / 2)

            annotations.append(
                dict(
                    x=x1, y=y1,
                    ax=x0, ay=y0,
                    xref='x', yref='y', axref='x', ayref='y',
                    showarrow=True,
                    arrowhead=3,  # Arrowhead style
                    arrowsize=1.5,
                    arrowwidth=2,
                    arrowcolor='#888'
            )
        )

        # nx.draw(G, positions, with_labels=True, node_color='skyblue', node_size=2000, font_size=10, font_weight='bold', font_color='black')
        # plt.show()

        # Step 4: Create traces for the graph visualization
        edge_trace = go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=1, color='#888'),
            hoverinfo='none',
            mode='lines'
        )

        decorator_trace = go.Scatter(
            x=decorator_x, y=decorator_y,
            mode='lines',
            line=dict(width=3, color='pink', dash='dash'),
            hoverinfo='none'
        )

        # arrow_trace = go.Scatter(
        #     x=arrow_x, y=arrow_y,
        #     mode='markers',
        #     marker=dict(
        #         color='red',
        #         size=10,
        #         symbol='triangle-up'  # You can adjust to another arrow symbol if preferred
        #     ),
        #     hoverinfo='none'
        # )

        node_trace = go.Scatter(
            x=node_x, y=node_y,
            mode='markers+text',
            text=[node for node in G.nodes()],
            hoverinfo='text',
            textfont=dict(
                color="lightblue",
                size= 9,
                weight = "bold"
            ),
            marker=dict(
                color='black',
                size=110,
                line_width=2,
                symbol='square'
            )
        )

        # Step 5: Create the Plotly figure
        fig = go.Figure(
            data=[
                edge_trace, 
                #arrow_trace,
                decorator_trace,
                node_trace
                ],
            layout=go.Layout(
                title='Graph Visualization from Bidirectional Adjacency List',
                showlegend=False,
                annotations=annotations,
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

    def erd_plt(self):
        def create_graph():
            adj = self.server.serve_erd()
            G = nx.DiGraph()
            visited_edges = set()  

            for node, neighbors in adj.items():
                for neighbor, _ in neighbors:
                    if (node, neighbor) not in visited_edges and (neighbor, node) not in visited_edges:
                        G.add_edge(node, neighbor)
                        visited_edges.add((node, neighbor))
            return G

        def draw_graph(G):
            plt.figure(figsize=(12, 10))
            positions = nx.nx_pydot.graphviz_layout(G, prog='neato')
            nx.draw(G, positions, with_labels=True, node_color='skyblue', node_size=2000, font_size=10, font_weight='bold', font_color='black')
            # plt.show()
            fig = plt.gcf()
            # plt.close()
            return fig

        def convert_to_plotly(matplotlib_fig):
            plotly_fig = tls.mpl_to_plotly(matplotlib_fig)
            plotly_fig.update_layout(
                width=1000,
                height=800,
                margin=dict(l=50, r=50, t=50, b=50)
            )
            return plotly_fig

        G = create_graph()
        fig = draw_graph(G)
        fig.show()
        plotly = convert_to_plotly(fig)
        return plotly

    def graph(self):
        adj = self.server.serve_erd()
        G = nx.DiGraph()
        visited_edges = set()  

        for node, neighbors in adj.items():
            for neighbor, _ in neighbors:
                if (node, neighbor) not in visited_edges and (neighbor, node) not in visited_edges:
                    G.add_edge(node, neighbor)
                    visited_edges.add((node, neighbor))
        positions = nx.nx_pydot.graphviz_layout(G, prog='neato')
        nx.draw(G, positions, with_labels=True, node_color='skyblue', node_size=2000, font_size=10, font_weight='bold', font_color='black')
        plt.show()


if __name__ == "__main__":
    dgms = Diagrams(
    "backend/covid.db",
    "backend/graph.db"
    )

    dgms.graph()
