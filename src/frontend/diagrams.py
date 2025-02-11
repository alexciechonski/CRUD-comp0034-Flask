import pandas as pd
from backend.data_server import DataServer
import plotly.graph_objs as go
import plotly.express as px
import networkx as nx
import matplotlib.pyplot as plt
import io
import base64
from src.prediction.pred import Model

class GraphVisualizer:
    @staticmethod
    def generate_pos(graph):
        return nx.nx_pydot.graphviz_layout(graph, prog='neato')

    @staticmethod
    def add_edges(G, adj, connection_types):
        for node, neighbors in adj.items():
            if node is None:
                continue
            if not neighbors:  # Add node even if it has no neighbors
                G.add_node(node)
            for neighbor, connection_type in neighbors:
                if neighbor is None or connection_type is None:
                    continue
                if connection_type in connection_types:
                    G.add_edge(node, neighbor, connection_type=connection_type)

    @staticmethod
    def create_edge_traces(G, pos, legend):
        edge_traces, arrow_traces = [], []
        for connection_type, color in legend.items():
            edge_x, edge_y, arrow_x, arrow_y = [], [], [], []
            for edge in G.edges(data=True):
                if edge[2]['connection_type'] == connection_type:
                    x0, y0 = pos[edge[0]]
                    x1, y1 = pos[edge[1]]
                    edge_x.extend([x0, x1, None])
                    edge_y.extend([y0, y1, None])
                    arrow_x.append(x1 * 0.9 + x0 * 0.1)
                    arrow_y.append(y1 * 0.9 + y0 * 0.1)
            edge_trace = go.Scatter(x=edge_x, y=edge_y, mode='lines', line=dict(width=2, color=color), hoverinfo='none')
            arrow_trace = go.Scatter(x=arrow_x, y=arrow_y, mode='markers', marker=dict(size=10, color=color, symbol='triangle-up'), hoverinfo='none')
            edge_traces.append(edge_trace)
            arrow_traces.append(arrow_trace)
        return edge_traces, arrow_traces

    @staticmethod
    def create_node_trace(pos, G, labels):
        node_trace = go.Scatter(
            x=[], y=[],
            text=[],
            mode='markers+text',
            textposition='top center',
            marker=dict(size=10, color='lightblue'),
            customdata=[]
        )

        for node in G.nodes:
            x, y = pos[node]
            node_trace.x += (x,)
            node_trace.y += (y,)
            node_trace.text += (labels[node],)
            node_trace.customdata += (labels[node], )

        for node in labels:
            if node not in G.nodes:
                node_trace.x += (0,)  
                node_trace.y += (0,)
                node_trace.text += (labels[node],)

        return node_trace

class Diagrams:
    def __init__(self, db_path, graph_path, mental_path) -> None:
        self.server = DataServer(db_path, graph_path, mental_path)

    @staticmethod
    def create_legend_base64(legend):
        fig, ax = plt.subplots(figsize=(2, 1))
        ax.axis('off')
        legend_handles = [plt.Line2D([0], [0], color=color, lw=4, label=key) for key, color in legend.items()]
        ax.legend(handles=legend_handles, loc='center', frameon=True, framealpha=0.9, edgecolor='black')
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

        G = nx.DiGraph()
        GraphVisualizer.add_edges(G, adj, legend.keys())

        pos = nx.spring_layout(G) if G.nodes else {node: (0, 0) for node in adj}

        edge_traces, arrow_traces = GraphVisualizer.create_edge_traces(G, pos, legend)
        node_trace = GraphVisualizer.create_node_trace(pos, G, {node: f"{node}" for node in adj})

        fig = go.Figure(
            data=edge_traces + arrow_traces + [node_trace],
            layout=go.Layout(
                title='Directed Graph Visualization',
                showlegend=False,
                images=[dict(source=legend_image_base64, x=0, y=0, xref='paper', yref='paper', xanchor='left', yanchor='bottom', sizex=0.15, sizey=0.15, opacity=1)],
                hovermode='closest',
                margin=dict(b=0, l=0, r=0, t=40),
                xaxis=dict(showgrid=False, zeroline=False),
                yaxis=dict(showgrid=False, zeroline=False)
            )
        )
        # fig.show()
        return fig

    def get_table(self, db_name, table_name):
        data = self.server.serve_table(db_name, table_name)
        df = pd.DataFrame(data, columns=['Column ID', 'Field Name', 'Data Type', 'Not Null', 'Default', 'Primary Key'])
        return go.Figure(data=[go.Table(header=dict(values=list(df.columns), fill_color='paleturquoise', align='left'), cells=dict(values=[df[col] for col in df.columns], fill_color='lavender', align='left'))])

    def time_series(self, restrs, mental=True):
        sql = self.server.serve_time_series(restrs)
        x_line, y_line = zip(*sql)

        if mental:
            mental_data = self.server.serve_mental_series()
            x_scatter, y_scatter = zip(*mental_data)
        else:
            x_scatter, y_scatter = [], []

        return {
            "data": [
                {
                    "x": x_line,
                    "y": y_line,
                    "type": "line",
                    "name": "Time Series",
                    "yaxis": "y" 
                },
                {
                    "x": x_scatter,
                    "y": y_scatter,
                    "type": "scatter",
                    "mode": "lines+markers", 
                    "name": "Mental Series",
                    "yaxis": "y2"  
                }
            ],
            "layout": {
                "title": "Time Series Plot",
                "yaxis": {
                    "title": "Time Series Value",
                    "side": "left"  
                },
                "yaxis2": {
                    "title": "Mental Series Value",
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

    def overlayed_series(self, restrs: list):
        model = Model(restrs)
        df = model.train_linear()
        return {
            "data": [
                {
                    "x": df['restr_value'],
                    "y": df['predicted_mental'],
                    "type": "line",
                    "name": "Time Series",
                    "yaxis": "y"
                }
            ],
            "layout": {
                "title": "Time Series Plot",
                "yaxis": {
                    "title": "Mental Health"
                },
                "xaxis": {
                    "title": "Restrictions"
                }
            }
        }

    def restr_distr(self, final_date=None):
        restr, val = zip(*self.server.serve_restr_distr(final_date))
        return px.bar(x=restr, y=val, labels={'x': 'Restriction', 'y': 'Total Restrictions'}, title='Restrictions and Total Count')

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
    "src/backend/data/covid.db",
    "src/backend/data/graph.db",
    "src/backend/data/mental_health.db"
    )

    # print(dgms.overlayed_series([]))
    dgms.erd(2)
