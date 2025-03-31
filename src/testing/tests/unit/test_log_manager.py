import os
import tempfile
import pytest
import json
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String
from sqlalchemy.orm import declarative_base
from src.backend.log.log_manager import LogManager
import src.backend.log.log_manager as log_module  # to patch get_db_path + LOG_PATH

Base = declarative_base()

@pytest.fixture
def temp_log_file(monkeypatch):
    with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8') as tmp:
        tmp.write("[]")  # write an empty JSON array to initialize the log
        tmp.flush()      # make sure it's written to disk
        monkeypatch.setattr(log_module, "LOG_PATH", tmp.name)
        yield tmp.name
        os.remove(tmp.name)

@pytest.fixture
def in_memory_db(monkeypatch):
    monkeypatch.setattr(log_module, "get_db_path", lambda name: ":memory:")
    engine = create_engine("sqlite:///:memory:")
    metadata = MetaData()
    test_table = Table("test_table", metadata,
        Column("id", Integer, primary_key=True),
        Column("name", String),
    )
    metadata.create_all(engine)
    return engine

def test_create_change(temp_log_file, in_memory_db):
    manager = LogManager()
    new_data = {"id": 1, "time": "2020-01-01", "measured_value":100}
    manager.create_change("test.db", "test_table", new_data)

    assert len(manager.log) == 1
    entry = manager.log[-1]
    assert entry["change"] == "create"
    assert entry["new_data"] == new_data

def test_update_change(temp_log_file, in_memory_db):
    manager = LogManager()
    old_data = {"id": 1, "name": "Alice"}
    new_data = {"id": 1, "name": "Bob"}
    manager.update_change("test.db", "test_table", new_data, old_data)

    assert len(manager.log) == 1
    entry = manager.log[-1]
    assert entry["change"] == "update"
    assert entry["new_data"] == new_data
    assert entry["prev_data"] == old_data

def test_delete_change(temp_log_file, in_memory_db):
    manager = LogManager()
    old_data = {"id": 1, "name": "Alice"}
    manager.delete_change("test.db", "test_table", old_data)

    assert len(manager.log) == 1
    entry = manager.log[-1]
    assert entry["change"] == "delete"
    assert entry["prev_data"] == old_data

def test_remove_change(temp_log_file, in_memory_db):
    manager = LogManager()
    manager.create_change("test.db", "test_table", {"id": 1, "name": "A"})
    manager.update_change("test.db", "test_table", {"id": 1, "name": "B"}, {"id": 1, "name": "A"})
    manager.delete_change("test.db", "test_table", {"id": 1, "name": "B"})

    assert len(manager.log) == 3
    manager.remove_change("test.db", "test_table", "update")
    assert len(manager.log) == 2
    assert all(entry["change"] != "update" for entry in manager.log)

def test_to_tables_returns_dataframe(temp_log_file, in_memory_db):
    manager = LogManager()
    manager.create_change("test.db", "test_table", {"id": 1, "name": "A"})
    df = manager.to_tables()
    assert not df.empty
    assert "change_type" in df.columns
