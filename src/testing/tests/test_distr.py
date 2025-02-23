import pytest
from playwright.sync_api import sync_playwright, Page

# Define XPath selectors
SELECTORS = {
    "year_up": '//*[@id="input-year"]/div/span/b[1]',
    "year_down": '//*[@id="input-year"]/div/span/b[2]',
    "month_up": '//*[@id="input-month"]/div/span/b[1]',
    "month_down": '//*[@id="input-month"]/div/span/b[2]',
    "day_up": '//*[@id="input-day"]/div/span/b[1]',
    "day_down": '//*[@id="input-day"]/div/span/b[2]',
    "year_input": '//*[@id="input-year"]/div/span/input',
    "month_input": '//*[@id="input-month"]/div/span/input',
    "day_input": '//*[@id="input-day"]/div/span/input',
}

@pytest.fixture(scope="function")
def browser():
    """Fixture to set up Playwright and browser instance."""
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page()
        yield page
        browser.close()

def adjust_value(page: Page, button_xpath: str, times: int):
    """Clicks a button multiple times to adjust a date value."""
    for _ in range(abs(times)):
        page.locator(f'xpath={button_xpath}').click()
        page.wait_for_timeout(500)  # Wait for UI update

def set_date(page: Page, year_changes=(-5, 2), month_changes=(-2, 4), day_changes=(5, -5)):
    """
    Adjusts the year, month, and day.
    :param year_changes: Tuple (down clicks, up clicks)
    :param month_changes: Tuple (down clicks, up clicks)
    :param day_changes: Tuple (up clicks, down clicks)
    """
    # Adjust year
    adjust_value(page, SELECTORS["year_down"], year_changes[0])
    adjust_value(page, SELECTORS["year_up"], year_changes[1])

    # Adjust month
    adjust_value(page, SELECTORS["month_down"], month_changes[0])
    adjust_value(page, SELECTORS["month_up"], month_changes[1])

    # Adjust day
    adjust_value(page, SELECTORS["day_up"], day_changes[0])
    adjust_value(page, SELECTORS["day_down"], day_changes[1])

def get_selected_date(page: Page):
    """Returns the selected year, month, and day values."""
    return {
        "year": page.locator(f'xpath={SELECTORS["year_input"]}').input_value(),
        "month": page.locator(f'xpath={SELECTORS["month_input"]}').input_value(),
        "day": page.locator(f'xpath={SELECTORS["day_input"]}').input_value(),
    }

@pytest.mark.parametrize("expected_result, year_changes, month_changes, day_changes", [
    ({"year": "2021", "month": "4", "day": "5"}, (-5, 2), (-2, 4), (5, -5))
])
def test_workflow(browser, expected_result, year_changes, month_changes, day_changes):
    """Test the date selection workflow with a single test case."""
    browser.goto("http://127.0.0.1:8050/restriction-distribution")
    browser.wait_for_load_state("networkidle")

    # Set the date values dynamically
    set_date(browser, year_changes, month_changes, day_changes)

    # Get and validate results
    result = get_selected_date(browser)
    assert result == expected_result, f"Test Failed! Expected: {expected_result}, Got: {result}"
