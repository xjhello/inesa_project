#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright 2017 INESA (Group) Co., Ltd. R&D Center
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
#
# Author: wuzl@rc.inesa.com
# Date:   July 2018

"""
@file bugzilla.py
"""

import requests
import xml.etree.ElementTree as et
import pandas as pd
import webbrowser
from bs4 import BeautifulSoup
import time as tm
import xlrd
import csv
import sys
reload(sys)
sys.setdefaultencoding('utf-8')


def bug_info(url_info):
    """
    获取bug列表信息，并将信息写入excel文件和csv文件中
    :param url_info:获取列表的url
    :return: bug列表的个数
    """
    # 表格的头部信息列表
    th_list = []
    # 表格每一行的信息类别
    tr_list = []
    # 获取页面信息
    request_test = requests.get(url_info)
    content_html = request_test.content.decode('utf-8')
    soup = BeautifulSoup(content_html, features='lxml')
    # 查找页面中所有的tr标签
    items = soup.find_all('tr')
    length = len(items)
    index = list(range(1, length))
    # 使用for循环输出每条tr的信息
    for item in items:
        td_list = []
        # 获取tr中的td
        td_info = item.find_all('td')
        # 获取tr中的th
        th_info = item.find_all('th')
        # 判段tr中是否有th,如果存在就将内如加入th_list列表中
        if th_info:
            for th in th_info:
                th_list.append(th.a.get_text())
        # 判段tr中是否有td,如果存在就将内如加入td_list列表中
        if td_info:
            for td in td_info:
                tar_info = str(td.get_text())
                str_info = tar_info.replace("\n", '')
                td_list.append(''.join(str_info.split()))
        if td_list:
            tr_list.append(td_list)
    # 将信息存入
    df = pd.DataFrame(tr_list, columns=th_list, index=index)
    # 获取日期
    Timestamp = tm.strftime('%Y-%m-%d', tm.localtime(tm.time()))
    writer = pd.ExcelWriter('bug_info.xlsx')
    df.to_excel(writer, 'Sheet1')
    writer.save()
    data_xls = pd.read_excel('bug_info.xlsx', index_col=0)
    data_xls['Time'] = Timestamp
    data_xls.to_csv('bug_info.csv', encoding='utf-8')
    return length-1


def bug_history(url_history):
    """
    获取bug的历史修改信息列表，并将信息存入到bug_history.xml中
    :param url_history: bug历史信息url
    :return:无
    """
    # xml文件根元素
    xml_root = et.Element('history')
    # 获取请求页面
    request_test = requests.get(url_history)
    webbrowser.open(request_test.url)
    content_html = request_test.content.decode('utf-8')
    soup = BeautifulSoup(content_html, features='lxml')
    # 获取页面中所有的tr标签
    items = soup.find_all('tr')
    # 用于存取th标签中的值
    table_th_values = []
    # 用于存取td标签中的值
    td_list = []
    # 获取所有的th和td标签中的值，并将值存入th_list[]和table_th_values[]中
    for item in items:
        table_td_values = []
        table_th = item.find_all('th')
        if table_th:
            for th in table_th:
                table_th_values.append(th.string)

        table_td = item.find_all('td')
        if table_td:
            for td in table_td:
                # print(td.string)
                str_td = str(td.string).replace("\n", '')
                table_td_values.append(''.join(str_td.split()))
        if table_td_values:
            td_list.append(table_td_values)
    # 将table_th_values和td_list中的值写入bug_history.xml文件中
    for td in td_list:
        if len(td) == 5:
            root = et.Element("bug_history")
            root.attrib = {table_th_values[0]: td[0], table_th_values[1]: td[1]}
            xml = et.Element("change")
            xml.attrib = {table_th_values[2]: td[2], table_th_values[3]: td[3], table_th_values[4]: td[4]}
            root.append(xml)
            xml_root.append(root)
        else:
            xml = et.Element("change")
            xml.attrib = {table_th_values[2]: td[0], table_th_values[3]: td[1], table_th_values[4]: td[2]}
            root.append(xml)
    et.ElementTree(xml_root).write('bug_history.xml', encoding='utf-8', xml_declaration=True)


def bug_content(url_content):
    """
    获取bug的描述信息，并将结果存入bug_content.xml中
    :param url_content:页面url
    :return:无
    """
    # 对bug进行处理的人
    user_list = []
    # 提交bug的时间
    time_list = []
    # bug的描述信息
    description_list = []
    request_test = requests.get(url_content)
    content_html = request_test.content.decode('utf-8')
    soup = BeautifulSoup(content_html,features='lxml')
    # 获取每一次bug处理的所有信息
    content_list = soup.find_all('div', {"class": "bz_comment"})
    # 分别获取bug的创建时间,创建的人,和描述.并将这些信息存到对应的列表中
    for content in content_list:
        content_comments = content.find('pre', {"class": "bz_comment_text"})
        content_user = content.find('span', {"class": "fn"})
        content_time = content.find('span', {"class": "bz_comment_time"})
        if content_comments.string is None:
            content_comments = content.find('a', {"name": "attach_44"})
           # comments = content_comments['title']
            comments = 'None'
        else:
            comments = content_comments.string
        user = content_user.string
        time = content_time.string
        time = ''.join(time.split())
        user_list.append(user)
        time_list.append(time)
        description_list.append(comments)
    # 将信息存入到bug_content.xml中
    root = et.Element("bug")
    root.attrib = {"user": user_list[0], "time": time_list[0], "description": description_list[0]}
    for i in list(range(1,len(user_list))):
        xml = et.Element("content")
        xml.attrib = {"user": user_list[i], "time": time_list[i], "comments": description_list[i]}
        root.append(xml)
    et.ElementTree(root).write('bug_content.xml', encoding='utf-8', xml_declaration=True)


