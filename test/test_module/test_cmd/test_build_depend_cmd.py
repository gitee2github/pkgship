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
# -*- coding:utf-8 -*-
"""
test_build_depend
"""
import json
import os
import sys
import unittest
import argparse
from unittest import mock
from requests.exceptions import ConnectionError as ConnErr
from packageship.application.cli.commands.builddep import BuildDepCommand
from test.base_code.read_mock_data import MockData

MOCK_DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mock_data")
PACKAGES_INFO = MockData.read_mock_json_data(os.path.join(MOCK_DATA_FILE, "build_depend.json"))


class Redirect:
    _content = ""

    def write(self, s):
        self._content += s

    def flush(self):
        self._content = ""

    def getvalue(self):
        return self._content


class TestBuildDepend(unittest.TestCase):
    """
    class for test be depend
    """
    def setUp(self) -> None:
        self.r = Redirect()
        sys.stdout = self.r

    def test_true_params(self):
        """
        test true params
        """
        parser = argparse.ArgumentParser()
        build_depend = BuildDepCommand()
        with mock.patch("packageship.application.common.remote.RemoteService.status_code",
                        new_callable=mock.PropertyMock) as mock_status_code:
            mock_status_code.return_value = 200
            with mock.patch("packageship.application.common.remote.RemoteService.text",
                            new_callable=mock.PropertyMock) as mock_text:
                mock_text.return_value = json.dumps(PACKAGES_INFO)
                parser.add_argument('sourceName')
                parser.add_argument('-dbs')
                parser.add_argument('-level')
                parser.add_argument('-remote')
                args = parser.parse_args(['Judy', '-dbs=os_version_1'])
                build_depend.do_command(args)
                c = self.r.getvalue().strip()
                s = """
query Judy buildDepend result display:
Binary
====================================================================================================
  Binary name               Source name               Version          Database name                
====================================================================================================
  gcc                       gcc                       9.3.1            os_version_1                    
  make                      make                      4.3              os_version_1                    
  coreutils                 coreutils                 8.32             os_version_1                    
  gawk                      gawk                      5.1.0            os_version_1                    
  sed                       sed                       4.8              os_version_1                    
====================================================================================================
Source
====================================================================================================
  Source name                        Version                Database name                           
====================================================================================================
  Judy                               1.0.5                  os_version_1                               
  gcc                                9.3.1                  os_version_1                               
  make                               4.3                    os_version_1                               
  coreutils                          8.32                   os_version_1                               
  gawk                               5.1.0                  os_version_1                               
  sed                                4.8                    os_version_1                               
====================================================================================================
Statistics
====================================================================================================
  Database name                          Binary Sum                    Source Sum                   
====================================================================================================
  os_version_1                              5                             6                            
====================================================================================================
                                            """.strip()
                self.assertEqual(c, s)

    def test_wrong_status_code(self):
        """
        test wrong status code
        """
        parser = argparse.ArgumentParser()
        build_depend = BuildDepCommand()
        with mock.patch("packageship.application.common.remote.RemoteService.status_code",
                        new_callable=mock.PropertyMock) as mock_status_code:
            mock_status_code.return_value = 500
            parser.add_argument('sourceName')
            parser.add_argument('-dbs')
            parser.add_argument('-level')
            parser.add_argument('-remote')
            args = parser.parse_args(['Judy', '-dbs=os_version_1'])
            build_depend.do_command(args)
            c = self.r.getvalue().strip()
            s = """
ERROR_CONTENT  :{"code":"4001","message":"Request parameter error","resp":null,"tip":"Please check the parameter is valid and query again"}

HINT           :Please check the service and try again
                """.strip()
            self.assertEqual(c, s)

    def test_wrong_resp_code(self):
        """
        test wrong resp code
        """
        parser = argparse.ArgumentParser()
        build_depend = BuildDepCommand()
        with mock.patch("packageship.application.common.remote.RemoteService.status_code",
                        new_callable=mock.PropertyMock) as mock_status_code:
            mock_status_code.return_value = 200
            with mock.patch("packageship.application.common.remote.RemoteService.text",
                            new_callable=mock.PropertyMock) as mock_text:
                mock_text.return_value = json.dumps({'code': '4001'})
                parser.add_argument('sourceName')
                parser.add_argument('-dbs')
                parser.add_argument('-level')
                parser.add_argument('-remote')
                args = parser.parse_args(['Judy', '-dbs=os_version_1'])
                build_depend.do_command(args)
                c = self.r.getvalue().strip()
                s = """
ERROR_CONTENT  :
HINT           :Please check the parameter is valid and query again
                    """.strip()
                self.assertEqual(c, s)

    def test_wrong_resp_text(self):
        """
        test wrong resp text
        """
        parser = argparse.ArgumentParser()
        build_depend = BuildDepCommand()
        with mock.patch("packageship.application.common.remote.RemoteService.status_code",
                        new_callable=mock.PropertyMock) as mock_status_code:
            mock_status_code.return_value = 200
            with mock.patch("packageship.application.common.remote.RemoteService.text",
                            new_callable=mock.PropertyMock) as mock_text:
                mock_text.return_value = ''
                parser.add_argument('sourceName')
                parser.add_argument('-dbs')
                parser.add_argument('-level')
                parser.add_argument('-remote')
                args = parser.parse_args(['Judy', '-dbs=os_version_1'])
                build_depend.do_command(args)
                c = self.r.getvalue().strip()
                s = """
ERROR_CONTENT  :
HINT           :The content is not a legal json format,please check the parameters is valid
                    """.strip()
                self.assertEqual(c, s)

    @mock.patch("packageship.application.common.remote.RemoteService.request", side_effect=ConnErr)
    def test_bad_request(self, mock_get):
        """
        test bad request
        """
        parser = argparse.ArgumentParser()
        build_depend = BuildDepCommand()
        mock_get.return_value = None
        parser.add_argument('sourceName')
        parser.add_argument('-dbs')
        parser.add_argument('-level')
        parser.add_argument('-remote')
        args = parser.parse_args(['Judy', '-dbs=os_version_1'])
        build_depend.do_command(args)
        c = self.r.getvalue().strip()
        s = """
ERROR_CONTENT  :
HINT           :Please check the connection and try again
            """.strip()
        self.assertEqual(c, s)
