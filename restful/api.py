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

"""
@file api.py
"""

import sys
sys.path.append("../lib/")
import os
from flask_restful import abort, Api, Resource
from flask import Flask, jsonify, request, abort,url_for,render_template
from document import ProjectInfo
from config import getconfig
from logger import logger 
from get_mongo_data import bug_level_distribution
from get_mongo_data import bug_model_distribution
from get_mongo_data import testcases_information
from get_mongo_data import feature_complicate
from get_mongo_data import bug_handing
from get_mongo_data import patch_statistics
from get_mongo_data import home_feature_bug_patch_data
from get_mongo_data import home_case_data
from get_mongo_data import time_data

from helper import week_get
from helper import time_derivate
import datetime

from get_project_case_info import proj_case_info

app = Flask(__name__)
api = Api(app)
file_path = getconfig("document", "file_path")

class DocumentCont(Resource):
    """获取文档excel中某个sheet的内容"""

    def get(self):
        project_name = request.args.get('project_name')
        if not project_name:
            logger("INFO", "It have not project_name argument")
            return {"code": 1, "message": "project_name argument is not exist"} 
        logger("INFO", "start to get document by restful api")
        logger("INFO", "project name is %s" % project_name)
        project = ProjectInfo()
        project_id = project.get_projectid(project_name)
        if project_id is None:
            logger("WARN", "project %s is not exist!" % project_name)
            return {"code": 1, "message": "project is not exist"} 
        folder_path = os.path.join(project.local_dir, project_id + "_" + project_name)
        if not os.path.isdir(folder_path):
            logger("WARN", "folder %s is not exist!" % folder_path)
            return {"code": 1, "message": "project folder is not exist"} 
        docinfo = project.get_doc_tree(folder_path)
        logger("INFO", "get document by restful api successfully")
        return {"code": 0, "message": "get project document successfully!", "data": docinfo}

class ProjectStage(Resource):
    """获取文档excel中各项目的阶段"""

    def get(self):
        logger("INFO", "start to get project stage from excel by restful api")
        sheet_name = u"概览"
        sheet_con = readexcel_list(file_path, sheet_name)
        project_list = []
        if sheet_con is not None:
            for project in sheet_con:
                project_name = project[u"项目名称"]
                if project_name == "":
                    continue
                stage = project_stage(project[u"阶段"])
                project_list.append({u"项目名称": project_name, u"阶段": stage})
            logger("INFO", "get project stage from excel by restful api successfully")
            return project_list
        else:
            logger("WARN", "document file or sheet name is not exist")
            abort(404, message="sheet name {} doesn't exist".format(sheet_name)) 


class bug_level(Resource):
     """获取bug严重程度分布"""
     def get(self):
         param_list = request.args.items()
         project_name = param_list[0][1]
         timestamp = param_list[1][1]
         bug_level_distribution_dict = bug_level_distribution(project_name, timestamp)
         return {"code": 0, "message": "get bug data successfully!", "data": bug_level_distribution_dict}

class bug_model(Resource):
     """获取bug模块分布"""
     def get(self):
         param_list = request.args.items()
         project_name = param_list[0][1]
         timestamp = param_list[1][1]        
         bug_model_distribution_list = bug_model_distribution(project_name, timestamp)
         return {"code": 0, "message": "get bug data successfully!", "data": bug_model_distribution_list}

class case_num(Resource):
     """case数量统计"""
     def get(self):
         data_dict_list = []
         param_list = request.args.items()
         project_name = param_list[0][1]
         # 获取显示间隔
         interval = param_list[1][1]
         # 获取当前时间数据
         time_now = param_list[2][1]
         # 获取显示point
         point = param_list[3][1]
         data_dict_list = time_data(time_now, interval, point, project_name, 'project_case')
         data_dict_list.reverse()
         return data_dict_list   


class FeaCompApi(Resource):
     """获取需求完成情况"""
     def get(self):
         data_dict_list = []
         param_list = request.args.items()
         project_name = param_list[0][1]
         # 获取显示间隔
         interval = param_list[1][1]
         # 获取当前时间数据
         time_now = param_list[2][1]
         # 获取显示point
         point = param_list[3][1]
         data_dict_list = time_data(time_now, interval, point, project_name, 'project_feature')
         data_dict_list.reverse()
         res_data = {}
         all_features = []
         fin_features = []
         times = []
         for feature in data_dict_list:
             all_features.append(feature["data"]["all_feature"])
             fin_features.append(feature["data"]["fin_feature"])
             times.append(feature["time"])
         res_data[u"总需求"] = all_features
         res_data[u"已完成需求"] = fin_features
         res_data[u"时间"] = times
         #logger("INFO", "get feature info from mongodb by restful api successfully")
         return {"code": 0, "message": "get features successfully!", "data": res_data}

class BugHandingApi(Resource):  
     """获取bug处理情况"""
     def get(self):
         data_dict_list = []
         param_list = request.args.items()
         project_name = param_list[0][1]
         # 获取显示间隔
         interval = param_list[1][1]
         # 获取当前时间数据
         time_now = param_list[2][1]
         # 获取显示point
         point = param_list[3][1]
         data_dict_list = time_data(time_now, interval, point, project_name, 'project_bughanding')
         data_dict_list.reverse()
         #logger("INFO", "get bughanding info from mongodb by restful api successfully")
         return data_dict_list
  

class PatchStaApi(Resource):
     """获取patch数量"""
     def get(self):
         param_list = request.args.items()
         # 获取项目名称
         project_name = param_list[0][1]
         # 获取显示间隔
         interval = param_list[1][1]
         # 获取当前时间数据
         time_now = param_list[2][1]
         # 获取显示point
         point = int(param_list[3][1]) + int(1)
         data_dict_list = time_data(time_now, interval, point, project_name, 'project_patch')
         data_dict_list.reverse()
         data_return = {}
         patch_count = []
         patch_count1 = []
         times = []
         for patch in data_dict_list:
             patch_count.append(patch["data"])    
             times.append(patch["time"])
         sum_patch_count = patch_count[len(patch_count)-1]
         times.remove(times[0])
         for i in range(len(patch_count)-1):
             data1 = patch_count[i+1] - patch_count[i]
             patch_count1.append(data1)
         data_return["patch_count"] = patch_count1
         data_return["time"] = times
         data_return["sum_patch_count"] = sum_patch_count
         return {"code": 0, "message": "get patch successfully!", "data": data_return}

class Home_feature_bug_patch_data(Resource):
    def get(self):
        """
        :param project_name: istack-pike;istack-liberty;食品溯源联动
        :return:
        """
        param_list = request.args.items()
        project_name = param_list[0][1]
        timestamp = param_list[1][1]
        data_list = home_feature_bug_patch_data(project_name, timestamp)
        return data_list


class Home_case_data(Resource):
    def get(self):
        """
        :param project_name: spsyld-1967;istack-pike-1848;istack-1848
        :return:
        """
        param_list = request.args.items()
        project_name = param_list[0][1]
        timestamp = param_list[1][1]
        case_list = home_case_data(project_name, timestamp)
        return case_list
##
# Actually setup the Api resource routing here
##

class StageStatusNum(Resource):
    """统计项目总数，不同阶段的数量,不同状态的数量，进行项目数量"""

    def get(self):
        pro_info = ProjectInfo()
        stage_num = pro_info.statistical_stage_num()
        if stage_num is not None:
            logger("INFO", "get the number of stage and status by restful api successfully")
            return {"code": 0, "message": "Count the number of stage and status  successfully!", "data": stage_num}
        else:
            logger("WARN", "the information of stage and status is null")
            return {"code": 1, "message": "Count the number of stage and status  failed!", "data": stage_num}

class Proj_in_Progress(Resource):
    """筛选进行中项目信息，返回list，list每项是一个项目信息字典"""

    def get(self):
        pro_info = ProjectInfo()
        progress_project = pro_info.filter_progress_prj()
        logger("INFO", "start statistical information by restful api")
        logger("INFO", "the information of project in progress is %s" % progress_project)
        if progress_project is not None:
            logger("INFO", "get the information of process project from excel content by restful api successfully")
            return {"code": 0, "message": "get the information of in progress project successfully!", "data": progress_project}
        else:
            logger("WARN", " the information of project in progress is null")
            return {"code": 1, "message": "get the information of in progress project failed!","data": progress_project}


class Get_Projectname_Info(Resource):
    """由项目名获得该项目的信息，不输入项目名返回包含所有项目信息的list，
       输入项目名，找到该项目名，返回长为1的list，该项目的信息；否则找不到返回None"""

    def get(self):
        project_name = request.args.get('project_name')
        logger("INFO", "project name is %s" % project_name)
        pro_info = ProjectInfo()
        project_info = pro_info.get_projectname_info(project_name)
        logger("INFO", "start to get the information of this projectname by restful api")
        logger("INFO", "the information of project is %s" % project_info)
        if project_info:
            logger("INFO", "get the information of this project name by restful api successfully")
            return {"code": 0, "message": "get the information of this projectname successfully!",
                        "data": project_info}
        else:
            logger("INFO", "information about this project name could not be find")
            return {"code": 1, "message": "This project name is not exit!",
                        "data": project_info}

class Get_case_info(Resource):
    """由项目名获得该项目的用例总数、需求ID和该ID的描述及下的用例个数，和需求覆盖率"""
    def get(self):
        project_name = request.args.get('project_name')
        if project_name:
            result = proj_case_info(project_name)
            if result:
                logger("INFO", "the casenum of all project is %s" % result)
                logger("INFO", "get the casenum of all project successfully")
                return {"code": 0, "message": "get the casenum of all project successfully!", "data": result}
            else:
                logger("INFO", "get the casenum of all project failed")
                return {"code": 1, "message": "Can not find the information about {}!".format(project_name), "data": result}
        else:
            logger("INFO", "get the casenum of all project failed")
            return {"code": 1, "message": "The input of project_name is None", "data": None}

class Get_projectnames(Resource):
    """由项目名获得该项目的用例总数、需求ID和该ID的描述及下的用例个数，和需求覆盖率"""
    def get(self):
        pro_info = ProjectInfo()
        names = pro_info.get_names()
        if names:
            logger("INFO", "the names of all project is %s" % names)
            logger("INFO", "get all project names successfully!")
            return {"code": 0, "message": "get all project names successfully!", "data": names}
        else:
            logger("INFO", "get all project names failed")
            return {"code": 1, "message": "the information return by the method get_names() is None", "data": None}

class Get_projectplan(Resource):
    """获取项目计划"""
    def get(self):
        project_name = request.args.get('project_name')
        if project_name:
            project = ProjectInfo()
            result = project.get_format_projectplan(project_name)
            if result:
                logger("INFO", "get project plan successfully")
                return {"code": 0, "message": "get project plan successfully!", "data": result}
            else:
                logger("INFO", "get project planfailed")
                return {"code": 1, "message": "Can not find the information about {}!".format(project_name), "data": result}
        else:
            logger("INFO", "get project plan failed")
            return {"code": 1, "message": "The input of project_name is None", "data": None}

# 获取异常状态项目或提醒项目信息
class Get_unusual_remind(Resource):
    """获取异常状态项目或提醒项目信息"""
    def get(self):
        project = ProjectInfo()
        status = request.args.get('status')
        days = request.args.get('days')
        if status and days == None:
            if status == "异常":
                unusual_project = project.get_unusual_project()
                logger("INFO", "get unusual project information successfully")
                return {"code": 0, "message": "get unusual project information successfully!", "data": unusual_project}
            elif status == "提醒" :
                # 不带天数，默认返回7天的
                default_days = 7
                remind_project = project.get_remind_project(default_days)
                logger("INFO", "get remind project information successfully")
                return {"code": 0, "message": "get remind project information successfully!", "data": remind_project}
        elif status== "提醒" and days != None:
            remind_project = project.get_remind_project(days)
            logger("INFO", "get remind project information successfully")
            return {"code": 0, "message": "get remind project information successfully!", "data": remind_project}
        else:
            logger("INFO", "get status information failed")
            return {"code": 1, "message": "The input of status is False", "data": None}

api.add_resource(Home_feature_bug_patch_data, '/process/v1/home/feature-bug-patch')
api.add_resource(Home_case_data, '/process/v1/home/case')
# 获取项目文档，参数为项目名称，如：/process/v1/document?project_name=异常检测
api.add_resource(DocumentCont, '/process/v1/document')
api.add_resource(ProjectStage, '/process/v1/project-stage')
api.add_resource(FeaCompApi, '/process/v1/feature')
api.add_resource(BugHandingApi, '/process/v1/bug-handing')
api.add_resource(PatchStaApi, '/process/v1/patch')

api.add_resource(bug_level, '/process/v1/bug-level')
api.add_resource(bug_model, '/process/v1/bug-model')
api.add_resource(case_num, '/process/v1/case')

# 统计项目总数，不同阶段项目数量，不同状态项目数量, /process/v1/stage_status_num,返回字典
api.add_resource(StageStatusNum, '/process/v1/stage_status_num')
# 正在进项项目信息， /process/v1/proj_in_progress ,返回list
api.add_resource(Proj_in_Progress, '/process/v1/proj_in_progress')
# 由项目名，获取该项目的信息，1：/process/v1/get_projectname_info 不加参数，返回所有项目信息，2：/process/v1/get_projectname_info?project_name=项目名1，加项目名参数，返回对应的信息，若找不到该项目返回None
api.add_resource(Get_Projectname_Info, '/process/v1/get_projectname_info')
# 由项目名获得需求ID及描述、用例个数和需求覆盖率， /process/v1/get_case_info?project_name=项目名1
api.add_resource(Get_case_info, '/process/v1/get_case_info')
# 获取所有项目名,无参数，/process/v1/get_projectnames
api.add_resource(Get_projectnames, '/process/v1/get_projectnames')
# 获取项目计划,参数为项目名，/process/v1/get_projectplan?project_name=项目名
api.add_resource(Get_projectplan, '/process/v1/projectplan')
# 获取状态异常项目信息或提醒项目信息，1.状态异常信息/process/v1/unusual_remind?status=异常;
# 2.提醒项目信息，不带参数days,默认返回7天的，/process/v1/unusual_remind?status=提醒；
# 3.有参数days,/process/v1/unusual_remind?status=提醒&days=10
api.add_resource(Get_unusual_remind, '/process/v1/unusual_remind')

if __name__ == '__main__':
    app_port = getconfig("api", "port") 
    app.run(host="0.0.0.0", port=app_port, debug=True)

