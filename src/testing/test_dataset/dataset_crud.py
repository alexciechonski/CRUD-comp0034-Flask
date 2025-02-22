from playwright.sync_api import sync_playwright
import time
from src.utils import show_tables, query_db
from src.config import PATHS
import pandas as pd
from testing.crud_actions import fillout_form, dropdown_select, upload_data

def show_mouse(page, x, y):
    page.evaluate(f"""
        const box = document.createElement('div');
        box.style.position = 'absolute';
        box.style.left = '{x}px';
        box.style.top = '{y}px';
        box.style.border = '2px solid red';
        box.style.zIndex = '10000';
        document.body.appendChild(box);
    """)

def test_view_table(url):
    res = {}

    def click_table(table_name):
        table = page.get_by_text(table_name)
        box = table.bounding_box()
        x, y = box['x'] + box['width']/2, box['y'] + box['height']/2 + 10
        page.mouse.click(x, y)
        time.sleep(1)
        table_contents = page.locator('xpath=//*[@id="erd-chart"]').inner_text()
        res[table_name] = table_contents
        back = page.locator('#back-btn')
        back.wait_for(state='visible', timeout=5000)
        back.click()
        time.sleep(3)

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto(url)
        page.wait_for_load_state("networkidle")

        # click Date
        click_table("Date")

        # click Week
        click_table("Source")

        # select custom.db
        dropdown_select(page, "#select_db", 'custom.db')
        time.sleep(3)

        # click MHCare Cluster
        click_table("MHCareCluster")

    assert res == {
        'Date': '0\n1\nColumn ID\ndate\ndate_id\nField Name\nTEXT\nINTEGER\nData Type\n1\n0\nNot Null\nnull\nnull\nDefault\n0\n1\nPrimary Key',
        'Source': '0\n1\n2\nColumn ID\nsource\nsource_id\nname\nField Name\nTEXT\nINTEGER\nTEXT\nData Type\n1\n0\n1\nNot Null\nnull\nnull\nnull\nDefault\n0\n1\n0\nPrimary Key',
        'MHCareCluster': '0\n1\n2\nColumn ID\nid\ntime\nmeasured_value\nField Name\nINTEGER\nINTEGER\nINTEGER\nData Type\n0\n1\n1\nNot Null\nnull\nnull\nnull\nDefault\n1\n0\n0\nPrimary Key'
        }, "Wrong or missing data"

def test_add(url):
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto(url)
        page.wait_for_load_state("networkidle")

        dropdown_select(page, "#select_db", 'custom.db')
        time.sleep(1)

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
