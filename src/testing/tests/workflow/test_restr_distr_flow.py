from playwright.sync_api import Page, expect
import pytest
from datetime import datetime

def fill_date_and_submit(page: Page, date: str):
    # Convert date to YYYY-MM-DD
    formatted = datetime.strptime(date, "%d/%m/%Y").strftime("%Y-%m-%d")

    # Fill date input directly via JS
    date_input = page.locator("#endDate")
    expect(date_input).to_be_visible(timeout=5000)
    date_input.evaluate(f"el => el.value = '{formatted}'")

    # Click "Update"
    page.get_by_text("Update").click()

def get_stat_card_text(page: Page, index: int) -> str:
    card = page.locator(".stat-card").nth(index)
    expect(card).to_be_visible(timeout=5000)
    return card.locator("p").inner_text().strip()

@pytest.mark.parametrize(
    "date, most_common, total",
    [
        ("15/06/2021", "Wfh", 1892),
        ("17/03/2020", "Wfh", 1),
        ("11/04/2021", "Wfh", 1762),
        ("11/02/2020", "No data available", 0),
        ("31/12/2022", "Wfh", 2342),
    ]
)
def test_restr_distr(page: Page, date, most_common, total):
    page.goto("http://127.0.0.1:5000/restriction-distribution?end_date=2022-12-31")
    page.wait_for_load_state("networkidle")

    fill_date_and_submit(page, date)

    # Wait for stats
    expect(page.locator(".stats-container")).to_be_visible(timeout=10000)
    stat_cards = page.locator(".stat-card")
    expect(stat_cards.first).to_be_visible(timeout=5000)
    assert stat_cards.count() >= 3

    # Extract card values
    restriction_type = get_stat_card_text(page, 0)
    total_restrs = get_stat_card_text(page, 1)
    as_of_date_str = get_stat_card_text(page, 2)

    # Validate values
    displayed_date = datetime.strptime(as_of_date_str, "%Y-%m-%d").strftime("%d/%m/%Y")
    assert restriction_type == most_common, f"Expected most common: '{most_common}', got: '{restriction_type}'"
    assert displayed_date == date, f"Expected date: '{date}', got: '{displayed_date}'"
    assert str(total) == total_restrs, f"Expected total: '{total}', got: '{total_restrs}'"
