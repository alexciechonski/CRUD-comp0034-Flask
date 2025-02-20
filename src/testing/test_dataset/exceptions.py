from playwright.sync_api import sync_playwright
import time

def test_create_table(url):
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto(url)
        time.sleep(1)

        #create Date
        page.locator('#table-name-input').fill("Date")
        page.locator('#submit-create-button').click()
        time.sleep(1)

def test_delete_immutable_table(url):
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto(url)
        time.sleep(1)

        # delete Date
        dropdown = page.locator('#delete-input')
        dropdown.click()
        time.sleep(5)
        table = dropdown.get_by_text('Date')
        table.click()
        time.sleep(1)
        page.locator('#submit-delete-button').click()

def test_insert_immutable_table(url):
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto(url)
        time.sleep(1)

        # insert into Date
        with page.expect_file_chooser() as fc_info:
            page.locator('#upload-data').click()  # Click upload button
        file_chooser = fc_info.value
        file_chooser.set_files("src/testing/test.csv")  # Set the file

        dropdown = page.locator('#insert-to-table')
        dropdown.click()
        time.sleep(1)
        table = dropdown.get_by_text('Date')
        table.click()
        time.sleep(1)

def test_insert_bad_schema(url):
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

        # create Test
        page.locator('#table-name-input').fill("Test")
        page.locator('#submit-create-button').click()
        time.sleep(1)

        # upload csv
        with page.expect_file_chooser() as fc_info:
            page.locator('#upload-data').click()  # Click upload button
        file_chooser = fc_info.value
        file_chooser.set_files("src/testing/bad_schema.csv")  # Set the file

        dropdown = page.locator('#insert-to-table')
        dropdown.click()
        time.sleep(1)
        table = dropdown.get_by_text('Test')
        table.click()
        time.sleep(1)

        page.locator('#submit-insert').click()

if __name__ == "__main__":
    test_insert_bad_schema("http://127.0.0.1:8050/dataset")