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
# Date:  Aug 2018

"""
@file document.py
"""

import xlrd
import json
import os
import datetime
from config import getconfig
from helper import shell_cmd_timeout
from helper import readexcel_list
from helper import check_task_output
from helper import transfer_date
from helper import get_location
from logger import logger


class ProjectInfo(object):

    def __init__(self):
        self.local_dir = getconfig("document", "local_dir")
        self.svn_address = getconfig("document", "svn_address")
        self.username = getconfig("document", "username")
        self.password = getconfig("document", "password")
        self.project_summary_file = getconfig("document", "file_path")
        self.project_plan_file = os.path.join(
            self.local_dir, getconfig(
                "document", "project_plan"))

    def get_svn_doc(self):
        """下载svn文件至本地目录.
        Args:
           cmd: svn checkout cmd
        Returns:
            svn命令执行结果返回码
        """
        logger("INFO", "start to download document files from SVN")
        # 如果local_dir目录不存在，则创建
        if not os.path.isdir(self.local_dir):
            os.makedirs(self.local_dir)
        cmd = "svn checkout --no-auth-cache --username " + self.username + \
            " --password " + self.password + " " + self.svn_address + " " + self.local_dir
        logger("INFO", cmd)
        ret, output = shell_cmd_timeout(cmd)
        logger("INFO", "ret, output is %d, %s" % (ret, output))
        if ret == 0:
            logger("INFO", "update svn doc successfully!")
        else:
            logger("ERROR", "update svn doc failed!")
        return ret

    def get_projectid(self, projectname):
        # 根据项目名获取项目id
        projects = readexcel_list(self.project_summary_file)
        projectid = None
        for item in projects:
            if item[u"项目名"] == projectname:
                projectid = item["ID"]
                return projectid
        return projectid

    def project_plan(self, file_path):
        """根据项目计划获取里程碑开始时间、结束时间、完成情况"""
        project_plans = readexcel_list(file_path)
        if not project_plans:
            logger("WARN", 'project plan is not exist!')
            return None
        nowdate = datetime.date.today()
        milestone = []
        # 获取里程碑计划
        for plan in project_plans:
            templan = {}
            templan[u"内容"] = plan[u"内容"]
            templan[u"开始时间"] = plan[u"开始时间"]
            templan[u"结束时间"] = plan[u"结束时间"]
            templan[u"完成进度"] = plan[u"完成进度"]
            if not plan[u"完成进度"]:
                templan[u"完成进度"] = 0
            templan[u"状态"] = u"正常"
            if plan[u"里程碑"]:
                templan[u"里程碑"] = plan[u"里程碑"]
            else:
                templan[u"里程碑"] = u"否"
            if plan[u"里程碑"] == u"是":
                endtime = plan[u"结束时间"].split('.')
                endtime = datetime.date(
                    int(endtime[0]), int(endtime[1]), int(endtime[2]))
                if endtime.__lt__(nowdate):
                    res = check_task_output(
                        self.username, self.password, plan[u"产出内容获取位置"])
                    if res:
                        templan[u"状态"] = u"正常"
                    else:
                        templan[u"状态"] = u"异常"
                else:
                    templan[u"状态"] = u"正常"
            milestone.append(templan)
        return milestone

    def get_unusual_project(self):
        # 通过检查项目计划，返回异常状态的项目
        project_info = readexcel_list(self.project_summary_file)
        unusual_project = []
        for project in project_info:
            projectid = project["ID"]
            # projectname = project[u"项目名"].replace("(", "\(").replace(")", "\)")
            projectname = project[u"项目名"]
            project_plan_file = self.project_plan_file.replace(
                "projectdir", projectid + "_" + projectname)
            print project_plan_file
            project_plan = self.project_plan(project_plan_file)
            for plan in project_plan:
                if plan[u"状态"] == u"异常":
                    unusual_project.append(
                        {u"项目名": projectname, u"里程碑": plan[u"内容"], u"截止时间": plan[u"结束时间"]})
                    break
        return unusual_project

    def get_remind_project(self, days):
        # 获取即将到期的任务, days为提前预警的天数
        project_info = readexcel_list(self.project_summary_file)
        nowdate = datetime.date.today()
        remind_project = []
        for project in project_info:
            projectid = project["ID"]
            projectname = project[u"项目名"]
            project_plan_file = self.project_plan_file.replace(
                "projectdir", projectid + "_" + projectname)
            project_plan = readexcel_list(project_plan_file)
            for plan in project_plan:
                if not plan[u"产出内容获取位置"]:
                    endtime = plan[u"结束时间"].split('.')
                    endtime = datetime.date(
                        int(endtime[0]), int(endtime[1]), int(endtime[2]))
                    interval = endtime.__sub__(nowdate).days
                    if interval <= days and interval >= 0:
                        remind_project.append(
                            {u"项目名": projectname, u"里程碑": plan[u"内容"], u"截止时间": plan[u"结束时间"]})
        return remind_project

    def get_doc_tree(self, folder):
        """
        :param folder:文件目录
        :return:目录的字典
        """
        dirtree = {"children": []}
        if os.path.isfile(folder):
            return {"label": os.path.basename(folder), 'type': "file"}
        else:
            dirlist = sorted(os.listdir(folder))
            # 把指定文件目录里的文件夹的名字放进到列表中，然后进行排序
            basename = os.path.basename(folder)
            dirtree['label'] = basename
            for item in dirlist:
                dirtree['children'].append(
                    self.get_doc_tree(
                        os.path.join(
                            folder, item)))
            return dirtree

    # 从excel文件获取所有项目名
    def get_names(self):
        excel_content = readexcel_list(self.project_summary_file)
        if excel_content:
            logger("INFO", "start to get the names of all projects")
            project_names = []
            for i in excel_content:
                for key, val in i.items():
                    if key == u'项目名':
                        project_names.append(val)
            logger("INFO", "all project names is ".format(project_names))
            return project_names
        else:
            logger("INFO", "the content of excel is null!")
            return None

    def statistical_stage_num(self):
        """统计项目总数，不同阶段的数量,不同状态的数量，进行项目数量,结果status_num{u'项目总数': 10, u'立项'：1, ... ,}"""
        res_data = {}
        # 获取项目概况数据
        excel_content = readexcel_list(self.project_summary_file)
        res_data[u'项目总数'] = len(excel_content)
        res_data[u'完结项目'] = 0
        res_data[u'异常项目'] = 0
        res_data[u'进行项目'] = 0
        res_data[u'阶段项目'] = []
        # 用来保存当前阶段的类型
        current_stage = [u"立项", u"设计", u"开发", u"验收"]
        stage_count = [0, 0, 0, 0]
        res_data[u'阶段项目'].append(current_stage)
        # 用来保存状态类型
        unusual_status = u"异常"
        # 获取所有当前阶段类型和状态类型
        for i in excel_content:
            val = i[u'当前阶段']
            if val == u"立项":
                stage_count[0] += 1
                res_data[u'进行项目'] += 1
            if val == u"设计":
                stage_count[1] += 1
                res_data[u'进行项目'] += 1
            if val == u"开发":
                stage_count[2] += 1
                res_data[u'进行项目'] += 1
            if val == u"验收":
                stage_count[3] += 1
                res_data[u'进行项目'] += 1
            if val == u"结项":
                res_data[u"完结项目"] += 1
            if i[u'状态'] == u"异常":
                res_data[u'异常项目'] = 0
        res_data[u'阶段项目'].append(stage_count)
        return res_data

    def filter_progress_prj(self):
        """刷选非完结项目，即进行中项目信息"""
        excel_content = readexcel_list(self.project_summary_file)
        # 用来保存当前阶段为非完结项目信息
        process_project = []
        for i in excel_content:
            for key, val in i.items():
                if key == u'当前阶段' and val != u'结项':
                    process_project.append(i)
        # 非完结数据不为空
        if len(process_project):
            logger(
                "INFO",
                "get the information of in progress project successfully")
            return process_project
        else:
            logger("INFO", "the information of in progress project is None")
            return None

    def get_projectname_info(self, projectname):
        """由项目名称，获得该项目的具体信息,"""
        excel_content = readexcel_list(self.project_summary_file)
        project_info = []
        # 如果输入项目名称空，返回所有项目信息；否则查找名为projectname的项目信息
        if projectname is None:
            logger("INFO", "the input of projectname is None!")
            for item in excel_content:
                project_info.append(item)
            return project_info
        else:
            for item in excel_content:
                if item[u"项目名"] == projectname:
                    project_info.append(item)
        # project_info的长度不为0，有信息， 否则找不到该项目返回None
        if len(project_info):
            logger("INFO", "get the information successfully!")
            return project_info
        else:
            logger("INFO", "information about the project could not be find!")
            return None

    def get_project_plan(self, project_name):
        # 获取项目计划列表
        project_info = readexcel_list(self.project_summary_file)
        for project in project_info:
            if project[u"项目名"] == project_name:
                projectid = project["ID"]
                break
        project_plan_file = self.project_plan_file.replace(
            "projectdir", projectid + "_" + project_name)
        project_plan = self.project_plan(project_plan_file)
        # 对项目任务的开始时间进行从小到大排序
        count = len(project_plan)
        for i in range(count - 1):
            for j in range(count - 1 - i):
                endtime1 = project_plan[j][u"开始时间"].split('.')
                endtime1 = datetime.date(
                    int(endtime1[0]), int(endtime1[1]), int(endtime1[2]))
                endtime2 = project_plan[j + 1][u"开始时间"].split('.')
                endtime2 = datetime.date(
                    int(endtime2[0]), int(endtime2[1]), int(endtime2[2]))
                if endtime1.__gt__(endtime2):
                    project_plan[j], project_plan[j + 1] = project_plan[j + 1], project_plan[j]
        # 计算项目计划中当前时间的索引位置
        nowdate = datetime.date.today()
        lo = 0
        hi = count
        while lo < hi:
            mid = (lo + hi) // 2
            compdate = transfer_date(project_plan[mid][u"开始时间"])
            if nowdate.__lt__(compdate):
                hi = mid
            else:
                lo = mid + 1
        print lo
        # 获取当前时间前后相关的7个任务
        location = get_location(count, lo)
        print location
        if location == count:
            return project_plan
        before = location[0]
        after = location[1]
        beforedata = project_plan[lo - before: lo]
        afterdata = project_plan[lo: lo + after]
        return beforedata + afterdata

    def get_format_projectplan(self, project_name):
        # 反回项目计划数据，适应前端API要求
        plans = self.get_project_plan(project_name)
        nowday = datetime.date.today()
        res_data = {}
        plan_task = []
        plan_startime = []
        plan_endtime = []
        plan_real_starttime = []
        plan_real_endtime = []
        plan_progress = []
        for plan in plans:
            plan_task.append(plan[u"内容"])
            plan_startime.append(plan[u"开始时间"].replace(".", "-"))
            plan_endtime.append(plan[u"结束时间"].replace(".", "-"))
            # 如果项目任务未开始，实际开始时间设置为null
            datetime_date = transfer_date(plan[u"开始时间"])
            endtime_date = transfer_date(plan[u"结束时间"])
            if datetime_date.__gt__(nowday):
                plan_real_starttime.append("null")
                plan_real_endtime.append("null")
                plan_progress.append("%0.0f%%" % (plan[u"完成进度"] * 100))
            else:
                plan_real_starttime.append(plan[u"开始时间"].replace(".", "-"))
                if plan[u"状态"] == u"异常":
                    plan_real_endtime.append(nowday.isoformat())
                    plan_progress.append(False)
                else:
                    if endtime_date.__gt__(nowday):
                        plan_real_endtime.append(nowday.isoformat())
                    else:
                        plan_real_endtime.append(
                            plan[u"结束时间"].replace(".", "-"))
                    plan_progress.append("%0.0f%%" % (plan[u"完成进度"] * 100))
        res_data[u"项目任务"] = plan_task
        res_data[u"计划开始时间"] = plan_startime
        res_data[u"计划结束时间"] = plan_endtime
        res_data[u"实际开始时间"] = plan_real_starttime
        res_data[u"实际结束时间"] = plan_real_endtime
        res_data[u"任务进度"] = plan_progress
        return res_data


if __name__ == '__main__':
    file_path = u"/root/研究院项目管理/项目计划.xlsx"
    pp = ProjectInfo()
    # res = pp.project_plan(file_path)
    # res = pp.get_unusual_project()
    # res = pp.get_remind_project(50)
    # res = pp.get_project_plan(u"异常检测")
    res = pp.get_format_projectplan(u"异常检测")
    print res
    for key, val in res.items():
        print key, val
