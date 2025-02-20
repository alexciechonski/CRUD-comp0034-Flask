from playwright.sync_api import sync_playwright
import time

def test_series_flow(url):
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto(url)
        time.sleep(1)

        # select restrictions
        dropdown = page.locator("#restr-select")
        dropdown.click()
        time.sleep(1)
        curfew = dropdown.get_by_text('curfew')
        curfew.click()

        dropdown = page.locator("#restr-select")
        dropdown.click()
        time.sleep(1)
        wfh = dropdown.get_by_text('WFH')
        wfh.click()

        dropdown = page.locator("#restr-select")
        dropdown.click()
        time.sleep(1)
        pubs_closed = dropdown.get_by_text('Pubs Closed')
        pubs_closed.click()

        time.sleep(1)

        #show plot
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
        cluster = dropdown.get_by_text('MHCareCluster')
        cluster.click()
        time.sleep(3)

        page.locator('#user-prompt').fill("Explain the relationship")
        page.locator('#submit-prompt').click()
        time.sleep(10)


if __name__ == "__main__":
    test_series_flow("http://127.0.0.1:8050/time-series")