from playwright.sync_api import sync_playwright
import time

def show_mouse(page, x, y):
    page.evaluate(f"""
        const box = document.createElement('div');
        box.style.position = 'absolute';
        box.style.left = '{x}px';
        box.style.top = '{y}px';
        box.style.border = '2px solid red';
        box.style.zIndex = '10000';
        document.body.appendChild(box);
    """)

def test_view_table(url):
    res = {}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto(url)
        time.sleep(1)

        # select custom.db
        dropdown = page.locator("#select_db")
        dropdown.click()
        time.sleep(1)
        custom_db = dropdown.get_by_text('custom.db')
        custom_db.click()
        time.sleep(3)

        # click MHCare Cluster
        cluster = page.get_by_text('MHCareCluster')
        box = cluster.bounding_box()
        x, y = box['x'] + box['width']/2, box['y'] + box['height']/2 + 10
        page.mouse.click(x, y)
        time.sleep(1)
        table = page.locator('xpath=//*[@id="erd-chart"]/div[2]/div/div').inner_text()
        res['MHCareCluster'] = table
        time.sleep(1)
        page.locator('#back-btn').click()
        time.sleep(3)





def test_add(url):
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto(url)
        time.sleep(1)

if __name__ == "__main__":
    test_view_table("http://127.0.0.1:8050/dataset")