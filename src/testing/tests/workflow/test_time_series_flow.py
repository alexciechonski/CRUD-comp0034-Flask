from playwright.sync_api import sync_playwright, Page, expect
import pytest
import time

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
    "table,restrictions,prompt,expected_elements",
    [
        (
            "Deaths",
            ["Wfh"],  # Single restriction
            "Explain the correlation",
            ["time_series_plot", "regression_plot", "analysis-content"]
        ),
        (
            "MHCareCluster",
            ["Wfh"],  # Single restriction
            "Analyze the relationship",
            ["time_series_plot", "regression_plot", "analysis-content"]
        ),
    ]
)
def test_time_series_analysis(page: Page, table, restrictions, prompt, expected_elements):
    """Test the complete time series analysis workflow"""
    # Navigate to the time series page
    page.goto("http://127.0.0.1:5000/time-series")
    
    # Wait for the page to load
    page.wait_for_selector("#tableSelect")
    
    # Select the table
    page.locator("#tableSelect").select_option(table)
    
    # Wait for and select restrictions using the multi-select
    page.wait_for_selector("#restrictionSelect")
    page.locator("#restrictionSelect").select_option(restrictions)
    
    # Enter analysis prompt in the textarea
    page.locator("textarea#analysisInput").fill(prompt)
    
    # Submit the form
    page.locator("button.submit-button").click()
    
    # Wait for analysis to complete and verify results
    for element in expected_elements:
        if element == "time_series_plot":
            expect(page.locator(".js-plotly-plot")).to_be_visible(timeout=10000)
        elif element == "regression_plot":
            expect(page.locator(".js-plotly-plot")).to_be_visible(timeout=10000)
        elif element == "analysis-content":
            expect(page.locator(".analysis-content")).to_be_visible(timeout=10000)
            content = page.locator(".analysis-content").inner_text()
            assert content != "", "Analysis content should not be empty"

def test_empty_form_submission(page: Page):
    """Test form validation when submitting without required fields"""
    # Navigate to the time series page
    page.goto("http://127.0.0.1:5000/time-series")
    
    # Wait for the form to load
    page.wait_for_selector("form")
    
    # Submit the form without filling in any fields
    page.locator("form").evaluate("form => form.submit()")
    
    # Wait for and verify the error message
    error_div = page.locator(".alert.alert-danger.mt-4")
    expect(error_div).to_be_visible()
    expect(error_div).to_contain_text("Please fill in all required fields")

def test_prompt_input(page: Page):
    """Test that the prompt input works correctly"""
    page.goto("http://127.0.0.1:5000/time-series")
    
    # Find the prompt input
    prompt_input = page.locator("textarea#analysisInput")
    expect(prompt_input).to_be_visible()
    
    # Test input
    test_prompt = "Test analysis prompt"
    prompt_input.fill(test_prompt)
    
    # Get the value and verify it was set correctly
    value = prompt_input.input_value()
    assert value == test_prompt, "Prompt input should contain entered text"
