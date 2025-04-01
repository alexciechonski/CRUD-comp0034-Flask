"""
Module for visualizing graphs and serving ERD-related diagrams.

This module provides two classes:
1. `GraphVisualizer`: Handles graph layout generation, edge creation, and
   node tracing for visualization.
2. `Diagrams`: Manages the visualization of ERD diagrams, tables, time series,
   correlation plots, restriction distributions, and event timelines.
"""
from typing import Any, Tuple, Dict, List
import io
import base64
import pandas as pd
import plotly.graph_objs as go
import plotly.express as px
import networkx as nx # nx uses graphviz: https://graphviz.org/
import matplotlib.pyplot as plt
import matplotlib
from src.backend.data_server import DataServer
from src.prediction.pred import Model
from src.utils import table_not_empty

matplotlib.use('Agg')

class GraphVisualizer:
    """
    Provides methods for generating graph layouts, adding edges,
    and creating edge and node traces for visualization.
    """
    @staticmethod
    def generate_pos(graph: nx.Graph) -> dict[Any, tuple[float, float]]:
        """
        Generates a node position dictionary for visualization.

        Args:
            graph (nx.Graph): The graph to generate positions for.

        Returns:
            Dict[Any, Tuple[float, float]]: A dictionary mapping nodes to (x, y) positions.
        """
        graph.graph['overlap'] = 'false'
        graph.graph['mode'] = 'KK'
        return nx.nx_pydot.graphviz_layout(graph, prog='neato')

    @staticmethod
    def add_edges(graph: nx.Graph, adj:dict, connection_types:list[str]) -> None:
        """
        Adds edges to a graph based on adjacency data and allowed connection types.

        Args:
            graph (nx.Graph): The graph object to modify.
            adj (dict): Dictionary where keys are nodes, and values are lists of tuples
                        (neighbor, connection_type).
            connection_types (list): List of allowed connection types.
        """
        for node, neighbors in adj.items():
            if node is None:
                continue
            graph.add_node(node)
            for neighbor, connection_type in neighbors:
                if neighbor is None or connection_type is None:
                    continue
                if connection_type in connection_types:
                    graph.add_edge(node, neighbor, connection_type=connection_type)

    @staticmethod
    def create_edge_traces(
        graph: nx.Graph,
        pos:dict[Any, tuple[float, float]],
        legend: dict[str, str]
        ) -> Tuple[List[go.Scatter], List[Dict[str, Any]]]:
        """
        Creates edge traces and annotations for visualization.

        Args:
            graph (nx.Graph): The graph object.
            pos (dict): Node positions.
            legend (dict): Mapping of connection types to colors.

        Returns:
            Tuple[List[go.Scatter], List[Dict[str, Any]]]: Edge traces and arrow annotations.
        """
        edge_traces = []
        annotations = []

        for connection_type, color in legend.items():
            edge_x, edge_y = [], []
            for edge in graph.edges(data=True):
                if edge[2]['connection_type'] == connection_type:
                    x0_val, y0_val = pos[edge[0]]
                    x1_val, y1_val = pos[edge[1]]

                    edge_x.extend([x0_val, x1_val, None])
                    edge_y.extend([y0_val, y1_val, None])

                    annotations.append(dict(
                        x=x1_val, y=y1_val,  # Arrowhead position
                        ax=x0_val, ay=y0_val,  # Arrow tail position
                        xref="x", yref="y",
                        axref="x", ayref="y",
                        showarrow=True,
                        arrowhead=3,  # Arrow style
                        arrowsize=1.5,  # Arrow size
                        arrowwidth=2,  # Thickness
                        arrowcolor=color  # Match edge color
                    ))

            edge_trace = go.Scatter(
                x=edge_x, y=edge_y,
                mode='lines',
                line=dict(width=2, color=color),
                hoverinfo='none'
            )
            edge_traces.append(edge_trace)

        return edge_traces, annotations

    @staticmethod
    def create_node_trace(
        pos: Dict[Any, Tuple[float, float]],
        graph: nx.Graph, labels: Dict[Any, str]
        ) -> go.Scatter:
        """
        Creates a node trace for visualization.

        Args:
            pos (dict): Node positions.
            graph (nx.Graph): The graph object.
            labels (dict): Node labels.

        Returns:
            go.Scatter: A Scatter plot representing nodes.
        """
        node_trace = go.Scatter(
            x=[], y=[],
            text=[],
            mode='markers+text',
            textposition='top center',
            marker=dict(size=10, color='black'),
            textfont=dict(size=10, color='black'),
            customdata=[],
            hoverinfo='none'
        )

        for node in graph.nodes:
            x_val, y_val = pos[node]
            node_trace.x += (x_val,)
            node_trace.y += (y_val,)
            node_trace.text += (labels[node],)
            node_trace.customdata += (labels[node], )

        for node in labels:
            if node not in graph.nodes:
                node_trace.x += (0,)
                node_trace.y += (0,)
                node_trace.text += (labels[node],)

        return node_trace

class Diagrams:
    """
    Handles ERD visualization, table rendering, time series plots, and
    restriction data visualizations.
    """
    def __init__(self, db_name: str) -> None:
        """
        Initializes the Diagrams class with database name.

        Args:
            db_name (str): Name of the database to connect to.
        """
        self.db_name = db_name

    def get_data_server(self) -> DataServer:
        """Create a new DataServer instance for each method call"""
        return DataServer(self.db_name)

    @staticmethod
    def create_legend_base64(legend: Dict[str, str]) -> str:
        """
        Generates a legend image as a base64-encoded string.

        Args:
            legend (dict): Mapping of connection types to colors.

        Returns:
            str: Base64-encoded PNG legend.
        """
        fig, axis = plt.subplots(figsize=(2, 1))
        axis.axis('off')
        legend_handles = [
            plt.Line2D([0], [0], color=c, lw=4, label=k)
            for k, c in legend.items()
        ]
        axis.legend(
            handles=legend_handles,
            loc='center',
            frameon=True,
            framealpha=0.9,
            edgecolor='black'
            )
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight', transparent=True)
        plt.close(fig)
        buffer.seek(0)
        base64_image = base64.b64encode(buffer.read()).decode('utf-8')
        buffer.close()
        return f"data:image/png;base64,{base64_image}"

    def erd(self, db_name: str) -> go.Figure:
        """
        Generates an ERD diagram for a given database.

        Args:
            db_name (str): Name of the database.

        Returns:
            go.Figure: A Plotly figure representing the ERD.
        """
        data_server = self.get_data_server()
        adj = data_server.serve_erd(db_name)
        legend = {"1:1": "salmon", "1:N": "darkblue", "N:M": "lime"}
        legend_image_base64 = self.create_legend_base64(legend)

        graph = nx.DiGraph()
        GraphVisualizer.add_edges(graph, adj, legend.keys())

        if len(graph.edges) > 0:
            pos = GraphVisualizer.generate_pos(graph)
        else:
            pos = nx.spring_layout(graph)

        node_trace = GraphVisualizer.create_node_trace(
            pos, graph, {node: f"{node}" for node in adj}
            )

        edge_traces, annotations = GraphVisualizer.create_edge_traces(graph, pos, legend)

        fig = go.Figure(
            data=edge_traces + [node_trace],
            layout=go.Layout(
                showlegend=False,
                images=[dict(
                    source=legend_image_base64, x=0, y=1, xref='paper', yref='paper',
                    xanchor='left', yanchor='top', sizex=0.15, sizey=0.15, opacity=1
                )],
                hovermode='closest',
                margin=dict(b=0, l=0, r=0, t=40),
                plot_bgcolor="white",
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, visible=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, visible=False),
                annotations=annotations
            )
        )
        return fig

    def get_table(self, db_name: str, table_name: str) -> go.Figure:
        """
        Fetches and visualizes table metadata as a table figure.

        Args:
            db_name (str): Name of the database.
            table_name (str): Name of the table.

        Returns:
            go.Figure: A Plotly table figure.
        """
        data = self.get_data_server().serve_table(db_name, table_name)
        table_df = pd.DataFrame(
            data,
            columns=['Column ID', 'Field Name', 'Data Type', 'Not Null', 'Default', 'Primary Key']
            )
        return go.Figure(
            data=[go.Table(header=dict(values=list(table_df.columns),
            fill_color='black',
            font=dict(color='white', size=12),
            align='left'),
            cells=dict(values=[table_df[col] for col in table_df.columns],
            fill_color='white',
            font=dict(color='black', size=12),
            align='left'))]
            )

    def time_series(
        self,
        restrs: list[str] = [],
        db_name: str = "custom.db",
        table: str = 'MHCareCluster',
        custom: bool = True
        ) -> Dict[str, Any]:
        """
        Generates a time series plot of restrictions with optional custom data.

        Args:
            restrs (list, optional): List of restrictions to include. Defaults to [].
            db_name (str, optional): Database name. Defaults to "custom.db".
            table (str, optional): Table name for custom data. Defaults to 'MHCareCluster'.
            custom (bool, optional): Whether to include custom data. Defaults to True.

        Returns:
            dict: A dictionary defining the plot data and layout.
        """
        data_server = self.get_data_server()
        try:
            sql = data_server.serve_time_series(restrs)
            x_line, y_line = zip(*sql)

            if custom:
                if not table_not_empty(db_name, table):
                    x_scatter, y_scatter = [], []
                else:
                    custom_data = data_server.serve_second_series(db_name, table)
                    x_scatter, y_scatter = zip(*custom_data)
            else:
                x_scatter, y_scatter = [], []

            return {
                "data": [
                    {
                        "x": x_line,
                        "y": y_line,
                        "type": "line",
                        "name": "Restriction Series",
                        "yaxis": "y"
                    },
                    {
                        "x": x_scatter,
                        "y": y_scatter,
                        "type": "scatter",
                        "name": "Custom Series",
                        "yaxis": "y2"
                    }
                ],
                "layout": {
                    "title": "Time Series Plot",
                    "yaxis": {
                        "title": "Restrictions",
                        "side": "left"
                    },
                    "yaxis2": {
                        "title": "Custom",
                        "side": "right",
                        "overlaying": "y"
                    }
                }
            }
        finally:
            data_server._db_session.close()

    def correlation(
        self,
        restrs: List[str] = [],
        db_name: str = "custom.db",
        table_name: str = "MHCareCluster"
        ) -> Dict[str, Any]:
        """
        Generates a correlation plot between restrictions and predicted values.

        Args:
            restrs (list, optional): List of restrictions to include. Defaults to [].
            db_name (str, optional): Database name. Defaults to "custom.db".
            table_name (str, optional): Table name for analysis. Defaults to "MHCareCluster".

        Returns:
            dict: A dictionary defining the plot data and layout.
        """
        if not table_not_empty(db_name, table_name):
            return {"data": [], "layout": {"title": "Time Series Plot"}}

        model = Model(restrs, db_name, table_name)
        model_df = model.train_linear()
        return {
            "data": [
                {
                    "x": model_df['restr_value'],
                    "y": model_df['predicted'],
                    "type": "line",
                    "name": "Restriction Series",
                    "yaxis": "y"
                }
            ],
            "layout": {
                "title": "Time Series Plot",
                "yaxis": {
                    "title": "custom"
                },
                "xaxis": {
                    "title": "Restrictions"
                }
            }
        }

    def restr_distr(self, final_date: str = None) -> go.Figure:
        """
        Generates a bar chart of restriction distributions.

        Args:
            final_date (str, optional): The last date to consider for restriction distribution.

        Returns:
            go.Figure: A Plotly bar chart.
        """
        data_server = self.get_data_server()
        try:
            restr, val = zip(*data_server.serve_restr_distr(final_date))
            return px.bar(x=restr, y=val, labels={'x': 'Restriction', 'y': 'Total Restrictions'})
        finally:
            data_server._db_session.close()

    def timeline(self) -> go.Figure:
        """
        Creates a timeline visualization of events.

        Returns:
            go.Figure: A Plotly scatter plot with events.
        """
        sql = self.get_data_server().serve_timeline()
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
                showlegend=False
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
                    showlegend=False
                )
            )

        # Customize the layout
        fig.update_layout(
            xaxis=dict(title="Date"),
            yaxis=dict(visible=False),
            showlegend=False,
            height=600,
            margin=dict(l=40, r=40, t=40, b=40)
        )

        return fig


if __name__ == "__main__":
    dgms = Diagrams(
    "src/backend/data/covid.db"
    )
    dgms.erd("covid")
