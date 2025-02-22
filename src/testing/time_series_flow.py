from playwright.sync_api import sync_playwright
import time
from testing.crud_actions import dropdown_select, fillout_form
import pytest

@pytest.fixture(scope="function")
def browser():
    """Setup and teardown Playwright browser instance."""
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False)
        page = browser.new_page()
        yield page 
        browser.close()

def test_series_flow(browser):
    res = ""
    browser.goto("http://127.0.0.1:8050/time-series")
    browser.wait_for_load_state("networkidle")

    dropdown_select(browser, "#restr-select", "curfew")
    dropdown_select(browser, "#restr-select", "WFH")
    dropdown_select(browser, "#restr-select", "Pubs Closed")

    browser.get_by_role("checkbox").check()

    dropdown_select(browser, "#select-db", 'custom.db')

    dropdown_select(browser, "#select-table", 'Deaths')

    fillout_form(browser, "#user-prompt", "#submit-prompt", "Explain the relationship")

    browser.wait_for_selector('#llm-response')
    res += str(browser.locator('#llm-response').inner_text())

    assert res, "Missing explanation"