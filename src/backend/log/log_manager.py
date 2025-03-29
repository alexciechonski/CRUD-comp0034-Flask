import json
from src.config import LOG_PATH
from collections import deque
import pandas as pd
import os

class LogManager:
    def __init__(self) -> None:
        # Create the log directory if it doesn't exist
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
        
        # Create the log file with empty list if it doesn't exist
        if not os.path.exists(LOG_PATH):
            with open(LOG_PATH, 'w') as f:
                json.dump([], f, indent=2)
        
        # Read the log file
        with open(LOG_PATH, 'r') as f:
            log_data = json.load(f)
        self.log = deque(log_data)
        self.length = len(self.log)

    def update_length(self):
        if self.length > 10:
            self.log.popleft()

    def create_change(self, database, table_name, new_data_dict):
        self.log.append({
            "change":"create",
            "database":database,
            "table":table_name,
            "new_data":new_data_dict
        })
        self.update_length()
        self.save_log()

    def update_change(self, database, table_name, new_data_dict, old_data_dict):
        self.log.append({
                "change":"update",
                "database":database,
                "table":table_name,
                "new_data":new_data_dict,
                "prev_data":old_data_dict
            })
        self.update_length()
        self.save_log()

    def delete_change(self, database, table_name, old_data_dict):
        self.log.append({
                "change":"delete",
                "database":database,
                "table":table_name,
                "prev_data":old_data_dict
            })
        self.update_length()
        self.save_log()

    def save_log(self):
        with open(LOG_PATH, 'w') as f:
            json.dump(list(self.log), f, indent=2)
        
    def to_tables(self):
        res = []
        # Convert deque to list and reverse it to show newest changes first
        for change in reversed(list(self.log)):
            if change['change'] == "create":
                df = pd.DataFrame([{
                    'change_type': change['change'],
                    'database': change['database'],
                    'table': change['table'],
                    **change['new_data']
                }])
                res.append(df)
            elif change['change'] == 'delete':
                df = pd.DataFrame([{
                    'change_type': change['change'],
                    'database': change['database'],
                    'table': change['table'],
                    **change['prev_data']
                }])
                res.append(df)
            elif change['change'] == 'update':
                # Create a dictionary with previous data prefixed with 'prev_'
                prev_data_dict = {f'prev_{k}': v for k, v in change['prev_data'].items()}
                df = pd.DataFrame([{
                    'change_type': change['change'],
                    'database': change['database'],
                    'table': change['table'],
                    **change['new_data'],
                    **prev_data_dict
                }])
                res.append(df)
        return pd.concat(res, ignore_index=True) if res else pd.DataFrame()

