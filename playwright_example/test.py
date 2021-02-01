# -*- coding: UTF-8 -*-
from playwright import sync_playwright


def click_alert(dialog):
    try:
        dialog.accept()
    except:
        pass


def run(excel_file):
    with sync_playwright() as playwright:
        browser_type = playwright.chromium
        executablePath = r'ms-playwright\chromium-833159\chrome-win\chrome.exe'
        browser = browser_type.launch(headless=False, executablePath=executablePath)
        context = browser.newContext()

        # Open new page
        page = context.newPage()
        page.setViewportSize(1920, 1040)
        logger.info(' - 开始登陆网站')
        # Go to http://uniner.synology.me:88/LKT/index.php
        page.goto("http://uniner.synology.me:88/LKT/index.php")

        # Go to http://uniner.synology.me:88/LKT/index.php?module=Login
        page.goto("http://uniner.synology.me:88/LKT/index.php?module=Login")

        # Click input[name="login"]
        page.click("input[name=\"login\"]")

        # Fill input[name="login"]
        page.fill("input[name=\"login\"]", "laiketui")

        # Click input[name="pwd"]
        page.click("input[name=\"pwd\"]")

        # Fill input[name="pwd"]
        page.fill("input[name=\"pwd\"]", "laiketui")

        # Press Enter
        # with page.expect_navigation(url="http://uniner.synology.me:88/LKT/index.php?module=AdminLogin"):
        with page.expect_navigation():
            page.press("input[name=\"pwd\"]", "Enter")

        logger.info(' - 网站登录成功')
        page.waitForLoadState('networkidle')

        # Click //dt[normalize-space(.)='商品管理']
        page.click("//dt[normalize-space(.)='商品管理']")

        # Click text="商品列表"
        page.click("text=\"商品列表\"")

        frame_product = page.frames[2]

        # result = input('是否删除之前商品信息 (y/n) :')
        logger.info(' - 开始自动删除历史数据')
        while True:
            # if result != 'y':
            #     break

            if frame_product.textContent('//div[@class="mt-20"]/div/table/tbody').strip():
                frame_product.click("//label")
                frame_product.click("text=/.*删除.*/")
                frame_product.click("text=\"确认\"")
                frame_product.click("text=\"确认\"")
            else:
                logger.info(' - 历史商品信息全部删除成功')
                time.sleep(2)
                break
        logger.info(' - 10s后开始自动录入数据...')
        time.sleep(10)


        logger.info(' - 开始读取并处理Excel表格数据')
        df = pd.read_excel(excel_file)

        logger.info(' - 开始自动上传商品信息')
        for i in df.index:
            sku = df.loc[i, 'sku']
            title = df.loc[i, '标题']
            s_price = int(df.loc[i, '售价'])
            m_price = int(df.loc[i, '市场价'])
            img_path = df.loc[i, '图片路径']

            # Click text=/.*发布商品.*/
            frame_product.click("text=/.*发布商品.*/")

            frame_product.waitForLoadState('networkidle')

            # Fill input[name="product_title"]
            frame_product.fill("input[name=\"product_title\"]", title)  # 商品标题

            # Fill input[name="subtitle"]
            frame_product.fill("input[name=\"subtitle\"]", title)  # 副标题

            frame_product.selectOption('//*[@id="product_classId"]', '-7-28-')  # 商品类别

            frame_product.selectOption('//*[@id="brand_classId"]', '9')  # 商品品牌

            frame_product.click('//*[@id="image"]')

            frame_product.click("text=/.*本地上传.*/")

            # Upload 003dd00372c3f98156512c62afe559cc.jpg
            frame_product.setInputFiles("input[name=\"imgFile\"]", img_path)  # 商品主图

            frame_product.click("text=/.*确定.*/")

            # Upload 微信图片_20201208093221.jpg
            frame_product.setInputFiles("input[name=\"imgurls[]\"]", img_path)  # 商品展示图

            # Fill input[name="initial[cbj]"]
            frame_product.fill("input[name=\"initial[cbj]\"]", f'{int(s_price * 0.5)}')  # 成本价

            # Fill input[name="initial[yj]"]
            frame_product.fill("input[name=\"initial[yj]\"]", f'{m_price}')  # 原价

            # Fill input[name="initial[sj]"]
            frame_product.fill("input[name=\"initial[sj]\"]", f'{s_price}')  # 售价

            frame_product.selectOption('//*[@id="unit"]', '双')  # 单位

            # Fill input[name="initial[kucun]"]
            frame_product.fill("input[name=\"initial[kucun]\"]", f'{random.randint(1000, 10000)}')  # 库存

            # Fill input[placeholder="请输入属性名称"]
            frame_product.fill("input[placeholder=\"请输入属性名称\"]", f'{sku}')  # sku

            frame_product.click(f'//label[@for="sex-{random.randint(1, 4)}"]')  # 类型

            frame_product.hover('//*[@id="form1"]//input[@name="Submit"]')

            frame_product.fill('//input[@id="volumeId"]', f'{random.randint(500, 5000)}')  # 拟定销量

            frame_product.selectOption('//select[@id="freightId"]', f'{random.randint(1, 2)}')  # 运费设置

            frame_ueditor_0 = page.frames[4]
            frame_ueditor_0.addScriptTag(content='document.body.innerHTML="{}"'.format('无'))

            page.once("dialog", lambda dialog: click_alert(dialog))
            frame_product.click('//*[@id="form1"]//input[@name="Submit"]')  # 提交
            msg = '第%s款产品发布成功！' % (i + 1)
            logger.info(' - %s' % msg)

        else:
            page.click("text=\"商品列表\"")
            time.sleep(2)
            logger.info(' - 商品信息全部上传完成')
            time.sleep(2)
            logger.info(' - 自动录入完成，60后自动关闭程序')

        time.sleep(56)

        logger.info(' - 程序结束')

        # Close page
        page.close()

        # ---------------------
        context.close()
        browser.close()


# excel_file = '云钠电商商品信息.xlsx'
run(data_file)
