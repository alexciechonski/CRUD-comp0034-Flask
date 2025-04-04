import pytest
import os
from pathlib import Path
import shutil
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker
from src.backend.erd_manager import Visualizer, CRUD
from src.testing.helpers.unit_helpers import get_exp_data
from src.utils import get_db_path


# --- Fixtures ---

@pytest.fixture(scope="session")
def test_db_dir(tmp_path_factory):
    """Create a temporary directory to hold test.db."""
    db_dir = tmp_path_factory.mktemp("test_db")
    return db_dir

@pytest.fixture(scope="session")
def test_db_path(test_db_dir, request):
    """Path to test.db inside the temporary directory."""
    db_path = test_db_dir / "test.db"

    def cleanup():
        # First dispose of any database connections
        if 'test_db_engine' in request._fixture_values:
            request._fixture_values['test_db_engine'].dispose()
        # Then remove the entire directory and its contents
        if test_db_dir.exists():
            shutil.rmtree(test_db_dir, ignore_errors=True)

    request.addfinalizer(cleanup)
    return str(db_path)

@pytest.fixture(scope="session")
def test_db_engine(test_db_path):
    """SQLAlchemy engine for test.db."""
    engine = create_engine(f'sqlite:///{test_db_path}')
    return engine

@pytest.fixture
def test_db_session(test_db_engine):
    """SQLAlchemy session for test.db."""
    Session = sessionmaker(bind=test_db_engine)
    session = Session()
    yield session
    session.close()

@pytest.fixture
def db_visualizer(test_db_session):
    """Visualizer using test DB session."""
    def _create():
        return Visualizer(test_db_session)
    return _create

@pytest.fixture
def test_crud(test_db_path, request):
    """CRUD using isolated engine and session for test.db."""
    class MockCRUD(CRUD):
        def __init__(self, db_path):
            self.db_path = db_path
            self.db_name = os.path.basename(db_path)
            self.engine = create_engine(f"sqlite:///{db_path}")
            self.session = sessionmaker(bind=self.engine)()

        def dispose(self):
            self.session.close()
            self.engine.dispose()

    crud = MockCRUD(test_db_path)

    def cleanup():
        crud.dispose()

    request.addfinalizer(cleanup)
    return crud

@pytest.fixture(autouse=True)
def setup_test_table(test_db_engine):
    """Ensure test_table is cleaned up before and after each test."""
    with test_db_engine.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS test_table"))
    yield
    with test_db_engine.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS test_table"))


# --- Tests ---

def test_get_adj_list():
    """Test getting adjacency list from example db."""
    engine = create_engine(f'sqlite:///{get_db_path("covid.db")}')
    Session = sessionmaker(bind=engine)
    session = Session()
    vis = Visualizer(session)
    adj = vis.get_adj_list()
    exp = get_exp_data()
    assert adj == exp['erds']['covid.db']
    session.close()
    engine.dispose()

def test_add_table(test_crud, test_db_engine):
    """Test adding a new table to the database."""
    test_crud.add_table("test_table")

    inspector = inspect(test_db_engine)
    assert "test_table" in inspector.get_table_names()

    columns = [col['name'] for col in inspector.get_columns("test_table")]
    assert set(columns) == {"id", "time", "measured_value"}

def test_remove_table(test_crud, test_db_engine):
    """Test removing a table from the database."""
    test_crud.add_table("test_table")
    test_crud.remove_table("test.db", "test_table")

    inspector = inspect(test_db_engine)
    assert "test_table" not in inspector.get_table_names()

def test_insert_data(test_crud, test_db_engine):
    """Test inserting data into a table."""
    test_crud.add_table("test_table")

    with test_db_engine.begin() as conn:
        conn.execute(text(
            "INSERT INTO test_table (id, time, measured_value) "
            "VALUES (1, '2020-01-03', 1162)"
        ))
        result = conn.execute(text("SELECT * FROM test_table")).fetchall()
        assert len(result) == 1
        assert result[0]["measured_value"] == 1162
