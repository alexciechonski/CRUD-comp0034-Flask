from playwright.sync_api import sync_playwright
import time
from testing.crud_actions import dropdown_select, fillout_form

def test_series_flow():
    res = ""
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto("http://127.0.0.1:8050/time-series")
        page.wait_for_load_state("networkidle")

        dropdown_select(page, "#restr-select", "curfew")
        dropdown_select(page, "#restr-select", "WFH")
        dropdown_select(page, "#restr-select", "Pubs Closed")

        page.get_by_role("checkbox").check()

        dropdown_select(page, "#select-db", 'custom.db')

        dropdown_select(page, "#select-table", 'Deaths')

        fillout_form(page, "#user-prompt", "#submit-prompt", "Explain the relationship")

        page.wait_for_selector('#llm-response')
        res += str(page.locator('#llm-response').inner_text())

    assert res, "Missing explanation"