"""
Module for handling UI interactions using Playwright.

This module provides utility functions for interacting with a web application
through Playwright, including dropdown selection, form filling, file uploads,
and waiting for page elements to load.
"""
from playwright.sync_api import Page

def dropdown_select(page: Page, dropdown_id: str, selection: str) -> None:
    """
    Selects an option from a dropdown menu.

    Args:
        page (Page): The Playwright page instance.
        dropdown_id (str): The CSS selector for the dropdown element.
        selection (str): The text of the option to select.
    """
    page.wait_for_selector(dropdown_id, timeout=5000)
    dropdown = page.locator(dropdown_id)
    dropdown.click()

    custom_db = dropdown.get_by_text(selection)
    custom_db.click()

def fillout_form(page: Page, input_id: str, button_id: str, user_input: str) -> None:
    """
    Fills out an input field and clicks a button to submit the form.

    Args:
        page (Page): The Playwright page instance.
        input_id (str): The CSS selector for the input field.
        button_id (str): The CSS selector for the submit button.
        user_input (str): The text to enter into the input field.
    """
    page.locator(input_id).fill(user_input)
    page.locator(button_id).click()

def upload_data(page: Page, filepath: str) -> None:
    """
    Uploads a file via a file input.

    Args:
        page (Page): The Playwright page instance.
        filepath (str): The path to the file to be uploaded.
    """
    with page.expect_file_chooser() as fc_info:
        page.locator('#upload-data').click()
    file_chooser = fc_info.value
    file_chooser.set_files(filepath)

def load_all(page: Page) -> None:
    """
    Waits until the database selection dropdown has finished loading.

    Args:
        page (Page): The Playwright page instance.
    """
    page.wait_for_function(
        "document.querySelector('#select_db').getAttribute('data-dash-is-loading') === null"
        )
    