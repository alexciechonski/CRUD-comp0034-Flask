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
    page.wait_for_load_state("networkidle")

    # Step 1: Click the dropdown (inside iframe)
    iframe = page.frame_locator("iframe[src='/table-crud/']")
    dropdown = iframe.locator("#table-select")
    dropdown.click(force=True)

    # Step 2: Type into the input field inside iframe
    iframe.locator("input").fill(option_text)
    page.keyboard.press("Enter")

def fill_record_form(page: Page, id_value: str, time_value: str, measured_value: str):
    page.wait_for_load_state("networkidle")
    # Get iframe
    iframe = page.frame_locator("iframe[src='/table-crud/']")

    # Fill the input after the label "id"
    iframe.locator("label:has-text('id') + input").fill(id_value)

    # Fill the input after the label "time"
    iframe.locator("label:has-text('time') + input").fill(time_value)

    # Fill the input after the label "measured_value"
    iframe.locator("label:has-text('measured_value') + input").fill(measured_value)

    # Click the save button
    iframe.locator("button", has_text="Save Record").click()

def get_last_row(page: Page):
    iframe = page.frame_locator("iframe[src='/table-crud/']")
    last_row = iframe.locator("table tbody tr").last
    cells = last_row.locator("td")
    cell_values = [cells.nth(i).inner_text() for i in range(cells.count())]    
    return cell_values[2], cell_values[3], cell_values[4]

def revert_last(page: Page):
    page.goto("http://127.0.0.1:5000/audit-log")
    page.wait_for_load_state("networkidle")

    page.locator('xpath=/html/body/main/div/div[1]/div[2]/div[2]/form/button').click()
    


def test_add(page: Page):
    """Test adding a record"""
    # Navigate to the page and wait for load
    page.goto("http://127.0.0.1:5000/crud-view")
    
    page.wait_for_load_state("networkidle")
    
    # Select the table using the helper function
    select_table(page, "deaths deaths.db")

    fill_record_form(page, '80', '2021-07-15', '1000')

    time.sleep(3)
    
    id, date, measured_val = get_last_row(page)
    assert id == '80'
    assert date == '2021-07-15'
    assert measured_val == '1000'


if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # set headless=True if you want it hidden
        page = browser.new_page()
        test_add(page)
