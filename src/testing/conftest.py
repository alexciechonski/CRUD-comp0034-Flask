EXP_OUTPUTS = "src/testing/exp_outputs.json"
DEATHS_FILEPATH = "src/testing/resources/deaths.csv"
BAD_SCHEMA_PATH = "src/testing/resources/bad_schema.csv"

import pytest
import os
import sys
from pathlib import Path
import sqlite3
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.backend.data_server import DataServer
from src.backend.erd_manager import CRUD
from src.backend.log.log_manager import LogManager
from src.backend.revert_manager import RevertManager
from src.backend.validation import Validator as v
from src.utils import get_db_path, get_table_info, show_tables
from src.backend.erd_manager import Visualizer
from src.frontend.app import app
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String
from sqlalchemy.orm import declarative_base
from src.backend.log.log_manager import LogManager
import src.backend.log.log_manager as log_module  # to patch get_db_path + LOG_PATH
import tempfile
from playwright.sync_api import sync_playwright, Page

# Add the project root to Python path
project_root = str(Path(__file__).parent.parent.parent.parent)
sys.path.append(project_root)

@pytest.fixture
def test_db_path():
    """Fixture to get the path to the test database."""
    return get_db_path('test.db')

@pytest.fixture
def test_db_engine(test_db_path):
    """Fixture to create a SQLAlchemy engine for the test database."""
    return create_engine(f'sqlite:///{test_db_path}')

@pytest.fixture
def covid_server():
    return DataServer("covid.db")

@pytest.fixture
def test_data_server():
    """Fixture to create a DataServer instance for testing."""
    return DataServer('test.db')

@pytest.fixture
def test_validator():
    """Fixture to create a Validator instance for testing."""
    return v()

@pytest.fixture
def client():
    with app.test_client() as client:
        yield client

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

@pytest.fixture(scope="function")
def page():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False) 
        context = browser.new_context()
        page = context.new_page()
        yield page
        context.close()
        browser.close()