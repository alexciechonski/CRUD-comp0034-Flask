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
from src.utils import get_databases, get_table_info, show_tables, get_db_path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.backend.erd_manager import Visualizer

matplotlib.use('Agg')

class ERD:
    def __init__(self, selected_db: str):
        self.selected_db = selected_db
        self.tables = show_tables(selected_db)
        self.table_info = self._get_table_info()
        self.adj_list = self._get_adjacency_list()
        self.graph = self._build_graph()
        self.edge_count = self.graph.number_of_edges()
        self.img = self._generate_image()

    def _get_table_info(self):
        info = {}
        for table in self.tables:
            try:
                schema_info = get_table_info(table, get_db_path(self.selected_db))
                formatted = [{
                    'Column Name': col[1],
                    'Type': col[2],
                    'Constraints': ' '.join(filter(None, [
                        'NOT NULL' if col[3] else '',
                        'PRIMARY KEY' if col[5] else ''
                    ]))
                } for col in schema_info] if schema_info else []
                info[table] = formatted
            except Exception as e:
                print(f"Schema error for {table}: {e}")
                info[table] = []
        return info

    def _get_adjacency_list(self):
        engine = create_engine(f"sqlite:///{get_db_path(self.selected_db)}")
        session = sessionmaker(bind=engine)()
        try:
            visualizer = Visualizer(session)
            return visualizer.get_adj_list()
        finally:
            session.close()
            engine.dispose()

    def _build_graph(self):
        G = nx.DiGraph()
        for table in self.tables:
            G.add_node(table)

        if not any(self.adj_list.values()):
            return G

        actual_tables = {table.lower(): table for table in self.tables}
        case_mapping = {
            tbl.lower(): actual_tables[tbl.lower()]
            for tbl in set(
                k.lower() for k in self.adj_list.keys()
            ).union(
                t.lower() for rels in self.adj_list.values() for t, _ in rels
            )
            if tbl.lower() in actual_tables
        }

        for src, rels in self.adj_list.items():
            src_canon = case_mapping.get(src.lower())
            for tgt, rel_type in rels:
                tgt_canon = case_mapping.get(tgt.lower())
                if src_canon and tgt_canon:
                    G.add_edge(src_canon, tgt_canon, relationship=rel_type)
        return G

    def _generate_image(self):
        img = io.BytesIO()
        plt.figure(figsize=(12, 10))
        layout = nx.spring_layout(self.graph, k=2, iterations=50) if self.edge_count > 0 else nx.circular_layout(self.graph)

        nx.draw_networkx_nodes(self.graph, layout, node_color='lightblue', node_size=3000, alpha=0.7)
        nx.draw_networkx_labels(self.graph, layout, font_size=10, font_weight='bold')

        if self.edge_count > 0:
            nx.draw_networkx_edges(self.graph, layout, edge_color='gray', arrows=True, arrowsize=20, width=1.5)
            edge_labels = nx.get_edge_attributes(self.graph, 'relationship')
            nx.draw_networkx_edge_labels(self.graph, layout, edge_labels=edge_labels, font_size=8, font_color='red')

        plt.margins(0.2)
        plt.savefig(img, format='png', bbox_inches='tight', dpi=200)
        plt.close()
        img.seek(0)
        return img

    def render_erd_html(self):
        if not self.tables:
            return '''
                <div class="erd-container">
                    <div class="alert alert-info">
                        <h4 class="alert-heading">Empty Database</h4>
                        <p>This database has no tables yet. Create a table to get started!</p>
                    </div>
                </div>
            '''
        desc = "Showing tables" + (" and their relationships (1:1, 1:N, N:M)" if self.edge_count > 0 else " (no relationships)")
        img_base64 = base64.b64encode(self.img.getvalue()).decode()
        return f'''
            <div class="erd-container">
                <h4 class="text-center mb-3">Entity Relationship Diagram</h4>
                <p class="text-muted text-center mb-3">{desc}</p>
                <img src="data:image/png;base64,{img_base64}" 
                     class="img-fluid" 
                     style="max-width: 100%; height: auto; border: 1px solid #ddd; border-radius: 4px; padding: 5px;">
            </div>
        '''
