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
# Author: zhangjk@rc.inesa.com
# Date:   November 2017

"""
@file helper.py
"""

import time
import subprocess
import os
import xlrd
import datetime
from logger import logger

def shell_cmd_timeout(cmd, timeout=0):
    """Execute shell command till timeout"""
    cmd_proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    if not cmd_proc:
        return -1, ''
    t_timeout, tick = timeout, 2
    ret, output = None, ''
    while True:
        time.sleep(tick)
        output = cmd_proc.communicate()[0]
        ret = cmd_proc.poll()
        if ret is not None:
            break

        if t_timeout > 0:
            t_timeout -= tick

        if t_timeout <= 0:
            # timeout, kill command
            cmd_proc.kill()
            ret = -99999
            break
    return ret, output



def week_get(d, interval):
    # dayscount = datetime.timedelta(days=d.isoweekday())
    # days=d.isoweekday() 是否是星期一
    # dayscount = datetime.timedelta() #获取时间分钟小时秒
    # dayto = d - dayscount
    dayto = d
    interval.encode("utf-8")
    interval = int(interval)
    sixdays = datetime.timedelta(days = interval)
    dayfrom = dayto - sixdays
    date_from = datetime.date(dayfrom.year, dayfrom.month, dayfrom.day)
    date_to = datetime.date(dayto.year, dayto.month, dayto.day)
    # print '---'.join([str(date_from), str(date_to)])
    return date_from


def time_derivate(time_now, point, interval):
    # 获取推导时间
    time_before = []
    time_now = datetime.datetime.strptime(time_now, '%Y-%m-%d')
    time_before.append(time_now)
    for i in range(int(point) - 1):
        time_before.append(week_get(time_before[i], interval))
    return time_before

def svn_check(username, password, svnfile):
    # 检查svnfile是否为svn文件或者目录，如果是目录，目录下是否存在内容
    cmd = "svn info --username " + username + " --password " + password + " " + svnfile
    logger("INFO", cmd)
    ret, output = shell_cmd_timeout(cmd)
    if ret == 0:
        logger("INFO", "check svn doc successfully!")
        # 如果svnfile是文件，则返回True
        if output.find("Node Kind: file") != -1:
            logger("INFO", "svnfile %s is a file")
            return True
        # 如果svnfile为目录，则进一步查看目录下是否有内容，存在内容返回True，否则返回False
        elif output.find("Node Kind: directory") != -1:   
            logger("INFO", "svnfile %s is a directory")
            cmd = "svn list --username " + username + " --password " + password + " " + svnfile
            logger("INFO", cmd)
            ret2, output2 = shell_cmd_timeout(cmd)
            if ret2 == 0:
                if output2:
                    logger("INFO", "svnfile %s has child file or directory")
                    return True
                else:
                    logger("INFO", "svnfile %s have not child file or directory")
                    return False
            else:
                logger("ERROR", output2)
                return False
        else:
            logger("INFO", output)
            return False
    else:
        logger("INFO", output)
        return False
       
def artifactory_check(username, password, url):
    # 检查版本机文件是否存在
    # 如果url为版本机目录
    cmd1 = "curl -u " + username + ":" + password + " -L -X GET " + url
    # 如果url为版本机文件
    cmd2 = "curl -u " + username + ":" + password + " -L -X GET " + "/".join(url.split('/')[:-1])
    lastfile = url.split('/')[-1]
    print lastfile
    # url为目录的情况, 检查url是否可访问，以及目录下是否有内容
    logger("INFO", cmd1)
    ret, output = shell_cmd_timeout(cmd1)
    sun_str = "a href="
    if ret == 0:
        count = 0
        for i in range(len(output)-1):
            if output[i:i+len(sun_str)] == sun_str:
                count+=1
        if count > 1:
            logger("INFO", "版本机目录下存在文件")
            return True
        else:
            # 如果url为文件,判断文件是否存在
            ret2, output2 = shell_cmd_timeout(cmd2)
            count = 0
            if ret2 == 0:
                for i in range(len(output2)-1):
                    if output2[i:i+len(sun_str)] == sun_str:
                        count+=1
                if count > 1:
                    logger("INFO", "版本机目录下存在文件")
                    return True
            #if output2.find(lastfile) != -1:
            #    return True
            logger("WARN", "版本机目录下不存在文件")
            return False
    else:
        logger("WARN", "版本机地址有误，无法访问")
        return Flase

def check_task_output(username, password, url):
    "检查任务产出是否存在，包括SVN文档，版本机打包文件"
    if url.find("svn:") != -1:
        res = svn_check(username, password, url)
        return res
    if url.find("artifactory") != -1:
        res = artifactory_check(username, password, url)
        return res
    logger("WARN", "%s 产出内容路径位置不属于SVN或者版本机，请确认！" % url)
    return False 
    

def readexcel_list(file_path):
    """读取excel数据成一个list.
    Args:
       file_path: excel file path
    Returns:
        excel数据转换成的list
    """
    try:
        # 打开excel
        logger("INFO", "start to get excel file info, %s" % file_path)
        book = xlrd.open_workbook(file_path)
    except Exception as err:
        # 如果路径不在或者excel不正确，返回报错信息
        logger("WARN", 'excel file is not exist!')
        logger("ERROR", err)
        return None
    sheet = book.sheets()[0]
    # 取这个sheet页的所有行数
    rows = sheet.nrows
    project_list = []
    cloumn_name = sheet.row_values(0)
    for i in range(rows):
        if i != 0:
            # 把每一个项目添加到project_list中
            project_list.append(dict(zip(cloumn_name, sheet.row_values(i))))
    logger("INFO", "get excel file info successfully")
    return project_list

def transfer_date(date):
    """转换时间格式为datetime格式，date: 2019.01.25"""
    endtime = date.split('.')
    endtime = datetime.date(int(endtime[0]), int(endtime[1]), int(endtime[2]))
    return endtime

def get_location(count, lo):
    # 获取当前时间前后相关的7个任务
    # count为数组长度，lo为数组中的一个分隔索引，interval为获取的列表长度
    if count <= 7:
        return count
    temp = count - lo
    if lo >= 4 and temp >= 3:
        before = 4
        after = 3
    elif lo >= 4 and temp < 3:
        before = 7 - temp
        after = temp
    else:
        before = lo
        after = 7 - lo
    return before, after
