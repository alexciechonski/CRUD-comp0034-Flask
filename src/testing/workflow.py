from playwright.sync_api import sync_playwright, Page
import time

def dropdown_select(page: Page, dropdown_id, selection):
    page.wait_for_selector(dropdown_id, timeout=5000)
    dropdown = page.locator(dropdown_id)
    dropdown.click()

    custom_db = dropdown.get_by_text(selection)
    custom_db.click()

def fillout_form(page: Page, input_id, button_id, user_input):
    page.locator(input_id).fill(user_input)
    page.locator(button_id).click()
    time.sleep(1)

def upload_data(page: Page, filepath):
    with page.expect_file_chooser() as fc_info:
        page.locator('#upload-data').click()
    file_chooser = fc_info.value
    file_chooser.set_files(filepath)

def test_workflow():
    res = ""
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto("http://127.0.0.1:8050/dataset")
        page.wait_for_load_state("networkidle")

        dropdown_select(page, "#select_db", 'custom.db')

        fillout_form(page, "#table-name-input", "#submit-create-button", "Deaths2")

        upload_data(page, "src/testing/resources/deaths.csv")

        dropdown_select(page, '#insert-to-table', 'Deaths2')
    
        page.locator('#submit-insert').click()

        # get correlation graph
        page.goto("http://127.0.0.1:8050/time-series")
        page.wait_for_load_state("networkidle")

        page.get_by_role("checkbox").check()

        dropdown_select(page, "#select-db", 'custom.db')

        dropdown_select(page, "#select-table", 'Deaths2')

        fillout_form(page, "#user-prompt", "#submit-prompt", "Explain the relationship")

        page.wait_for_selector('#llm-response')
        res += str(page.locator('#llm-response').inner_text())

        page.goto("http://127.0.0.1:8050/dataset")
        page.wait_for_load_state("networkidle")

        dropdown_select(page, "#select_db", 'custom.db')

        dropdown_select(page, "#delete-input", "Deaths2")

        page.locator('#submit-delete-button').click()

    assert res, "Explanation missing"


