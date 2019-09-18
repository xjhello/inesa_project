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
@file logger.py
"""

import os
import sys
import time
from config import getconfig

l_type_lst = ["ERROR", "WARN", "DEBUG", "INFO"]


def logger(level, log_info):
    """collect the running log to log file"""
    log_path = getconfig("log", "LOG_PATH")
    log_level = getconfig("log", "LOG_LEVEL")
    log_enable = getconfig("log", "LOG_ENABLE")
    log_fname = getconfig("log", "LOG_FNAME")
    if not os.path.exists(log_path):
        os.makedirs(log_path)
    log_file = os.path.join(log_path, log_fname)
    # base on input string "DEBUG","ERROR"... get level number
    lvl = l_type_lst.index(level)

    # now, begin to write into log file
    log_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
    log_pid = os.getpid()
    log_script = sys._getframe().f_back.f_code.co_filename.split('/')[-1]
    log_method = sys._getframe().f_back.f_code.co_name
    log_line = sys._getframe().f_back.f_lineno
    with open(log_file, "a") as log:
        if lvl <= int(log_level) and bool(log_enable):
            log.write("%s %s %s %s:%s:%s %s\
\n" % (log_time, log_pid, level, log_script, log_method, log_line, log_info))
