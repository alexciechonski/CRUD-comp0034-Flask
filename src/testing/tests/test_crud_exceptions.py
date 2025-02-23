import pytest
import pandas as pd
from playwright.sync_api import sync_playwright, Page
from src.utils import show_tables, query_db
from src.config import PATHS
from testing.helpers.crud_actions import fillout_form, dropdown_select, upload_data, load_all

@pytest.fixture(scope="function")
def browser():
    """Setup and teardown Playwright browser instance."""
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page()
        yield page 
        browser.close()

@pytest.mark.parametrize("url", ["http://127.0.0.1:8050/dataset"])
def test_create_table(browser, url):
    """Tests creating a new table."""
    browser.goto(url)
    browser.wait_for_load_state("networkidle")

    fillout_form(browser, "#table-name-input", "#submit-create-button", "Date")

    assert show_tables("covid.db").count("Date") == 1, "❌ Created a duplicate table"

@pytest.mark.parametrize("url", ["http://127.0.0.1:8050/dataset"])
def test_delete_immutable_table(browser, url):
    """Tests that an immutable table cannot be deleted."""
    browser.goto(url)
    browser.wait_for_load_state("networkidle")

    dropdown_select(browser, "#delete-input", "Date")
    browser.locator("#submit-delete-button").click()

    assert "Date" in show_tables("covid.db"), "❌ Deleted an immutable table"

@pytest.mark.parametrize("url", ["http://127.0.0.1:8050/dataset"])
def test_insert_immutable_table(browser, url):
    """Tests that data cannot be inserted into an immutable table."""
    browser.goto(url)
    browser.wait_for_load_state("networkidle")

    upload_data(browser, "src/testing/resources/test.csv")
    dropdown_select(browser, "#insert-to-table", "Date")

    df = pd.read_csv("src/testing/resources/test.csv")
    assert query_db("SELECT * FROM Date", PATHS["covid.db"]) != list(df.itertuples(index=False, name=None)), "❌ Inserted into an immutable table"

@pytest.mark.parametrize("url", ["http://127.0.0.1:8050/dataset"])
def test_insert_bad_schema(browser, url):
    """Tests that data with an incorrect schema is not inserted."""
    browser.goto(url)
    browser.wait_for_load_state("networkidle")

    dropdown_select(browser, "#select_db", 'custom.db')
    load_all(browser)

    # create Test
    fillout_form(browser, "#table-name-input", "#submit-create-button", "Test")

    # upload csv
    upload_data(browser, "src/testing/resources/test.csv")
    dropdown_select(browser, '#insert-to-table', 'Test')
    data = query_db("SELECT * FROM Test", PATHS['custom.db'])

    dropdown_select(browser, "#delete-input", "Test")
    browser.locator('#submit-delete-button').click()

    assert not data, "Inserted Bad Schema"

