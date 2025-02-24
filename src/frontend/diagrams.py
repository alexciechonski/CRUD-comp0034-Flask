import io
import base64
import pandas as pd
import plotly.graph_objs as go
import plotly.express as px
import networkx as nx # nx uses graphviz: https://graphviz.org/
import matplotlib.pyplot as plt
import matplotlib
from backend.data_server import DataServer
from src.prediction.pred import Model
from src.utils import table_not_empty
matplotlib.use('Agg')

class GraphVisualizer:
    @staticmethod
    def generate_pos(graph):
        graph.graph['overlap'] = 'false'
        graph.graph['mode'] = 'KK'
        return nx.nx_pydot.graphviz_layout(graph, prog='neato')

    @staticmethod
    def add_edges(graph, adj, connection_types):
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
    def create_edge_traces(graph, pos, legend):
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
    def create_node_trace(pos, graph, labels):
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
    def __init__(self, db_path, graph_path, custom_path) -> None:
        self.server = DataServer(db_path, graph_path, custom_path)

    @staticmethod
    def create_legend_base64(legend):
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

    def erd(self, graph_id):
        adj = self.server.serve_erd(graph_id)
        legend = {"one-n": "salmon", "zero-one": "black", "zero-n": "darkblue", "one-only": "lime"}
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

    def get_table(self, db_name, table_name):
        data = self.server.serve_table(db_name, table_name)
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

    def time_series(self, restrs = [], db_name = "custom.db", table = 'MHCareCluster', custom=True):
        sql = self.server.serve_time_series(restrs)
        x_line, y_line = zip(*sql)

        if custom:
            if not table_not_empty(db_name, table):
                x_scatter, y_scatter = [], []
            else:
                custom_data = self.server.serve_second_series(db_name, table)
                x_scatter, y_scatter = zip(*custom_data)
        else:
            x_scatter, y_scatter = [], []

        return {
            "data": [
                {
                    "x": x_line,
                    "y": y_line,
                    "type": "line",
                    "name": "Restrictions",
                    "yaxis": "y"
                },
                {
                    "x": x_scatter,
                    "y": y_scatter,
                    "type": "scatter",
                    "mode": "lines+markers",
                    "name": "custom Series",
                    "yaxis": "y2"
                }
            ],
            "layout": {
                "title": "Time Series Plot",
                "yaxis": {
                    "title": "Restriction Value",
                    "side": "left"
                },
                "yaxis2": {
                    "title": "custom Series Value",
                    "overlaying": "y",
                    "side": "right",
                    "showgrid": False
                },
                "xaxis": {
                    "title": "Time"
                },
                "legend": {
                    "x": 1.05,
                    "y": 1,
                    "xanchor": "left",
                    "yanchor": "top"
                }
            }
        }

    def correlation(self, restrs = [], db_name = "custom.db", table_name= "MHCareCluster"):
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

    def restr_distr(self, final_date=None):
        restr, val = zip(*self.server.serve_restr_distr(final_date))
        return px.bar(x=restr, y=val, labels={'x': 'Restriction', 'y': 'Total Restrictions'})

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
            xaxis=dict(title="Date"),
            yaxis=dict(visible=False),
            showlegend=False,
            height=600,
            margin=dict(l=40, r=40, t=40, b=40)
        )

        return fig
        # fig.show()


if __name__ == "__main__":
    dgms = Diagrams(
    "src/backend/data/covid.db",
    "src/backend/data/graph.db",
    "src/backend/data/custom.db"
    )
    dgms.erd(2)
