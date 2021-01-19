#!/usr/bin/python3
# ******************************************************************************
# Copyright (c) Huawei Technologies Co., Ltd. 2020-2020. All rights reserved.
# licensed under the Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#     http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR
# PURPOSE.
# See the Mulan PSL v2 for more details.
# ******************************************************************************/
"""
Description:System exception information
Class:Error,ContentNoneException,DbnameNoneException,
    DatabaseRepeatException,DataMergeException
"""


class Error(Exception):

    """
    Description: Read the configuration file base class in the system
    Attributes:
        message:Exception information
    """

    def __init__(self, msg=''):
        self.message = msg
        Exception.__init__(self, msg)

    def __repr__(self):
        return self.message

    __str__ = __repr__


class ContentNoneException(Error):
    """
    Description: Content is empty exception
    Attributes:
    """

    def __init__(self, message):
        Error.__init__(self, 'No content: %r' % (message,))


class DbnameNoneException(ContentNoneException):
    """
    Description: Exception with empty database name
    Attributes:
    """

    def __init__(self, message):
        ContentNoneException.__init__(self, '%r' % (message,))


class DatabaseRepeatException(Error):
    """
    Description: There are duplicate exceptions in the database
    Attributes:
    """

    def __init__(self, message):
        Error.__init__(self, 'Database repeat: %r' % (message,))


class DataMergeException(Error):
    """
    Description: abnormal integration data
    Attributes:
    """

    def __init__(self, message):
        Error.__init__(self, 'DataMerge exception: %r' % (message,))


class ConfigurationException(Error):
    """
    Description: Configuration file exception information
    """

    def __init__(self, message):
        Error.__init__(self, 'Configuration exception : %r' % (message,))