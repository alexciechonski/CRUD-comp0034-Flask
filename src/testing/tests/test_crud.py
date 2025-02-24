"""
Automated UI Tests for Dataset Management.

This module contains Playwright-based tests for verifying dataset-related
functionalities, including table viewing, creation, insertion, and deletion
within the web application.
"""
from playwright.sync_api import sync_playwright, Page
import pandas as pd
import pytest
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

def click_table(page: Page, table_name: str):
    """
    Clicks on a table in the UI and extracts its displayed data.

    Args:
        page (Page): The Playwright browser instance.
        table_name (str): The name of the table to click.

    Returns:
        list[str]: Extracted and processed table contents.
    """
    table = page.get_by_text(table_name)
    box = table.bounding_box()
    x_val, y_val = box['x'] + box['width']/2, box['y'] + box['height']/2 + 32
    page.mouse.click(x_val, y_val)
    load_all(page)
    table_contents = page.locator('xpath=//*[@id="erd-chart"]').inner_text()
    processed_contents = [line.strip() for line in table_contents.split("\n") if line.strip()]
    return processed_contents

def go_back(page: Page):
    """
    Navigates back to the previous view in the dataset UI.

    Args:
        page (Page): The Playwright browser instance.
    """
    back = page.locator('#back-btn')
    back.wait_for(state='attached', timeout=5000)
    back.click()
    page.wait_for_selector('xpath=//*[@id="erd-chart"]', state='visible', timeout=5000)

@pytest.mark.parametrize("table_name, expected_data", [
    ("Date", [
        '0', '1', 'Column ID', 'date', 'date_id',
        'Field Name', 'TEXT', 'INTEGER', 'Data Type',
        '1', '0', 'Not Null', 'null', 'null', 'Default',
        '0', '1', 'Primary Key'
    ]),
    ("Source", [
        '0', '1', '2', 'Column ID', 'source', 'source_id',
        'name', 'Field Name', 'TEXT', 'INTEGER', 'TEXT',
        'Data Type', '1', '0', '1', 'Not Null', 'null', 'null',
        'null', 'Default', '0', '1', '0', 'Primary Key'
    ]),
    ("WeeklyRestriction", [
        '0', '1', '2', 'Column ID', 'week_id', 'restriction_id',
        'in_place', 'Field Name', 'INTEGER', 'INTEGER', 'INTEGER',
        'Data Type', '1', '1', '1', 'Not Null', 'null', 'null',
        'null', 'Default', '0', '0', '0', 'Primary Key'
    ])
])
def test_view_table(browser: Page, table_name: str, expected_data: list[str]):
    """
    Tests viewing different tables and verifying their contents.

    Steps:
    - Navigates to the dataset page.
    - Clicks on the specified table.
    - Extracts table data from the UI.
    - Navigates back.
    - Compares extracted data with expected data.

    Args:
        browser (Page): The Playwright browser instance.
        table_name (str): The name of the table to test.
        expected_data (list[str]): The expected table content.

    Asserts:
        - Extracted data should match expected data.
    """
    browser.goto("http://127.0.0.1:8050/dataset")
    browser.wait_for_load_state("networkidle")
    extracted_data = click_table(browser, table_name)
    go_back(browser)
    assert extracted_data == expected_data, f"Data mismatch for {table_name}"

def test_add(browser: Page):
    """
    Tests adding a new table through the UI.

    Steps:
    - Navigates to the dataset page.
    - Selects 'custom.db'.
    - Creates a new table named "Test".
    - Verifies that the table appears in the database.

    Args:
        browser (Page): The Playwright browser instance.

    Asserts:
        - The table "Test" should be present in 'custom.db'.
    """
    browser.goto("http://127.0.0.1:8050/dataset")
    browser.wait_for_load_state("networkidle")
    dropdown_select(browser, "#select_db", 'custom.db')
    load_all(browser)
    fillout_form(browser, "#table-name-input", "#submit-create-button", "Test")
    assert 'Test' in show_tables('custom.db')

def test_insert(browser: Page):
    """
    Tests inserting data into a newly created table.

    Steps:
    - Navigates to the dataset page.
    - Selects 'custom.db'.
    - Uploads a test CSV file.
    - Inserts data into the "Test" table.
    - Retrieves the database content and compares it with expected data.

    Args:
        browser (Page): The Playwright browser instance.

    Asserts:
        - Inserted data should match the expected CSV data.
    """
    browser.goto("http://127.0.0.1:8050/dataset")
    browser.wait_for_load_state("networkidle")
    dropdown_select(browser, "#select_db", 'custom.db')
    upload_data(browser, "src/testing/resources/test.csv")
    dropdown_select(browser, '#insert-to-table', 'Test')
    browser.locator('#submit-insert').click()
    test_df = pd.read_csv("src/testing/resources/test.csv")
    expected = list(test_df.itertuples(index=False, name=None))
    actual = query_db("SELECT * FROM Test", PATHS['custom.db'])
    assert expected == actual, "Wrong or missing data"

def test_delete(browser: Page):
    """
    Tests deleting a table through the UI.

    Steps:
    - Navigates to the dataset page.
    - Selects 'custom.db'.
    - Deletes the "Test" table.
    - Verifies that the table no longer exists.

    Args:
        browser (Page): The Playwright browser instance.

    Asserts:
        - The table "Test" should not be present in 'custom.db'.
    """
    browser.goto("http://127.0.0.1:8050/dataset")
    browser.wait_for_load_state("networkidle")
    dropdown_select(browser, "#select_db", 'custom.db')
    dropdown_select(browser, "#delete-input", 'Test')
    browser.locator('#submit-delete-button').click()
    assert "Test" not in show_tables('custom.db')
