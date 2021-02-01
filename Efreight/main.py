# C:\Users\Neo\AppData\Local\ms-playwright
import json
import time
import re
import os
import sys
import datetime
import subprocess
import configparser
import utility

import random
import requests

import asyncio
from playwright import sync_playwright
from playwright import async_playwright
from time import sleep

import pandas
from pandas.io.json import json_normalize

'''
查看所有运行中进程的命令行参数：

wmic process get caption,commandline /value

查询指定进程的命令行参数：

wmic process where caption=”chrome.exe” get caption,commandline /value
'''


class Efreight:
    def __init__(self):
        utility.write_log("开始执行...")
        self.ses = requests.session()

    def __del__(self):
        utility.write_log("执行结束...")
        self.ses.close()

    def get_short_date(self, dts):
        dt = datetime.datetime.strptime(dts, '%Y%m%d')
        return dt.strftime('%d%b').upper()

    def get_summary(self, desc):
        sum = 0.0
        pattern = re.compile(r"(.*):(.*)")
        for (code, amount) in re.findall(pattern, desc):
            print(code, amount)
            sum = sum + float(amount)
        return sum

    def run(self, playwright):
        # chrome://settings/content/insecureContent
        # chrome://flags/#mixed-forms-disable-autofill
        # chrome://flags/#safe-browsing-enhanced-protection-message-in-interstitials
        context = playwright.chromium.launchPersistentContext(headless=False, args=["--allow-running-insecure-content",
                                                                                    "--disable-popup-blocking"],
                                                              userDataDir=r"E:\Project\YunnaProjects\Python\Efreight\UserData")

        # context = browser.newContext()

        # Open new page
        page = context.pages[0]
        page.setViewportSize(1280, 800)
        # page.on("popup", lambda popup: print("Popup %s" % popup.message))  # https://github.com/microsoft/playwright/blob/master/docs/api.md#pageonpopup
        # page.on("dialog", lambda dialog: print("Dialog %s" % dialog.message))
        # page.on("framenavigated", lambda frame: print("Frame navigated to %s" % frame.url))
        # page.on("request", lambda request: print("Request %s" % request.url))
        # page.on(
        #     "requestFinished", lambda request: print("Request finished %s" % request.url)
        # )
        # page.on(
        #     "response",
        #     lambda response: print(
        #         "Response %s, request %s in frame %s"
        #         % (response.url, response.request.url, response.frame.url)
        #     ),
        # )
        #
        page.goto("https://login.ccnhub.com/LINC/")
        # dimensions = page.evaluate('''() => {
        #   return {
        #     width: document.documentElement.clientWidth,
        #     height: document.documentElement.clientHeight,
        #     deviceScaleFactor: window.devicePixelRatio
        #   }
        # }''')
        # print(dimensions)
        page.on("dialog", lambda dialog: (print("Dialog %s" % dialog.message),
                                          # dialog.accept(),
                                          ))
        page.click("input[name=\"ctl00$Content$txtCompanyID\"]")
        page.fill("input[name=\"ctl00$Content$txtCompanyID\"]", "SGECAN01")
        page.click("input[name=\"ctl00$Content$txtUserID\"]")
        page.fill("input[name=\"ctl00$Content$txtUserID\"]", "canadmin")
        page.click("input[name=\"ctl00$Content$txtPasswordCCNHub\"]")
        page.fill("input[name=\"ctl00$Content$txtPasswordCCNHub\"]", "password")
        page.click("button[id=\"ctl00_Content_btnLoginCCNHub\"]")
        # selector = page.querySelector("button[id=\"ctl00_Content_rwForceLogin_C_BtnForceLogin\"]")
        # if selector != None:
        #     page.click("button[id=\"ctl00_Content_rwForceLogin_C_BtnForceLogin\"]")

        # page.waitForSelector("button[id=\"ctl00_Content_rwForceLogin_C_BtnForceLogin\"]")
        try:
            page.click("button[id=\"ctl00_Content_rwForceLogin_C_BtnForceLogin\"]", timeout=3000)
        except:
            pass
        sleep(1)

        # page.waitForEvent('popup')
        # page1 = context.pages[1]

        # 加载运单信息
        with page.expect_popup() as popup_info:
            page.click("div[id=\"myAppCCNhub2\"]")
        page1 = popup_info.value
        page1.waitForLoadState(state="networkidle")
        sleep(1)

        page1.evaluate(
            "document.getElementById(\"proceed-button\").click()")  # playwright.helper.Error: Execution context was destroyed, most likely because of a navigation.
        # page1.waitForNavigation(waitUntil="networkidle")
        page1.waitForLoadState(state="networkidle")
        sleep(1)

        page1.hover("text=\"航空公司功能\"")
        page1.hover("text=\"主运单打印\"")
        page1.click("text=\"中性主运单打印\"")
        page1.waitForLoadState(state="networkidle")
        sleep(1)

        # 第一页
        page1.fill("input[id=\"txtAWB_Prefix\"]", self.zhu_dan_hao[0:3])
        page1.fill("input[id=\"txtAWB_Suffix\"]", self.zhu_dan_hao[3:])
        page1.click("input[id=\"txtOrigin_Code\"]")
        page1.waitForLoadState(state="networkidle")
        page1.waitForFunction("document.getElementById(\"txtAWBTop\").value != \"\"")
        # page1.fill("input[id=\"txtTotal_Pcs\"]", self.huo_wu_jian_shu)
        # page1.fill("input[id=\"txtTotal_Wtg\"]", self.huo_wu_mao_zhong)

        # 加载运单详情
        with page1.expect_popup() as popup_info:
            page1.click("img[title=\"Click here to enter Shipper/Consignee\"]")
        page2 = popup_info.value
        page2.waitForLoadState(state="networkidle")

        page2.on("dialog", lambda dialog: dialog.accept())
        page2.fill("input[id=\"txtShipper_Name\"]", self.fa_huo_ren_ming_cheng)
        page2.fill("input[id=\"txtShipper_Addr\"]", self.fa_huo_ren_di_zhi)
        page2.fill("input[id=\"txtShipper_Place\"]", self.fa_huo_ren_cheng_shi_ming_cheng)
        page2.fill("input[id=\"txtShipper_Postal\"]", self.fa_huo_ren_you_bian)
        page2.fill("input[id=\"txtShipper_Country\"]", self.fa_huo_ren_guo_jia_dai_ma)
        page2.fill("input[id=\"txtTotal_Pcs\"]", self.huo_wu_jian_shu)
        page2.fill("input[id=\"txtTotal_Wtg\"]", self.huo_wu_mao_zhong)
        page2.fill("input[id=\"txtSLAC\"]", self.xiao_jian_shu_slac)
        page2.fill("input[id=\"txtConsignee_Name\"]", self.shou_huo_ren_ming_cheng)
        page2.fill("input[id=\"txtConsignee_Addr\"]", self.shou_huo_ren_di_zhi)
        page2.fill("input[id=\"txtConsignee_Place\"]", self.shou_huo_ren_cheng_shi_ming_cheng)
        page2.fill("input[id=\"txtConsignee_State\"]", self.shou_huo_ren_zhou_ming)
        page2.fill("input[id=\"txtConsignee_Postal\"]", self.shou_huo_ren_you_bian)
        page2.fill("input[id=\"txtConsignee_Country\"]", self.shou_huo_ren_guo_jia_dai_ma)
        sleep(1)
        page2.click("input[id=\"imgSubmit\"]")

        # 第二页
        page1.click("text=\"储存与下页\"")
        page1.waitForLoadState(state="networkidle")
        # page1.on("dialog", lambda dialog: print("Dialog %s" % dialog.message))
        # page1.on("dialog", lambda dialog: dialog.accept())
        page1.fill("input[name=\"txtTo1\"]", self.yi_cheng_mu_di_gang)
        page1.fill("input[name=\"txtFlight1_Carr\"]", self.yi_cheng_hang_ban_hao[0:2])
        page1.fill("input[name=\"txtFlight1_Num\"]", self.yi_cheng_hang_ban_hao[2:])
        page1.fill("input[name=\"txtFlight_Date1\"]", self.get_short_date(self.yi_cheng_hang_ban_ri_qi))
        page1.fill("input[name=\"txtTo2\"]", self.er_cheng_mu_di_gang)
        if page1.getAttribute("input[name=\"txtFlight3_Carr\"]", "readonly") == None:
            page1.fill("input[name=\"txtFlight3_Carr\"]", self.yi_cheng_hang_ban_hao[0:2])
        if page1.getAttribute("input[name=\"txtFlight3_Num\"]", "readonly") == None:
            page1.fill("input[name=\"txtFlight3_Num\"]", self.yi_cheng_hang_ban_hao[2:])
        if page1.getAttribute("input[name=\"txtFlight_Date3\"]", "readonly") == None:
            page1.fill("input[name=\"txtFlight_Date3\"]", self.yi_cheng_hang_ban_ri_qi[:2])

        # 第三页
        page1.click("text=\"储存与下页\"")
        page1.waitForLoadState(state="networkidle")
        page1.fill("input[id=\"txtRCP_Pcs1\"]", self.huo_wu_jian_shu)
        page1.fill("input[id=\"txtGross_Wtg1\"]", self.huo_wu_mao_zhong)
        page1.fill("input[id=\"txtChg_Wtg1\"]", self.ji_fei_zhong)
        page1.fill("input[id=\"txtRate_Chg_Dis1\"]", self.dan_jia)
        page1.fill("input[id=\"txtTotal_Chg1\"]", self.zong_yun_fei)
        page1.fill("input[id=\"txtGoods_Desc1\"]", self.huo_wu_jian_yao_miao_shu)

        # 加载主运单尺寸
        with page1.expect_popup() as popup_info:
            page1.click("input[name=\"imgDimm\"]")
        page3 = popup_info.value
        page3.waitForLoadState(state="networkidle")

        # 清空数据
        for i in range(9):
            page3.click("input[id=\"imgReset\"]")

        # 填写数据
        index = 1
        pattern = re.compile(r"(.*)\*(.*)\*(.*)/(.*)")
        for (length, width, height, count) in re.findall(pattern, self.chi_cun):
            print(index, length, width, height, count)
            page3.click("input[name=\"txtDC0R{}\"]".format(index))
            page3.fill("input[name=\"txtDC0R{}\"]".format(index), str(1))
            page3.fill("input[name=\"txtDC1R{}\"]".format(index), length)
            page3.fill("input[name=\"txtDC2R{}\"]".format(index), width)
            page3.fill("input[name=\"txtDC3R{}\"]".format(index), height)
            # page3.fill("input[name=\"txtDC4R{}\"]".format(index), "CM")
            page3.click("input[name=\"txtDC4R{}\"]".format(index))
            page3.fill("input[name=\"txtDC5R{}\"]".format(index), count)
            index = index + 1
        sleep(1)
        page3.click("input[id=\"imgSubmit\"]")

        # 第四页
        page1.click("text=\"储存与下页\"")
        page1.waitForLoadState(state="networkidle")
        if page1.getAttribute("input[name=\"txtTotal_Wtg_Chg_PP\"]", "readonly") == None:
            page1.fill("input[id=\"txtTotal_Wtg_Chg_PP\"]", self.zong_yun_fei)
        if page1.getAttribute("input[name=\"txtChg_Due_Carr_PP\"]", "readonly") == None:
            page1.fill("input[id=\"txtChg_Due_Carr_PP\"]", str(self.get_summary(self.za_fei)))
        if page1.getAttribute("input[name=\"txtTotalPP\"]", "readonly") == None:
            page1.fill("input[id=\"txtTotalPP\"]", str(self.zong_yun_fei + self.get_summary(self.za_fei)))

        # 加载主运单其他收费
        with page1.expect_popup() as popup_info:
            page1.click("input[name=\"imgOthChg\"]")
        page4 = popup_info.value
        page4.waitForLoadState(state="networkidle")

        # 清空数据
        for i in range(9):
            page4.click("input[id=\"imgReset\"]")

        # 填写数据
        index = 1
        pattern = re.compile(r"(.*):(.*)")
        for (code, amount) in re.findall(pattern, self.za_fei):
            print(code, amount)
            page4.click("input[name=\"txtOCC0R{}\"]".format(index))
            page4.fill("input[name=\"txtOCC0R{}\"]".format(index), code)
            page4.click("input[name=\"txtOCC2R{}\"]".format(index))
            page4.fill("input[name=\"txtOCC2R{}\"]".format(index), amount)
            index = index + 1
        sleep(1)
        page4.click("input[id=\"imgSubmit\"]")

        # page1.click("text=\"递交\"")

        # page.waitForEvent('popup')
        # popup.waitForLoadState('load')

        context.close()

    def process(self, file_name):
        # data_frame = pandas.read_excel(file_name, keep_default_na=False, converters ={"货物件数 *": str})
        data_frame = pandas.read_excel(file_name, keep_default_na=False, dtype=str)
        data_frame = data_frame.iloc[1:]
        print(data_frame)
        for index, row in data_frame.iterrows():
            # print(row.filter(like="主单号").iloc[0])
            # print(row.get("主单号 *"))
            # print(row.get("分单号"))
            # print(row.get("始发港*"))
            # print(row.get("一程航班号 *"))
            # print(row.get("一程航班日期 *"))
            # print(row.get("一程目的港*"))
            # print(row.get("二程航班号"))
            # print(row.get("二程航班日期"))
            # print(row.get("二程目的港"))
            # print(row.get("运费支付方法代码*"))
            # print(row.get("货物件数 *"))
            # print(row.get("货物毛重 *"))
            # print(row.get("货物简要描述*"))
            # print(row.get("发货人名称*"))
            # print(row.get("发货人地址*"))
            # print(row.get("发货人城市名称*"))
            # print(row.get("发货人国家代码*"))
            # print(row.get("发货人邮编"))
            # print(row.get("收货人名称*"))
            # print(row.get("收货人地址*"))
            # print(row.get("收货人城市名称*"))
            # print(row.get("收货人国家代码*"))
            # print(row.get("收货人州名"))
            # print(row.get("收货人邮编"))
            # print(row.get("小件数SLAC"))
            # print(row.get("尺寸"))
            # print(row.get("杂费"))
            # print(row.get("计费重"))
            # print(row.get("单价"))
            # print(row.get("总运费"))

            self.zhu_dan_hao = row.get("主单号 *")
            self.fen_dan_hao = row.get("分单号")
            self.shi_fa_gang = row.get("始发港*")
            self.yi_cheng_hang_ban_hao = row.get("一程航班号 *")
            self.yi_cheng_hang_ban_ri_qi = row.get("一程航班日期 *")
            self.yi_cheng_mu_di_gang = row.get("一程目的港*")
            self.er_cheng_hang_ban_hao = row.get("二程航班号")
            self.er_cheng_hang_ban_ri_qi = row.get("二程航班日期")
            self.er_cheng_mu_di_gang = row.get("二程目的港")
            self.yun_fei_zhi_fu_fang_fa_dai_ma = row.get("运费支付方法代码*")
            self.huo_wu_jian_shu = row.get("货物件数 *")
            self.huo_wu_mao_zhong = row.get("货物毛重 *")
            self.huo_wu_jian_yao_miao_shu = row.get("货物简要描述*")
            self.fa_huo_ren_ming_cheng = row.get("发货人名称*")
            self.fa_huo_ren_di_zhi = row.get("发货人地址*")
            self.fa_huo_ren_cheng_shi_ming_cheng = row.get("发货人城市名称*")
            self.fa_huo_ren_guo_jia_dai_ma = row.get("发货人国家代码*")
            self.fa_huo_ren_you_bian = row.get("发货人邮编")
            self.shou_huo_ren_ming_cheng = row.get("收货人名称*")
            self.shou_huo_ren_di_zhi = row.get("收货人地址*")
            self.shou_huo_ren_cheng_shi_ming_cheng = row.get("收货人城市名称*")
            self.shou_huo_ren_guo_jia_dai_ma = row.get("收货人国家代码*")
            self.shou_huo_ren_zhou_ming = row.get("收货人州名")
            self.shou_huo_ren_you_bian = row.get("收货人邮编")
            self.xiao_jian_shu_slac = row.get("小件数SLAC")
            self.chi_cun = row.get("尺寸")
            self.za_fei = row.get("杂费")
            self.ji_fei_zhong = row.get("计费重")
            self.dan_jia = row.get("单价")
            self.zong_yun_fei = row.get("总运费")

            if self.zhu_dan_hao == "":
                continue

            with sync_playwright() as playwright:
                self.run(playwright)


efreight = Efreight()
efreight.process('template.xlsx')

# async def main():
#     async with async_playwright() as p:
#         # for browser_type in [p.chromium]:
#         # browser = await browser_type.launch(headless=False)
#         # page = await browser.newPage()
#         # await page.goto('http://baidu.com')
#         # await page.screenshot(path=f'example-{browser_type.name}.png')
#         # await browser.close()
#
#         context = await p.chromium.launchPersistentContext(headless=False, locale='en-US', args=["--allow-running-insecure-content"], userDataDir=r"E:\Project\YunnaProjects\Python\Efreight\UserData")
#         page = context.pages[0]
#         await page.goto("https://login.ccnhub.com/LINC/")
#         await page.click("input[name=\"ctl00$Content$txtCompanyID\"]")
#         await page.fill("input[name=\"ctl00$Content$txtCompanyID\"]", "SGECAN01")
#         await page.click("input[name=\"ctl00$Content$txtUserID\"]")
#         await page.fill("input[name=\"ctl00$Content$txtUserID\"]", "canadmin")
#         await page.click("input[name=\"ctl00$Content$txtPasswordCCNHub\"]")
#         await page.fill("input[name=\"ctl00$Content$txtPasswordCCNHub\"]", "password")
#         await page.click("button[id=\"ctl00_Content_btnLoginCCNHub\"]")
#         await page.click("button[id=\"ctl00_Content_rwForceLogin_C_BtnForceLogin\"]")
#         await page.click("div[id=\"myAppCCNhub2\"]")
#         await asyncio.sleep(3)
#         page1 = context.pages[1]
#         await page1.evaluate("document.getElementById(\"proceed-button\").click()")
#         await asyncio.sleep(60)
#
#
# asyncio.get_event_loop().run_until_complete(main())
# print("ok")
