import json
from src.config import LOG_PATH
from collections import deque

class LogManager:
    def __init__(self) -> None:
        with open(LOG_PATH, 'r') as f:
            log_data = json.load(f)
        self.log = deque(log_data)
        self.length = len(self.log)

    def update_length(self):
        if self.length > 10:
            self.log.popleft()
    
