# -*- coding: UTF-8 -*-
import os
import zipfile


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
    z = zipfile.ZipFile(zip_file_path,'w',zipfile.ZIP_DEFLATED)
    for dir_path, dir_names, file_names in os.walk(folder_path):
        f_path = dir_path.replace(folder_path,'')
        f_path = f_path and f_path + os.sep or ''
        for file_name in file_names:
            z.write(os.path.join(dir_path,file_name),f_path+file_name)
            print('压缩成功')
    z.close()


zip_folder(r'C:\Users\EDZ\PycharmProjects\portal-tmp\web\static\download\HASLK01201008203',
           r'C:\Users\EDZ\PycharmProjects\portal-tmp\web\static\download\xxx.zip')
