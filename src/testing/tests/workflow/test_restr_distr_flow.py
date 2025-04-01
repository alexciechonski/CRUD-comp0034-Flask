from playwright.sync_api import sync_playwright, Page, expect
import pytest
import time
from datetime import datetime

@pytest.fixture(scope="function")
def page():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # set headless=True if you want it hidden
        context = browser.new_context()
        page = context.new_page()
        yield page
        context.close()
        browser.close()

@pytest.mark.parametrize(
    "date, most_common, total",
    [
        ("15/06/2021", "Wfh", 1892),
        ("17/03/2020", "Wfh", 1),
        ("11/04/2021", "Wfh", 1762),
        ("11/02/2020", "No data available", 0),
        ("31/12/2022", "Wfh", 2342)
    ]
)
def test_restr_distr(page: Page, date, most_common, total):
    try:
        # Navigate to the page
        page.goto("http://127.0.0.1:5000/restriction-distribution?end_date=2022-12-31")
        
        # Wait for the page to be fully loaded
        page.wait_for_load_state("networkidle", timeout=10000)
        
        # Wait for and fill the date input
        date_input = page.locator("#endDate")  # Use ID selector instead of class
        expect(date_input).to_be_visible(timeout=5000)
        
        # Convert date format from DD/MM/YYYY to YYYY-MM-DD
        date_obj = datetime.strptime(date, "%d/%m/%Y")
        formatted_date = date_obj.strftime("%Y-%m-%d")
        
        # Fill the date input using the value attribute
        date_input.evaluate(f"el => el.value = '{formatted_date}'")
        
        # Click update and wait for the update to complete
        update_button = page.get_by_text("Update")
        update_button.click()
        
        # Wait for the update to complete
        page.wait_for_load_state("networkidle", timeout=10000)
        
        # Wait for the container to be visible first
        page.wait_for_selector(".stats-container", timeout=10000)
        
        # Then wait for stat cards
        stat_cards = page.locator(".stat-card")
        expect(stat_cards.first).to_be_visible(timeout=10000)
        
        # Verify we have the correct number of cards
        card_count = stat_cards.count()
        print(f"Found {card_count} stat cards")
        assert card_count >= 3, f"Expected at least 3 stat cards, found {card_count}"
        
        # Most Common Restriction
        most_common_card = stat_cards.nth(0)
        expect(most_common_card).to_be_visible(timeout=5000)
        restriction_type = most_common_card.locator("p").inner_text().strip()
        
        # Total Restrictions Applied
        total_restrictions_card = stat_cards.nth(1)
        expect(total_restrictions_card).to_be_visible(timeout=5000)
        total_restrs = total_restrictions_card.locator("p").inner_text().strip()
        
        # As of Date
        as_of_date_card = stat_cards.nth(2)
        expect(as_of_date_card).to_be_visible(timeout=5000)
        as_of_date = as_of_date_card.locator("p").inner_text().strip()
        
        # Convert the displayed date back to DD/MM/YYYY format for comparison
        displayed_date_obj = datetime.strptime(as_of_date, "%Y-%m-%d")
        formatted_displayed_date = displayed_date_obj.strftime("%d/%m/%Y")
        
        # Print debug information
        print(f"Input Date: {date}")
        print(f"Formatted Date: {formatted_date}")
        print(f"Most Common: {restriction_type}")
        print(f"Total: {total_restrs}")
        print(f"As of Date: {as_of_date}")
        print(f"Formatted Displayed Date: {formatted_displayed_date}")
        
        # Assertions
        assert restriction_type == most_common, f"Expected most common to be '{most_common}', got '{restriction_type}'"
        assert date == formatted_displayed_date, f"Expected date to be '{date}', got '{formatted_displayed_date}'"
        assert str(total) == total_restrs, f"Expected total to be '{total}', got '{total_restrs}'"
        
    except Exception as e:
        print(f"Test failed with error: {str(e)}")
        # Take a screenshot on failure
        page.screenshot(path=f"restr_distr_test_failure_{int(time.time())}.png")
        raise