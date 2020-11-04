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
Dynamically obtain the content of the yaml file \
that saves the package information, periodically \
obtain the content and save it in the database
"""
import copy
from concurrent.futures import ThreadPoolExecutor
import datetime as date
import requests
import yaml

from requests.exceptions import HTTPError
from packageship.application.models.package import Packages
from packageship.application.models.package import PackagesMaintainer
from packageship.libs.dbutils import DBHelper
from packageship.libs.exception import Error
from packageship.libs.conf import configuration
from packageship.libs.log import LOGGER
from .gitee import Gitee
from .concurrent import ProducerConsumer


class ParseYaml():
    """
    Description: Analyze the downloaded remote yaml file, obtain the tags
    and maintainer information in the yaml file, and save the obtained
    relevant information into the database

    Attributes:
        base: base class instance
        pkg: Specific package data
        _table_name: The name of the data table to be operated
        openeuler_advisor_url: Get the warehouse address of the yaml file
        _yaml_content: The content of the yaml file
    """

    def __init__(self, pkg_info, table_name):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW 64; rv:50.0) Gecko/20100101 \
                Firefox / 50.0 '}
        self.pkg = pkg_info
        self._table_name = table_name
        self.openeuler_advisor_url = configuration.WAREHOUSE_REMOTE + \
            '{pkg_name}.yaml'.format(pkg_name=pkg_info.name)
        self._yaml_content = None
        self.timed_task_open = configuration.OPEN
        self.producer_consumer = ProducerConsumer()

    def update_database(self):
        """
            For the current package, determine whether the specific yaml file exists, parse
            the data in it and save it in the database if it exists, and record the relevant
            log if it does not exist

        """
        if self._openeuler_advisor_exists_yaml():
            self._save_to_database()
        else:
            msg = "The yaml information of the [%s] package has not been" \
                  "obtained yet" % self.pkg.name
            LOGGER.warning(msg)

    def _get_yaml_content(self, url):
        """
            Gets the contents of the YAML file
            Args:
                url:The network address where the YAML file exists
        """
        try:
            response = requests.get(
                url, headers=self.headers)
            if response.status_code == 200:
                self._yaml_content = yaml.safe_load(response.content)
        except HTTPError as error:
            LOGGER.error(error)

    def _openeuler_advisor_exists_yaml(self):
        """
            Determine whether there is a yaml file with the current \
                package name under the openeuler-advisor project

        """
        self._get_yaml_content(self.openeuler_advisor_url)
        if self._yaml_content:
            return True
        return False

    def _save_to_database(self):
        """
            Save the acquired yaml file information to the database

            Raises:
                Error: An error occurred during data addition
        """

        def _save_package(package_module):
            with DBHelper(db_name="lifecycle") as database:
                database.add(package_module)

        def _save_maintainer_info(maintainer_module):
            with DBHelper(db_name="lifecycle") as database:
                _packages_maintainer = database.session.query(
                    PackagesMaintainer).filter(PackagesMaintainer.name ==
                                               maintainer_module['name']).first()
                if _packages_maintainer:
                    for key, val in maintainer_module.items():
                        setattr(_packages_maintainer, key, val)
                else:
                    _packages_maintainer = PackagesMaintainer(
                        **maintainer_module)
                database.add(_packages_maintainer)

        self._parse_warehouse_info()
        tags = self._yaml_content.get('git_tag', None)
        if tags:
            self._parse_tags_content(tags)
            self.producer_consumer.put(
                (copy.deepcopy(self.pkg), _save_package))
        if self.timed_task_open:
            maintainer = {'name': self.pkg.name}
            _maintainer = self._yaml_content.get('maintainers')
            if _maintainer and isinstance(_maintainer, list):
                maintainer['maintainer'] = _maintainer[0]
            maintainer['maintainlevel'] = self._yaml_content.get(
                'maintainlevel')

            self.producer_consumer.put((maintainer, _save_maintainer_info))

    def _parse_warehouse_info(self):
        """
            Parse the warehouse information in the yaml file

        """
        if self._yaml_content:
            self.pkg.version_control = self._yaml_content.get(
                'version_control')
            self.pkg.src_repo = self._yaml_content.get('src_repo')
            self.pkg.tag_prefix = self._yaml_content.get('tag_prefix')

    def _parse_tags_content(self, tags):
        """
            Parse the obtained tags content

        """
        try:
            # Integrate tags information into key-value pairs
            _tags = [(tag.split()[0], tag.split()[1]) for tag in tags]
            _tags = sorted(_tags, key=lambda x: x[0], reverse=True)
            self.pkg.latest_version = _tags[0][1]
            self.pkg.latest_version_time = _tags[0][0]
            _end_time = date.datetime.strptime(
                self.pkg.latest_version_time, '%Y-%m-%d')
            if self.pkg.latest_version != self.pkg.version:
                for _version in _tags:
                    if _version[1] == self.pkg.version:
                        _end_time = date.datetime.strptime(
                            _version[0], '%Y-%m-%d')
            self.pkg.release_time = _end_time
            self.pkg.used_time = (date.datetime.now() - _end_time).days

        except (IndexError, Error) as index_error:
            LOGGER.error(index_error)


def update_pkg_info(pkg_info_update=True):
    """
        Update the information of the upstream warehouse in the source package

    """
    try:
        # Open thread pool
        pool = ThreadPoolExecutor(max_workers=configuration.POOL_WORKERS)
        with DBHelper(db_name="lifecycle") as database:
            for table_name in filter(lambda x: x not in ['packages_issue',
                                                         'packages_maintainer',
                                                         'databases_info'],
                                     database.engine.table_names()):
                cls_model = Packages.package_meta(table_name)
                # Query a specific table
                for package_item in database.session.query(cls_model).all():
                    if pkg_info_update:
                        parse_yaml = ParseYaml(
                            pkg_info=copy.deepcopy(package_item),
                            table_name=table_name)
                        pool.submit(parse_yaml.update_database)
                    else:
                        # Get the issue of each warehouse and save it
                        gitee_issue = Gitee(
                            copy.deepcopy(package_item),
                            configuration.WAREHOUSE,
                            package_item.name,
                            table_name)
                        pool.submit(gitee_issue.query_issues_info)
        pool.shutdown()
    except(RuntimeError, Exception) as error:
        LOGGER.error(error)
