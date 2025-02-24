from playwright.sync_api import Page

def dropdown_select(page: Page, dropdown_id, selection):
    page.wait_for_selector(dropdown_id, timeout=5000)
    dropdown = page.locator(dropdown_id)
    dropdown.click()

    custom_db = dropdown.get_by_text(selection)
    custom_db.click()

def fillout_form(page: Page, input_id, button_id, user_input):
    page.locator(input_id).fill(user_input)
    page.locator(button_id).click()

def upload_data(page: Page, filepath):
    with page.expect_file_chooser() as fc_info:
        page.locator('#upload-data').click()
    file_chooser = fc_info.value
    file_chooser.set_files(filepath)

def load_all(page: Page):
    page.wait_for_function(
        "document.querySelector('#select_db').getAttribute('data-dash-is-loading') === null"
        )
    