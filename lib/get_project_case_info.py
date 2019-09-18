# -*- coding: utf-8 -*-
__author__ = 'Eggsy'
__date__ = '2019/4/23 13:36'


import sys
sys.path.append("../lib/")
sys.path.append("../restful/")
from transfer_project_name import find_project
from pymongo import MongoClient
from config import getconfig
from logger import logger
import pymysql
reload(sys)
sys.setdefaultencoding('utf-8')

# 获取mongodb：IP，port,databases
databases = getconfig("mongodb", "dbs")
# 数据库IP、端口号
IP = getconfig("mongodb", "IP")
# IP = "10.200.43.160"
port = int(getconfig("mongodb", "port"))
#testlink的IP
testlink_ip = getconfig("testlink", "testlink_url").split("/")[2]

# 连接mongodb数据库
def connect_Mongo():
    client = MongoClient(IP, port)
    dblist = client.list_database_names()
    if databases in dblist:
        # print u"数据库存在"
        database = client[databases]
        return database
# 获取mongodb中最新日期
def get_date():
    database = connect_Mongo()
    collection_bug = database['all_project_bug']
    query = {"Resolution": {'$regex': "---|FIXE|WONT|DUPL|WORK|NEEDINFO"}}
    bug_data_cursor = collection_bug.find(query).sort([("Time", -1)])
    display_time = bug_data_cursor[0]['Time']
    return display_time

# 获取某个项目的所有bug列表
def new_bug_query(project_name):
    """
    获取所有项目的bug列表
    :param project_name: i-stack;食品溯源联动
    :param time: 2018-08-17
    :return: list
    """
    time = get_date()
    database = connect_Mongo()
    logger("INFO", "Mongodb connection successful!")
    collection_bug = database['all_project_bug']
    query = {"Product": project_name, "Time": time,"Comp":"需求管理" ,"Resolution": {'$regex': "---|FIXE|WONT|DUPL|WORK|NEEDINFO"}}
    bug_data_cursor = collection_bug.find(query)
    bug_data_list = []
    for bug_data in bug_data_cursor:
        bug_data_list.append(bug_data)
    return bug_data_list


# 取出需求ID及描述
def get_featureID_description(bug_data_list):
    """取出需求ID及描述,输入是从mongo数据库得到的某个项目的返回结果，函数返回字典形如{1142:i-stack平台浮动IP流量监控自动化创建功能,...}"""
    requreID = ["" for n in range(len(bug_data_list))]
    description = ["" for n in range(len(bug_data_list))]
    for i in range(len(bug_data_list)):
        for key in bug_data_list[i]:
            requreID[i]=bug_data_list[i]["ID"]
            description[i]=bug_data_list[i]["Summary"]
    ID_desc = dict(zip(requreID,description))
    return ID_desc


# 连接testlink数据库
def get_con():
    """连接testlink数据库"""
    try:
        conn = pymysql.connect(
            testlink_ip,
            "testlink",
            "testlink",
            "testlink",
            use_unicode=True,
            charset="utf8")
        return conn
    except:
        print "Mysqldb Error"

# 根据需求ID在Testlink中拿到用例ID
def get_case_id(feature_id):
    """根据需求ID从testlink获得用例ID"""
    # 连接数据库
    db = get_con()
    logger("INFO", "TestLink connection successful!")
    cursor = db.cursor()
    tcversion_id_sql = "select node_id from cfield_design_values where value='%s'" % feature_id
    cursor.execute(tcversion_id_sql)
    tcversion_id = cursor.fetchall()
    new_case_id = []
    for i in tcversion_id:
        sql = "select parent_id from nodes_hierarchy where node_type_id=4 and id='%s'" % i[0]
        cursor.execute(sql)
        case_id = cursor.fetchall()[0][0]
        if case_id not in new_case_id:
            new_case_id.append(case_id)
    return new_case_id

# 把输入需求ID转换成，TestLink里的完整需求形式，如f1153,e634
def make_featureid_info(e_f_ids):
    """把输入需求ID转换成，TestLink里的完整需求形式，如f1153,e1153,f634,e634"""
    id_info = {}
    featureid_info = {}
    id_name = ''
    id_name2 = ''
    for e_f_id in e_f_ids:
        id_name = 'f%s' % e_f_id
        id_name2 = 'e%s' % e_f_id
        id_info = {}
        id_info['name'] = ['fname', 'ename']
        id_info['fname'] = id_name
        id_info['ename'] = id_name2
        id_info[id_name] = []
        id_info[id_name2] = []
        featureid_info[e_f_id] = id_info
    return featureid_info


# 由输入ID，得到该需求ID的用例ID
def get_num_case(e_f_ids):
    """由输入ID，得到该需求ID的用例ID,返回一个list数据，每两个对应同一个需求ID的基础功能和扩展功能"""
    property_list = []
    feature_id = ''
    total_list = e_f_ids
    # 把输入需求ID转换成，TestLink里的完整需求形式，如f1153, e634
    logger("INFO", "Start getting the use case ID based on the requirement ID")
    feature_info = make_featureid_info(e_f_ids)
    for id in total_list:
        for name in feature_info[id]['name']:
            feature_id = feature_info[id][name]
            # 取出需求ID对应的用例ID
            caseid = get_case_id(feature_id)
            property_list.append({feature_id:caseid})
            # property_list.append(caseid)
    logger("INFO", "Get the case ID successfull！")
    return property_list


def proj_case_info(projectname):
    """由项目名获取该项目的需求ID及描述、用例的个数、需求覆盖率"""
    # 名称转换，转成“KY19002”编号项目名
    newname = find_project(projectname)
    if newname:
        # 由项目名得到需求ID及描述
        requirement = get_featureID_description(new_bug_query(newname))
        logger("INFO", "正在处理%s" % newname)
        info_reID = []
        requireID = []
        for content in requirement:
            # 取出需求ID
            requireID.append(int(content))
            # 需求ID及描述信息转成list，[{"需求ID":487,"需求描述":"创建"}，{ }，...]
            cell_info = dict()
            cell_info[u"需求ID"] = content
            cell_info[u"需求描述"] = requirement[content]
            info_reID.append(cell_info)
        logger("INFO", "{}的需求ID{}".format(newname, requireID))
        # 由需求ID获得用例ID,[{'f1141': [42660]},{'e1141': [42665, 42667, 42673]},...]
        case_id = get_num_case(requireID)
        logger("INFO", "Start calculating the number of {} use case IDs".format(newname))
        for cell_info in info_reID:
            numcase1= 0
            for re_caid in case_id:
                numcase = 0
                for key in re_caid:
                    if  key[1:] == cell_info[u"需求ID"]:
                        numcase = numcase + len(re_caid[key])
                        numcase1 = numcase1 + numcase
            cell_info[u"用例个数"] = numcase1
        # 计算用例ID的总数及需求覆盖率
        sum_case_num = 0 # 该项目的用例总数
        not_zero_num = 0
        for cell_info in info_reID:
            if cell_info[u"用例个数"]!=0:
                sum_case_num = sum_case_num + cell_info[u"用例个数"]
                not_zero_num = not_zero_num + 1
        logger("INFO", " the number of {} use case IDs is{}".format(newname, sum_case_num))
        # 计算覆盖率
        if len(info_reID):
            require_coverage = not_zero_num / float(len(info_reID))
        else:
            require_coverage = 0
        info = dict()
        info[u'用例总数'] = sum_case_num
        info[u'需求信息'] = info_reID
        # info[u'需求覆盖率'] = require_coverage
        info[u'需求覆盖率'] = '%.2f%%' % (require_coverage * 100)
        return info
    else:
        logger("INFO", "project name is None" )
        return None




if __name__ == '__main__':

    name = u"地表水水质监测及数据管理和分析系统"
    a = proj_case_info(name)
    for i in a:
        print i,a[i]
