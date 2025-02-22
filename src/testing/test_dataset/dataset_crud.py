from playwright.sync_api import sync_playwright
import time
from src.utils import show_tables, query_db
from src.config import PATHS
import pandas as pd
from testing.crud_actions import fillout_form, dropdown_select, upload_data, load_all


def test_view_table(url):
    res = {}

    def click_table(table_name):
        table = page.get_by_text(table_name)
        box = table.bounding_box()
        x, y = box['x'] + box['width']/2, box['y'] + box['height']/2 + 32
        page.mouse.click(x, y)
        load_all(page)
        table_contents = page.locator('xpath=//*[@id="erd-chart"]').inner_text()
        processed_contents = [line.strip() for line in table_contents.split("\n") if line.strip()]
        res[table_name] = processed_contents

    def go_back():
        back = page.locator('#back-btn')
        back.wait_for(state='attached', timeout=5000)
        back.click()
        time.sleep(1)

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto(url)
        page.wait_for_load_state("networkidle")

        # click Date
        click_table("Date")
        go_back()

        # click Week
        click_table("Source")
        go_back()

        # click MHCare Cluster
        click_table("WeeklyRestriction")
        go_back()

    assert res == {
        'Date': ['0', '1', 'Column ID', 'date', 'date_id', 'Field Name', 'TEXT', 'INTEGER', 'Data Type', '1', '0', 'Not Null', 'null', 'null', 'Default', '0', '1', 'Primary Key'],
        'Source': ['0', '1', '2', 'Column ID', 'source', 'source_id', 'name', 'Field Name', 'TEXT', 'INTEGER', 'TEXT', 'Data Type', '1', '0', '1', 'Not Null', 'null', 'null', 'null', 'Default', '0', '1', '0', 'Primary Key'],
        'WeeklyRestriction': ['0', '1', '2', 'Column ID', 'week_id', 'restriction_id', 'in_place', 'Field Name', 'INTEGER', 'INTEGER', 'INTEGER', 'Data Type', '1', '1', '1', 'Not Null', 'null', 'null', 'null', 'Default', '0', '0', '0', 'Primary Key']
        }, "Wrong or missing data"


def test_add(url):
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto(url)
        page.wait_for_load_state("networkidle")

        dropdown_select(page, "#select_db", 'custom.db')
        load_all(page)

        fillout_form(page, "#table-name-input", "#submit-create-button", "Test")
    
    assert 'Test' in show_tables('custom.db')

def test_insert(url):
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto(url)
        page.wait_for_load_state("networkidle")
        dropdown_select(page, "#select_db", 'custom.db')
        upload_data(page, "src/testing/resources/test.csv")
        dropdown_select(page, '#insert-to-table', 'Test')
        page.locator('#submit-insert').click()
    
    df = pd.read_csv("src/testing/resources/test.csv")
    assert query_db("SELECT * FROM Test", PATHS['custom.db']) == list(df.itertuples(index=False, name=None)), "Wrong or missing data"

def test_delete(url):
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto(url)
        page.wait_for_load_state("networkidle")
        dropdown_select(page, "#select_db", 'custom.db')
        dropdown_select(page, "#delete-input", 'Test')
        page.locator('#submit-delete-button').click()
    assert "Test" not in show_tables('custom.db')


if __name__ == "__main__":
    test_view_table("http://127.0.0.1:8050/dataset")
