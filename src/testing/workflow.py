from playwright.sync_api import sync_playwright
import time

def test_workflow():
    res = ""
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto("http://127.0.0.1:8050/dataset")
        time.sleep(1)

        # select custom.db
        dropdown = page.locator("#select_db")
        dropdown.click()
        time.sleep(1)
        custom_db = dropdown.get_by_text('custom.db')
        custom_db.click()
        time.sleep(3)

        # create new table
        page.locator('#table-name-input').fill("Deaths2")
        page.locator('#submit-create-button').click()
        time.sleep(1)

        # insert data
        with page.expect_file_chooser() as fc_info:
            page.locator('#upload-data').click()  # Click upload button
        file_chooser = fc_info.value
        file_chooser.set_files("src/testing/deaths.csv")  # Set the file

        dropdown = page.locator('#insert-to-table')
        dropdown.click()
        time.sleep(1)
        table = dropdown.get_by_text('Deaths2')
        table.click()
        time.sleep(1)
        page.locator('#submit-insert').click()

        # get correlation graph
        page.goto("http://127.0.0.1:8050/time-series")
        time.sleep(1)

        page.get_by_role("checkbox").check()
        time.sleep(1)

        dropdown = page.locator('#select-db')
        dropdown.click()
        time.sleep(1)

        custom_db = dropdown.get_by_text('custom.db')
        custom_db.click()
        time.sleep(1)

        dropdown = page.locator('#select-table')
        dropdown.click()
        cluster = dropdown.get_by_text('Deaths2')
        cluster.click()
        time.sleep(3)

        page.locator('#user-prompt').fill("Explain the relationship")
        page.locator('#submit-prompt').click()
        time.sleep(10)

        page.goto("http://127.0.0.1:8050/dataset")

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
        table = dropdown.get_by_text('Deaths2')
        table.click()
        time.sleep(1)
        page.locator('#submit-delete-button').click()

if __name__ == "__main__":
    test_workflow()

