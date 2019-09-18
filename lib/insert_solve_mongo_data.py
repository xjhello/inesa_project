# -*- coding: utf-8 -*-
from pymongo import MongoClient
from gerrit_data import get_project_count
from config import getconfig
from datetime import datetime,timedelta
# 连接数据库
mongodb_ip = getconfig("mongodb", "IP")
mongodb_port = int(getconfig("mongodb", "port"))
client = MongoClient(mongodb_ip, mongodb_port)
dbs = getconfig("mongodb", "dbs")
database = client[dbs]


def patch_count_to_mongodb():
    """将统计的patch数量存入mongodb中去"""
    get_project_count()
    #获取gerrit上面所有的项目名
    collection_all_gerrit = database.gerrit_all_project
    #获取当前时间点
    Timestamp = datetime.now().strftime('%Y-%m-%d')
    query_all ={"Time":  Timestamp}
    #获取当前时间下的所有项目概况游标cursor
    database_gerrit = collection_all_gerrit.find(query_all)
    #获取每条符合条件的项目的count数
    list1 = []
    list_project = database_gerrit.distinct("project")
    list_branch = database_gerrit.distinct("branch")
    for i in list_project:
        for j in list_branch:
            query_all = {"project": i, "branch": j,"Time": Timestamp}
            patch_count = collection_all_gerrit.count(query_all)
            if patch_count != 0:
                query_all =  {"project": i, "branch": j,
                            "count": patch_count}
                list1.append(query_all)
    patch_count_dict= {"Time": Timestamp, "Resource": list1}
    # 插入gerrit所有项目代码提交信息"""
    collection_patch_count = database['gerrit_patch_count']
    collection_patch_count.insert_one(patch_count_dict)


if __name__ == '__main__':
    res = patch_count_to_mongodb()
    print res
