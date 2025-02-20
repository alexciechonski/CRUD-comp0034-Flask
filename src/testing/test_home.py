from playwright.sync_api import sync_playwright
import time

def home_flow(url):
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto(url)
        time.sleep(3)

        dataset_page = page.get_by_text("Dataset")
        dataset_page.click()
        time.sleep(3)

        time_series_page = page.get_by_text("Time Series")
        time_series_page.click()
        time.sleep(3)

        distribution_page = page.get_by_text("Restriction Distribution")
        distribution_page.click()
        time.sleep(3)

        timeline_page = page.get_by_text("Timeline")
        timeline_page.click()
        time.sleep(3)

if __name__ == "__main__":
    home_flow("http://127.0.0.1:8050/")