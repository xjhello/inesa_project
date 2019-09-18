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
# Date:   July 2018

"""
@file testlink_data.py
"""

##
# @addtogroup server
# @brief This is server component
# @{
# @addtogroup server
# @brief This is server module
# @{
##
import sys
import time
import pymysql
from testlink import TestlinkAPIClient
from config import getconfig
reload(sys)
sys.setdefaultencoding('utf-8')

testlink_url = getconfig("testlink", "testlink_url")
ip = testlink_url.split("/")[2]
TLURL = testlink_url + "/lib/api/xmlrpc/v1/xmlrpc.php"
DEVKey = getconfig("testlink", "DEVKey")
test_user_name = getconfig("testlink", "test_user_name")
tls = TestlinkAPIClient(TLURL, DEVKey)
nowtime = time.strftime("%Y-%m-%d")


def getsql(sql):
    """
    根据项目名称和文件夹名称查找文件夹对应的
    此方法只能查找到根目录下的文件夹的id，多级目录无法查找
    :param sql: sql语句
    :return:查询结果
    """
    db = pymysql.connect(ip, "testlink", "testlink", "testlink", use_unicode=True, charset="utf8")
    cursor = db.cursor()
    cursor.execute(sql)
    results = cursor.fetchall()
    if len(results) == 0:
        return None
    db.close()
    return results

def get_project():
    """获取testlink中的所有项目信息.

    Returns:
        项目信息列表
    """
    projects_info = []
    projects = tls.getProjects()
    for project in projects:
        project["date_time"] = nowtime
        projects_info.append(project)
    return projects_info


def get_testcase():
    """获取testlink中的所有测试用例信息.

    Returns:
       测试用例信息列表
    """
    # 获取所有case的id
    sql = "select id from nodes_hierarchy where node_type_id = 3 and parent_id != 0"
    results = getsql(sql)

    case_list = []
    for result in results:
        # 根据case id获取case的基础信息
        case_id = result[0]
        case_dict = tls.getTestCase(case_id)
        case_dict[0]['data_time'] = nowtime
        case_list.append(case_dict[0])
    return case_list

def get_testplan():
    """获取testlink中的所有测试计划信息.

    Returns:
       测试计划信息列表
    """
    projects = tls.getProjects()
    testplans = []
    for project in projects:
        project_id = project['id']
        response = tls.getProjectTestPlans(project_id)
        for i in response:
            i['data_time'] = nowtime
            testplans.append(i)
    return testplans

def get_testplan_build():
    """获取testlink中的所有测试计划的版本信息.

    Returns:
       测试计划的版本信息列表
    """
    testplans = get_testplan()
    testplan_builds = []
    for testplan in testplans:
        testplan_id = testplan['id']
        response = tls.getBuildsForTestPlan(testplan_id)
        for i in response:
            i['data_time'] = nowtime
            testplan_builds.append(i)
    return testplan_builds

def get_testcase_exec_result():
    """获取testlink中的所有执行过的测试用例信息.

    Returns:
       测试用例执行结果信息列表
    """
    testbuilds = get_testplan_build()
    testcase_exec_results = []
    for build in testbuilds:
        testplan_id = build['testplan_id']
        testbuild_id = build['id']
        try:
            response = tls.getTestCasesForTestPlan(testplan_id, build=testbuild_id)
            if isinstance(response, dict):
                for key, value in response.items():
                    for i in value:
                        i["data_time"] = nowtime
                        testcase_exec_results.append(i)
            else:
                print response
        except Exception as msg:
            print msg 
    return testcase_exec_results

def get_custom_fields():
    """获取测试用例自定义字段信息及与测试用例的绑定关系

    Return:
       测试用例自定义字段信息及与测试用例的绑定关系信息列表
    """
    custom_fields_testcase = []
    sql = "select a.name, a.label, b.* from custom_fields a, cfield_design_values b where a.id = b.field_id"
    result = getsql(sql)
    fields = ["costom_field_name", "costom_field_label", "field_id", "node_id", "value"]
    for i in result:
        field_dict = dict(zip(fields, i))
        field_dict["data_time"] = nowtime
        custom_fields_testcase.append(field_dict)
    return custom_fields_testcase

if __name__ == '__main__':
    print get_testcase_exec_result()
