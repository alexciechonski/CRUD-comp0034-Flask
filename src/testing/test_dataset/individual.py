from playwright.sync_api import sync_playwright
import time
from src.utils import show_tables, query_db
from src.config import PATHS
import pandas as pd

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
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto(url)
        time.sleep(1)

        # click Date
        date = page.get_by_text('Date')
        box = date.bounding_box()
        x, y = box['x'] + box['width']/2, box['y'] + box['height']/2 + 10
        page.mouse.click(x, y)
        time.sleep(1)
        table = page.locator('xpath=//*[@id="erd-chart"]').inner_text()
        res['Date'] = table
        time.sleep(1)
        page.locator('#back-btn').click()
        time.sleep(3)

        # click Week
        source = page.get_by_text('Source')
        box = source.bounding_box()
        x, y = box['x'] + box['width']/2, box['y'] + box['height']/2 + 10
        page.mouse.click(x, y)
        time.sleep(1)
        table = page.locator('xpath=//*[@id="erd-chart"]').inner_text()
        res['Source'] = table
        time.sleep(1)
        page.locator('#back-btn').click()
        time.sleep(3)

        # select custom.db
        dropdown = page.locator("#select_db")
        dropdown.click()
        time.sleep(1)
        custom_db = dropdown.get_by_text('custom.db')
        custom_db.click()
        time.sleep(3)

        # click MHCare Cluster
        cluster = page.get_by_text('MHCareCluster')
        box = cluster.bounding_box()
        x, y = box['x'] + box['width']/2, box['y'] + box['height']/2 + 10
        page.mouse.click(x, y)
        time.sleep(1)
        table = page.locator('xpath=//*[@id="erd-chart"]/div[2]/div/div').inner_text()
        res['MHCareCluster'] = table
        time.sleep(1)
        page.locator('#back-btn').click()
        time.sleep(3)

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
        time.sleep(1)

        # select custom.db
        dropdown = page.locator("#select_db")
        dropdown.click()
        time.sleep(1)
        custom_db = dropdown.get_by_text('custom.db')
        custom_db.click()
        time.sleep(3)

        # add table
        page.locator('#table-name-input').fill("Test")
        page.locator('#submit-create-button').click()
        time.sleep(1)
    
    assert 'Test' in show_tables('custom.db')

def test_insert(url):
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto(url)
        time.sleep(1)

        # select custom.db
        dropdown = page.locator("#select_db")
        dropdown.click()
        time.sleep(1)
        custom_db = dropdown.get_by_text('custom.db')
        custom_db.click()
        time.sleep(3)

        # upload csv
        with page.expect_file_chooser() as fc_info:
            page.locator('#upload-data').click()  # Click upload button
        file_chooser = fc_info.value
        file_chooser.set_files("src/testing/resources/test.csv")  # Set the file

        dropdown = page.locator('#insert-to-table')
        dropdown.click()
        time.sleep(1)
        table = dropdown.get_by_text('Test')
        table.click()
        time.sleep(1)

        page.locator('#submit-insert').click()
    
    df = pd.read_csv("src/testing/resources/test.csv")
    assert query_db("SELECT * FROM Test", PATHS['custom.db']) == list(df.itertuples(index=False, name=None)), "Wrong or missing data"

def test_delete(url):
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto(url)
        time.sleep(1)

        # select custom.db
        dropdown = page.locator("#select_db")
        dropdown.click()
        time.sleep(1)
        custom_db = dropdown.get_by_text('custom.db')
        custom_db.click()
        time.sleep(3)

        dropdown = page.locator('#delete-input')
        dropdown.click()
        time.sleep(5)
        table = dropdown.get_by_text('Test')
        table.click()
        time.sleep(1)
        page.locator('#submit-delete-button').click()

    assert "Test" not in show_tables('custom.db')


if __name__ == "__main__":
    test_delete("http://127.0.0.1:8050/dataset")
