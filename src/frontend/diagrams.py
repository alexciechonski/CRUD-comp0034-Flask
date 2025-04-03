# """
# Module for visualizing graphs and serving ERD-related diagrams.

# This module provides two classes:
# 1. `GraphVisualizer`: Handles graph layout generation, edge creation, and
#    node tracing for visualization.
# 2. `Diagrams`: Manages the visualization of ERD diagrams, tables, time series,
#    correlation plots, restriction distributions, and event timelines.
# """
# from typing import Any, Tuple, Dict, List
# import io
# import base64
# import pandas as pd
# import plotly.graph_objs as go
# import plotly.express as px
# import networkx as nx # nx uses graphviz: https://graphviz.org/
# import matplotlib.pyplot as plt
# import matplotlib
# from src.backend.data_server import DataServer
# from src.prediction.pred import Model
# from src.utils import table_not_empty

# matplotlib.use('Agg')
