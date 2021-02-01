# -*- coding: UTF-8 -*-
from playwright import sync_playwright
from pandas import DataFrame


def run(playwright):
    browser = playwright.chromium.launch(headless=False)
    context = browser.newContext()

    # Open new page
    page = context.newPage()

    # Go to http://www.infoccsp.com/sso/sso-login.do
    page.goto("http://www.infoccsp.com/sso/sso-login.do")

    # Click input[name="companyCode"]
    page.click("input[name=\"companyCode\"]")

    # Fill input[name="companyCode"]
    page.fill("input[name=\"companyCode\"]", "HAXSHAAG")

    # Fill input[name="username"]
    page.fill("input[name=\"username\"]", "haxsha009")

    # Fill input[name="password"]
    page.fill("input[name=\"password\"]", "ccsp8888")

    page.on("dialog", lambda dialog: dialog.accept())

    # Go to http://www.infoccsp.com/sso/ui-agent_index.do
    page.click("//a[@id='btnLogin']")

    page2 = context.newPage()

    page2.goto("http://www.infoccsp.com/iportal/servicecenter/cargotracking.aspx")

    # Fill input[type="text"]
    page2.fill("input[type=\"text\"]", "112-84092396")

    # Click text=/.*查询.*/
    page2.click("text=/.*查询.*/")
    # assert page1.url == "http://www.infoccsp.com/iportal/servicecenter/cargotracking.aspx?ID=112-8409239%206,"

    page2.waitForLoadState(state="networkidle")
    page2.screenshot(path='img/%s.png'%('112-84092396'))
    # ths = page2.querySelectorAll('//*[@id="tbcargostatus"]/thead/tr/th')
    # columns = [i.textContent().strip() for i in ths]
    # trs = page2.querySelectorAll('//*[@id="tbcargostatus"]/tbody/tr')
    # data = []
    # for tr in trs:
    #     tds = tr.querySelectorAll('td')
    #     data.append([td.textContent().strip() if td.textContent().strip() else '' for td in tds])
    #
    # df = DataFrame(data=data,columns=columns)
    # df.to_excel('data/112-84092396.xlsx')

    # print(columns)
    # print(data)
    # Close page
    page2.close()

    # Close page
    page.close()

    # ---------------------
    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)
