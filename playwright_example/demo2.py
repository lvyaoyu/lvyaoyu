# -*- coding: UTF-8 -*-

from playwright import sync_playwright

def run(playwright):
    browser = playwright.webkit.launch(headless=False)
    context = browser.newContext()

    # Open new page
    page = context.newPage()

    # Go to https://www.baidu.com/
    page.goto("https://www.baidu.com/")

    # Click input[name="wd"]
    page.click("input[name=\"wd\"]")

    # Fill input[name="wd"]
    page.fill("input[name=\"wd\"]", "微博")

    # Press Enter
    page.press("input[name=\"wd\"]", "Enter")
    # assert page.url == "https://www.baidu.com/s?ie=utf-8&f=8&rsv_bp=1&rsv_idx=1&tn=baidu&wd=%E5%BE%AE%E5%8D%9A&fenlei=256&rsv_pq=863e3bd700021fda&rsv_t=4a7dwfb93S1Dyofgxa9a%2BUKiP9fX06rS7W7FQTYWNShV6JDU3Au2i27Ys3I&rqlang=cn&rsv_enter=1&rsv_dl=ib&rsv_sug3=2"

    # Click text="-随时随地发现新鲜事"
    with page.expect_popup() as popup_info:
        page.click("text=\"-随时随地发现新鲜事\"")
    page1 = popup_info.value

    # Go to https://passport.weibo.com/visitor/visitor?entry=miniblog&a=enter&url=https%3A%2F%2Fweibo.com%2F&domain=.weibo.com&sudaref=https%3A%2F%2Fwww.baidu.com%2Flink%3Furl%3DQytJwWndKUWFv42zHyf0khz8clwTm9CWwAiwHpPezzi%26wd%3D%26eqid%3Db1af15900000b38f000000045fe012bf&ua=php-sso_sdk_client-0.6.36&_rand=1608520393.7667
    page1.goto("https://passport.weibo.com/visitor/visitor?entry=miniblog&a=enter&url=https%3A%2F%2Fweibo.com%2F&domain=.weibo.com&sudaref=https%3A%2F%2Fwww.baidu.com%2Flink%3Furl%3DQytJwWndKUWFv42zHyf0khz8clwTm9CWwAiwHpPezzi%26wd%3D%26eqid%3Db1af15900000b38f000000045fe012bf&ua=php-sso_sdk_client-0.6.36&_rand=1608520393.7667")

    # Go to https://weibo.com/
    page1.goto("https://weibo.com/")

    # Click text="美女"
    page1.click("text=\"美女\"")
    # assert page1.url == "https://weibo.com/?category=10007"

    # Click input[name="16085204203272"]
    page1.click("input[name=\"16085204203272\"]")

    # Click text="冬至"
    page1.click("text=\"冬至\"")
    # assert page1.url == "https://s.weibo.com/weibo/%25E5%2586%25AC%25E8%2587%25B3?topnav=1&wvr=6&Refer=top_hot"

    # Click //img
    # with page1.expect_navigation(url="https://weibo.com/cctvxinwen?refer_flag=1001030103_"):
    with page1.expect_navigation():
        with page1.expect_popup() as popup_info:
            page1.click("//img")
        page2 = popup_info.value

    # Close page
    page2.close()

    # Close page
    page1.close()

    # Close page
    page.close()

    # ---------------------
    context.close()
    browser.close()

with sync_playwright() as playwright:
    run(playwright)