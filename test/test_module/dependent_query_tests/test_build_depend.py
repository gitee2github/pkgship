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
 build_depend unittest
"""
import json
import unittest

from test.base_code.read_data_base import ReadTestBase
from packageship.application.apps.package.function.constants import ResponseCode


class TestBuildDepend(ReadTestBase):
    """
    class for test build_depend
    """
    REQUESTS_KWARGS = {
        "url": "/packages/findBuildDepend",
        "method": "post",
        "data": "",
        "content_type": "application/json"
    }

    def test_not_found_database_info_response(self):
        """
        Initialization failed. No database was generated. Database information could not be found
        Returns:
        """
        self.REQUESTS_KWARGS["data"] = json.dumps({'sourceName': ['CUnit']})
        self.without_dbs_folder(
            self.REQUESTS_KWARGS,
            met=self,
            code=ResponseCode.NOT_FOUND_DATABASE_INFO)
        self.when_db_no_content(
            self.REQUESTS_KWARGS,
            met=self,
            code=ResponseCode.NOT_FOUND_DATABASE_INFO)

    def test_param_error_response(self):
        """
        test empty parameters:sourceName,dbList
        Returns:
        """

        param_error_list = [
            "{}",
            json.dumps({"sourceName": [""],
                        "level": "1"}),
            json.dumps({"sourceName": ["dsd" * 120],
                        "level": "1"}),
            json.dumps({"sourceName": [0],
                        "level": "1"}),
            json.dumps({"sourceName": "CUnit",
                        "db_list": ["1", 2, 3, 4],
                        "level": "1"}),
            json.dumps({"sourceName": ["CUnit"],
                        "db_list": "ccaa",
                        "level": "1"}),
            json.dumps({"sourceName": ["CUnit"],
                        "db_list": ["mainline"],
                        "level": "a"}),
            json.dumps({"sourceName": ["CUnit"],
                        "db_list": ["mainline"],
                        "level": "-2"})
        ]
        for error_param in param_error_list:
            self.REQUESTS_KWARGS["data"] = error_param

            resp_dict = self.client_request(**self.REQUESTS_KWARGS)
            self.response_json_error_judge(
                resp_dict, resp_code=ResponseCode.PARAM_ERROR, method=self)

    def test_pkg_name_not_found_response(self):
        """
        The package name is not in the database
        Returns:
        """
        self.REQUESTS_KWARGS["data"] = json.dumps(
            {"sourceName": ["qitiandasheng"]})
        resp_dict = self.client_request(**self.REQUESTS_KWARGS)

        self.response_json_error_judge(
            resp_dict,
            resp_code=ResponseCode.PACK_NAME_NOT_FOUND,
            method=self)

    def test_db_name_error_response(self):
        """
        Database name error
        Returns:
        """
        self.REQUESTS_KWARGS["data"] = json.dumps(
            {"sourceName": ["CUnit"], "db_list": ["shifu", "bajie"]})

        resp_dict = self.client_request(**self.REQUESTS_KWARGS)

        self.response_json_error_judge(
            resp_dict, resp_code=ResponseCode.DB_NAME_ERROR, method=self)

    def test_true_params_result(self):
        """
        test_true_params_result
        Returns:
        """
        self.compare_resp_and_output("build_depend", met=self)


if __name__ == '__main__':
    unittest.main()
