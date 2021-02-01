# -*- coding:utf-8 -*-
import json
import datetime
import decimal
import uuid
import os
import random
import re
import time
import base64
import hashlib
import hmac
import requests
import logging
import configparser
import subprocess
import sys

from logging.handlers import TimedRotatingFileHandler
from logging.handlers import RotatingFileHandler
from http.client import HTTPConnection
from binascii import *
from Crypto.Hash import MD5
from Crypto.Cipher import DES, AES
from Crypto.Util.Padding import pad, unpad
from Crypto.Util.py3compat import *
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5 as Cipher_pkcs1_v1_5
from Crypto.Signature import PKCS1_v1_5 as Signature_pkcs1_v1_5
from Crypto import Random

ENABLE_QUICK_EDIT_MODE = 0x40
ENABLE_EXTENDED_FLAGS = 0x80

cf = configparser.ConfigParser()
cf.read("config.conf", encoding="utf-8-sig")  # 带有签名的utf-8
timeout = cf.getint("worker", "timeout")

requests.packages.urllib3.disable_warnings()


# int(x [,base ])         将x转换为一个整数
# long(x [,base ])        将x转换为一个长整数
# float(x )               将x转换到一个浮点数
# complex(real [,imag ])  创建一个复数
# str(x)                 将对象 x 转换为字符串
# repr(x)                将对象 x 转换为表达式字符串
# eval(str)              用来计算在字符串中的有效Python表达式,并返回一个对象
# tuple(s)               将序列 s 转换为一个元组
# list(s)                将序列 s 转换为一个列表
# chr(x)                 将一个整数转换为一个字符
# unichr(x)              将一个整数转换为Unicode字符
# ord(x)                 将一个字符转换为它的整数值
# hex(x)                 将一个整数转换为一个十六进制字符串
# oct(x)                 将一个整数转换为一个八进制字符串

# str.encode(s)   # str to bytes
# bytes.decode(b) # bytes to str


# --------------------Help--------------------

class CJsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(obj, datetime.date):
            return obj.strftime("%Y-%m-%d")
        elif isinstance(obj, decimal.Decimal):
            return str(obj)
        else:
            return json.JSONEncoder.default(self, obj)


def get_json(dict):
    return json.dumps(dict, cls=CJsonEncoder)


def get_dict(str):
    return json.loads(str)


# version1是否大于等于version2
def compare_version(version1, version2):
    v1 = version1.split(".")
    v2 = version2.split(".")

    if len(v1) != len(v2):
        return False

    for i in range(len(v1)):
        if int(v1[i]) < int(v2[i]):
            return False
        elif int(v1[i]) > int(v2[i]):
            return True

    return True


def str_contains(str, sub, sep=","):
    str_list = str.split(sep)
    str_list = [x.strip() for x in str_list]  # trim一下
    str_list = list(filter(lambda x: x.strip(), str_list))  # 去掉空字符串
    if sub in str_list:
        return True
    else:
        return False


def str_split(str, sep=","):
    str_list = str.split(sep)
    str_list = [x.strip() for x in str_list]  # trim一下
    str_list = list(filter(lambda x: x.strip(), str_list))  # 去掉空字符串
    return str_list


def get_file_mtime(path):
    t = os.path.getmtime(path)
    return int(t)


def get_file_size(path):
    size = os.path.getsize(path)
    return size


def get_short(text, length):
    if len(text) > length:
        return text[0:length] + "..."
    else:
        return text


def get_all_files(path):
    all_files = []
    for root, dirs, files in os.walk(path):
        for name in files:
            all_files.append((name, root, os.path.join(root, name)))
            print(root)
        for name in dirs:
            # all_files.append(os.path.join(root, name))
            pass
    return all_files


def dt_2_dts(date_time):
    return date_time.strftime('%Y-%m-%d %H:%M:%S')


def dts_2_dt(date_time_string):
    return datetime.datetime.strptime(date_time_string, '%Y-%m-%d %H:%M:%S')


def ts_2_dts(time_stamp):
    time_struct = time.localtime(time_stamp)
    return time.strftime('%Y-%m-%d %H:%M:%S', time_struct)


def dts_2_ts(date_time_string):
    time_struct = time.strptime(date_time_string, '%Y-%m-%d %H:%M:%S')
    return int(time.mktime(time_struct))


def dt_2_ts(date_time):
    return int(time.mktime(date_time.timetuple()))


def ts_2_dt(time_stamp):
    return datetime.datetime.fromtimestamp(time_stamp)


def int_2_str(number, base):
    convertString = "0123456789ABCDEF"  # 最大转换为16进制
    if number < base:
        return convertString[number]
    else:
        return int_2_str(number // base, base) + convertString[number % base]


def get_current_time(dt=datetime.datetime.now()):
    return datetime.datetime.strftime(dt, '%Y-%m-%d %H:%M:%S')


def get_current_date(dt=datetime.datetime.now()):
    return datetime.datetime.strftime(dt, '%Y-%m-%d')


def get_current_timestamp13():
    return round(time.time() * 1000)


def get_current_timestamp10():
    return int(time.time())


def get_date_list(days):
    result = []

    current_date = datetime.datetime.now()

    for i in range(days):
        date_str = current_date.strftime("%Y-%m-%d")
        result.append(date_str)

        current_date -= datetime.timedelta(days=1)

    return result


def format_file_size(size):
    KB = 1024
    MB = 1024 * KB
    GB = 1024 * MB
    TB = 1024 * GB

    if size > TB:
        return "%.2f TB" % (size / TB)
    elif size > GB:
        return "%.2f GB" % (size / GB)
    elif size > MB:
        return "%.2f MB" % (size / MB)
    elif size > KB:
        return "%.2f KB" % (size / KB)
    else:
        return "%d Byte" % (size)


def get_rand_string(len, force=False):
    result = ""

    while True:
        seed = "1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"

        sa = []
        for i in range(len):
            sa.append(random.choice(seed))
        result = ''.join(sa)

        if not force:
            break

        if re.search('[a-z]', result) and re.search('[A-Z]', result) and re.search('[0-9]', result):
            break

    return result


# --------------------Crypt--------------------

def get_md5(plain, salt=""):
    obj = MD5.new()
    obj.update("{}{}".format(plain, salt).encode("utf-8"))  # gb2312 Or utf-8
    cipher = obj.hexdigest()
    return cipher


def get_hmac_sha265(plain, key=None):
    if key == None:
        key = "money888"

    cipher = hmac.new(key.encode('utf-8'), plain.encode('utf-8'), digestmod=hashlib.sha256).digest()
    cipher = base64.b64encode(cipher)
    return str(cipher, 'utf-8')


def get_file_md5(path):
    chunk_size = 8192
    obj = MD5.new()
    with open(path, 'rb') as f:
        while True:
            chunk = f.read(chunk_size)
            if len(chunk):
                obj.update(chunk)
            else:
                break

    cipher = obj.hexdigest()
    return cipher


def get_file_base64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


# https://en.wikipedia.org/wiki/Padding_(cryptography)#Zero_padding
def pad(data_to_pad, block_size, style='pkcs7'):
    padding_len = block_size - len(data_to_pad) % block_size  # 1-8
    if style == 'pkcs7':
        padding = bchr(padding_len) * padding_len
    elif style == 'x923':
        padding = bchr(0) * (padding_len - 1) + bchr(padding_len)
    elif style == 'iso7816':
        padding = bchr(128) + bchr(0) * (padding_len - 1)  # iso7816时填充长度为1-8
    elif style == 'zero':
        padding = bchr(0) * (padding_len % block_size)  # zero时填充长度为0-7
    else:
        raise ValueError("Unknown padding style")
    return data_to_pad + padding


def unpad(padded_data, block_size, style='pkcs7'):
    pdata_len = len(padded_data)
    if pdata_len % block_size:
        raise ValueError("Input data is not padded")
    if style in ('pkcs7', 'x923'):
        padding_len = bord(padded_data[-1])
        if padding_len < 1 or padding_len > min(block_size, pdata_len):
            raise ValueError("Padding is incorrect.")
        if style == 'pkcs7':
            if padded_data[-padding_len:] != bchr(padding_len) * padding_len:
                raise ValueError("PKCS#7 padding is incorrect.")
        else:
            if padded_data[-padding_len:-1] != bchr(0) * (padding_len - 1):
                raise ValueError("ANSI X.923 padding is incorrect.")
    elif style == 'iso7816':
        padding_len = pdata_len - padded_data.rfind(bchr(128))
        if padding_len < 1 or padding_len > min(block_size, pdata_len):
            raise ValueError("Padding is incorrect.")
        if padding_len > 1 and padded_data[1 - padding_len:] != bchr(0) * (padding_len - 1):
            raise ValueError("ISO 7816-4 padding is incorrect.")
    elif style == 'zero':
        padding_len = pdata_len - len(padded_data.rstrip(bchr(0)))
        if padding_len < 0 or padding_len > min(block_size, pdata_len) - 1:
            raise ValueError("Padding is incorrect.")
        if padding_len > 0 and padded_data[-padding_len:] != bchr(0) * padding_len:
            raise ValueError("Zero padding is incorrect.")
    else:
        raise ValueError("Unknown padding style")
    return padded_data if padding_len == 0 else padded_data[:-padding_len]


def des_encode(plain, key=None):
    if key == None:
        key = "money888"

    # MODE_CBC need IV
    obj = DES.new(key.encode('utf-8'), DES.MODE_ECB)
    plain = plain.encode("utf-8")
    plain = pad(plain, 8, "zero")
    cipher = hexlify(obj.encrypt(plain))
    return cipher.decode("utf-8")


def des_decode(cipher, key=None):
    if key == None:
        key = "money888"

    obj = DES.new(key.encode('utf-8'), DES.MODE_ECB)
    plain = obj.decrypt(unhexlify(cipher))
    plain = unpad(plain, 8, "zero")
    return plain.decode("utf-8")


def aes_encode(plain, key=None, padding="zero", is_hex=True):
    if key == None:
        key = "money888money888"

    # MODE_CBC need IV
    obj = AES.new(key.encode('utf-8'), AES.MODE_ECB)
    plain = plain.encode("utf-8")
    plain = pad(plain, 16, padding)
    if is_hex:
        cipher = hexlify(obj.encrypt(plain))
    else:
        cipher = base64.b64encode(obj.encrypt(plain))
    return cipher.decode("utf-8")


def aes_decode(cipher, key=None, padding="zero", is_hex=True):
    if key == None:
        key = "money888money888"

    obj = AES.new(key.encode('utf-8'), AES.MODE_ECB)
    if is_hex:
        plain = obj.decrypt(unhexlify(cipher))
    else:
        plain = obj.decrypt(base64.b64decode(cipher))
    plain = unpad(plain, 16, padding)
    return plain.decode("utf-8")


def base64_encode(plain, is_url_safe=False):
    if is_url_safe:
        cipher = base64.urlsafe_b64encode(plain.encode('utf-8'))
    else:
        cipher = base64.b64encode(plain.encode('utf-8'))
    return str(cipher, 'utf-8')


def base64_decode(cipher, is_url_safe=False):
    if is_url_safe:
        plain = base64.urlsafe_b64decode(cipher.encode('utf-8'))
    else:
        plain = base64.b64decode(cipher.encode('utf-8'))
    return str(plain, 'utf-8')


def hex_encode(plain):
    return str(hexlify(plain.encode('utf-8')), 'utf-8')


def hex_decode(cipher):
    return str(unhexlify(cipher), 'utf-8')


# https://www.jb51.net/article/86022.htm
# plain 最大长度是 证书key位数/8 - 11
def rsa_encode(plain, key=None, is_hex=True):
    if key == None:
        # PEM编码
        key = '''-----BEGIN PUBLIC KEY-----
MIGdMA0GCSqGSIb3DQEBAQUAA4GLADCBhwKBgQC7ekIJqelqVK+oQr0Pq1zZUr3V20gBtAko
lvBMQQtSbq57fEi1gR+gAssvbXp0PzCESY/qOMXnwNFSg3OQevNzuXJF97Jd0uMBKum0fAey
aHjSby/W9MWymcrM1DF1C0dsqWD9mIPYi25mdtcTG1PZLzN8c2/57syui+Zt+7e65QIBEQ==
-----END PUBLIC KEY-----'''

    rsakey = RSA.importKey(key)

    obj = Cipher_pkcs1_v1_5.new(rsakey)
    plain = plain.encode("utf-8")
    if is_hex:
        cipher = hexlify(obj.encrypt(plain))
    else:
        cipher = base64.b64encode(obj.encrypt(plain))
    return cipher.decode("utf-8")


def rsa_decode(cipher, key=None, is_hex=True):
    if key == None:
        # PEM编码
        key = '''-----BEGIN RSA PRIVATE KEY-----
MIICdQIBADANBgkqhkiG9w0BAQEFAASCAl8wggJbAgEAAoGBALt6Qgmp6WpUr6hCvQ+rXNlS
vdXbSAG0CSiW8ExBC1Jurnt8SLWBH6ACyy9tenQ/MIRJj+o4xefA0VKDc5B683O5ckX3sl3S
4wEq6bR8B7JoeNJvL9b0xbKZyszUMXULR2ypYP2Yg9iLbmZ21xMbU9kvM3xzb/nuzK6L5m37
t7rlAgERAoGAWDmIfQSqE+ud9NQcvBRn7cyVkdCaWyeL1t2eQgB9zHBSG/5AVWnww8UUUo3f
RcNiICKeE957P+JEYxCu2pQ2U8RGC8pYSpTutzfW8PfGt7ierAcgmvgKMSYEK0F8UMVvjD36
5SaW2/GFG2ye19pMsTVqa6SGuIPQA2d3q+veA1ECQQDGIrk9cvL9ncsuIuT2tCgtZToXBUcj
Ib+PFBa3whsR7ckEkTLh+EH9X/cZDWphall8KjCBke/SSNXaSq/gB1hLAkEA8jqzrEPMWMnw
ph4Pds1D0sJqyQVGgo5Kme3aMUcuVcyZoRqjxIsDLNOVFvgeCgaHIYcnND/CBGnRdb1wxnib
jwJAOkZyt7hlleMdpChhdbyESZY+QwGNZK+SsZx/JvzayQmzl+54YJRPpN/9Ybim0VuDuxt3
raNkp0KZQDQVnD5lQwJBAKr8Qpe3YxF/fLF+oYEJXQ098QZeE6dzf/QvbNd9ih5yTlOaVXut
a6cr8MTrYH+MIya5wVIO405o0BbgE17ruRkCQQCdA7A8v9jnxLsWgorAh7h6b/yH6i1dsyEt
Mtb0U3j1tMnwb7Xs2y6fYKeEyOzNF6gbzSv0tLs396zJkFJvkwAE
-----END RSA PRIVATE KEY-----'''

    # 伪随机数生成器
    random_generator = Random.new().read

    rsakey = RSA.importKey(key)

    obj = Cipher_pkcs1_v1_5.new(rsakey)
    if is_hex:
        plain = obj.decrypt(unhexlify(cipher), random_generator)
    else:
        plain = obj.decrypt(base64.b64decode(cipher), random_generator)
    return plain.decode("utf-8")


def get_uuid():
    return str(uuid.uuid4())  # uuid1机器码


# print(os.urandom(10))
# print(hexlify(os.urandom(10)))
# print(ascii(hexlify(os.urandom(10))))

# --------------------Http--------------------

def get(url, params=None, headers=None, proxies=None):
    res = requests.get(url, params=params, headers=headers, timeout=timeout, proxies=proxies, verify=False)
    # print(url, res.text)
    return res


def post(url, json=None, data=None, headers=None, proxies=None):
    '''
    data与json既可以是str类型，也可以是dict类型。
    区别：
    1、不管json是str还是dict，如果不指定headers中的content-type，默认为application/json
    2、data为dict时，如果不指定content-type，默认为application/x-www-form-urlencoded，相当于普通form表单提交的形式
    3、data为str时，如果不指定content-type，默认为application/json
    4、用data参数提交数据时，request.body的内容则为a=1&b=2的这种形式，用json参数提交数据时，request.body的内容则为'{"a": 1, "b": 2}'的这种形式
    '''
    res = requests.post(url, json=json, data=data, headers=headers, timeout=timeout, proxies=proxies,
                        verify=False)  # data:application/x-www-form-urlencoded, json:application/json
    # print(url, res.text)
    return res


def get_current_ip(proxy=None):
    res = requests.get('http://gpt5.com/ip/my.php', timeout=timeout, proxies=proxy)
    # print(res.text)
    dic = json.loads(res.text)
    return dic["ip"]


def get_and_remove_line(file_name):
    ret = ""
    f = open(file_name, "r+", encoding='utf-8')
    d = f.readlines()
    f.seek(0)
    for i in d:
        if ret == "":
            ret = i
            continue
        f.write(i)
    f.truncate()
    f.close()
    return ret.strip()


'''
模式	可做操作	若文件不存在	是否覆盖
r	只能读	报错	-
r+	可读可写	报错	是
w	只能写	创建	是
w+　可读可写	创建	是
a　　只能写	创建	否，追加写
a+	可读可写	创建	否，追加写
'''


def get_rand_line(file_name):
    with open(file_name, "r", encoding='utf-8') as f:
        lines = f.readlines()

    return random.choice(lines).strip()


# --------------------Log--------------------
def clear_data(file_name="data.txt"):
    try:
        os.remove(file_name)
    except:
        pass


def write_data(data, file_name="data.txt", encoding='utf-8'):
    with open(file_name, 'a+', encoding=encoding) as f:
        f.write(data)


def read_data(file_name="data.txt", encoding='utf-8'):
    with open(file_name, 'a+', encoding=encoding) as f:
        f.seek(0)
        return f.read()


def launch_app(path, args):
    ret = subprocess.Popen(path + " " + args)
    return ret


# ------------------机器人工作台------------------------

def post_file(filename):
    base_url = cf['worker']['base_url']
    serial_no = cf['worker']['serial_no']
    robot_secret = cf['worker']['robot_secret']

    url = f'{base_url}/task/update_output'
    headers = {
        'serial-no': serial_no,
        'robot-secret': robot_secret
    }
    data = None
    files = {'file': (filename, open('data/'+filename, 'rb'))}
    r = requests.post(url, data,headers=headers, files=files)

def get_download_url(filename):
    base_url = cf['worker']['base_url']
    serial_no = cf['worker']['serial_no']
    robot_secret = cf['worker']['robot_secret']

    url = f'{base_url}/task/download/{filename}?serial-no={serial_no}&robot-secret={robot_secret}'
    return url

# # --------------------Windows--------------------
# if os.name == "nt":
#     import win32console
#     def quick_edit_mode(turn_on=True):
#         if os.name != "nt" or not sys.stdout.isatty():
#             return
#
#         """ Enable/Disable windows console Quick Edit Mode """
#         screen_buffer = win32console.GetStdHandle(-10)
#         orig_mode = screen_buffer.GetConsoleMode()
#         is_on = (orig_mode & ENABLE_QUICK_EDIT_MODE)
#
#         if turn_on:
#             new_mode = orig_mode | ENABLE_QUICK_EDIT_MODE
#         else:
#             new_mode = orig_mode & ~ENABLE_QUICK_EDIT_MODE
#
#         screen_buffer.SetConsoleMode(new_mode | ENABLE_EXTENDED_FLAGS)
