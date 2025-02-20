from playwright.sync_api import sync_playwright
import time

def test_workflow(url):
    year_up = '//*[@id="input-year"]/div/span/b[1]'
    year_down = '//*[@id="input-year"]/div/span/b[2]'
    month_up = '//*[@id="input-month"]/div/span/b[1]'
    month_down = '//*[@id="input-month"]/div/span/b[2]'
    day_up = '//*[@id="input-day"]/div/span/b[1]'
    day_down = '//*[@id="input-day"]/div/span/b[2]'

    res = {}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto(url)
        time.sleep(1)
        # year
        for _ in range(5):
            page.locator(f'xpath={year_down}').click()
            time.sleep(1)

        for _ in range(2):
            page.locator(f'xpath={year_up}').click()
            time.sleep(1)
        res['year'] = page.locator('xpath=//*[@id="input-year"]/div/span/input').input_value()


        # month 
        for _ in range(2):
            page.locator(f'xpath={month_down}').click()
            time.sleep(1)

        for _ in range(4):
            page.locator(f'xpath={month_up}').click()
            time.sleep(1)
        res['month'] = page.locator('xpath=//*[@id="input-month"]/div/span/input').input_value()


        # day
        for _ in range(5):
            page.locator(f'xpath={day_up}').click()
            time.sleep(1)

        for _ in range(5):
            page.locator(f'xpath={day_down}').click()
            time.sleep(1)
        res['day'] = page.locator('xpath=//*[@id="input-day"]/div/span/input').input_value()

        time.sleep(1)
        browser.close()

    assert res == {'year': '2021', 'month': '4', 'day': '5'}


if __name__ == "__main__":
    test_workflow("http://127.0.0.1:8050/restriction-distribution")
