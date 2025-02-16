import json
with open('src/config.json', 'r') as f:
    config = json.load(f)
    
PATHS = config['paths']
IMMUTABLE = config['immutable']
SCHEMA = config['schema']