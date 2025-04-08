import io
import base64
import pandas as pd
import plotly.express as px
import plotly.io as pio
import networkx as nx # nx uses graphviz: https://graphviz.org/
import matplotlib.pyplot as plt
import matplotlib
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy import text, inspect
from src.backend.data_server import DataServer
from src.prediction.pred import Model
from src.utils import (
    get_databases,
    get_table_info,
    show_tables,
    get_db_path,
    get_graphable_tables,
    get_resp
    )
from src.backend.erd_manager import Visualizer
from src.backend.revert_manager import RevertManager
from src.backend.log.log_manager import LogManager
from src.utils import get_primary_keys

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


class TimeSeries:
    def __init__(self, selected_db: str):
        self.selected_db = selected_db
        self.databases = get_databases()
        self.tables = get_graphable_tables()
        self.data_server = DataServer('covid.db')
        self.restrictions = self.data_server.get_restrictions()

    def validate_form_data(self, form):
        """Validate form data from WTForms"""
        table = form.table.data
        selected_restrictions = form.restrictions.data
        prompt = form.prompt.data

        if not table or not selected_restrictions or not prompt:
            raise ValueError("Please fill in all required fields")

        table_info = next((t for t in self.tables if t['name'] == table), None)
        if not table_info:
            raise ValueError(f"Could not find database information for table {table}")

        return table_info['database'], table, selected_restrictions, prompt

    def analyze(self, db_name, table_name, selected_restrictions, prompt):
        model = Model(selected_restrictions, db_name, table_name)
        correlation = model.get_correlation()
        system_prompt = f"The correlation between number of restrictions and {table_name} is {correlation:.3f}. "
        analysis_result = get_resp(system_prompt + prompt)

        ts_data = self.data_server.serve_time_series(selected_restrictions)
        custom_server = DataServer(db_name)
        try:
            custom_data = custom_server.serve_second_series(db_name, table_name)
        finally:
            custom_server._db_session.close()

        time_series_plot = self._build_time_series_plot(ts_data, custom_data, table_name)
        regression_plot = self._build_regression_plot(model, table_name)

        return {
            'analysis_result': analysis_result,
            'time_series_plot': time_series_plot,
            'regression_plot': regression_plot
        }

    def _build_time_series_plot(self, restrictions_data, custom_data, table_name):
        restrictions_df = pd.DataFrame(restrictions_data, columns=['date', 'total_restrictions'])
        restrictions_df['date'] = pd.to_datetime(restrictions_df['date'])

        custom_df = pd.DataFrame(custom_data, columns=['date', 'measured_value'])
        custom_df['date'] = pd.to_datetime(custom_df['date'])

        merged_df = pd.merge_asof(restrictions_df, custom_df, on='date', direction='nearest')

        fig = px.line(merged_df, x='date', y='total_restrictions', title='Time Series Analysis')
        fig.add_scatter(x=merged_df['date'], y=merged_df['measured_value'],
                        name=table_name, yaxis='y2')

        fig.update_layout(
            yaxis=dict(
                title=dict(
                    text='Number of Restrictions',
                    font=dict(color='blue')
                ),
                tickfont=dict(color='blue')
            ),
            yaxis2=dict(
                title=dict(
                    text=f'{table_name} Value',
                    font=dict(color='red')
                ),
                tickfont=dict(color='red'),
                overlaying='y',
                side='right'
            ),
            xaxis=dict(
                title=dict(
                    text='Date'
                )
            ),
            showlegend=True
        )


        fig.data[0].name = 'Restrictions'
        fig.data[0].line.color = 'blue'
        fig.data[1].line.color = 'red'

        return pio.to_html(fig, full_html=False)

    def _build_regression_plot(self, model, table_name):
        df = model.prepare()
        if df.empty:
            return None
        fig = px.scatter(df, x='restr_value', y='custom_value',
                         title='Correlation Analysis',
                         labels={'restr_value': 'Number of Restrictions',
                                 'custom_value': f'{table_name} Value'})
        return pio.to_html(fig, full_html=False)


class RevertChange:
    def __init__(self, database, table, change_type):
        self.database = database
        self.table = table
        self.change_type = change_type
        self.revert_manager = RevertManager(database)
        self.log_manager = LogManager()
        self.engine = self.revert_manager.engine
        self.session = self.revert_manager.Session()

    def find_change(self):
        changes = self.log_manager.to_tables()
        match = changes[
            (changes['database'] == self.database) &
            (changes['table'] == self.table) &
            (changes['change_type'] == self.change_type)
        ]
        if match.empty:
            return None
        return match.iloc[0].to_dict()

    def revert(self, change_data):
        self.revert_manager.store_state()

        if self.change_type == 'create':
            self._revert_create(change_data)
        elif self.change_type == 'delete':
            self._revert_delete(change_data)
        elif self.change_type == 'update':
            self._revert_update(change_data)

        self.session.commit()
        self.log_manager.remove_change(self.database, self.table, self.change_type)

    def _revert_create(self, change_data):
        primary_keys = get_primary_keys(self.table, self.database) or ['id']
        where_clause = [f"{key} = {change_data[key]}" for key in primary_keys if key in change_data]

        if not where_clause:
            print("No primary keys found in change data")
            return

        delete_query = f"DELETE FROM {self.table} WHERE {' AND '.join(where_clause)}"
        self.session.execute(text(delete_query))

    def _revert_delete(self, change_data):
        prev_data = {
            k[5:]: v for k, v in change_data.items() if k.startswith('prev_')
        } or {
            k: v for k, v in change_data.items()
            if k not in ['change_type', 'database', 'table']
        }

        inspector = inspect(self.engine)
        table_columns = [col['name'] for col in inspector.get_columns(self.table)]
        valid_data = {k: v for k, v in prev_data.items() if k in table_columns}

        if not valid_data:
            print("No valid columns found in previous data")
            return

        insert_query = f"INSERT INTO {self.table} ({', '.join(valid_data)}) VALUES ({', '.join([':' + k for k in valid_data])})"
        self.session.execute(text(insert_query), valid_data)

    def _revert_update(self, change_data):
        prev_data = {k.replace('prev_', ''): v for k, v in change_data.items() if k.startswith('prev_')}
        inspector = inspect(self.engine)
        table_columns = [col['name'] for col in inspector.get_columns(self.table)]
        valid_data = {k: v for k, v in prev_data.items() if k in table_columns}

        primary_keys = get_primary_keys(self.table, self.database) or ['id']
        where_clause = [f"{key} = {change_data[key]}" for key in primary_keys if key in change_data]

        if not where_clause or not valid_data:
            if not where_clause:
                print("No primary keys found in change data")
            if not valid_data:
                print("No valid columns found in previous data")
            return

        set_clause = ', '.join([f"{k} = :{k}" for k in valid_data])
        update_query = f"UPDATE {self.table} SET {set_clause} WHERE {' AND '.join(where_clause)}"
        self.session.execute(text(update_query), valid_data)
        self.log_manager.update_length()

    def cleanup(self):
        self.session.close()
        self.engine.dispose()
