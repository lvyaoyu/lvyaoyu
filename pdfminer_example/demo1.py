import re

from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import LAParams, LTTextBoxHorizontal
from pdfminer.pdfinterp import PDFTextExtractionNotAllowed, PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfparser import PDFParser, PDFDocument

import pyexcel
import pandas as pd
from pandas import DataFrame


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
                    result += x.get_text()
        text = re.search("===================\n(.*\n)+ TOTAL INTERNATIONAL", result)
        result=text.group()
        data = re.findall(' (\d+.+?\d+)\n', result)
        print(len(data))
        rows = []
        for i in data:
            row = re.findall('\S+', i)
            # print(row)
            rows.append(row)
        df = DataFrame(data=rows)
        for i in df.columns[3:13]:
            df[i] = df[i].astype('float64')
        return df


if __name__ == '__main__':
    # file_path = r'C:\Users\EDZ\Desktop\喜嘉材料\RY544提单.pdf'
    file_path = r'C:\Users\EDZ\Desktop\汉星\excel-pdf\UA201811月上.pdf'
    df = process_pdf(file_path)
    print(df[13])
    # # print(result)
    # data = re.findall(' (\d+.+?\d+)\n', result)
    # print(len(data))
    # rows = []
    # for i in data:
    #     # print(i)
    #     # row = re.findall('\d+|\d+\.\d+|[A-Z]+',i)
    #     row = re.findall('\S+', i)
    #     print(row)
    #     rows.append(row)
    # df = DataFrame(data=rows)
    # df.to_excel('data.xlsx')

