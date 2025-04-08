from playwright.sync_api import Page

def insert_data(page: Page, table_name, file_path):
    page.locator("#insert-table-select").select_option(table_name)
    with page.expect_file_chooser() as fc_info:
        page.locator('#csv-file').click()
    file_chooser = fc_info.value
    file_chooser.set_files(file_path)
    page.get_by_text("UPLOAD AND INSERT DATA").click()

def create_new_table(page: Page, db_name):
    page.locator("table-name-input").fill(db_name)
    page.get_by_text("CREATE TABLE").click()

def delete_table(page: Page, table_name):
    page.on("dialog", accept_dialog)
    page.locator("#delete-table-select").select_option(table_name)
    page.get_by_text("DELETE TABLE").click()

def get_schema_contents(page: Page, table_name):
    # Wait for the table section to be visible
    page.wait_for_selector(".table-section", timeout=5000)

    # Find all table sections
    table_sections = page.locator(".table-section").all()

    if not table_sections:
        print("No table sections found. Page content:")
        print(page.content())
        raise ValueError("No table sections found on the page")

    # Find the section with matching heading
    target_section = None
    found_headings = []
    for section in table_sections:
        try:
            # Get the heading (h4 instead of h3)
            heading = section.locator("h4").inner_text()
            found_headings.append(heading)
            if heading == table_name:
                target_section = section
                break
        except Exception as e:
            print(f"Error getting heading: {e}")
            continue

    if not found_headings:
        print("No headings found. Section HTML:")
        for section in table_sections:
            print(section.inner_html())
        raise ValueError("No table headings found in any section")

    if not target_section:
        raise ValueError(f"Table '{table_name}' not found. Available tables: {', '.join(found_headings)}")

    try:
        # Get all rows from the table
        rows = target_section.locator(".table-responsive table tbody tr").all()
        schema = []

        for row in rows:
            # Get the cells from each row
            cells = row.locator("td").all()
            if len(cells) == 3:  # Make sure we have all three columns
                column_info = {
                    "name": cells[0].inner_text(),
                    "type": cells[1].inner_text(),
                    "constraints": cells[2].inner_text()
                }
                schema.append(column_info)

        return schema

    except Exception as e:
        print(f"Error getting table content: {e}")
        raise

def get_table_schemas(page: Page):
    """
    Gets all table schemas from the dataset page.
    Returns a dictionary mapping table names to their schemas.
    """
    # Wait for the table section to be visible
    page.wait_for_selector(".table-section", timeout=5000)

    # Get all table sections
    table_sections = page.locator(".table-section").all()

    schemas = {}
    for section in table_sections:
        # Get table name from the section
        table_name = section.locator("h3").inner_text()

        # Get all column definitions
        columns = section.locator(".column-definition").all()
        schema = []

        for column in columns:
            # Extract column name and type
            col_text = column.inner_text()
            name, col_type = col_text.split(": ")
            schema.append({
                "name": name,
                "type": col_type
            })

        schemas[table_name] = schema

    return schemas

def accept_dialog(dialog):
    dialog.accept()

def dialog_appeared(dialog):
    return dialog.message is not None and dialog.message != ""
