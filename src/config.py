"""
Module for initializing global variables from config.json
Variables:
- IMMUTABLE: list of immutable tables
- SCHEMA: list of required columns for user created tables
- NON-GRAPHABLE: list of non-graphable tables used for time series
- BASE_PATH: base path for databases
"""
import json
from pathlib import Path

def load_config():
    """Reload configuration from config.json"""
    global IMMUTABLE, SCHEMA, NON_GRAPHABLE, BASE_PATH, LOG_PATH, NON_DELETEABLE
    config_path = Path(__file__).parent / 'config.json'
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    IMMUTABLE = config['immutable']
    SCHEMA = config['schema']
    NON_GRAPHABLE = config['non_graphable']
    BASE_PATH = config['base_path']
    LOG_PATH = config['log_path']
    NON_DELETEABLE = config['non_deleteable']

# Initial load of configuration
load_config()
