import json 
from src.testing.conftest import EXP_OUTPUTS
import tempfile
import os
from contextlib import contextmanager
from src.backend.erd_manager import get_db_path  # Only for type hints, not used directly


def get_exp_data():
    with open(EXP_OUTPUTS, "r") as f:
        data = json.load(f)
    return data

def create_tmp_db(monkeypatch, setattr = False):
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name
    if setattr:
        monkeypatch.setattr("src.backend.erd_manager.get_db_path", lambda name: db_path)
    return db_path
