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
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto(url)
        time.sleep(1)

        element = page.get_by_text("Lockdown 2")
        box = element.bounding_box()

        show_box(page, box['x'], box['y'])

        time.sleep(1)
        page.mouse.click(514, 267)
        time.sleep(1)

        print(page.url)

if __name__ == "__main__":
    test_workflow("http://127.0.0.1:8050/timeline")

# x': 479.838134765625, 'y': 267.6499938964844