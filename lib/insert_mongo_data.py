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
@file insert_mongo_data.py
"""

from pymongo import MongoClient
import xmltodict
import json
from logger import logger
from testlink_data import get_project
from testlink_data import get_testcase
from testlink_data import get_testplan
from testlink_data import get_testplan_build
from testlink_data import get_testcase_exec_result
from testlink_data import get_custom_fields
from bugzilla_data import *
from gerrit_data import get_project_count
from config import getconfig
reload(sys)
sys.setdefaultencoding('utf-8')

# 连接数据库
mongodb_ip = getconfig("mongodb", "IP")
mongodb_port = int(getconfig("mongodb", "port"))
client = MongoClient(mongodb_ip, mongodb_port)
dbs = getconfig("mongodb", "dbs")
database = client[dbs]


def all_project_bug():
    """
    获取所有项目的bug信息,将数据存入mongodb
    Return:无
    """
    collection_all_project_bug = database['all_project_bug']
    all_project_bug_url = getconfig("bugzilla", "all_project_bug_url")
    # 调用bugzilla_data里面的bug_info函数，将所有项目的bug信息存入.csv文件
    bug_info(all_project_bug_url)
    # 读取csv文件
    csvfile = file('bug_info.csv', 'rb')
    csv_reader = csv.DictReader(csvfile)
    for i in range(3, 10003):
        for row in csv_reader:
            collection_all_project_bug.insert(row)
    print "insert all_project_bug to mongodb successfully"
    csvfile.close()


def all_bug_history():
    """
    根据生成的csv文件的ID获取所有bug的历史信息，将数据存入mongodb
    Return:无
    """
    csvfile = file('bug_info.csv', 'rb')
    csv_reader = csv.DictReader(csvfile)
    collection_all_bug_history = database['all_bug_history']
    for i in range(3, 10003):
        for row in csv_reader:
            all_bug_history_url = getconfig("bugzilla", "all_bug_history_url")
            all_bug_history_url = all_bug_history_url + row['ID']
            # 调用bugzilla里的bug_history函数,生成bug历史信息的xml文件
            bug_history(all_bug_history_url)
            # 获取xml文件
            xml_file = open('bug_history.xml', 'r')
            # 读取xml文件内容
            xml_str = xml_file.read()
            # 将读取的xml内容转为json
            convertedDict = xmltodict.parse(xml_str)
            jsonStr = json.dumps(convertedDict, indent=1)
            fileObject = open('bug_history.json', 'w')
            fileObject.write(jsonStr)
            fileObject.close()
            filename = 'bug_history.json'
            Timestamp = tm.strftime('%Y-%m-%d', tm.localtime(tm.time()))
            with open(filename, 'r') as f:
                content = json.load(f)
                content['ID'] = row['ID']
                content['Time'] = Timestamp
                collection_all_bug_history.insert_one(content)
    print "insert all_bug_history to mongodb successfully"


def all_bug_content():
    """
    根据生成的csv文件的ID获取每条bug的具体内容信息，将数据存入mongodb
    Return:无
    """
    csvfile = file('bug_info.csv', 'rb')
    csv_reader = csv.DictReader(csvfile)
    collection_all_bug_content = database['all_bug_content']
    for i in range(3, 10003):
        for row in csv_reader:
            all_bug_content_url = getconfig("bugzilla", "all_bug_content_url")
            all_bug_content_url = all_bug_content_url + row['ID']
            # 调用bugzilla里的bug_content函数，生成bug内容信息的xml文件
            bug_content(all_bug_content_url)
            # 获取xml文件
            xml_file = open('bug_content.xml', 'r')
            # 读取xml文件内容
            xml_str = xml_file.read()
            # 将读取的xml内容转为json
            convertedDict = xmltodict.parse(xml_str)
            jsonStr = json.dumps(convertedDict, indent=1)
            fileObject = open('bug_content.json', 'w')
            fileObject.write(jsonStr)
            fileObject.close()
            filename = 'bug_content.json'
            Timestamp = tm.strftime('%Y-%m-%d', tm.localtime(tm.time()))
            with open(filename, 'r') as f:
                content = json.load(f)
                content['ID'] = row['ID']
                content['Time'] = Timestamp
                collection_all_bug_content.insert_one(content)
    print "insert all_bug_content to mongodb successfully"


def testlink_to_mongodb():
    """将testlink数据插入mongodb."""
    # 插入testlink 项目信息
    collection_project = database['testlink_projects']
    projects = get_project()
    collection_project.insert_many(projects)
    logger("INFO", "insert testlink_projects to mongodb successfully")

    # 插入testlink测试用例信息
    collection_testcase = database['testlink_testcases']
    testcases = get_testcase()
    collection_testcase.insert_many(testcases)
    logger("INFO", "insert testlink_testcases to mongodb successfully")

    # 插入testlink测试计划信息
    collection_testplan = database['testlink_testplans']
    testplans = get_testplan()
    collection_testplan.insert_many(testplans)
    logger("INFO", "insert testlink_testplans to mongodb successfully")

    # 插入testlink测试计划版本信息
    collection_testplan_build = database['testlink_testplan_builds']
    testplan_builds = get_testplan_build()
    collection_testplan_build.insert_many(testplan_builds)
    logger("INFO", "insert testlink_testplan_builds to mongodb successfully")

    # 插入testlink测试用例执行结果信息
    collection_testcase_exec = database['testlink_testcase_exec_result']
    testcase_exec_result = get_testcase_exec_result()
    collection_testcase_exec.insert_many(testcase_exec_result)
    logger("INFO", "insert testlink_testcase_exec_result to mongodb successfully")

    # 插入testlink自定义字段信息
    collection_custom_fields = database['testlink_custom_fields']
    custom_fields = get_custom_fields()
    collection_custom_fields.insert_many(custom_fields)
    logger("INFO", "insert testlink_custom_fields to mongodb successfully")


def gerrit_to_mognodb():
    """将gerrit信息存入mongodb"""
    #生成all_gerrit.json,one_gerrit_information.json两个json文件"""
    get_project_count()
    # 插入gerrit所有项目git信息"""
    collection_all_gerrit = database['gerrit_all_project']
    filename = 'all_gerrit.json'
    # Timestamp = tm.strftime('%Y-%m-%d', tm.localtime(tm.time()))
    with open(filename, 'r') as f:
        content = json.load(f)
        # time_dict = {'Time':Timestamp}
        # content.append(time_dict)
        collection_all_gerrit.insert_many(content)
    print "insert gerrit_all_project to mongogodb successfully"
    # 插入每一条gerrit的具体信息
    collection_one_gerrit = database['gerrit_one_information']
    filename = 'one_gerrit_information.json'
    with open(filename, 'r') as f:
        content = json.load(f)
        # time_dict = {'Time':Timestamp}
        # content.append(time_dict)
        collection_one_gerrit.insert_many(content)
    print "insert gerrit_one_information to mongogodb successfully"

