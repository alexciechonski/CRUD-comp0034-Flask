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
    iframe = page.frame_locator(IFRAME_SRC)
    dropdown = iframe.locator("#table-select")
    dropdown.wait_for(timeout=5000)
    dropdown.click(force=True)
    table_input = iframe.locator("input")
    table_input.wait_for(timeout=5000)
    table_input.fill(option_text)
    page.keyboard.press("Enter")

def fill_record_form(page: Page, id_value: str, time_value: str, measured_value: str):
    page.wait_for_load_state("networkidle")
    iframe = page.frame_locator(IFRAME_SRC)
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
    iframe = page.frame_locator(IFRAME_SRC)
    last_row = iframe.locator(TABLE_ROWS).last
    cells = last_row.locator("td")
    cells.first.wait_for(timeout=5000)
    cell_values = [cells.nth(i).inner_text() for i in range(cells.count())]    
    return cell_values[2], cell_values[3], cell_values[4]

def check_last_row(page, exp_id, exp_date, exp_val):
    id, date, val = get_last_row(page)
    assert exp_id == id
    assert exp_date == date
    assert exp_val == val

def revert_last(page: Page):
    page.goto(AUDIT_LOG_URL)
    page.wait_for_load_state("networkidle")
    page.once("dialog", lambda dialog: dialog.accept())
    button_path = 'xpath=/html/body/main/div/div[1]/div[2]/div[2]/form/button'
    page.wait_for_selector(button_path)
    revert_button = page.locator(button_path)
    revert_button.click()

def delete_last_row(page: Page):
    page.wait_for_load_state("networkidle")
    iframe = page.frame_locator(IFRAME_SRC)
    iframe.locator(TABLE_ROWS).first.wait_for(timeout=3000)
    delete_button = iframe.locator(TABLE_ROWS).last.locator("td.dash-delete-cell")
    delete_button.click()

def update_value(page: Page, new_value):
    iframe = page.frame_locator(IFRAME_SRC)
    iframe.locator(TABLE_ROWS).first.wait_for(timeout=3000)
    last_row = iframe.locator(TABLE_ROWS).last
    last_cell = last_row.locator("td").last
    last_cell.click()
    page.keyboard.press("Control+A")
    page.keyboard.type(new_value)
    page.keyboard.press("Enter")
    
def test_add(page: Page):
    """Test adding a record"""
    page.goto(CRUD_VIEW_URL)
    page.wait_for_load_state("networkidle")
    select_table(page, TABLE_NAME)
    fill_record_form(page, '80', '2021-07-15', '1000')
    check_last_row(page, '80', '2021-07-15', '1000')

    revert_last(page)
    page.goto(CRUD_VIEW_URL)
    page.wait_for_load_state("networkidle")
    select_table(page, TABLE_NAME)
    check_last_row(page, '79', '2021-07-02', '899')

def test_delete(page: Page):
    page.goto(CRUD_VIEW_URL)
    page.wait_for_load_state("networkidle")
    select_table(page, TABLE_NAME)
    delete_last_row(page)
    check_last_row(page, '78', '2021-06-25', '909')

    revert_last(page)
    page.goto(CRUD_VIEW_URL)
    page.wait_for_load_state("networkidle")
    select_table(page, TABLE_NAME)
    check_last_row(page, '79', '2021-07-02', '899')

def test_update(page: Page):
    page.goto(CRUD_VIEW_URL)
    page.wait_for_load_state("networkidle")
    select_table(page, TABLE_NAME)
    update_value(page, "1")
    check_last_row(page, '79', '2021-07-02', '1899')

    revert_last(page)
    page.goto(CRUD_VIEW_URL)
    page.wait_for_load_state("networkidle")
    select_table(page, TABLE_NAME)
    check_last_row(page, '79', '2021-07-02', '899')
