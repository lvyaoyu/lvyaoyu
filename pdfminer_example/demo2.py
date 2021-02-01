# -*- coding: UTF-8 -*-


import codecs
import os
import PyPDF2 as PyPDF2


def merge_pdf(dirPath):
    # 建立一个存放pdf文件的列表
    files = list()

    # 遍历存放pdf文件的文件夹
    for fileName in os.listdir(dirPath):
        # 如果是以.pdf结尾的文件，则追加到数组中
        if fileName.endswith('.pdf'):
            files.append(fileName)

    # 进入该目录
    os.chdir(dirPath)

    # 生成一个空白的pdf文件
    pdfwriter = PyPDF2.PdfFileWriter()
    for i in files:
        # 以只读方式依次打开pdf文件
        pdfreader = PyPDF2.PdfFileReader(open(i, 'rb'))
        for page in range(pdfreader.numPages):
            # 将打开的pdf文件内容一页一页的复制到新建的空白pdf里
            pdfwriter.addPage(pdfreader.getPage(page))

    # 生成all.pdf文件
    with codecs.open(r'C:\Users\EDZ\Desktop\all.pdf', 'wb') as f:
        # 将复制的内容全部写入all.pdf文件中
        pdfwriter.write(f)

if __name__ == '__main__':
    merge_pdf(r'C:\Users\EDZ\Desktop\喜嘉材料\pdf')
