import logging
import logging.handlers
import sys
import aiohttp
import asyncio
import urllib
import time
import requests
import configparser

import queue
from logging.handlers import QueueHandler, QueueListener

cf = configparser.ConfigParser()
cf.read("config.conf", encoding="utf-8-sig")  # 带有签名的utf-8
serial_no = cf.get("worker", "serial_no")
robot_secret = cf.get("worker", "robot_secret")
log_url = cf.get("worker", "log_url")


class RemoteLogHandler(logging.Handler):
    def emit(self, record):
        headers = {
            "serial-no": serial_no,
            "robot-secret": robot_secret,
        }

        payload = {
            "logs": [
                {
                    "content": record.msg,
                    "level": record.levelno
                },
            ]
        }

        res = requests.post(log_url, headers=headers, json=payload)
        # print(res.text)


log_queue = queue.Queue(0)
remote_handler = RemoteLogHandler()
remote_listener = QueueListener(log_queue, remote_handler)
remote_listener.start()

# 初始化logger
logger = logging.getLogger("uniner")
logger.setLevel(logging.DEBUG)
# 设置日志格式
fmt = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s', '%Y-%m-%d %H:%M:%S')

# 添加cmd handler
cmd_handler = logging.StreamHandler(sys.stdout)
cmd_handler.setLevel(logging.DEBUG)
cmd_handler.setFormatter(fmt)

# 添加文件的handler
file_handler = logging.handlers.TimedRotatingFileHandler(filename="logs\\log.txt", encoding='utf-8', when="D",
                                                         interval=1, backupCount=31)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(fmt)

# 添加http handler
queue_handler = QueueHandler(log_queue)
queue_handler.setLevel(logging.INFO)
queue_handler.setFormatter(fmt)

# 将handlers添加到logger中
logger.addHandler(cmd_handler)
logger.addHandler(file_handler)
logger.addHandler(queue_handler)

# logger.debug("今天天气不错")
