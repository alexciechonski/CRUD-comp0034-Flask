from playwright.sync_api import sync_playwright, Page, expect
import pytest
import time

@pytest.fixture(scope="function")
def page():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # set headless=True if you want it hidden
        context = browser.new_context()
        page = context.new_page()
        yield page
        context.close()
        browser.close()

def select_table(page: Page, option_text):
    page.goto("http://127.0.0.1:5000/crud-view")
    page.wait_for_load_state("networkidle")

    # Step 1: Click the dropdown (inside iframe)
    iframe = page.frame_locator("iframe[src='/table-crud/']")
    dropdown = iframe.locator("#table-select")
    dropdown.click(force=True)

    # Step 2: Type into the input field inside iframe
    iframe.locator("input").fill(option_text)
    page.keyboard.press("Enter")


def test_add(page: Page):
    """Test adding a record"""
    # Navigate to the page and wait for load
    page.goto("http://127.0.0.1:5000/crud-view")
    
    page.wait_for_load_state("networkidle")
    
    # Select the table using the helper function
    select_table(page)
    
    # Take initial screenshot
    page.screenshot(path="initial_page.png")
    
    # Fill in the form using semantic locators
    page.get_by_label("ID").fill("80")
    page.get_by_label("Time").fill("2021-07-15")
    page.get_by_label("Measured Value").fill("1000")
    
    # Click save button
    page.get_by_role("button", name="Save Record").click()
    
    # Wait for table to update
    time.sleep(2)
    
    # Verify the new record in the table
    id_value = page.locator('//*[@id="data-table"]/div[2]/div/div[2]/div[2]/table/tbody/tr[81]/td[3]').inner_text()
    assert id_value == "80"
    
    time_value = page.locator('//*[@id="data-table"]/div[2]/div/div[2]/div[2]/table/tbody/tr[81]/td[4]').inner_text()
    assert time_value == "2021-07-15"
    
    measured_value = page.locator('//*[@id="data-table"]/div[2]/div/div[2]/div[2]/table/tbody/tr[81]/td[5]').inner_text()
    assert measured_value == "1000"


if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # set headless=True if you want it hidden
        page = browser.new_page()
        select_table(page, "deaths deaths.db")
