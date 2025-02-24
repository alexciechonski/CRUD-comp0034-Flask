"""
Automated UI Tests for Date Selection in Restriction Distribution.

This module contains Playwright-based tests for verifying the date selection workflow
within the web application. The tests interact with year, month, and day selectors
to simulate user input and validate the expected output.

Dependencies:
- `pytest`: For test execution and parameterization.
- `sync_playwright`: For browser automation.
- `Page`: Represents a browser page instance in Playwright.
- `SELECTORS`: A dictionary of XPath selectors for date input fields.

Example Usage:
    Run all tests:
    ```sh
    pytest
    ```

    Run a specific test:
    ```sh
    pytest -k "test_workflow"
    ```
"""
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
    """
    Sets up and tears down a Playwright browser instance for testing.

    Yields:
        Page: A Playwright browser page instance.
    """
    with sync_playwright() as pw_instance:
        browser = pw_instance.chromium.launch(headless=True)
        page = browser.new_page()
        yield page
        browser.close()

def adjust_value(page: Page, button_xpath: str, times: int):
    """
    Adjusts the year, month, and day values in the UI.

    Args:
        page (Page): The Playwright browser instance.
        year_changes (tuple[int, int]):
            A tuple representing (down clicks, up clicks) for the year.
        month_changes (tuple[int, int]):
            A tuple representing (down clicks, up clicks) for the month.
        day_changes (tuple[int, int]):
            A tuple representing (up clicks, down clicks) for the day.
    """
    for _ in range(abs(times)):
        page.locator(f'xpath={button_xpath}').click()
        page.wait_for_timeout(500)  # Wait for UI update

def set_date(
    page: Page,
    year_changes: tuple[int] = (-5, 2),
    month_changes: tuple[int] =(-2, 4),
    day_changes: tuple[int] = (5, -5)
    ):
    """
    Adjusts the year, month, and day values in the UI.

    Args:
        page (Page): The Playwright browser instance.
        year_changes (tuple[int, int]):
            A tuple representing (down clicks, up clicks) for the year.
        month_changes (tuple[int, int]):
            A tuple representing (down clicks, up clicks) for the month.
        day_changes (tuple[int, int]):
            A tuple representing (up clicks, down clicks) for the day.
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

def get_selected_date(page: Page) -> dict:
    """Returns the selected year, month, and day values."""
    return {
        "year": page.locator(f'xpath={SELECTORS["year_input"]}').input_value(),
        "month": page.locator(f'xpath={SELECTORS["month_input"]}').input_value(),
        "day": page.locator(f'xpath={SELECTORS["day_input"]}').input_value(),
    }

@pytest.mark.parametrize("expected_result, year_changes, month_changes, day_changes", [
    ({"year": "2021", "month": "4", "day": "5"}, (-5, 2), (-2, 4), (5, -5))
])
def test_workflow(browser: Page, expected_result, year_changes, month_changes, day_changes):
    """
    Tests the date selection workflow using parameterized values.

    Steps:
    - Navigates to the restriction distribution page.
    - Adjusts year, month, and day values based on parameterized input.
    - Retrieves the selected date values.
    - Compares retrieved values with expected results.

    Args:
        browser (Page): The Playwright browser instance.
        expected_result (dict[str, str]): The expected date selection result.
        year_changes (tuple[int, int]): Down/up click adjustments for the year.
        month_changes (tuple[int, int]): Down/up click adjustments for the month.
        day_changes (tuple[int, int]): Up/down click adjustments for the day.

    Asserts:
        - The retrieved date values match the expected result.
    """
    browser.goto("http://127.0.0.1:8050/restriction-distribution")
    browser.wait_for_load_state("networkidle")

    # Set the date values dynamically
    set_date(browser, year_changes, month_changes, day_changes)

    # Get and validate results
    result = get_selected_date(browser)
    assert result == expected_result, f"Test Failed! Expected: {expected_result}, Got: {result}"
