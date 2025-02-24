"""
Automated UI Tests for the Dataset Management System.

This module contains Playwright-based tests for verifying table creation, deletion,
and data insertion functionalities within the web application.

Dependencies:
- `pytest`: For test execution and parameterization.
- `pandas` (pd): For handling test data validation.
- `sync_playwright`: For browser automation.
- `show_tables`: Retrieves a list of tables from the database.
- `query_db`: Executes SQL queries for data verification.
- `PATHS`: Defines database locations.
- `fillout_form`, `dropdown_select`, `upload_data`, `load_all`: Helper functions
  for UI interactions.

Example Usage:
    Run all tests:
    pytest

    Run a specific test:
    pytest -k "test_create_table"
"""

import pytest
import pandas as pd
from playwright.sync_api import sync_playwright, Page
from src.utils import show_tables, query_db
from src.config import PATHS
from testing.helpers.crud_actions import fillout_form, dropdown_select, upload_data, load_all

@pytest.fixture(scope="function")
def browser():
    """
    Sets up and tears down a Playwright browser instance for testing.

    Yields:
        Page: A Playwright browser page instance.
    """
    with sync_playwright() as pw_instance:
        browser = pw_instance.chromium.launch(headless=True)
        page = browser.new_page()
        yield page
        browser.close()

@pytest.mark.parametrize("url", ["http://127.0.0.1:8050/dataset"])
def test_create_table(browser: Page, url: str):
    """
    Tests the creation of a new table through the UI.

    Steps:
    - Navigates to the dataset page.
    - Fills out the form to create a new table.
    - Verifies that the table is created in the database.

    Args:
        browser (Page): The Playwright browser instance.
        url (str): The test URL.

    Asserts:
        - The table "Date" should be created only once.
    """
    browser.goto(url)
    browser.wait_for_load_state("networkidle")

    fillout_form(browser, "#table-name-input", "#submit-create-button", "Date")

    assert show_tables("covid.db").count("Date") == 1, "Created a duplicate table"

@pytest.mark.parametrize("url", ["http://127.0.0.1:8050/dataset"])
def test_delete_immutable_table(browser: Page, url: str):
    """
    Tests that an immutable table cannot be deleted.

    Steps:
    - Navigates to the dataset page.
    - Selects an immutable table for deletion.
    - Clicks the delete button.
    - Ensures that the table is still present in the database.

    Args:
        browser (Page): The Playwright browser instance.
        url (str): The test URL.

    Asserts:
        - The "Date" table should remain in the database.
    """
    browser.goto(url)
    browser.wait_for_load_state("networkidle")

    dropdown_select(browser, "#delete-input", "Date")
    browser.locator("#submit-delete-button").click()

    assert "Date" in show_tables("covid.db"), "Deleted an immutable table"

@pytest.mark.parametrize("url", ["http://127.0.0.1:8050/dataset"])
def test_insert_immutable_table(browser: Page, url: str):
    """Tests that data cannot be inserted into an immutable table."""
    browser.goto(url)
    browser.wait_for_load_state("networkidle")

    upload_data(browser, "src/testing/resources/test.csv")
    dropdown_select(browser, "#insert-to-table", "Date")

    test_df = pd.read_csv("src/testing/resources/test.csv")
    actual = query_db("SELECT * FROM Date", PATHS["covid.db"])
    expected = list(test_df.itertuples(index=False, name=None))
    assert actual != expected, "Inserted into an immutable table"

@pytest.mark.parametrize("url", ["http://127.0.0.1:8050/dataset"])
def test_insert_bad_schema(browser: Page, url: str):
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
