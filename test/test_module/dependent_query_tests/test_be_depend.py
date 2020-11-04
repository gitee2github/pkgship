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
Less transmission is always parameter transmission
"""
import unittest
import json
from test.base_code.read_data_base import ReadTestBase
from test.base_code.common_test_code import compare_two_values, get_correct_json_by_filename
from packageship.application.apps.package.function.constants import ResponseCode
from packageship.application.apps.package.function.searchdb import db_priority


class TestBeDepend(ReadTestBase):
    """
    The dependencies of the package are tested
    """
    db_name = db_priority()[0]

    def test_lack_parameter(self):
        """
        Less transmission is always parameter transmission
        """
        # No arguments passed
        resp = self.client.post("/packages/findBeDepend",
                                data='{}',
                                content_type="application/json")

        resp_dict = json.loads(resp.data)

        self.assertIn("code", resp_dict, msg="Error in data format return")
        self.assertEqual(ResponseCode.PARAM_ERROR,
                         resp_dict.get("code"),
                         msg="Error in status code return")

        self.assertIn("msg", resp_dict, msg="Error in data format return")
        self.assertEqual(
            ResponseCode.CODE_MSG_MAP.get(
                ResponseCode.PARAM_ERROR),
            resp_dict.get("msg"),
            msg="Error in status code return")

        self.assertIn("data", resp_dict, msg="Error in data format return")
        self.assertIsNone(
            resp_dict.get("data"),
            msg="Error in data information return")

        # Only the packagename
        resp = self.client.post("/packages/findBeDepend",
                                data=json.dumps({
                                    "packagename": "CUnit",
                                }),
                                content_type="application/json")

        resp_dict = json.loads(resp.data)

        self.assertIn("code", resp_dict, msg="Error in data format return")
        self.assertEqual(ResponseCode.PARAM_ERROR,
                         resp_dict.get("code"),
                         msg="Error in status code return")

        self.assertIn("msg", resp_dict, msg="Error in data format return")
        self.assertEqual(
            ResponseCode.CODE_MSG_MAP.get(
                ResponseCode.PARAM_ERROR),
            resp_dict.get("msg"),
            msg="Error in status code return")

        self.assertIn("data", resp_dict, msg="Error in data format return")
        self.assertIsNone(
            resp_dict.get("data"),
            msg="Error in data information return")

        # Only the withsubpack
        resp = self.client.post("/packages/findBeDepend",
                                data=json.dumps({
                                    "withsubpack": "0",
                                }),
                                content_type="application/json")

        resp_dict = json.loads(resp.data)

        self.assertIn("code", resp_dict, msg="Error in data format return")
        self.assertEqual(ResponseCode.PARAM_ERROR,
                         resp_dict.get("code"),
                         msg="Error in status code return")

        self.assertIn("msg", resp_dict, msg="Error in data format return")
        self.assertEqual(
            ResponseCode.CODE_MSG_MAP.get(
                ResponseCode.PARAM_ERROR),
            resp_dict.get("msg"),
            msg="Error in status code return")

        self.assertIn("data", resp_dict, msg="Error in data format return")
        self.assertIsNone(
            resp_dict.get("data"),
            msg="Error in data information return")

        # Only the dbname
        resp = self.client.post("/packages/findBeDepend",
                                data=json.dumps({
                                    "dbname": f"{self.db_name}",
                                }),
                                content_type="application/json")

        resp_dict = json.loads(resp.data)

        self.assertIn("code", resp_dict, msg="Error in data format return")
        self.assertEqual(ResponseCode.PARAM_ERROR,
                         resp_dict.get("code"),
                         msg="Error in status code return")

        self.assertIn("msg", resp_dict, msg="Error in data format return")
        self.assertEqual(
            ResponseCode.CODE_MSG_MAP.get(
                ResponseCode.PARAM_ERROR),
            resp_dict.get("msg"),
            msg="Error in status code return")

        self.assertIn("data", resp_dict, msg="Error in data format return")
        self.assertIsNone(
            resp_dict.get("data"),
            msg="Error in data information return")

        # Don't preach withsubpack
        resp = self.client.post("/packages/findBeDepend",
                                data=json.dumps({
                                    "packagename": "A",
                                    "dbname": f"{self.db_name}"
                                }),
                                content_type="application/json")

        resp_dict = json.loads(resp.data)

        self.assertIn("code", resp_dict, msg="Error in data format return")
        self.assertEqual(ResponseCode.SUCCESS,
                         resp_dict.get("code"),
                         msg="Error in status code return")

        self.assertIn("msg", resp_dict, msg="Error in data format return")
        self.assertEqual(ResponseCode.CODE_MSG_MAP.get(ResponseCode.SUCCESS),
                         resp_dict.get("msg"),
                         msg="Error in status code return")

        self.assertIn("data", resp_dict, msg="Error in data format return")
        self.assertIsNotNone(
            resp_dict.get("data"),
            msg="Error in data information return")

        # Don't preach dbname
        resp = self.client.post("/packages/findBeDepend",
                                data=json.dumps({
                                    "packagename": "CUnit",
                                    "withsubpack": "0"
                                }),
                                content_type="application/json")

        resp_dict = json.loads(resp.data)

        self.assertIn("code", resp_dict, msg="Error in data format return")
        self.assertEqual(ResponseCode.PARAM_ERROR,
                         resp_dict.get("code"),
                         msg="Error in status code return")

        self.assertIn("msg", resp_dict, msg="Error in data format return")
        self.assertEqual(
            ResponseCode.CODE_MSG_MAP.get(
                ResponseCode.PARAM_ERROR),
            resp_dict.get("msg"),
            msg="Error in status code return")

        self.assertIn("data", resp_dict, msg="Error in data format return")
        self.assertIsNone(
            resp_dict.get("data"),
            msg="Error in data information return")

        # Don't preach packagename
        resp = self.client.post("/packages/findBeDepend",
                                data=json.dumps({
                                    "dbname": f"{self.db_name}",
                                    "withsubpack": "0"
                                }),
                                content_type="application/json")

        resp_dict = json.loads(resp.data)

        self.assertIn("code", resp_dict, msg="Error in data format return")
        self.assertEqual(ResponseCode.PARAM_ERROR,
                         resp_dict.get("code"),
                         msg="Error in status code return")

        self.assertIn("msg", resp_dict, msg="Error in data format return")
        self.assertEqual(
            ResponseCode.CODE_MSG_MAP.get(
                ResponseCode.PARAM_ERROR),
            resp_dict.get("msg"),
            msg="Error in status code return")

        self.assertIn("data", resp_dict, msg="Error in data format return")
        self.assertIsNone(
            resp_dict.get("data"),
            msg="Error in data information return")

        # All incoming withsubpack=0
        resp = self.client.post("/packages/findBeDepend",
                                data=json.dumps({
                                    "packagename": "A",
                                    "dbname": f"{self.db_name}",
                                    "withsubpack": "0"
                                }),
                                content_type="application/json")

        resp_dict = json.loads(resp.data)

        self.assertIn("code", resp_dict, msg="Error in data format return")
        self.assertEqual(ResponseCode.SUCCESS,
                         resp_dict.get("code"),
                         msg="Error in status code return")

        self.assertIn("msg", resp_dict, msg="Error in data format return")
        self.assertEqual(ResponseCode.CODE_MSG_MAP.get(ResponseCode.SUCCESS),
                         resp_dict.get("msg"),
                         msg="Error in status code return")

        self.assertIn("data", resp_dict, msg="Error in data format return")
        self.assertIsNotNone(
            resp_dict.get("data"),
            msg="Error in data information return")

        # All incoming withsubpack=1
        resp = self.client.post("/packages/findBeDepend",
                                data=json.dumps({
                                    "packagename": "A",
                                    "dbname": f"{self.db_name}",
                                    "withsubpack": "1"
                                }),
                                content_type="application/json")

        resp_dict = json.loads(resp.data)

        self.assertIn("code", resp_dict, msg="Error in data format return")
        self.assertEqual(ResponseCode.SUCCESS,
                         resp_dict.get("code"),
                         msg="Error in status code return")

        self.assertIn("msg", resp_dict, msg="Error in data format return")
        self.assertEqual(ResponseCode.CODE_MSG_MAP.get(ResponseCode.SUCCESS),
                         resp_dict.get("msg"),
                         msg="Error in status code return")

        self.assertIn("data", resp_dict, msg="Error in data format return")
        self.assertIsNotNone(
            resp_dict.get("data"),
            msg="Error in data information return")

    def test_wrong_parameter(self):
        """
        Parameter error
        """

        # packagename Parameter error
        resp = self.client.post("/packages/findBeDepend",
                                data=json.dumps({
                                    "packagename": "詹姆斯",
                                    "dbname": f"{self.db_name}",
                                    "withsubpack": "0"
                                }),
                                content_type="application/json")

        resp_dict = json.loads(resp.data)

        self.assertIn("code", resp_dict, msg="Error in data format return")
        self.assertEqual(ResponseCode.PACK_NAME_NOT_FOUND,
                         resp_dict.get("code"),
                         msg="Error in status code return!")
        self.assertIn("msg", resp_dict, msg="Error in data format return")
        self.assertEqual(
            ResponseCode.CODE_MSG_MAP.get(
                ResponseCode.PACK_NAME_NOT_FOUND),
            resp_dict.get("msg"),
            msg="Error in status code return")

        self.assertIn("data", resp_dict, msg="Error in data format return")
        self.assertIsNone(
            resp_dict.get("data"),
            msg="Error in data information return")

        # dbname Parameter error
        resp = self.client.post("/packages/findBeDepend",
                                data=json.dumps({
                                    "packagename": "ATpy",
                                    "dbname": "asdfgjhk",
                                    "withsubpack": "0"
                                }),
                                content_type="application/json")

        resp_dict = json.loads(resp.data)

        self.assertIn("code", resp_dict, msg="Error in data format return")
        self.assertEqual(ResponseCode.DB_NAME_ERROR,
                         resp_dict.get("code"),
                         msg="Error in status code return")

        self.assertIn("msg", resp_dict, msg="Error in data format return")
        self.assertEqual(
            ResponseCode.CODE_MSG_MAP.get(
                ResponseCode.DB_NAME_ERROR),
            resp_dict.get("msg"),
            msg="Error in status code return")

        self.assertIn("data", resp_dict, msg="Error in data format return")
        self.assertIsNone(
            resp_dict.get("data"),
            msg="Error in data information return")

        # withsubpack Parameter error
        resp = self.client.post("/packages/findBeDepend",
                                data=json.dumps({
                                    "packagename": "CUnit",
                                    "dbname": f"{self.db_name}",
                                    "withsubpack": "3"
                                }),
                                content_type="application/json")

        resp_dict = json.loads(resp.data)

        self.assertIn("code", resp_dict, msg="Error in data format return")
        self.assertEqual(ResponseCode.PARAM_ERROR,
                         resp_dict.get("code"),
                         msg="Error in status code return")

        self.assertIn("msg", resp_dict, msg="Error in data format return")
        self.assertEqual(
            ResponseCode.CODE_MSG_MAP.get(
                ResponseCode.PARAM_ERROR),
            resp_dict.get("msg"),
            msg="Error in status code return")

        self.assertIn("data", resp_dict, msg="Error in data format return")
        self.assertIsNone(
            resp_dict.get("data"),
            msg="Error in data information return")

    def test_true_params_result(self):
        """
        Results contrast
        """
        correct_list = get_correct_json_by_filename("be_depend")

        self.assertNotEqual([], correct_list, msg="Error reading JSON file")

        for correct_data in correct_list:
            input_value = correct_data["input"]
            resp = self.client.post("/packages/findBeDepend",
                                    data=json.dumps(input_value),
                                    content_type="application/json")
            output_for_input = correct_data["output"]
            resp_dict = json.loads(resp.data)
            self.assertTrue(compare_two_values(output_for_input, resp_dict),
                            msg="The answer is not correct")
