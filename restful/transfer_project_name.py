# coding:utf-8

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
# Author: zhounh@rc.inesa.com
# Date:   Aug 2018

import sys
sys.path.append("../lib/")
from logger import logger
from config import getconfig
from document import ProjectInfo

"""
@file transfer_project_name.py
"""

def define_project_name(project_name, sys_type):
    """由于项目名称在Bugzilla、Testlink上不一致，所以需要进行项目名称的转换，将API Url中传入的项目名称转换成对应系统中的项目，
    API Url中作为参数的名称定义如下：
    istack一期对应为：istack-liberty；istack二期对应为：istack-pike；食品溯源联动对应为：spsyld。
    后续有新增项目时，在该方法中增加定义。

    :param project_name: API Url中传入的项目名称，为istack-liberty、istack-pike、spsyld等
    :param sys_type: 指管理系统类型，为bugzilla、testlink
    :return: 对应系统中的项目名称，字符串类型
    """
    # 项目转换后的名称变量
    project_transfer_name = ""
    # 若sys_type不是bugzilla或者testlink，返回None
    if sys_type != "bugzilla" and sys_type != "testlink":
        logger("ERROR", "System %s is not bugzilla or testlink" % sys_type)
        return None
    # 项目名称转换
    if project_name == "istack-liberty":
        if sys_type == "bugzilla":
            project_transfer_name = "i-stack"
        if sys_type == "testlink":
            project_transfer_name = "istack"
    elif project_name == "istack-pike":
        if sys_type == "bugzilla":
            project_transfer_name = "i-stack"
        if sys_type == "testlink":
            project_transfer_name = "istack-pike"
    elif project_name == "spsyld":
        if sys_type == "bugzilla":
            project_transfer_name = u"食品溯源联动"
        if sys_type == "testlink":
            project_transfer_name = "spsyld"
    else:
        # 若Api Url中定义的项目名称与管理系统中的一致，则直接返回，不需要转换
        project_transfer_name = project_name
    logger("INFO", "转换前的项目名称为: %s" % project_name)
    logger("INFO", "转换后的项目名称为: %s" % project_transfer_name)
    return project_transfer_name

def find_project(project_name):
    """通过项目名找到bugzilla和testlink上的项目名"""
    # 通过项目名找到项目id
    if project_name == u"i-stack智慧城市操作系统(二期)":
        real_project = "i-stack"
    else: 
        pp = ProjectInfo()
        project_id = pp.get_projectid(project_name)
        real_project = project_id.replace("2019", "19")
    return real_project

def find_gerrit_project(project_name):
    """通过项目名找到gerrit上的项目名"""
    if project_name == u"i-stack智慧城市操作系统(二期)":
        project_name = "istack-pike"
        return project_name
    try:
        # 返回项目名对应的项目id,gerrit中2019年项目以项目id_xxx的方式命名
        pp = ProjectInfo()
        project_id = pp.get_projectid(project_name)
        return project_id
    except:
        # 若项目名在项目概况的excel中不存在，直接返回项目名
        return project_name
