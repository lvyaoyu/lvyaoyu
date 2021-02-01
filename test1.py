import sys

import pyexcel

from selenium.webdriver import ChromeOptions, Chrome
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

if __name__ == '__main__':

    keyword = '变形金刚'

    if len(sys.argv) > 1:
        keyword = sys.argv[1]

    option = ChromeOptions()
    option.add_experimental_option('excludeSwitches', ['enable-automation'])
    option.add_experimental_option('useAutomationExtension', False)
    # option.add_argument('--headless')

    driver = Chrome(options=option)

    # execute_cdp_cmd执行Chrome Devtools协议命令并获得返回结果
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
        Object.defineProperty(navigator, 'webdriver', {
          get: () => undefined
        })
      """
    })

    driver.get('https://secure.assrt.net/')

    # key = driver.find_element_by_id('key')
    key = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, 'key'))
    )
    # searchword.click()
    key.send_keys(keyword)
    key.send_keys(Keys.RETURN)
    rows = []
    while True:

        # body = driver.find_element_by_xpath('//div[@class="body"]')
        body = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//div[@class="body"]'))
        )
        y = body.location['y'] + body.rect['height']
        # 下拉滚动到商品节点最下方的位置
        driver.execute_script('window.scrollTo(0,%s)' % y)

        # datas = driver.find_elements_by_xpath('//div[contains(@onmouseover,"addclass")]')
        datas = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, '//div[contains(@onmouseover,"addclass")]'))
        )
        for data in datas:
            data_dict = {}
            a = data.find_element_by_xpath('.//a[@class="introtitle"]')
            data_dict['title'] = a.get_attribute('title')
            try:
                data_dict['version'] = data.find_element_by_xpath('.//div[@id="meta_top"]//b').text
            except:
                data_dict['version'] = None
            try:
                data_dict['webName'] = data.find_element_by_xpath('.//div[@id="meta_top"]/span[last()]').text
            except:
                data_dict['webName'] = None
            spans = data.find_elements_by_xpath('.//div[@id="sublist_div"]/span')
            for i in range(len(spans)):
                t = [j.strip() for j in spans[i].text.split('：')]
                data_dict['%s' % t[0]] = t[1]
            print(data_dict)
            rows.append(data_dict)
        try:
            # next_page = driver.find_element_by_xpath('//a[@id="pl-current"]/following-sibling::a[1]')
            next_page = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//a[@id="pl-current"]/following-sibling::a[1]'))
            )
            print('**' * 20, '下一页为第%s页' % next_page.text, '**' * 20)
            next_page.click()
        except:
            break
    pyexcel.save_as(records=rows, dest_file_name='%s.xls' % keyword)
    driver.quit()
