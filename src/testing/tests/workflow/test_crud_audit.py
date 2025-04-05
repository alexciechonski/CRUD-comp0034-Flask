from playwright.sync_api import sync_playwright, Page, expect
import pytest
from src.testing.helpers.crawl_helpers import accept_dialog
from src.utils import query_db, get_db_path
import time

# Constants for reusability
IFRAME_SRC = "iframe[src='/table-crud/']"
TABLE_ROWS = "table tbody tr"
CRUD_VIEW_URL = "http://127.0.0.1:5000/crud-view"
AUDIT_LOG_URL = "http://127.0.0.1:5000/audit-log"
TABLE_NAME = "deaths deaths.db"

def select_table(page: Page, option_text):
    page.wait_for_load_state("networkidle")

    # Step 1: Click the dropdown (inside iframe)
    iframe = page.frame_locator("iframe[src='/table-crud/']")
    dropdown = iframe.locator("#table-select")
    dropdown.wait_for(timeout=5000)
    dropdown.click(force=True)

    # Step 2: Type into the input field inside iframe
    table_input = iframe.locator("input")
    table_input.wait_for(timeout=5000)
    table_input.fill(option_text)
    page.keyboard.press("Enter")

def fill_record_form(page: Page, id_value: str, time_value: str, measured_value: str):
    page.wait_for_load_state("networkidle")
    iframe = page.frame_locator("iframe[src='/table-crud/']")
    id_input = iframe.locator("label:has-text('id') + input")
    id_input.wait_for(timeout=5000)
    id_input.fill(id_value)
    time_input = iframe.locator("label:has-text('time') + input")
    time_input.wait_for(timeout=5000)
    time_input.fill(time_value)
    val_input = iframe.locator("label:has-text('measured_value') + input")
    val_input.wait_for(timeout=5000)
    val_input.fill(measured_value)
    save_button = iframe.locator("button", has_text="Save Record")
    save_button.wait_for(timeout=5000)
    save_button.click()

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
    iframe = page.frame_locator("iframe[src='/table-crud/']")
    iframe.locator("table tbody tr").first.wait_for(timeout=3000)
    delete_button = iframe.locator("table tbody tr").last.locator("td.dash-delete-cell")
    delete_button.click()

def update_value(page: Page, new_value):
    iframe = page.frame_locator("iframe[src='/table-crud/']")
    iframe.locator("table tbody tr").first.wait_for(timeout=3000)
    last_row = iframe.locator("table tbody tr").last
    last_cell = last_row.locator("td").last
    last_cell.click()
    time.sleep(1)
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

def test_delete(page: Page):
    page.goto("http://127.0.0.1:5000/crud-view")
    page.wait_for_load_state("networkidle")
    select_table(page, "deaths deaths.db")
    delete_last_row(page)
    time.sleep(3)
    id, date, val = get_last_row(page)
    assert id == '78'
    assert date == '2021-06-25'
    assert val == '909'

    revert_last(page)
    page.goto("http://127.0.0.1:5000/crud-view")
    page.wait_for_load_state("networkidle")
    select_table(page, "deaths deaths.db")
    time.sleep(1)
    id, date, val = get_last_row(page)
    assert id == '79'
    assert date == '2021-07-02'
    assert val == '899'

def test_update(page: Page):
    page.goto("http://127.0.0.1:5000/crud-view")
    page.wait_for_load_state("networkidle")
    select_table(page, "deaths deaths.db")
    update_value(page, "1")
    time.sleep(3)
    id, date, val = get_last_row(page)
    assert id == '79'
    assert date == '2021-07-02'
    assert val == '1899'

    revert_last(page)
    page.goto("http://127.0.0.1:5000/crud-view")
    page.wait_for_load_state("networkidle")
    select_table(page, "deaths deaths.db")
    time.sleep(1)
    id, date, val = get_last_row(page)
    assert id == '79'
    assert date == '2021-07-02'
    assert val == '899'
