"""
Automated UI Tests for Dataset Workflow.

This module contains Playwright-based tests to verify the end-to-end workflow
of dataset creation, data insertion, correlation analysis, and deletion
within the web application.
"""
from playwright.sync_api import sync_playwright, Page
import pytest
from testing.helpers.crud_actions import load_all

@pytest.fixture(scope="function")
def browser():
    """Setup and teardown Playwright browser instance."""
    with sync_playwright() as pw_instance:
        browser = pw_instance.chromium.launch(headless=True)
        page = browser.new_page()
        yield page
        browser.close()

def dropdown_select(page: Page, dropdown_id: str, selection: str):
    """
    select a given value from dropdown
    """
    page.wait_for_selector(dropdown_id, timeout=5000)
    dropdown = page.locator(dropdown_id)
    dropdown.click()

    custom_db = dropdown.get_by_text(selection)
    custom_db.click()

def fillout_form(page: Page, input_id: str, button_id: str, user_input: str):
    """
    fillout a form consisting of text input and submit button
    """
    page.locator(input_id).fill(user_input)
    page.locator(button_id).click()

def upload_data(page: Page, filepath):
    """
    upload data
    """
    with page.expect_file_chooser() as fc_info:
        page.locator('#upload-data').click()
    file_chooser = fc_info.value
    file_chooser.set_files(filepath)

def test_workflow(browser: Page):
    """
    Test the complete workflow
    """
    res = ""
    browser.goto("http://127.0.0.1:8050/dataset")
    browser.wait_for_load_state("networkidle")

    dropdown_select(browser, "#select_db", 'custom.db')
    load_all(browser)

    fillout_form(browser, "#table-name-input", "#submit-create-button", "Deaths2")

    upload_data(browser, "src/testing/resources/deaths.csv")

    dropdown_select(browser, '#insert-to-table', 'Deaths2')

    browser.locator('#submit-insert').click()

    # get correlation graph
    browser.goto("http://127.0.0.1:8050/time-series")
    browser.wait_for_load_state("networkidle")

    browser.get_by_role("checkbox").check()

    dropdown_select(browser, "#select-db", 'custom.db')

    dropdown_select(browser, "#select-table", 'Deaths2')

    fillout_form(browser, "#user-prompt", "#submit-prompt", "Explain the relationship")

    browser.wait_for_function(
        """document.querySelector('#llm-response')
        && document.querySelector('#llm-response').innerText.length > 0""",
        timeout=30000
    )
    res += str(browser.locator('#llm-response').inner_text())

    browser.goto("http://127.0.0.1:8050/dataset")
    browser.wait_for_load_state("networkidle")

    dropdown_select(browser, "#select_db", 'custom.db')
    load_all(browser)

    dropdown_select(browser, "#delete-input", "Deaths2")

    browser.locator('#submit-delete-button').click()

    assert res, "Explanation missing"
