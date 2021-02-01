import pandas as pd
import numpy as np
from pandas import Series, DataFrame
import xlrd
"""
Series 一维 带有标签的同构类型数组
DataFrame 二维 表格结构、带有标签、大小可变的包含异构类型数据列
"""
fileName = '数据1.xlsx'
df1 = pd.read_excel(fileName,sheet_name='Sheet1')
print(df1)
# print(df1.head()) # 默认读取前5行
print("="*10)

# print(pd.read_excel(fileName,sheet_name=1))
# print("="*10)
# print(pd.read_excel(fileName,sheet_name=['Sheet1','Sheet2']))
print(df1.index)
print(df1.values)
print(df1.values[0]) # 读取单行
print("="*10)
print(df1.values[[1,2]]) # 读取多行
print("="*10)
print(df1.values[1,2]) # 读取索引为[1,2]的值
print("="*10)
print(df1.columns) # 查看列名
print("="*10)
print(df1.dtypes) # 查看各列数据类型
print("="*10)
print(df1.loc[:,'序号':'姓名']) # 选择‘序号’列到‘姓名’列的数据
print("="*10)
df1['身高']=170 # 添加列并全部赋值为170
print(df1)
print("="*10)
df1 = df1.drop(['身高'],axis=1)# 删除'身高列'
# print(df1.drop(['身高'],axis=1)) # drop删除并返回新的
print(df1)
print("="*10)
df1['余额'] = [np.nan,120,np.nan,'',1000,2000,4000,np.nan,10]
print(df1)
print("="*10)
# print(df1.isnull())
# print("="*10)
# print(df1['余额'][df1['余额'].isnull()]
# df1['余额'] = df1['余额'].isnull()
print(df1['余额'])
df1['余额']=df1['余额'].fillna(0)
print(df1)
# print("="*10)
# print(df1[df1['余额'].isnull()])
# print(df1)

print("="*10)
clean_z = df1['余额']
print(clean_z)
clean_z[clean_z==''] = 'hello'
df1['余额'] = clean_z
print(df1)

# print(df1['余额'] == '')

