# -*- coding: UTF-8 -*-
import time
import datetime
from pandas import DataFrame
from playwright import sync_playwright
import asyncio
import os
from playwright_example.logger import *

from common import *
import utility


def process_ccsp(ccsp_values):
    if not ccsp_values:
        return
    with sync_playwright() as playwright:
        browser_type = playwright.chromium
        executablePath = r'ms-playwright\chromium-833159\chrome-win\chrome.exe'
        browser = browser_type.launch(headless=False,executablePath=executablePath)
        context = browser.newContext()

        # Open new page
        page = context.newPage()
        page.setViewportSize(1920, 1040)

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
        page2.setViewportSize(1920, 1040)

        page2.goto("http://www.infoccsp.com/iportal/servicecenter/cargotracking.aspx")

        for waybills_number in ccsp_values:
            # Fill input[type="text"]
            page2.press('input[type=\"text\"]', 'Control+A')
            page2.press('input[type=\"text\"]', 'Backspace')
            page2.fill("input[type=\"text\"]", waybills_number)

            # Click text=/.*查询.*/
            page2.click("text=/.*查询.*/")
            # assert page1.url == "http://www.infoccsp.com/iportal/servicecenter/cargotracking.aspx?ID=112-8409239%206,"

            page2.waitForLoadState(state="networkidle")
            page2.screenshot(path=f'{hx_path}/%s.png' % waybills_number)
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


def process_tang(tang_values):
    if not tang_values:
        return
    with sync_playwright() as playwright:
        browser_type = playwright.chromium
        executablePath = r'ms-playwright\chromium-833159\chrome-win\chrome.exe'
        browser = browser_type.launch(headless=False,executablePath=executablePath)
        context = browser.newContext()

        # Open new page
        page = context.newPage()
        page.setViewportSize(1920, 1040)

        # Go to http://tang.csair.com/WebFace/Tang.WebFace.Cargo/AgentAwbBrower.aspx?menuID=1
        page.goto("http://tang.csair.com/WebFace/Tang.WebFace.Cargo/AgentAwbBrower.aspx?menuID=1")

        for waybills_number in tang_values:
            prefix = waybills_number.split('-')[0]
            suffix = waybills_number.split('-')[-1]

            # Click input[name="ctl00$ContentPlaceHolder1$txtPrefix"]
            page.click("input[name=\"ctl00$ContentPlaceHolder1$txtPrefix\"]")
            # Fill input[name="ctl00$ContentPlaceHolder1$txtPrefix"]
            page.press("input[name=\"ctl00$ContentPlaceHolder1$txtPrefix\"]", 'Control+A')
            page.press("input[name=\"ctl00$ContentPlaceHolder1$txtPrefix\"]", 'Backspace')
            page.fill("input[name=\"ctl00$ContentPlaceHolder1$txtPrefix\"]", prefix)

            # Click input[name="ctl00$ContentPlaceHolder1$txtNo"]
            page.click("input[name=\"ctl00$ContentPlaceHolder1$txtNo\"]")

            # Fill input[name="ctl00$ContentPlaceHolder1$txtNo"]
            page.press("input[name=\"ctl00$ContentPlaceHolder1$txtNo\"]", 'Control+A')
            page.press("input[name=\"ctl00$ContentPlaceHolder1$txtNo\"]", 'Backspace')
            page.fill("input[name=\"ctl00$ContentPlaceHolder1$txtNo\"]", suffix)

            # Press Enter
            page.click("//input[@id='btnSearch']")
            # assert page.url == "http://tang.csair.com/WebFace/Tang.WebFace.Cargo/AgentAwbBrower.aspx?menuID=1"

            page.waitForLoadState(state="domcontentloaded")
            time.sleep(10)
            page.screenshot(path=f'{hx_path}/%s.png' % waybills_number)

        # Close page
        page.close()

        # ---------------------
        context.close()
        browser.close()


def process_cargo(cargo_values):
    if not cargo_values:
        return
    with sync_playwright() as playwright:
        browser_type = playwright.chromium
        executablePath = r'ms-playwright\chromium-833159\chrome-win\chrome.exe'
        browser = browser_type.launch(headless=False,executablePath=executablePath)
        context = browser.newContext()

        # Open new page
        page = context.newPage()
        page.setViewportSize(1920, 1040)

        # Go to https://cargo.china-airlines.com/CCNetv2/content/manage/ShipmentTracking.aspx
        page.goto("https://cargo.china-airlines.com/CCNetv2/content/manage/ShipmentTracking.aspx")

        for waybills_number in cargo_values:
            suffix = waybills_number.split('-')[-1]
            # Click input[name="ctl00$ContentPlaceHolder1$txtAwbNum"]
            page.click("input[name=\"ctl00$ContentPlaceHolder1$txtAwbNum\"]")

            # Fill input[name="ctl00$ContentPlaceHolder1$txtAwbNum"]
            page.press("input[name=\"ctl00$ContentPlaceHolder1$txtAwbNum\"]", 'Control+A')
            page.press("input[name=\"ctl00$ContentPlaceHolder1$txtAwbNum\"]", 'Backspace')
            page.fill("input[name=\"ctl00$ContentPlaceHolder1$txtAwbNum\"]", suffix)

            # Click input[name="ctl00$ContentPlaceHolder1$btnSearch"]
            page.click("input[name=\"ctl00$ContentPlaceHolder1$btnSearch\"]")
            # assert page.url == "https://cargo.china-airlines.com/CCNetv2/content/manage/ShipmentTracking.aspx"

            page.waitForLoadState(state="networkidle")
            page.screenshot(path=f'{hx_path}/%s.png' % waybills_number)

        # Close page
        page.close()

        # ---------------------
        context.close()
        browser.close()


def run_hss(account_number,password):
    with sync_playwright() as playwright:
        browser_type = playwright.chromium
        executablePath = r'ms-playwright\chromium-833159\chrome-win\chrome.exe'
        browser = browser_type.launch(headless=False,executablePath=executablePath)
        context = browser.newContext()

        # Open new page
        page = context.newPage()
        page.setViewportSize(1920, 1040)

        # Go to http://hss.forwarder365.com/forwarder/login.do
        page.goto("http://hss.forwarder365.com/forwarder/login.do")

        # Click input[name="code"]
        page.click("input[name=\"code\"]")

        # Fill input[name="code"]
        # page.fill("input[name=\"code\"]", "testyn")
        page.fill("input[name=\"code\"]", account_number)

        # Fill input[name="password"]
        # page.fill("input[name=\"password\"]", "12345678")
        page.fill("input[name=\"password\"]", password)

        # Go to http://hss.forwarder365.com/forwarder/console.do
        page.press("input[name=\"password\"]", "Enter")

        page.waitForLoadState()

        # Click text=/.*出口订单查询.*/
        page.click("text=/.*出口订单.*/")
        # page.hover("text=/.*出口订单.*/")
        page.click("text=/.*出口订单查询.*/")
        # assert page.url == "http://hss.forwarder365.com/forwarder/order/export/query.do"
        page.selectOption('//select[@id="pageSize"]', '8000')

        page.click('//input[@id="flightDateStart"]')
        page.click('//td[@class="today day"]/preceding-sibling::td[1]')
        page.click('//input[@id="flightDateEnd"]')
        page.click('//td[@class="today day"]')

        page.click("//label[normalize-space(.)='通过']/span")

        # Click text=/.*查询订单.*/
        page.click("text=/.*查询订单.*/")
        page.waitForLoadState(state="networkidle")
        # assert page.url == "http://hss.forwarder365.com/forwarder/order/export/doQuery.do?pageSize=30&serialNo=&entrySerialNo=&awbFullNo=&customerName=&customerCode=&bookingAgentName=&bookingAgentCode=&flightNo=&flightDateStart=&flightDateEnd=&originAirportCode=&serviceUserName=&serviceUserId=&salerUserName=&salerUserId=&destAirportCode=&_operateModeList=on&_operateModeList=on&_operateModeList=on&_operateModeList=on&_operateModeList=on&_operateModeList=on&_auditStatusList=on&auditStatusList=PASS&_auditStatusList=on&_auditStatusList=on&_auditStatusList=on&_own=on&_calculateTotalPcsWeightVol=on"
        ccsp_values = []
        tang_values = []
        cargo_values = []

        ccsp_data = []
        tang_data = []
        cargo_data = []

        trs = page.querySelectorAll('//div[@class="page-content"]/div[2]/div/div/table/tbody/tr')
        ths = page.querySelectorAll('//div[@class="page-content"]/div[2]/div/div/table/thead/tr/th')
        columns = [th.textContent() for th in ths]

        for tr in trs:
            tds = tr.querySelectorAll('td')
            waybills_number = strip_(tds[2].textContent())

            values = [strip_(td.textContent()) for td in tds]

            if waybills_number.startswith('112-') or waybills_number.startswith('999-'):
                ccsp_values.append(waybills_number)
                ccsp_data.append(values)
            elif waybills_number.startswith('784-'):
                tang_values.append(waybills_number)
                tang_data.append(values)
            elif waybills_number.startswith('297-'):
                cargo_values.append(waybills_number)
                cargo_data.append(values)

        if page.querySelector('//li[@class="active"]/following-sibling::li[1]/a').textContent().isdigit():
            page.querySelector('//li[@class="active"]/following-sibling::li[1]/a').click()

        df = DataFrame(data=ccsp_data, columns=columns)
        df.to_excel(f'{hx_path}/CCSP运单号.xlsx')

        df = DataFrame(data=tang_data, columns=columns)
        df.to_excel(f'{hx_path}/Tang运单号.xlsx')

        df = DataFrame(data=cargo_data, columns=columns)
        df.to_excel(f'{hx_path}/Cargo运单号.xlsx')

        page.close()

        # ---------------------
        context.close()
        browser.close()

        return ccsp_values, tang_values, cargo_values


if __name__ == '__main__':

    logger.info('程序开始启动')
    date = str(datetime.datetime.now()).split()[0]
    hx_path = f'data/hx_{date}'
    if os.path.exists(hx_path):
        rm_dir_file(hx_path)
    os.mkdir(hx_path)

    logger.info('开始查询运单号')
    print(setting['account_number'],setting['password'])
    ccsp_values, tang_values, cargo_values = run_hss(setting['account_number'],setting['password'])
    logger.info('运单号查询完成')

    logger.info('开始查询CCSP网站运单信息')
    process_ccsp(ccsp_values)
    logger.info('CCSP网站运单状态查询完成')

    logger.info('开始查询Tang网站运单信息')
    process_tang(tang_values)
    logger.info('Tang网站运单状态查询完成')

    logger.info('开始查询Cargo网站运单信息')
    process_cargo(cargo_values)
    logger.info('Cargo网站运单状态查询完成')

    data_path = zip_folder(hx_path)

    data_path = os.path.split(data_path)[-1]
    logger.info(data_path)
    utility.post_file(data_path)
    out_url = utility.get_download_url(data_path)
    logger.info(f'生成的数据，请下载<a href="{out_url}" target="_blank">文件</a>')
    logger.info('程序结束')
