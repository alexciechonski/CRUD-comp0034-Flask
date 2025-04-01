from playwright.sync_api import sync_playwright, Page
from src.testing.conftest import DEATHS_FILEPATH, BAD_SCHEMA_PATH
from src.utils import query_db, get_db_path, show_tables, get_databases
import pandas as pd
import pytest
from src.testing.helpers.crawl_helpers import insert_data, create_new_table, delete_table, get_schema_contents, accept_dialog, dialog_appeared
import time

@pytest.fixture(scope="function")
def page():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # set headless=True if you want it hidden
        context = browser.new_context()
        page = context.new_page()
        yield page
        context.close()
        browser.close()

def test_flow(page: Page):
    page.goto("http://127.0.0.1:5000/dataset")

    # create a new db
    page.wait_for_selector("#database-name-input", timeout=5000)
    page.locator("#database-name-input").fill("new.db")
    page.get_by_text("CREATE DATABASE").click()

    # select db
    page.wait_for_selector("#databaseSelect", timeout=5000)
    page.locator("#databaseSelect").select_option("NEW")

    # create new table
    page.locator("#table-name-input").fill("deaths")
    page.get_by_text("CREATE TABLE").click()

    assert "deaths" in show_tables("new.db")

    # insert data
    page.locator("#insert-table-select").select_option("deaths")
    with page.expect_file_chooser() as fc_info:
        page.locator('#csv-file').click()
    file_chooser = fc_info.value
    file_chooser.set_files(DEATHS_FILEPATH)
    page.get_by_text("UPLOAD AND INSERT DATA").click()

    # check schema
    schema = get_schema_contents(page, "deaths")
    print(schema)
    assert schema == [
        {'name': 'id', 'type': 'INTEGER', 'constraints': 'NOT NULL PRIMARY KEY'},
        {'name': 'time', 'type': 'DATE', 'constraints': 'NOT NULL'},
        {'name': 'measured_value', 'type': 'FLOAT', 'constraints': 'NOT NULL'}
        ]

    # check contents
    table_data = pd.DataFrame(query_db("SELECT * FROM deaths;", get_db_path("deaths.db")), columns=["id", "time", "measured_value"])
    og_data = pd.read_csv(DEATHS_FILEPATH)
    og_data["measured_value"] = og_data["measured_value"].astype(float)
    assert table_data.equals(og_data)

    # Set up dialog handler before triggering the action
    page.on("dialog", accept_dialog)

    # delete table
    page.locator("#delete-table-select").select_option("deaths")
    page.get_by_text("DELETE TABLE").click()
    assert "deaths" not in show_tables("new.db")

    # delete db
    page.get_by_text("DELETE DATABASE").click()
    assert "new.db" not in get_databases()

def test_bad_schema(page: Page):
    page.goto("http://127.0.0.1:5000/dataset")
    # select db
    page.wait_for_selector("#databaseSelect", timeout=5000)
    page.locator("#databaseSelect").select_option("COVID")

    # create table
    page.locator("#table-name-input").fill("test")
    page.get_by_text("CREATE TABLE").click()
    print('table created')

    insert_data(page, "test", BAD_SCHEMA_PATH)

    inserted_data = query_db("SELECT * FROM test;", get_db_path("covid.db"))
    assert not inserted_data

    delete_table(page, "test")

@pytest.mark.parametrize(
    "db_name, table_name",
    [
        ("COVID", "Date"),
        ("COVID", "Week"),
        ("COVID", "Source"),
        ("COVID", "SummaryRestriction"),
        ("COVID", "Restriction"),
        ("COVID", "DailyRestriction"),
        ("COVID", "WeeklyRestriction"),
        ("CUSTOM", "MHCareCluster")
    ]
)
def test_create_table_already_exists(page: Page, db_name, table_name):
    page.goto("http://127.0.0.1:5000/dataset")
    page.locator("#databaseSelect").select_option(db_name)
    page.locator("#table-name-input").fill(table_name)
    page.get_by_text("CREATE TABLE").click()
    assert show_tables(f"{db_name.lower()}.db").count(table_name) == 1

@pytest.mark.parametrize(
    "db_name, table_name",
    [
        ("COVID", "Date"),
        ("COVID", "Week"),
        ("COVID", "Source"),
        ("COVID", "SummaryRestriction"),
        ("COVID", "Restriction"),
        ("COVID", "DailyRestriction"),
        ("COVID", "WeeklyRestriction"),
    ]
)
def test_delete_immutable_table(page: Page, db_name, table_name):
    page.goto("http://127.0.0.1:5000/dataset")
    page.locator("#databaseSelect").select_option(db_name)

    delete_table(page, table_name)
    assert show_tables(f"{db_name.lower()}.db").count(table_name) == 1

@pytest.mark.parametrize(
    "db_name, table_name",
    [
        ("COVID", "Date"),
        ("COVID", "Week"),
        ("COVID", "Source"),
        ("COVID", "SummaryRestriction"),
        ("COVID", "Restriction"),
        ("COVID", "DailyRestriction"),
        ("COVID", "WeeklyRestriction"),
    ]
)
def test_insert_immutable(page: Page, db_name, table_name):
    page.goto("http://127.0.0.1:5000/dataset")
    page.locator("#databaseSelect").select_option(db_name)

    old_data = query_db(f"SELECT * FROM {table_name};", get_db_path(f"{db_name.lower()}.db"))
    insert_data(page, table_name, DEATHS_FILEPATH)
    new_data = query_db(f"SELECT * FROM {table_name};", get_db_path(f"{db_name.lower()}.db"))
    assert new_data == old_data

    

