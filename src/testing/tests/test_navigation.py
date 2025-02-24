"""
Automated UI Tests for Navigation Flow.

This module contains Playwright-based tests for verifying the navigation flow
between different sections of the web application.
"""
import pytest
from playwright.sync_api import sync_playwright, Page

BASE_URL = "http://127.0.0.1:8050"

@pytest.fixture(scope="function")
def browser():
    """Setup and teardown Playwright browser instance."""
    with sync_playwright() as pw_instance:
        browser = pw_instance.chromium.launch(headless=True)
        page = browser.new_page()
        yield page
        browser.close()

@pytest.mark.parametrize("link_text, expected_url", [
    ("Dataset", f"{BASE_URL}/dataset"),
    ("Time Series", f"{BASE_URL}/time-series"),
    ("Restriction Distribution", f"{BASE_URL}/restriction-distribution"),
    ("Timeline", f"{BASE_URL}/timeline"),
])
def test_navigation(browser: Page, link_text, expected_url):
    """Test navigation flow for different sections."""
    browser.goto(BASE_URL)
    browser.get_by_text(link_text).click()
    browser.wait_for_url(expected_url)
    assert browser.url == expected_url, f"Failed to navigate to {expected_url}"
