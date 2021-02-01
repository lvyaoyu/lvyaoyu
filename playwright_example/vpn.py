# -*- coding: UTF-8 -*-
import time

from playwright import sync_playwright

def run(playwright):
    browser = playwright.chromium.launch(headless=False)
    context = browser.newContext()

    # Open new page
    page = context.newPage()

    try:
        page.goto('http://sslvpn.amorepacific.com.cn:8080/vpns/homepage.html')
        print('VPN已经登录')
    except:
        # Go to https://sslvpn.amorepacific.com.cn/vpn/index.html
        page.goto("https://sslvpn.amorepacific.com.cn/vpn/index.html")

        # Click input[name="login"]
        page.click("input[name=\"login\"]")

        # Fill input[name="login"]
        page.fill("input[name=\"login\"]", "CN00000102")

        # Click input[name="passwd"]
        page.click("input[name=\"passwd\"]")

        # Fill input[name="passwd"]
        page.fill("input[name=\"passwd\"]", "apcm1234")

        # Press Enter
        page.press("input[name=\"passwd\"]", "Enter")
        # assert page.url == "https://sslvpn.amorepacific.com.cn/cgi/setclient?agnt"

        # Click input[name="cm"]
        # with page.expect_navigation(url="https://sslvpn.amorepacific.com.cn/vpns/f_ndisagent.html"):
        with page.expect_navigation():
            try:
                page.click("input[name=\"cm\"]")
            except:
                print('没有出现按钮')
            finally:
                for i in range(10):
                    if page.url == 'http://sslvpn.amorepacific.com.cn:8080/vpns/homepage.html':
                        print('VPN登陆成功')
                        break
                    time.sleep(1)
    finally:
        # Close page
        page.close()

        # ---------------------
        context.close()
        browser.close()

with sync_playwright() as playwright:
    run(playwright)