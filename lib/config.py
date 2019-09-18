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
# Author: weijp@rc.inesa.com
# Date:   September 2017

"""
@file config.py
"""

##
# @addtogroup webui
# @brief This is webui component
# @{
# @addtogroup webui
# @brief This is webui module
# @{
##
import sys
import ConfigParser
import os
reload(sys)
sys.setdefaultencoding('utf-8')

# 获取files目录下文件的绝对路径
def get_abspath():
    path = os.path.split(os.path.realpath(__file__))[0]
    path = path.replace('\\','/')
    path = path.replace('server/lib','server/configfile/')
    return path 

# 获取配置文件
def getconfig(section, key):
    config = ConfigParser.ConfigParser()
    # path = os.path.split(os.path.realpath(__file__))[0] + '/config.ini'
    path = get_abspath()
    path = path + 'config.ini'
    config.read(path)
    return config.get(section, key)
