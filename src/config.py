import json
with open('src/config.json', 'r') as f:
    config = json.load(f)

PATHS = config['paths']
IMMUTABLE = config['immutable']
SCHEMA = config['schema']
NON_GRAPHABLE = config['non_graphable']
BASE_PATH = config['base_path']