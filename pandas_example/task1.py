import pandas as pd
import os
from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import LAParams, LTTextBoxHorizontal
from pdfminer.pdfinterp import PDFTextExtractionNotAllowed, PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfparser import PDFParser, PDFDocument
import re



def process_brand(batch_number):
    Brand = {'INF':'INF-1','EDH':'EDH-2','SWS':'SWS-3',
             'LNG':'LNG-4','IOP':'IOP-5','RY': 'RY-6',
             'HR':'HR-7','LRS':'LRS-8','AMOS':'AMOS-16',
             'MISE':'MISE-21'}

    key = re.match('([A-Z])+',batch_number)

    return Brand[key.group()]

def process_contract(excel_file,sheet_name):
    df = pd.read_excel(excel_file,sheet_name=sheet_name)
    text = str(df.values)
    contract_no = re.findall("\\\'Contract No :\\\' \\\'(.+)\\\'", str(df.values))
    return contract_no[0]


def process_pdf(filePath):
    # 二进制读取pdf文件
    fp = open(filePath, 'rb')
    parser = PDFParser(fp)
    # 创建一个PDF文档对象
    doc = PDFDocument()
    # 分析器和文档相互连接

    parser.set_document(doc)
    doc.set_parser(parser)

    # 提供初始化密码
    # 如果没有密码 就创建一个空的字符串
    doc.initialize()

    # 检测文档是否提供txt转换，不提供就忽略
    if not doc.is_extractable:
        raise PDFTextExtractionNotAllowed
    else:
        # 创建一个PDF资源管理器来管理共享资源
        rsrcmgr = PDFResourceManager()
        # 创建一个PDF设备对象
        laparams = LAParams()
        device = PDFPageAggregator(rsrcmgr=rsrcmgr, laparams=laparams)
        # 创建一个PDF解释器对象
        interpreter = PDFPageInterpreter(rsrcmgr=rsrcmgr, device=device)

        result = ''

        # 循环遍历列表，每次只处理一个page内容
        for page in doc.get_pages():  # doc.get_pages()获取page列表
            interpreter.process_page(page)
            # 接受该页面的LTPage对象
            layout = device.get_result()
            for x in layout:
                if isinstance(x, LTTextBoxHorizontal):
                    # with open('test.txt', 'a') as f:
                    #     result = x.get_text()
                    #     print(result)
                    #     f.write(result + '\n')
                    result += x.get_text()
        try:
            invoice_no = re.search("INVOICE NO. (\d+)", result)
            return invoice_no.group(1)
        except:
            return None


def process_excel(batch_number, excel_file):
    if os.path.splitext(excel_file)[-1] in ['.xls', '.xlsx']:
        if os.path.isfile(excel_file):

            sheet_name1 = batch_number+'_发票箱单'
            sheet_name3 = batch_number+'_合同_platt'

            # try:
            df = pd.read_excel(excel_file,sheet_name=sheet_name3)

            df_new = pd.DataFrame(index=df.index)
            df_new['批次号'] = batch_number
            df_new['小批次号'] = batch_number
            df_new['合同号'] = process_contract(excel_file,sheet_name1)
            df_new['发票号'] = process_pdf(r'C:\Users\EDZ\Desktop\喜嘉材料\RY544提单.pdf')
            df_new['货号'] = df['GOODS']
            df_new['英文品名'] = df['DESCRIPTIONS']
            df_new['中文品名'] = df['中文']
            df_new['规格'] = df['容量']
            df_new['数量'] = df['QTY\n(Total)']
            df_new['生产日期'] = df['PROD. DATE']
            df_new['限制使用日期'] = df['EXP. DATE']
            df_new['生产批号'] = df['LOT NO']
            df_new['品牌'] = process_brand(batch_number)

            df_new.to_excel(r'C:\Users\EDZ\Desktop\表格.xls')
        # except:
        #     print('读取错误！！！')
        #     return
        else:
            print('%s 文件不存在' % excel_file)


    else:
        print('%s 不是excel文件' % excel_file)


if __name__ == '__main__':
    process_excel('RY544', r'C:\Users\EDZ\Desktop\RY544发票装箱单合同.xls')
    # process_excel('RY544', r'C:\Users\EDZ\Desktop\新建 XLS 工作表.xls')
    # df = pd.read_excel(r'C:\Users\EDZ\Desktop\RY544发票装箱单合同.xls',sheet_name='RY544_发票箱单')
    # print(df)
