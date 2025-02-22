from playwright.sync_api import sync_playwright
import time
import pytest

def test_workflow():
    res = {}

    def click_timeline(node_name):
        node = page.get_by_text(node_name)
        box = node.bounding_box()
        x, y = box['x'] + box['width']/2, box['y'] + box['height']/2 + 10
        with page.expect_navigation():
            page.mouse.click(x, y)
        page.wait_for_load_state("networkidle")
        res_url = page.evaluate("document.location.href")
        page.wait_for_load_state("networkidle")
        res[node_name] = res_url
        page.goto("http://127.0.0.1:8050/timeline")
        page.wait_for_load_state("networkidle")

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto("http://127.0.0.1:8050/timeline")
        page.wait_for_load_state("networkidle")

        click_timeline("Lockdown 2")

        click_timeline("Plan B")

        click_timeline("Stay Alert")

    assert res == {
        'Lockdown 2': 'https://www.gov.uk/government/publications/step-2-covid-19-restrictions-posters-12-april-2021',
        'Plan B': 'https://www.gov.uk/government/speeches/pm-statement-at-coronavirus-press-conference-29-march-2021',
        'Stay Alert': 'https://www.gov.uk/government/news/schools-colleges-and-early-years-settings-to-close'
        }, "Incorrect Urls"
