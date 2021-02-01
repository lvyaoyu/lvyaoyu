# -*- coding: UTF-8 -*-
from playwright import sync_playwright
import time


def run(playwright):
    browser = playwright.chromium.launch(headless=False)
    # 创建一个新的浏览器上下文。 它不会与其他浏览器上下文共享cookie / 缓存。
    context = browser.newContext()

    # Open new page
    # 在浏览器上下文中创建一个新页面。
    page = context.newPage()

    # Go to https://www.baidu.com/
    page.goto("https://www.baidu.com/")



    # Click input[name="wd"]
    # page.click("input[name=\"wd\"]")
    page.click('//input[@id="kw"]')

    # Fill input[name="wd"]
    # page.fill("input[name=\"wd\"]", "python")
    page.fill('//input[@id="kw"]', "python")


    # Press Enter
    # with page.expect_navigation(url="https://www.baidu.com/s?ie=utf-8&f=8&rsv_bp=1&rsv_idx=1&tn=baidu&wd=python&fenlei=256&rsv_pq=9c65ef080009a478&rsv_t=e0acsJaKyWhE30dcUDuy5BxzLnNuBV4z0eTaL4syoyux%2F%2FkCzG%2F%2Fq%2B30nDQ&rqlang=cn&rsv_enter=1&rsv_dl=tb&rsv_sug3=7&rsv_sug1=1&rsv_sug7=100&rsv_sug2=0&rsv_btype=i&inputT=3178&rsv_sug4=8331"):
    with page.expect_navigation():
        # page.press("input[name=\"wd\"]", "Enter")
        page.press('//input[@id="kw"]', "Enter")

    time.sleep(10)

    # Close page
    page.close()

    # ---------------------
    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)

# 安装驱动'python -m playwright install'
# python -m playwright codegen --help
#我们通过下面命令打开Chrome浏览器开始录制脚本
#指定生成语言为:Python（默认Python，可选）
#保存的文件名：1.py（可选）
#浏览器驱动：webkit（默认webkit，可选）
#最后跟着要打开的目标网站（默认仅仅是打开浏览器，可选）
# python -m playwright codegen --target python -o 'qwe.py' -b chromium https://www.baidu.com

# 打包成exe文件 pyinstaller -D laiketui.py --add-data ../venv/Lib/site-packages/playwright/driver;playwright/driver