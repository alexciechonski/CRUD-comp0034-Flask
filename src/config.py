"""
Module for initializing global variables from config.json
Variables:
- PATHS: dictionary for path to respective databases
- IMMUTABLE: list of immutable tables
- SCHEMA: list of required columns for user created tables
- NON-GRAPHABLE: list of non-graphable tables used for time series
- BASE_PATH: base path for databases
"""
import json
with open('src/config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

PATHS = config['paths']
IMMUTABLE = config['immutable']
SCHEMA = config['schema']
NON_GRAPHABLE = config['non_graphable']
BASE_PATH = config['base_path']
