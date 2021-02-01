# -*- coding: UTF-8 -*-
import os
import time
import requests
from playwright import sync_playwright
import pandas as pd


def run(playwright):
    browser = playwright.chromium.launch(headless=False)
    context = browser.newContext()

    # Open new page
    page = context.newPage()
    page.setViewportSize(1920, 1040)
    # Go to https://list.vip.com/100940180.html
    page.goto("https://list.vip.com/100940180.html")

    # Click text="女士靴子"
    page.click("text=\"女士靴子\"")

    page.waitForLoadState('networkidle')

    id_list = page.querySelectorAll('//*[@id="J_wrap_pro_add"]/div')
    a_list = page.querySelectorAll('//*[@id="J_wrap_pro_add"]/div/a')
    sale_price_list = page.querySelectorAll('//*[@id="J_wrap_pro_add"]/div/a/div[2]/div[1]/div/div[2]')
    market_price_list = page.querySelectorAll('//*[@id="J_wrap_pro_add"]/div/a/div[2]/div[1]/div/div[3]')
    for i in range(4):
        time.sleep(1)
        page.hover('//*[@id="J-pagingWrap"]')
    img_list = page.querySelectorAll('//*[@id="J_wrap_pro_add"]/div/a//img[@class="J-goods-item__img"]')
    values = []
    for id, a, img, sale_price, market_price in zip(id_list, a_list, img_list, sale_price_list, market_price_list):
        data_id = id.getAttribute('data-product-id')
        href = 'https:' + a.getAttribute('href')
        src = 'https:' + img.getAttribute('src')
        title = img.getAttribute('alt')
        s_price = sale_price.textContent()[1:]
        m_price = market_price.textContent()[1:]
        values.append([data_id,href,src,title,s_price,m_price])
    # Close page
    page.close()

    # ---------------------
    context.close()
    browser.close()

    df = pd.DataFrame(columns=['sku','url','图片链接','标题','售价','市场价'],data=values)

    img_path = []
    for idx,src in df['图片链接'].items():
        file_name = src.split('/')[-1]
        rsp = requests.get(url=src)
        with open(f'img/{file_name}','wb') as f:
            f.write(rsp.content)
            img_path.append(f'img/{file_name}')
            print(f'第{idx+1}张图片下载完成')
    df['图片路径'] = img_path

    df.to_excel('云钠电商商品信息1.xlsx')
    print('程序结束')
    return df


with sync_playwright() as playwright:
    run(playwright)
