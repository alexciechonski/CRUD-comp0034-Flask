import os
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from src.backend.erd_manager import Visualizer, CRUD
from src.utils import get_db_path
from src.testing.helpers.unit_helpers import get_exp_data, create_tmp_db

def test_get_adj_list():
    engine = create_engine(f'sqlite:///{get_db_path("covid.db")}')
    Session = sessionmaker(bind=engine)
    session = Session()
    vis = Visualizer(session)
    adj = vis.get_adj_list()
    exp = get_exp_data()
    assert adj == exp['erds']['covid.db']

def test_add_table(monkeypatch):
    db_path = create_tmp_db(monkeypatch)

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
        os.remove(get_db_path(db_name))  # Clean up temp DB file

def test_remove_table(monkeypatch):
    # Create a temp SQLite file
    db_path = create_tmp_db(monkeypatch, setattr=True)
    try:
        # Instantiate CRUD with the temp database file name
        db_name = os.path.basename(db_path)

        crud = CRUD(db_name)
        crud.engine = crud.engine.execution_options(isolation_level="AUTOCOMMIT")  # optional

        # Add table
        crud.add_table("test_table")
        crud.remove_table(db_name, "test_table")

        # Inspect and assert
        inspector = inspect(crud.engine)
        assert "test_table" not in inspector.get_table_names()

    finally:
        os.remove(get_db_path(db_name))

def test_insert_data(monkeypatch):
    # Create a temp SQLite file
    db_path = create_tmp_db(monkeypatch, setattr=True)

    try:
        db_name = os.path.basename(db_path)

        crud = CRUD(db_name)

        # Add table to be removed
        crud.add_table("test_table")
        with crud.engine.connect() as conn:
            conn.execute("INSERT INTO test_table VALUES (1, '2020-01-03', 1162)")
            result = conn.execute("SELECT * FROM test_table").fetchall()
            assert len(result) == 1
            assert result[0]["measured_value"] == 1162

    finally:
        os.remove(get_db_path(db_name))
