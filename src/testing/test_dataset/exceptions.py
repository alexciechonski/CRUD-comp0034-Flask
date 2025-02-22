from playwright.sync_api import sync_playwright
import time
from src.utils import show_tables, query_db
from src.config import PATHS
import pandas as pd
from testing.crud_actions import fillout_form, dropdown_select, upload_data, load_all

def test_create_table(url):
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto(url)
        page.wait_for_load_state("networkidle")
        fillout_form(page, '#table-name-input', '#submit-create-button', "Date")
    assert show_tables('covid.db').count("Date") == 1, "Created a duplicate table"

def test_delete_immutable_table(url):
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto(url)
        page.wait_for_load_state("networkidle")
        dropdown_select(page, '#delete-input', "Date")
        page.locator('#submit-delete-button').click()
    assert "Date" in show_tables('covid.db'), "Deleted immutable table"

def test_insert_immutable_table(url):
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto(url)
        page.wait_for_load_state("networkidle")
        upload_data(page, "src/testing/resources/test.csv")
        dropdown_select(page, '#insert-to-table', 'Date')
    df = pd.read_csv('src/testing/resources/test.csv')
    assert query_db("SELECT * FROM Date", PATHS['covid.db']) != list(df.itertuples(index=False, name=None)), "Inserted into immutable table"

def test_insert_bad_schema(url):
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto(url)
        page.wait_for_load_state("networkidle")

        dropdown_select(page, "#select_db", 'custom.db')
        load_all(page)

        # create Test
        fillout_form(page, "#table-name-input", "#submit-create-button", "Test")

        # upload csv
        upload_data(page, "src/testing/resources/test.csv")
        dropdown_select(page, '#insert-to-table', 'Test')
        data = query_db("SELECT * FROM Test", PATHS['custom.db'])

        dropdown_select(page, "#delete-input", "Test")
        page.locator('#submit-delete-button').click()

    assert not data, "Inserted Bad Schema"

if __name__ == "__main__":
    test_insert_bad_schema("http://127.0.0.1:8050/dataset")
    # print(query_db("SELECT * FROM Test", PATHS['custom.db']))