# coding: utf-8
import json
import re
import sys
import os
import time
from urllib import parse

import requests

import utility
new_datetime = time.time()
end_datetime = time.strptime('{} 18:30:00'.format(time.strftime('%Y-%m-%d',time.localtime())),"%Y-%m-%d %H:%M:%S")
surplus_time = int(time.mktime(end_datetime)-new_datetime)
print(surplus_time)

