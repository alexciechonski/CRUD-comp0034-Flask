import json
import tempfile
from src.testing.conftest import EXP_OUTPUTS


def get_exp_data():
    with open(EXP_OUTPUTS, "r") as file:
        data = json.load(file)
    return data

def create_tmp_db(monkeypatch, setattr = False):
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name
    if setattr:
        monkeypatch.setattr("src.backend.erd_manager.get_db_path", lambda name: db_path)
    return db_path
