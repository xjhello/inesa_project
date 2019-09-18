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
# Author: weijp@rc.inesa.com
# Date:   July 2018

"""
@file gerrit_data.py
"""

import requests
import json
from config import getconfig
import time as tm
import sys
reload(sys)
sys.setdefaultencoding('utf-8')


def get_data_dict(url):
    """
    获取要爬取的数据并将数据转换为字典的形式返回
    :param url:要爬数据的url
    :return: 页面的数据（以字典的形式返回）
    """
    request = requests.get(url)
    # 获取xhr中传递过来的json数据格式
    json_str = request.text
    list = json_str.split(")]}'")
    # 将json数据格式返回成字典
    data_dict = json.loads(''.join(list))
    return data_dict

def get_project_count():
    """
    获取gerrit中所有项目的git信息
    获取gerrit中每一条git的具体信息
    所有数据存在json文件中
    Return: 无
    """
    # 存储project全部gerrit数据信息的json列表
    json_all_gerrit_list = []
    # 存储project一次gerrit数据信息的json列表
    json_one_gerrit_list = []
    # 判断条件，当页面没有数据时调出循环
    judgment = True
    # 分页参数
    count = 0
    # 获取gerrit url
    gerrit_url = getconfig("gerrit", "gerrit_url")
    # gerrit_url = "http://10.200.43.166:8080"
    # 全部project的gerrit信息
    url_list = "%s/changes/?q=status:merged&n=25&O=81" % gerrit_url
    while judgment:
        if count != 0:
            url_list = "%s/changes/?q=status:merged&n=25&O=81&S=%s" % (gerrit_url, count)
        data_dict = get_data_dict(url_list)
        # 判断获取的数据是否为空，为空跳出循环
        if data_dict:
            Timestamp = tm.strftime('%Y-%m-%d', tm.localtime(tm.time()))
            
            for i in data_dict:
                i['Time'] = Timestamp
            json_all_gerrit_list.extend(data_dict)
            for data in data_dict:
                # 获取历史修改的数据
                url_info = "%s/changes/%s/detail?O=404" % (gerrit_url, data['_number'])
                history_dict = get_data_dict(url_info)
                history_dict['Time'] = Timestamp
                # 将数据加入数据列表
                json_one_gerrit_list.append(history_dict)
        else:
            judgment = False
        count = count + 25
    # 将project的总gerrit信息写入json
    with open('all_gerrit.json', 'w') as f:
        json.dump(json_all_gerrit_list, f)
    # 将每次gerrit数据信息写入json
    with open('one_gerrit_information.json', 'w') as f:
        json.dump(json_one_gerrit_list, f)
