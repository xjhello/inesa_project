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
# Date:   July 2018

"""
@file time_task.py
"""

from insert_mongo_data import *
from document import ProjectInfo
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

pr = ProjectInfo()
pr.get_svn_doc()
all_project_bug()
all_bug_history()
all_bug_content()
testlink_to_mongodb()
gerrit_to_mognodb()

