from playwright.sync_api import sync_playwright
import time

def show_box(page, x, y):
    page.evaluate(f"""
        const box = document.createElement('div');
        box.style.position = 'absolute';
        box.style.left = '{x}px';
        box.style.top = '{y}px';
        box.style.border = '2px solid red';
        box.style.zIndex = '10000';
        document.body.appendChild(box);
    """)

def test_workflow(url):
    res = {}
    with sync_playwright() as pw:
        # Lockdown 2
        browser = pw.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto(url)
        time.sleep(1)

        time.sleep(1)
        page.mouse.click(514, 267)
        time.sleep(1)

        res_url = page.evaluate("document.location.href")
        res['Lockdown 2'] = res_url
        page.go_back()
        time.sleep(1)

        # Plan B
        page.mouse.click(1166, 433)
        time.sleep(1)
        res_url = page.evaluate("document.location.href")
        res["Plan B"] = res_url
        page.go_back()
        time.sleep(1)

        # Stay Alert
        page.mouse.click(199, 285)
        time.sleep(1)
        res_url = page.evaluate("document.location.href")
        res["Stay Alert"] = res_url
        page.go_back()
        time.sleep(1)

    assert res == {
        'Lockdown 2': 'https://www.gov.uk/government/publications/step-2-covid-19-restrictions-posters-12-april-2021',
        'Plan B': 'https://www.gov.uk/government/speeches/pm-statement-at-coronavirus-press-conference-29-march-2021',
        'Stay Alert': 'https://www.gov.uk/government/news/schools-colleges-and-early-years-settings-to-close'
        }


if __name__ == "__main__":
    test_workflow("http://127.0.0.1:8050/timeline")
