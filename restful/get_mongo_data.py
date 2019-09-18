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
# Date:   Aug 2018

"""
@file get_mongo_data.py
"""

from __future__ import division
import sys

sys.path.append("../lib/")
from pymongo import MongoClient
from config import getconfig
from ConfigParser import NoOptionError
from logger import logger
import uniout
from helper import time_derivate
from transfer_project_name import define_project_name
from transfer_project_name import find_project
from transfer_project_name import find_gerrit_project

reload(sys)
import re

sys.setdefaultencoding('utf-8')

# 获取mongodb：IP，port,databases
databases = getconfig("mongodb", "dbs")
IP = getconfig("mongodb", "IP")
port = int(getconfig("mongodb", "port"))

client = MongoClient(IP, port)
database = client[databases]


def bug_query(project_name, time):
    """
    获取所有项目的bug列表
    :param project_name: i-stack;食品溯源联动
    :param time: 2018-08-17
    :return: list
    """
    collection_bug = database['all_project_bug']
    query = {"Product": project_name, "Time": time, "Resolution": {'$regex': "---|FIXE|WONT|DUPL|WORK|NEEDINFO"}}
    bug_data_cursor = collection_bug.find(query)
    bug_data_list = []
    for bug_data in bug_data_cursor:
        bug_data_list.append(bug_data)
    return bug_data_list

def bug_list_query(query):
    """
    根据搜索条件获取bug列表
    :param query: 搜索条件表达式，类型为字典
    :param time: 2018-08-17
    :return: list
    """
    collection_bug = database['all_project_bug']
    bug_data_cursor = collection_bug.find(query)
    bug_data_list = []
    for bug_data in bug_data_cursor:
        bug_data_list.append(bug_data)
    return bug_data_list

def case_query(project_name, time):
    """
    获取所有项目的case列表
    :param project_name: istack;istack-pike
    :param time: 2018-08-20
    :return: all_case_list
    """
    all_case_list = []
    collection_case = database['testlink_testcases']
    project_pattern = re.compile(project_name + r'.*')
    query_all_case = {"full_tc_external_id": project_pattern, "data_time": time}
    all_case_cursor = collection_case.find(query_all_case)
    for case in all_case_cursor:
        all_case_list.append(case)
    return all_case_list


def bug_level_init(bug_level_list):
    """
    获取项目bug严重级别
    :param bug_level_list:
    :return: list
    """
    bug_level_dict = {}
    for level in bug_level_list:
        bug_level_dict[level['Sev']] = 0
    bug_level = bug_level_dict.keys()
    return bug_level


def bug_level_distribution(project_name, time):
    """
    获取项目bug严重级别分布并计数
    :param project_name: istack-liberty;istack-pike;食品溯源联动
    :param time: 2018-08-17
    :return:list
    """
    # 函数返回列表：存储项目bug严重级别计数
    bug_level_return = []
    # 存储项目bug级别分布字典
    bug_level_dict = {}
    # 根据项目名称获取bugzilla上对应的项目
    transfer_project = find_project(project_name)
    # 获取i-stack项目feature数分布
    op = "$ne"
    if transfer_project == 'i-stack':
        query = {"Product": transfer_project, "Time": time, "Comp": {op:"需求管理"}, "Vers": "4.0", "Resolution": {'$regex': "---|FIXE|WONT|DUPL|WORK|NEEDINFO"}}
    else:
        query = {"Product": transfer_project, "Time": time, "Comp": {op:"需求管理"}, "Resolution": {'$regex': "---|FIXE|WONT|DUPL|WORK|NEEDINFO"}}
    # 统计项目bug严重级别分布
    bug_data_list = bug_list_query(query)
    bug_level = bug_level_init(bug_data_list)
    for level in bug_level:
        bug_level_dict[level] = 0
    for data in bug_data_list:
        for level in bug_level:
            if data['Sev'] == level:
                bug_level_dict[level] += 1
    # 转化成前端所需格式
    if "fea" in bug_level_dict.keys():
        del bug_level_dict["fea"]
    for key, value in bug_level_dict.items():
        bug_level_return.append({"name": key, "value": value})
    return bug_level_return

def bug_model_distribution(project_name, time):
    """
    获取项目bug模块分布
    project_name:istack-pike;istack;spsy
    time:年-月-日：2018-08-03
    :return: 字典
    """
    # 存储项目bug模块分布字典
    project_bug_model_dict = {}
    # 存储项目bug模块分布列表
    project_bug_model_list = []
    # 统计istack的bug模块分布并计数
    if project_name == 'istack-pike' or project_name == 'istack-liberty':
        istack_bug_model = getconfig("bug_model", "istack_bug_model").split(',')
        for i in range(len(istack_bug_model)):
            project_bug_model_dict[istack_bug_model[i]] = 0
        project = define_project_name(project_name, "bugzilla")
        istack_model_list = bug_query(project, time)
        if istack_model_list:
            for istack_data_model in istack_model_list:
                for i in range(len(istack_bug_model)):
                    if istack_data_model['Comp'] == istack_bug_model[i]:
                        if project_name == 'istack-pike' and istack_data_model['Vers'] == '3（Pik':
                            project_bug_model_dict[istack_bug_model[i]] += 1
                        if project_name == 'istack-liberty' and istack_data_model['Vers'] != '3（Pik':
                            project_bug_model_dict[istack_bug_model[i]] += 1
        if project_name == 'istack-liberty':
            del project_bug_model_dict['平台安全']
    # 统计其他项目的bug模块分布并计数
    else:
        project_model_list = bug_query(project_name, time)
        if project_model_list:
            for model in project_model_list:
                project_bug_model_dict[model['Comp']] = 0
        # 获取项目模块分布名
        project_bug_model = project_bug_model_dict.keys()
        for project_data in project_model_list:
            for i in range(len(project_bug_model)):
                if project_data[u'Comp'] == project_bug_model[i]:
                    project_bug_model_dict[project_bug_model[i]] += 1
        if project_bug_model_dict[u'需求管理']:
            del project_bug_model_dict[u'需求管理']
        # 转换前端所需格式
    for key, value in project_bug_model_dict.items():
        project_bug_model_list.append({'name': key, 'value': value})
    return project_bug_model_list


def testcases_information(project_name, time):
    """
    获取项目case数分布
    project_name；istack;istack-pike
    time:年-月：2018-08
    :return: 字典
    """
    # 初始化存储case字典
    case_dict = {
        "all_cases": 0,
        "automated_cases": 0,
        "auto_percent": 0,
    }
    # 获取i-stack一期的case数分布
    if project_name == 'istack':
        # 统计istack-pike的自动化case数
        auto_case = 0
        # 获取istack的case数分布
        case_list = case_query(project_name, time)
        case_dict["all_cases"] = len(case_list)
        for case in case_list:
            if case["execution_type"] == "2":
                case_dict["automated_cases"] += 1
        # 获取istack-pike的case数分布
        project = 'istack-pike'
        case2_list = case_query(project, time)
        case_dict["all_cases"] = case_dict["all_cases"] - len(case2_list)
        for case in case2_list:
            if case["execution_type"] == "2":
                auto_case += 1
        case_dict["automated_cases"] = case_dict["automated_cases"] - auto_case
    # 获取其他项目的case数分布
    else:
        case_list = case_query(project_name, time)
        case_dict["all_cases"] = len(case_list)
        for case in case_list:
            if case["execution_type"] == "2":
                case_dict["automated_cases"] += 1
    if case_dict["all_cases"]:
        case_dict["auto_percent"] = (case_dict["automated_cases"]) / (case_dict["all_cases"]) * 100
    else:
        case_dict["auto_percent"] = 0
    print "case_dict:"
    print case_dict
    return case_dict


def feature_complicate(project_name, time):
    """
    获取项目总需求个数，以及解决的需求个数
    :param project_name: istack-pike;istack-liberty;其他
    :param time: 2018-08-20
    :return: dict
    """
    # 初始化存数据字典
    final_dict = {
        "fin_feature": 0,
        "all_feature": 0
    }
    # 根据项目名获取bugzilla上对应的项目
    transfer_project = find_project(project_name) 
    # 获取i-stack项目feature数分布
    if transfer_project == 'i-stack':
        query = {"Product": transfer_project, "Time": time, "Comp": "需求管理", "Vers": "4.0", "Resolution": {'$regex': "---|FIXE|WONT|DUPL|WORK|NEEDINFO"}}
    else:
        query = {"Product": transfer_project, "Time": time, "Comp": "需求管理", "Resolution": {'$regex': "---|FIXE|WONT|DUPL|WORK|NEEDINFO"}}
    feature_list = bug_list_query(query)
    final_dict['all_feature'] = len(feature_list)
    for feature in feature_list:
        if feature[u'Status▲'] == "VERI":
            final_dict['fin_feature'] += 1
    return final_dict


def time_data(time_now, interval, point, project_name, type):
    """
    将数据和时间结合转化成前端所需格式
    :param time_now: 从前端所得的显示数据时间
    :param interval: 显示时间间隔
    :param point: 显示时间点数
    :param project_name: 项目名，从前端获取
    :param type: project_case,project_feature,project_patch
    :return:list
    """
    # 存储数据和时间的列表，列表套字典
    data_list_dict = []
    # 获取时间轴
    before_time = time_derivate(time_now, point, interval)
    # type对应的方法调用结果
    result_data = ""
    # 根据时间拿数据
    for d in before_time:
        d = d.strftime('%Y-%m-%d')
        if type == "project_case":
            result_data = testcases_information(project_name, d)
        if type == "project_feature":
            result_data = feature_complicate(project_name, d)
        if type == "project_patch":
            result_data = patch_statistics(project_name, d)
        if type == "project_bughanding":
            result_data = bug_handing(project_name, d)
        data_list_dict.append({'time': d, 'data': result_data})
    return data_list_dict


def bug_handing(project_name, time):
    """
    获取项目bug处理情况
    :param project_name: istack-pike,istack-liberty,其他
    :param time:2018-08-20
    :return:dict
    """
    collection = database.all_project_bug
    final_dict = {}
    time_pattern = re.compile(time + r'.*')
    project = define_project_name(project_name, "bugzilla")
    # 所有项目的bug处理情况的筛选条件
    query_valid_bug = {"Product": project, "Time": time_pattern, "Resolution": {'$nin': ["INVA"]}}
    query_valid_feature = {"Comp": "需求管理", "Product": project, "Time": time_pattern, "Resolution": {'$nin': ["INVA"]}}
    query_resolved_bug = {"Product": project, "Time": time_pattern, "Resolution": {'$nin': ["INVA"]}, "Status▲": "RESO"}
    query_resolved_feature = {"Comp": "需求管理", "Product": project, "Time": time_pattern,
                              "Resolution": {'$nin': ["INVA"]}, "Status▲": "RESO"}
    query_verify_bug = {"Product": project, "Time": time_pattern, "Resolution": {'$nin': ["INVA"]}, "Status▲": "VERI"}
    query_verify_feature = {"Comp": "需求管理", "Product": project, "Time": time_pattern, "Resolution": {'$nin': ["INVA"]},
                            "Status▲": "VERI"}
    # 增加i-stack一期的bug处理情况的筛选条件
    if project_name == "istack-pike":
        query_valid_bug["Vers"] = "3（Pik"
        query_valid_feature["Vers"] = "3（Pik"
        query_resolved_bug["Vers"] = "3（Pik"
        query_resolved_feature["Vers"] = "3（Pik"
        query_verify_bug["Vers"] = "3（Pik"
        query_verify_feature["Vers"] = "3（Pik"
    # 增加i-stack二期的bug处理情况的筛选条件
    elif project_name == "istack-liberty":
        query_valid_bug["Vers"] = {'$regex': "1.0|1.1（可|2.0"}
        query_valid_feature["Vers"] = {'$regex': "1.0|1.1（可|2.0"}
        query_resolved_bug["Vers"] = {'$regex': "1.0|1.1（可|2.0"}
        query_resolved_feature["Vers"] = {'$regex': "1.0|1.1（可|2.0"}
        query_verify_bug["Vers"] = {'$regex': "1.0|1.1（可|2.0"}
        query_verify_feature["Vers"] = {'$regex': "1.0|1.1（可|2.0"}
    else:
        pass
    valid_bug = collection.find(query_valid_bug).count() - collection.find(query_valid_feature).count()
    resolved_bug = collection.find(query_resolved_bug).count() - collection.find(query_resolved_feature).count()
    verify_bug = collection.find(query_verify_bug).count() - collection.find(query_verify_feature).count()
    resolved_bug = resolved_bug + verify_bug
    final_dict[u"有效bug"] = valid_bug
    final_dict[u"已解决"] = resolved_bug
    final_dict[u"已关闭"] = verify_bug
    return final_dict


def patch_statistics(project_name, time):
    """获取项目某一时间点下patch的数量
    
    :param project_name: 项目名称
    :param time: 打点时间
    :return: int, patch个数
    """
    logger("INFO", "project is %s, time is %s" % (project_name, time))
    # 将项目名转化为gerrit上的项目名
    project_name = find_gerrit_project(project_name)
    # mongodb gerrit集合 
    collection = database.gerrit_patch_count
    # 数据打点时间
    time_pattern = re.compile(time + r'.*')
    # 申明patch总数变量
    patch_count = 0
    # 项目对应的gerrit仓库
    git_repo = []
    try:
        git_repo = getconfig("gerrit", project_name).split(",")
    except NoOptionError:
        git_repo.append(project_name)
        logger("WARN", "git repository about %s is not in config.ini" % project_name)
    logger("INFO", "git repository about %s is %s" % (project_name, git_repo))
    # 根据项目判断mongodb查询条件，并获取查询结果
    for i in git_repo:
        if project_name == 'istack-pike':
            query_all= [{"$unwind": "$Resource"}, {"$match": {"Resource.project": i, "Resource.branch": {'$regex': "pike-core"}, "Time": time_pattern}}]
        elif project_name == 'istack-liberty':
            query_all= [{"$unwind": "$Resource"},{"$match": {"Resource.project": i, "Resource.branch": "liberty-core", "Time": time_pattern}}]
        else:
            project_pattern = re.compile(i + r'.*')
            query_all = [{"$unwind": "$Resource"},{"$match": {"Resource.project": project_pattern,"Time": time_pattern}}]
        curor = collection.aggregate(query_all)
        for i in curor:
            count = i["Resource"]["count"]
            logger("INFO", "%s, patch count is %d" % (i, count))
            patch_count = patch_count + count
    logger("INFO", "the total amount of patch is %d" % patch_count)
    return patch_count


def home_feature_bug_patch_data(project_name, time):
    """
    获取项目的总feature,bug;已解决的feature,bug
    :param project_name: istack-pike;istack-liberty;食品溯源联动
    :param time: 2018-08-10
    :return:字典
    """
    return_dict = {}
    # 获取feature
    feature_dict = feature_complicate(project_name, time)
    all_feature = feature_dict['all_feature']
    fix_feature = feature_dict['fin_feature']
    return_dict["fix_fea_num"] = fix_feature
    return_dict["all_fea_num"] = all_feature
    # 获取bug数
    bug_dict = bug_handing(project_name, time)
    all_bug = bug_dict[u'有效bug']
    resolved_bug = bug_dict[u'已关闭']
    return_dict["res_bug_num"] = resolved_bug
    return_dict["all_bug_num"] = all_bug
    # 获取patch
    patch = patch_statistics(project_name, time)
    return_dict["patch_num"] = patch
    return return_dict


def home_case_data(project_name, time):
    """
    获取项目的总case数
    :param project_name: spsyld-1967;istack-pike-1848;istack
    :param time:
    :return:
    """
    case_number = {}
    case_dict = testcases_information(project_name, time)
    case = case_dict['all_cases']
    case_number["case_num"] = case
    return case_number

if __name__ == '__main__':
    project_name = u"i-stack智慧城市操作系统(二期)"
    time = "2019-04-11"
   # res = feature_complicate(project_name, time)
    res =patch_statistics(project_name, time)
    print res
   # time_data("2019-05-23", 7, 7, "i-stack", "project_patch")
   
