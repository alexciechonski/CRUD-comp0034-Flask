from playwright.sync_api import sync_playwright, Page
import pytest

@pytest.fixture(scope="function")
def browser():
    """Setup and teardown Playwright browser instance."""
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False)
        page = browser.new_page()
        yield page 
        browser.close()

def click_timeline(page: Page, node_name):
    node = page.get_by_text(node_name)
    box = node.bounding_box()
    x, y = box['x'] + box['width']/2, box['y'] + box['height']/2 + 10
    with page.expect_navigation():
        page.mouse.click(x, y)
    page.wait_for_load_state("networkidle")
    res_url = page.evaluate("document.location.href")
    page.wait_for_load_state("networkidle")
    page.goto("http://127.0.0.1:8050/timeline")
    page.wait_for_load_state("networkidle")
    return res_url

@pytest.mark.parametrize("node_name, expected_url", [
    ("Lockdown 2", "https://www.gov.uk/government/publications/step-2-covid-19-restrictions-posters-12-april-2021"),
    ("Plan B", "https://www.gov.uk/government/speeches/pm-statement-at-coronavirus-press-conference-29-march-2021"),
    ("Stay Alert", "https://www.gov.uk/government/news/schools-colleges-and-early-years-settings-to-close"),
])
def test_timeline_navigation(browser, node_name, expected_url):
    """Tests timeline event navigation for different scenarios."""
    browser.goto("http://127.0.0.1:8050/timeline")
    result_url = click_timeline(browser, node_name)
    assert result_url == expected_url, f"URL mismatch for {node_name}: Expected {expected_url}, got {result_url}"