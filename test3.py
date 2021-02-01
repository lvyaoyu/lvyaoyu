# -*- coding: UTF-8 -*-
import time

from selenium.webdriver import ChromeOptions, Chrome
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

option = ChromeOptions()
option.add_experimental_option('excludeSwitches', ['enable-automation'])
option.add_experimental_option('useAutomationExtension', False)

driver = Chrome(options=option)
# execute_cdp_cmd执行Chrome Devtools协议命令并获得返回结果
driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
    "source": """
        Object.defineProperty(navigator, 'webdriver', {
          get: () => undefined
        })
      """
})
try:
    driver.get('http://sslvpn.amorepacific.com.cn:8080/vpns/homepage.html')
    print(driver.get_cookies())
    print('VPN已经启动过')
except Exception as e:
    print(e)
    driver.get('https://sslvpn.amorepacific.com.cn/vpn/index.html')
    user = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, '//input[@name="login"]'))
    )
    user.send_keys('CN00000102')
    pwd = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, '//input[@name="passwd"]'))
    )
    pwd.send_keys('51692560')
    submit = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, '//input[@type="submit"]'))
    )
    submit.click()

    try:
        # 获取Transfer按钮
        TransferButton = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 'TransferButton'))
        )
        # time.sleep(2)
        # 点击Transfer按钮
        TransferButton.click()

    except Exception as e:
        print(e)
    finally:
        result = WebDriverWait(driver,60,1).until(
            EC.presence_of_element_located((By.XPATH,'/html/body/table[2]/tbody/tr/td[1]/p[1]/strong/font'))
        ).text

        print(result)
        print(driver.current_url)
        if result == 'ACE POS 系统' and driver.current_url == 'http://sslvpn.amorepacific.com.cn:8080/vpns/homepage.html':
            print('VPN启动成功')


