from playwright.sync_api import sync_playwright, Page, expect
import pytest
import time
from src.testing.helpers.crawl_helpers import accept_dialog

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
    page.once("dialog", lambda dialog: dialog.accept())
    button_path = 'xpath=/html/body/main/div/div[1]/div[2]/div[2]/form/button'
    page.wait_for_selector(button_path)
    revert_button = page.locator(button_path)
    revert_button.click()

def delete_last_row(page: Page):
    page.wait_for_load_state("networkidle")

    # Access the iframe containing the Dash table
    iframe = page.frame_locator("iframe[src='/table-crud/']")

    # Wait until rows are rendered
    iframe.locator("table tbody tr").first.wait_for(timeout=3000)

    # Select the last row's delete cell (× button)
    delete_button = iframe.locator("table tbody tr").last.locator("td.dash-delete-cell")

    # Click the delete button
    delete_button.click()

def update_value(page: Page, new_value):
    iframe = page.frame_locator("iframe[src='/table-crud/']")

    # Wait for table to render
    iframe.locator("table tbody tr").first.wait_for(timeout=3000)

    # Locate the last row
    last_row = iframe.locator("table tbody tr").last

    # Locate the last cell in that row (assumed to be measured_value)
    last_cell = last_row.locator("td").last

    # Click to focus/edit
    last_cell.click()
    time.sleep(1)

    # Type: Ctrl+A to select all, then type new value and press Enter
    page.keyboard.press("Control+A")
    page.keyboard.type(new_value)
    page.keyboard.press("Enter")
    time.sleep(3)
    
def test_add(page: Page):
    """Test adding a record"""
    page.goto("http://127.0.0.1:5000/crud-view")
    page.wait_for_load_state("networkidle")
    select_table(page, "deaths deaths.db")
    fill_record_form(page, '80', '2021-07-15', '1000')
    time.sleep(3)
    id, date, measured_val = get_last_row(page)
    assert id == '80'
    assert date == '2021-07-15'
    assert measured_val == '1000'

    revert_last(page)
    page.goto("http://127.0.0.1:5000/crud-view")
    page.wait_for_load_state("networkidle")
    select_table(page, "deaths deaths.db")
    time.sleep(1)
    id, date, val = get_last_row(page)
    assert id == '79'
    assert date == '2021-07-02'
    assert val == '899'

# def test_delete(page: Page):
#     page.goto("http://127.0.0.1:5000/crud-view")
#     page.wait_for_load_state("networkidle")
#     select_table(page, "deaths deaths.db")
#     delete_last_row(page)
#     time.sleep(3)
#     id, date, val = get_last_row(page)
#     assert id == '78'
#     assert date == '2021-06-25'
#     assert val == '909'

#     revert_last(page)
#     page.goto("http://127.0.0.1:5000/crud-view")
#     page.wait_for_load_state("networkidle")
#     select_table(page, "deaths deaths.db")
#     time.sleep(1)
#     id, date, val = get_last_row(page)
#     assert id == '79'
#     assert date == '2021-07-02'
#     assert val == '899'

# def test_update(page: Page):
#     page.goto("http://127.0.0.1:5000/crud-view")
#     page.wait_for_load_state("networkidle")
#     select_table(page, "deaths deaths.db")
#     update_value(page, "1")
#     time.sleep(3)
#     id, date, val = get_last_row(page)
#     assert id == '79'
#     assert date == '2021-07-02'
#     assert val == '1899'

#     revert_last(page)
#     page.goto("http://127.0.0.1:5000/crud-view")
#     page.wait_for_load_state("networkidle")
#     select_table(page, "deaths deaths.db")
#     time.sleep(1)
#     id, date, val = get_last_row(page)
#     assert id == '79'
#     assert date == '2021-07-02'
#     assert val == '899'

