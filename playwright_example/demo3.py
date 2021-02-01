import time

from playwright import sync_playwright

with sync_playwright() as p:
    # for browser_type in [p.chromium, p.firefox, p.webkit]:
    for browser_type in [p.chromium]:
        browser = browser_type.launch(headless=False)
        context = browser.newContext()
        page = context.newPage()

        page.goto('https://baidu.com/')
        # page.click('//input[@id="kw"]')
        page.fill('//input[@id="kw"]','python')
        page.press('//input[@id="kw"]','Enter')
        page.screenshot(path=f'example-{browser_type.name}.png')

        page.close()
        context.close()
        browser.close()
