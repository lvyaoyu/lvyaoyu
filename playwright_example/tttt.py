# -*- coding: UTF-8 -*-
import time
print('开始')
for i in range(10, 0, -1):
    time.sleep(0.5)
    print(f' - {i}s后开始自动录入数据...')
    time.sleep(0.5)