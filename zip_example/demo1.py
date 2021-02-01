# -*- coding: UTF-8 -*-
import os
import zipfile


# def process_zip(zipPath,unzipPath):
#     with zipfile.ZipFile(zipPath,'r') as zf:
#         # # 解压到指定目录，首先创建一个解压目录
#         # if not os.path.exists(unzipPath):
#         #     os.mkdir(unzipPath)
#         for old_name in zf.namelist():
#             # 由于源码遇到中文是cp437方式，所以解码成gbk，windows即可正常
#             new_name = old_name.encode('cp437').decode('gbk')
#             print(new_name)
#             # 拼接文件的保存路径
#             new_path = os.path.join(unzipPath,new_name)
#             print(new_path)
#             # 获取文件大小，判断是文件还是文件夹
#             file_size = zf.getinfo(old_name).file_size
#             if file_size > 0:
#                 # 是文件夹，通过open创建文件，写入数据
#                 with open(new_path, 'wb') as f:
#                     f.write(zf.read(old_name))
#             else:
#                 # 是文件夹，就创建
#                 if not os.path.exists(new_path):
#                     os.mkdir(new_path)

def process_zip(zipPath,unzipPath):
    # 判断zipPath是否为一个文件
    if os.path.isfile(zipPath):
        # 判断unzipPath是否为一个文件夹
        if os.path.isdir(unzipPath):
            # 分离zipPath的路径和文件
            filePath_file = os.path.split(zipPath)
            # 取文件
            file_name = filePath_file[-1]
            # 分离文件的文件名和后缀
            fileName_suffix = os.path.splitext(file_name)
            # 判断后缀是否以.zip结尾
            if fileName_suffix[-1] == '.zip':
                with zipfile.ZipFile(zipPath,'r') as zf:
                    # 解压到指定目录，首先创建一个解压目录，目录为解压目录加压缩文件名拼接
                    new_unzipPath = os.path.join(unzipPath,fileName_suffix[0])
                    print('new_unzipPath',new_unzipPath)
                    # 判断拼接目录是否存在，不存在则创建
                    if not os.path.exists(new_unzipPath):
                        os.mkdir(new_unzipPath)

                    # 给定一个压缩文件形式状态
                    zip_form = True
                    for old_name in zf.namelist():
                        # 由于源码遇到中文是cp437方式，所以解码成gbk，windows即可正常
                        new_name = old_name.encode('cp437').decode('gbk')
                        print('new_name',new_name)
                        if new_name == fileName_suffix[0]+'/':
                            zip_form = False
                            # print('new_name:', new_name, "fileName_suffix[0]+'/'", fileName_suffix[0] + '/')
                            continue
                        # 判断压缩文件形式
                        if zip_form:
                            # 拼接文件的保存路径
                            new_path = os.path.join(new_unzipPath,new_name)
                            # print('new_path',new_path)
                        else:
                            new_path = os.path.join(unzipPath, new_name)
                            # print('new_path', new_path)
                        # 获取文件大小，判断是文件还是文件夹
                        file_size = zf.getinfo(old_name).file_size
                        if file_size > 0:
                            # 是文件夹，通过open创建文件，写入数据
                            with open(new_path, 'wb') as f:
                                f.write(zf.read(old_name))
                        else:
                            # 是文件夹，就创建
                            if not os.path.exists(new_path):
                                os.mkdir(new_path)
                            else:
                                print('%s该文件夹已存在'%new_path)
                    else:
                        batch_number = fileName_suffix[0]
                        return batch_number
            else:
                print('%s该文件不是以.zip结尾的压缩文件'%file_name)
        else:
            print('%s不是一个有效的文件夹路径')
    else:
        print('%s不是一个有效的文件路径'%zipPath)


process_zip(r'C:\Users\EDZ\Desktop\RY570.zip',r'C:\Users\EDZ\Desktop')