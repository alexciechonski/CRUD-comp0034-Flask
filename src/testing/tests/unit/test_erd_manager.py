from src.backend.erd_manager import Visualizer, CRUD
from src.backend.erd_manager import CRUD as crud_module
import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker, Session
from src.utils import get_db_path
from src.testing.helpers.unit_helpers import get_exp_data
import tempfile 
import os
import pandas as pd
from src.utils import get_db_path

def test_get_adj_list():
    engine = create_engine(f'sqlite:///{get_db_path("covid.db")}')
    Session = sessionmaker(bind=engine)
    session = Session()
    vis = Visualizer(session)
    adj = vis.get_adj_list()
    exp = get_exp_data()
    assert adj == exp['erds']['covid.db']

def test_add_table(monkeypatch):
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    try:
        # Instantiate CRUD with the temp database file name
        db_name = os.path.basename(db_path)
        monkeypatch.setattr("src.backend.erd_manager.get_db_path", lambda name: db_path)

        crud = CRUD(db_name)
        crud.engine = crud.engine.execution_options(isolation_level="AUTOCOMMIT")  # optional

        # Add table
        crud.add_table("test_table")

        # Inspect and assert
        inspector = inspect(crud.engine)
        assert "test_table" in inspector.get_table_names()
        columns = [col['name'] for col in inspector.get_columns("test_table")]
        assert set(columns) == {"id", "time", "measured_value"}  # or adjust if `id` is not included

    finally:
        os.remove(db_path)  # Clean up temp DB file

def test_remove_table(monkeypatch):
    # Create a temp SQLite file
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    try:
        db_name = os.path.basename(db_path)
        monkeypatch.setattr("src.backend.erd_manager.get_db_path", lambda name: db_path)

        crud = CRUD(db_name)
        crud.engine = crud.engine.execution_options(isolation_level="AUTOCOMMIT")  # optional

        # Add table to be removed
        crud.add_table("test_table")
        inspector = inspect(crud.engine)
        assert "test_table" in inspector.get_table_names()  # sanity check

        # Call remove_table (this must exist in CRUD)
        crud.remove_table("test_table")

        # Verify the table is gone
        inspector = inspect(crud.engine)
        assert "test_table" not in inspector.get_table_names()

    finally:
        os.remove(db_path)

def test_insert_data(monkeypatch):
    # Create a temp SQLite file
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    try:
        db_name = os.path.basename(db_path)
        crud = CRUD(db_name)
        monkeypatch.setattr("src.backend.erd_manager.get_db_path", lambda name: db_path)

        # Add table to be removed
        crud.add_table("test_table")
        with crud.engine.connect() as conn:
            conn.execute("INSERT INTO test_table VALUES (1, '2020-01-03', 1162)")
            result = conn.execute("SELECT * FROM test_table").fetchall()
            assert len(result) == 1
            assert result[0]["measured_value"] == 42.0

    finally:
        os.remove(db_path)

if __name__ == "__main__":
    engine = create_engine(f'sqlite:///{get_db_path("covid.db")}')
    Session = sessionmaker(bind=engine)
    session = Session()
    vis = Visualizer(session)
    adj = vis.get_adj_list()
    print(adj)