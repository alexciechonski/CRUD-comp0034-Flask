import json
from src.config import LOG_PATH

class LogManager:
    def __init__(self) -> None:
        with open(LOG_PATH, 'r') as f:
            self.log = json.load(f)
        self.length = len(self.log)