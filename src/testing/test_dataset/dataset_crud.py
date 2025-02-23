from playwright.sync_api import sync_playwright, Page
import time
from src.utils import show_tables, query_db
from src.config import PATHS
import pandas as pd
from testing.crud_actions import fillout_form, dropdown_select, upload_data, load_all
import pytest

@pytest.fixture(scope="function")
def browser():
    """Setup and teardown Playwright browser instance."""
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False)
        page = browser.new_page()
        yield page 
        browser.close()

def click_table(page: Page, table_name):
    table = page.get_by_text(table_name)
    box = table.bounding_box()
    x, y = box['x'] + box['width']/2, box['y'] + box['height']/2 + 32
    page.mouse.click(x, y)
    load_all(page)
    table_contents = page.locator('xpath=//*[@id="erd-chart"]').inner_text()
    processed_contents = [line.strip() for line in table_contents.split("\n") if line.strip()]
    return processed_contents

def go_back(page: Page):
    back = page.locator('#back-btn')
    back.wait_for(state='attached', timeout=5000)
    back.click()
    time.sleep(1)
    
@pytest.mark.parametrize("table_name, expected_data", [
    ("Date", [
        '0', '1', 'Column ID', 'date', 'date_id', 'Field Name', 'TEXT', 'INTEGER', 'Data Type', 
        '1', '0', 'Not Null', 'null', 'null', 'Default', '0', '1', 'Primary Key'
    ]),
    ("Source", [
        '0', '1', '2', 'Column ID', 'source', 'source_id', 'name', 'Field Name', 'TEXT', 'INTEGER', 'TEXT', 
        'Data Type', '1', '0', '1', 'Not Null', 'null', 'null', 'null', 'Default', '0', '1', '0', 'Primary Key'
    ]),
    ("WeeklyRestriction", [
        '0', '1', '2', 'Column ID', 'week_id', 'restriction_id', 'in_place', 'Field Name', 'INTEGER', 'INTEGER', 'INTEGER', 
        'Data Type', '1', '1', '1', 'Not Null', 'null', 'null', 'null', 'Default', '0', '0', '0', 'Primary Key'
    ])
])
def test_view_table(browser, table_name, expected_data):
    """Tests viewing different tables using parameterization."""
    browser.goto("http://127.0.0.1:8050/dataset")
    browser.wait_for_load_state("networkidle")
    extracted_data = click_table(browser, table_name)
    go_back(browser)
    assert extracted_data == expected_data, f"Data mismatch for {table_name}"

def test_add(browser):
    browser.goto("http://127.0.0.1:8050/dataset")
    browser.wait_for_load_state("networkidle")
    dropdown_select(browser, "#select_db", 'custom.db')
    load_all(browser)
    fillout_form(browser, "#table-name-input", "#submit-create-button", "Test")
    assert 'Test' in show_tables('custom.db')

def test_insert(browser):
    browser.goto("http://127.0.0.1:8050/dataset")
    browser.wait_for_load_state("networkidle")
    dropdown_select(browser, "#select_db", 'custom.db')
    upload_data(browser, "src/testing/resources/test.csv")
    dropdown_select(browser, '#insert-to-table', 'Test')
    browser.locator('#submit-insert').click()
    
    df = pd.read_csv("src/testing/resources/test.csv")
    assert query_db("SELECT * FROM Test", PATHS['custom.db']) == list(df.itertuples(index=False, name=None)), "Wrong or missing data"

def test_delete(browser):
    browser.goto("http://127.0.0.1:8050/dataset")
    browser.wait_for_load_state("networkidle")
    dropdown_select(browser, "#select_db", 'custom.db')
    dropdown_select(browser, "#delete-input", 'Test')
    browser.locator('#submit-delete-button').click()
    assert "Test" not in show_tables('custom.db')

