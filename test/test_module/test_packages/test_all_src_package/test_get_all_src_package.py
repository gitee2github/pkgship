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
test get all src package
"""
import unittest
import os
from unittest import mock
from mock import patch

from packageship.application.common.exc import ParametersError
from packageship.application.core.pkginfo.pkg import Package
from packageship.application.query.pkg import QueryPackage
from packageship.application.query import database
from test.base_code.read_mock_data import MockData

pkg = Package()
MOCK_DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

class TestAllSrcPackage(unittest.TestCase):
    """
    class for test all src package
    """

    def setUp(self) -> None:
        database.get_db_priority = mock.Mock(
            return_value=["openeuler", "fedora33333"])

    def test_wrong_parameters(self):
        """
        test wrong parameters
        Returns:

        """

        with self.assertRaises(ParametersError):
            pkg.all_src_packages("openEuler1", page_num=1, page_size=20)

        with self.assertRaises(ParametersError):
            pkg.all_src_packages("openeuler", page_num=0, page_size=1)

        with self.assertRaises(ParametersError):
            pkg.all_src_packages("openeuler", page_num=1, page_size=0)

        with self.assertRaises(ParametersError):
            pkg.all_src_packages("openeuler", page_num="a", page_size=0)

        with self.assertRaises(ParametersError):
            pkg.all_src_packages("openeuler", page_num=1, page_size=201)

        with self.assertRaises(ParametersError):
            pkg.all_src_packages("openeuler", page_num=1, page_size=1, command_line="111")

    @patch.object(QueryPackage, "get_src_info")
    def test_get_empty_src_info(self, mock1):
        """
        test empty src info
        Returns:

        """
        mock1.return_value = {}
        res = pkg.all_src_packages("openeuler", page_num=1, page_size=20)
        self.assertEqual(res, {}, "Error in testing empty src info.")

    @patch.object(QueryPackage, "get_src_info")
    def test_wrong_src_info(self, mock1):
        """
        test wrong src info
        Returns:

        """
        mock1.return_value = {"total":2}
        res = pkg.all_src_packages("openeuler", page_num=1, page_size=20)
        self.assertEqual(res, {}, "Error in testing wrong src info.")

    @patch.object(QueryPackage, "get_src_info")
    def test_true_result(self, mock1):
        """
        test true result
        Returns:

        """
        ALL_SRC_INFO = MockData.read_mock_json_data(os.path.join(MOCK_DATA_FILE, "all_src_package_info.json"))
        mock1.return_value = ALL_SRC_INFO
        res = pkg.all_src_packages("openeuler", page_num=1, page_size=20)
        self.assertNotEqual(res, {}, "Error in testing true result.")

