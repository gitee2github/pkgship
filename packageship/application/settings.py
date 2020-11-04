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
Description: Basic configuration of flask framework
"""
import random
from packageship.libs.conf import configuration


class Config():
    """
    Description: Configuration items in a formal environment
    Attributes:
        _read_config: read config
        _set_config_val: Set the value of the configuration item
    """
    SECRET_KEY = None

    DEBUG = False

    LOG_LEVEL = 'INFO'

    SCHEDULER_API_ENABLED = True

    def __init__(self):

        self.set_config_val()

    @classmethod
    def _random_secret_key(cls, random_len=32):
        """
        Description: Generate random strings
        """
        cls.SECRET_KEY = ''.join(
            [random.choice('abcdefghijklmnopqrstuvwxyz!@#$%^&*()') for index in range(random_len)])

    @classmethod
    def _set_log_level(cls, log_level):
        """
        Description: Set the log level
        """
        cls.LOG_LEVEL = log_level

    def set_config_val(self):
        """
        Description: Set the value of the configuration item
        Args:
        Returns:
        Raises:
        """
        Config._random_secret_key()
        Config._set_log_level(configuration.LOG_LEVEL)
