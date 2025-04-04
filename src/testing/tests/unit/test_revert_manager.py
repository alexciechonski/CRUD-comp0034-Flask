import os
import tempfile
import pytest
import json
from sqlalchemy import create_engine, inspect, text
from src.backend.revert_manager import RevertManager
import src.backend.revert_manager as revert_module


@pytest.fixture
def temp_db_and_patch(monkeypatch):
    # Create a temporary database file
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    # Patch get_db_path to return the full path
    monkeypatch.setattr(revert_module, "get_db_path", lambda name: db_path)

    yield os.path.basename(db_path), db_path  # return db_name, full path

    os.remove(db_path)


@pytest.fixture
def revert_manager(temp_db_and_patch):
    db_name, db_path = temp_db_and_patch
    engine = create_engine(f"sqlite:///{db_path}")
    engine.execute("""
        CREATE TABLE test_table (
            id INTEGER PRIMARY KEY,
            name TEXT
        )
    """)
    engine.execute("INSERT INTO test_table (id, name) VALUES (1, 'Alice')")
    return RevertManager(db_name)


def test_store_state_creates_backup_file(revert_manager):
    revert_manager.store_state()
    backup_path = os.path.join(revert_manager.revert_dir, f"{revert_manager.database}_state_backup.json")
    assert os.path.exists(backup_path)
    with open(backup_path) as f:
        data = json.load(f)
        assert "test_table" in data
        assert data["test_table"][0]["name"] == "Alice"
    os.remove(backup_path)


def test_restore_state_reverts_changes(revert_manager):
    revert_manager.store_state()

    # Change the row
    with revert_manager.engine.connect() as conn:
        conn.execute(text("DELETE FROM test_table"))
        conn.execute(text("INSERT INTO test_table (id, name) VALUES (2, 'Bob')"))
        result = conn.execute(text("SELECT * FROM test_table")).fetchall()
        assert result[0]["name"] == "Bob"

    success = revert_manager.restore_state()
    assert success

    # Verify restoration
    with revert_manager.engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM test_table")).fetchall()
        assert result[0]["name"] == "Alice"
        assert result[0]["id"] == 1

    backup_path = os.path.join(revert_manager.revert_dir, f"{revert_manager.database}_state_backup.json")
    if os.path.exists(backup_path):
        os.remove(backup_path)
