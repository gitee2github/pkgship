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

import requests
from requests.exceptions import RequestException, HTTPError
from retrying import retry
from packageship.libs.log import LOGGER


class RemoteService:
    """
    HTTP request service
    """

    def __init__(self, max_delay=1000):
        self._retry = 3
        self._max_delay = max_delay
        self._body = None
        self._response = None

    @property
    def status_code(self):
        """status code of the response"""
        if self._response is None:
            return requests.codes["internal_server_error"]
        return self._response.status_code

    @property
    def content(self):
        """ original content of the response """
        return self._response.content if self._response else None

    @property
    def text(self):
        """content of the decoded response"""
        return self._response.content.decode('utf-8') if self._response else None

    @property
    def response_headers(self):
        """request header for the response"""
        pass

    def _dispatch(self, method, url, **kwargs):
        """Request remote services in different ways

        :param method: request method， GET、 POST 、PUT 、DELETE
        :param url:Remote request address
        :param kwargs:parameters associated with the request
        """
        @retry(stop_max_attempt_number=self._retry, stop_max_delay=self._max_delay)
        def http(url):
            response = method(url, **kwargs)
            if response.status_code != requests.codes["ok"]:
                _msg = "There is an exception with the remote service [%s]，" \
                    "Please try again later.The HTTP error code is：%s" % (url, str(
                        response.status_code))
                raise HTTPError(_msg)
            return response

        method = getattr(self, method)
        if method is None:
            raise RequestException("")
        try:
            self._response = http(url)
        except HTTPError as error:
            raise RequestException("") from error

    def request(self, url, method, body=None, max_retry=3, **kwargs):
        """ Request a remote http service

        :param url: http service address
        :param method: mode of request ,only GET、 POST、 DELETE、 PUT is supported
        :param body: Request body content
        :param max_retry: The number of times the request failed to retry
        :param kwargs: Request the relevant parameters
        """
        self._retry = max_retry
        self._body = body
        try:
            self._dispatch(method=method, url=url, **kwargs)
        except RequestException as error:
            LOGGER.error(error)

    def get(self, url, **kwargs):
        """ HTTP get request method
        :param kwargs: requests parameters
        """
        response = requests.get(url=url, **kwargs)
        return response

    def post(self, url, **kwargs):
        """HTTP post request method
        """
        response = requests.post(url=url, data=self._body, **kwargs)
        return response