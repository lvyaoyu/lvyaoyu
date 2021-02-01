import os
import re
import zipfile

from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import LAParams, LTTextBoxHorizontal
from pdfminer.pdfinterp import PDFTextExtractionNotAllowed, PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfparser import PDFParser, PDFDocument

from icecream import ic
from datetime import datetime

ic.configureOutput(prefix=str(datetime.now()) + ' - ', includeContext=True)

# 删除文件或文件夹及里面的内容
def rm_dir_file(path):
    if os.path.isfile(path):
        os.remove(path)
        print('文件 %s 删除成功' % path)
    elif os.path.isdir(path):
        for root, dirs, files in os.walk(path, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
                print('文件 %s 删除成功' % os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
                print('文件 %s 删除成功' % os.path.join(root, name))
        else:
            os.rmdir(path)
            print('文件夹 %s 删除成功' % path)


# 解压文件
def unzip_files(zip_file_path, unzip_path=None):
    # 判断zip_file_path是否为一个文件
    if not os.path.isfile(zip_file_path):
        print('%s   不是一个有效的文件夹路径' % unzip_path)
        return
    if unzip_path:
        # 判断unzipPath是否为一个文件夹
        if not os.path.isdir(unzip_path):
            print('%s   不是一个有效的文件路径' % zip_file_path)
            return
    else:
        unzip_path = os.path.split(zip_file_path)[0]

    # 分离zipPath的路径和文件
    filePath_fileName = os.path.split(zip_file_path)
    # 取文件
    file_name = filePath_fileName[-1]
    # 分离文件的文件名和后缀
    fileName_suffix = os.path.splitext(file_name)
    # 判断后缀是否以.zip结尾
    if fileName_suffix[-1] != '.zip':
        print('%s   该文件不是以.zip结尾的压缩文件' % zip_file_path)
        return

    with zipfile.ZipFile(zip_file_path, 'r') as zf:
        # 解压到指定目录，首先创建一个解压目录，目录为解压目录加压缩文件名拼接
        new_unzip_path = os.path.join(unzip_path, fileName_suffix[0])
        # print('new_unzip_path',new_unzip_path)
        # 判断拼接目录是否存在，不存在则创建
        if os.path.exists(new_unzip_path):
            rm_dir_file(new_unzip_path)
        os.mkdir(new_unzip_path)

        # 给定一个压缩文件形式状态
        zip_form = True
        for old_name in zf.namelist():
            # 由于源码遇到中文是cp437方式，所以解码成gbk，windows即可正常
            new_name = old_name.encode('cp437').decode('gbk')
            if new_name == fileName_suffix[0] + '/':
                zip_form = False
                continue
            # 判断压缩文件形式
            if zip_form:
                # 拼接文件的保存路径
                new_path = os.path.join(new_unzip_path, new_name)
            else:
                new_path = os.path.join(unzip_path, new_name)
            # 获取文件大小，判断是文件还是文件夹
            file_size = zf.getinfo(old_name).file_size
            if os.path.exists(new_path):
                print('%s   该文件或文件夹已存在' % new_path)
                rm_dir_file(new_path)
                # continue
            if file_size > 0:
                # 是文件，通过open创建文件，写入数据
                with open(new_path, 'wb') as f:
                    f.write(zf.read(old_name))
            else:
                os.mkdir(new_path)
        else:
            return new_unzip_path


# 压缩文件夹
def zip_folder(folder_path, zip_file_path=None):
    if not os.path.isdir(folder_path):
        print('%s不是一个文件夹' % folder_path)
        return
    if zip_file_path:
        print(os.path.splitext(zip_file_path))
        if os.path.splitext(zip_file_path)[-1] != '.zip':
            print('%s不是以.zip结尾的压缩文件名' % zip_file_path)
            return
    else:
        zip_file_path = folder_path + '.zip'
    z = zipfile.ZipFile(zip_file_path, 'w', zipfile.ZIP_DEFLATED)
    for dir_path, dir_names, file_names in os.walk(folder_path):
        f_path = dir_path.replace(folder_path, '')
        f_path = f_path and f_path + os.sep or ''
        for file_name in file_names:
            z.write(os.path.join(dir_path, file_name), f_path + file_name)
            print('压缩成功')
    z.close()
    return folder_path+'.zip'


# 读取pdf当中的文字
def process_pdf(file_path):
        # 二进制读取pdf文件
        fp = open(file_path, 'rb')
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

            info = ''

            # 循环遍历列表，每次只处理一个page内容
            for page in doc.get_pages():  # doc.get_pages()获取page列表
                interpreter.process_page(page)
                # 接受该页面的LTPage对象
                layout = device.get_result()
                for result in layout:
                    if isinstance(result, LTTextBoxHorizontal):
                        info += result.get_text()

            return info

# 除去字符串当中的空格跟换行符
def strip_(s):
    s_ = ''
    s_.strip()
    for i in s:
        if i not in ['\n','\t','\r']:
            s_ += i
    return s_