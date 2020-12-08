#!/usr/bin/python3 # pylint: disable= too-many-lines
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
Description: Entry method for custom commands
Class: BaseCommand,PkgshipCommand,RemoveCommand,InitDatabaseCommand,
       AllPackageCommand,UpdatePackageCommand,BuildDepCommand,InstallDepCommand,
       SelfBuildCommand,BeDependCommand,SingleCommand
"""
import os
import json
import threading
from json.decoder import JSONDecodeError

try:
    import argparse
    import requests
    from requests.exceptions import ConnectionError as ConnErr
    from requests.exceptions import HTTPError
    import prettytable
    from prettytable import PrettyTable
    from packageship.libs.conf import configuration
    from packageship.libs.log import LOGGER
    from packageship.libs.exception import Error
except ImportError as import_error:
    print("Error importing related dependencies,"
          "please check if related dependencies are installed")
else:
    from packageship.application.apps.package.function.constants import ResponseCode
    from packageship.application.apps.package.function.constants import ListNode
    from packageship.application.apps.lifecycle.function.download_yaml import update_pkg_info
    from packageship.libs.tableutils.terminal_table import TerminalTable

DB_NAME = 0
DEPRECATION_LEN = 12
LIST_LEN = 6


def main():
    """
    Description: Command line tool entry, register related commands

    Raises:
        Error: An error occurred while executing the command
    """
    try:
        packship_cmd = PkgshipCommand()
        packship_cmd.parser_args()
    except Error as error:
        LOGGER.logger.error(error)
        print('Command execution error please try again')


class BaseCommand():
    """
    Description: Basic attributes used for command invocation
    Attributes:
        write_host: Can write operation single host address
        read_host: Can read the host address of the operation
        headers: Send HTTP request header information
    """

    def __init__(self):
        """
        Description: Class instance initialization

        """
        self.write_host = None
        self.read_host = None
        self.__http = 'http://'
        self.headers = {"Content-Type": "application/json",
                        "Accept-Language": "zh-CN,zh;q=0.9"}

        self.load_read_host()
        self.load_write_host()

    def load_write_host(self):
        """
        Description: Address to load write permission
        Args:

        Returns:
        Raises:

        """
        write_port = configuration.WRITE_PORT

        write_ip = configuration.WRITE_IP_ADDR
        if not all([write_ip, write_port]):
            raise Error(
                "The system does not configure the relevant port and ip correctly")
        _write_host = self.__http + write_ip + ":" + str(write_port)
        setattr(self, 'write_host', _write_host)

    def load_read_host(self):
        """
        Returns:Address to load read permission
        Args:

        Returns:
        Raises:

        """
        read_port = configuration.QUERY_PORT

        read_ip = configuration.QUERY_IP_ADDR
        if all([read_ip, read_port]):
            _read_host = self.__http + read_ip + ":" + str(read_port)

            setattr(self, 'read_host', _read_host)

    def _set_read_host(self, remote=False):
        """
            Set read domain name
        """
        if remote:
            self.read_host = configuration.REMOTE_HOST
        if self.read_host is None:
            raise Error(
                "The system does not configure the relevant port and ip correctly")


class PkgshipCommand(BaseCommand):
    """
    Description: PKG package command line
    Attributes:
        statistics: Summarized data table
        table: Output table
        columns: Calculate the width of the terminal dynamically
        params: Command parameters
    """
    parser = argparse.ArgumentParser(
        description='package related dependency management')
    subparsers = parser.add_subparsers(
        help='package related dependency management')

    def __init__(self):
        """
        Description: Class instance initialization
        """
        super(PkgshipCommand, self).__init__()
        self.statistics = dict()
        self.table = PkgshipCommand.create_table()
        # Calculate the total width of the current terminal
        self.columns = 100
        self.params = []

    @staticmethod
    def register_command(command):
        """
        Description: Registration of related commands

        Args:
            command: Related commands

        Returns:
        Raises:

        """
        command.register()

    def register(self):
        """
        Description: Command line parameter injection
        Args:

        Returns:

        Raises:

        """
        for command_params in self.params:
            self.parse.add_argument(  # pylint: disable=E1101
                command_params[0],
                # type=eval(command_params[1]),  # pylint: disable=W0123
                help=command_params[2],
                default=command_params[3],
                action=command_params[4])

    @classmethod
    def parser_args(cls):
        """
        Description: Register the command line and parse related commands
        Args:

        Returns:

        Raises:
            Error: An error occurred during command parsing
        """
        cls.register_command(RemoveCommand())
        cls.register_command(InitDatabaseCommand())
        cls.register_command(AllPackageCommand())
        cls.register_command(UpdatePackageCommand())
        cls.register_command(BuildDepCommand())
        cls.register_command(InstallDepCommand())
        cls.register_command(SelfBuildCommand())
        cls.register_command(BeDependCommand())
        cls.register_command(SingleCommand())
        cls.register_command(IssueCommand())
        cls.register_command(AllTablesCommand())
        cls.register_command(BatchTaskCommand())
        cls.register_command(GetFilelistInfoCommand())
        try:
            args = cls.parser.parse_args()
            args.func(args)
        except Error:
            print('command error')

    def parse_depend_package(self, response_data, params=None):
        """
        Description: Parsing package data with dependencies
        Args:
            response_data: http request response content
            params: Parameters passed in on the command line
        Returns:
            Summarized data table
        Raises:

        """
        bin_package_count = 0
        src_package_count = 0
        if response_data.get('code') == ResponseCode.SUCCESS:
            package_all = response_data.get('data')
            if isinstance(package_all, dict):
                if params:
                    if package_all.get("not_found_components"):
                        print("Problem: Not Found Components")
                        for not_found_com in package_all.get("not_found_components"):
                            print("  - nothing provides {} needed by {} ".format(
                                not_found_com, params.packagename))
                    package_all = package_all.get("build_dict")

                for bin_package, package_depend in package_all.items():
                    # distinguish whether the current data is the data of the root node
                    if isinstance(package_depend, list) and \
                            package_depend[ListNode.SOURCE_NAME] != 'source':

                        row_data = [bin_package,
                                    package_depend[ListNode.SOURCE_NAME],
                                    package_depend[ListNode.VERSION],
                                    package_depend[ListNode.DBNAME]]
                        # Whether the database exists
                        if package_depend[ListNode.DBNAME] not in self.statistics:
                            self.statistics[package_depend[ListNode.DBNAME]] = {
                                'binary': [],
                                'source': []
                            }
                        # Determine whether the current binary package exists
                        if bin_package not in \
                                self.statistics[package_depend[ListNode.DBNAME]]['binary']:
                            self.statistics[package_depend[ListNode.DBNAME]]['binary'].\
                                append(bin_package)
                            bin_package_count += 1
                        # Determine whether the source package exists
                        if package_depend[ListNode.SOURCE_NAME] not in \
                                self.statistics[package_depend[ListNode.DBNAME]]['source']:
                            self.statistics[package_depend[ListNode.DBNAME]]['source'].append(
                                package_depend[ListNode.SOURCE_NAME])
                            src_package_count += 1

                        if hasattr(self, 'table') and self.table:
                            self.table.add_row(row_data)
        else:
            LOGGER.logger.error(response_data.get('msg'))
            print(response_data.get('msg'))
        statistics_table = self.statistics_table(
            bin_package_count, src_package_count)
        return statistics_table

    def print_(self, content=None, character='=', dividing_line=False):
        """
        Description: Output formatted characters
        Args:
           content: Output content
           character: Output separator content
           dividing_line: Whether to show the separator
        Returns:

        Raises:

        """
        # Get the current width of the console

        if dividing_line:
            print(character * self.columns)
        if content:
            print(content)
        if dividing_line:
            print(character * self.columns)

    @staticmethod
    def create_table(title=None):
        """
        Description: Create printed forms
        Args:
            title: Table title
        Returns:
            ASCII format table
        Raises:

        """
        table = TerminalTable(title)
        # table.set_style(prettytable.PLAIN_COLUMNS)
        table.align = 'l'
        table.horizontal_char = '='
        table.junction_char = '='
        table.vrules = prettytable.NONE
        table.hrules = prettytable.FRAME
        return table

    def statistics_table(self, bin_package_count, src_package_count):
        """
        Description: Generate data for total statistical tables
        Args:
            bin_package_count: Number of binary packages
            src_package_count: Number of source packages
        Returns:
            Summarized data table
        Raises:

        """
        statistics_table = self.create_table(['', 'Binary', 'Source'])
        statistics_table.add_row(
            ['Self Depend Sum', bin_package_count, src_package_count])

        # cyclically count the number of source packages and binary packages in each database
        for database, statistics_item in self.statistics.items():
            statistics_table.add_row([database, len(statistics_item.get(
                'binary')), len(statistics_item.get('source'))])
        return statistics_table

    @staticmethod
    def http_error(response):
        """
        Description: Log error messages for http
        Args:
            response: Response content of http request
        Returns:

        Raises:
            HTTPError: http request error
        """
        try:
            print(response.raise_for_status())
        except HTTPError as http_error:
            LOGGER.logger.error(http_error)
            print('Request failed')
            print(http_error)

    @staticmethod
    def show_separation(value, separation, separation_str=" "):
        """
        Description:Split content as required
        Args:
            value: Need to be divided content
            separation: Split length
            separation_str: Delimiter
        Returns:
            value_separation: Content after segmentation as required
        Raises:
        """
        value_separation = []
        range_num = len(value) // separation + 1 if len(value) % separation else len(value) // separation
        for idx in range(range_num):
            value_separation.append(separation_str.join(value[separation * idx:
                                                              separation * (idx + 1)]))
        return value_separation


class RemoveCommand(PkgshipCommand):
    """
    Description: Delete database command
    Attributes:
        parse: Command line parsing example
        params: Command line parameters
    """

    def __init__(self):
        """
        Description: Class instance initialization
        """
        super(RemoveCommand, self).__init__()
        self.parse = PkgshipCommand.subparsers.add_parser(
            'rm', help='delete database operation')
        self.params = [
            ('db', 'str', 'name of the database operated', '', 'store')]

    def register(self):
        """
        Description: Command line parameter injection
        Args:

        Returns:

        Raises:

        """
        super(RemoveCommand, self).register()
        self.parse.set_defaults(func=self.do_command)

    def do_command(self, params):
        """
        Description: Action to execute command
        Args:
            params: Command line parameters
        Returns:

        Raises:
            ConnErr: Request connection error

        """
        if params.db is None:
            print('No database specified for deletion')
        else:
            _url = self.write_host + '/repodatas?dbName={}'.format(params.db)
            try:
                response = requests.delete(_url)
            except ConnErr as conn_err:
                LOGGER.logger.error(conn_err)
                print(str(conn_err))
            else:
                # Determine whether to delete the mysql database or sqlite database
                if response.status_code == 200:
                    try:
                        data = json.loads(response.text)
                    except JSONDecodeError as json_error:
                        LOGGER.logger.error(json_error)
                        print(response.text)
                    else:
                        if data.get('code') == ResponseCode.SUCCESS:
                            print('Delete database success')
                        else:
                            LOGGER.logger.error(data.get('msg'))
                            print(data.get('msg'))
                else:
                    self.http_error(response)


class InitDatabaseCommand(PkgshipCommand):
    """
    Description: Initialize  database command
    Attributes:
        parse: Command line parsing example
        params: Command line parameters
    """

    def __init__(self):
        """
        Description: Class instance initialization
        """
        super(InitDatabaseCommand, self).__init__()
        self.parse = PkgshipCommand.subparsers.add_parser(
            'init', help='initialization of the database')
        self.params = [
            ('-filepath', 'str', 'name of the database operated', '', 'store')]

    def register(self):
        """
        Description: Command line parameter injection
        Args:

        Returns:

        Raises:

        """
        super(InitDatabaseCommand, self).register()
        self.parse.set_defaults(func=self.do_command)

    def do_command(self, params):
        """
        Description: Action to execute command
        Args:
            params: Command line parameters
        Returns:

        Raises:

        """
        file_path = params.filepath
        try:
            if file_path:
                file_path = os.path.abspath(file_path)
            response = requests.post(self.write_host +
                                     '/initsystem', data=json.dumps({'configfile': file_path}),
                                     headers=self.headers)
        except ConnErr as conn_error:
            LOGGER.logger.error(conn_error)
            print(str(conn_error))
        else:
            if response.status_code == 200:
                try:
                    response_data = json.loads(response.text)
                except JSONDecodeError as json_error:
                    LOGGER.logger.error(json_error)
                    print(response.text)
                else:
                    if response_data.get('code') == ResponseCode.SUCCESS:
                        print('Database initialization success ')
                    else:
                        LOGGER.logger.error(response_data.get('msg'))
                        print(response_data.get('msg'))
            else:
                self.http_error(response)


class AllPackageCommand(PkgshipCommand):
    """
    Description: get all package commands
    Attributes:
        parse: Command line parsing example
        params: Command line parameters
        table: Output table
    """

    def __init__(self):
        """
        Description: Class instance initialization
        """
        super(AllPackageCommand, self).__init__()

        self.parse = PkgshipCommand.subparsers.add_parser(
            'list', help='get all package data')
        self.table = self.create_table(
            ['Package Names', 'Database', 'Version', 'License', 'Maintainer',
             'Release Date', 'Used Time'])
        self.params = [('tablename', 'str', 'name of the database operated', '', 'store'),
                       ('-remote', 'str', 'The address of the remote service',
                        False, 'store_true'),
                       ('-packagename', 'str',
                        'Package name that needs fuzzy matching', '', 'store'),
                       ('-maintainer', 'str', 'Maintainer\'s name', '', 'store')
                       ]

    def register(self):
        """
        Description: Command line parameter injection
        Args:

        Returns:

        Raises:

        """
        super(AllPackageCommand, self).register()
        self.parse.set_defaults(func=self.do_command)

    def __parse_package(self, response_data, table_name):
        """
        Description: Parse the corresponding data of the package
        Args:
            response_data: http request response content
        Returns:

        Raises:

        """
        if response_data.get('code') == ResponseCode.SUCCESS:
            package_all = response_data.get('data')
            if isinstance(package_all, list):
                for package_item in package_all:
                    row_data = [package_item.get('name'),
                                table_name,
                                package_item.get('version') if package_item.get(
                                    'version') else '',
                                package_item.get('rpm_license') if package_item.get(
                                    'rpm_license') else '',
                                package_item.get('maintainer') if package_item.get(
                                    'maintainer') else '',
                                package_item.get('release_time') if package_item.get(
                                    'release_time') else '',
                                package_item.get('used_time')]
                    self.table.add_row(row_data)
        else:
            print(response_data.get('msg'))

    def do_command(self, params):
        """
        Description: Action to execute command
        Args:
            params: Command line parameters
        Returns:

        Raises:
            ConnectionError: Request connection error
        """
        self._set_read_host(params.remote)
        _url = self.read_host + \
               '/packages?table_name={table_name}&query_pkg_name={pkg_name}&\
               maintainner={maintainer}&maintainlevel={maintainlevel}&\
               page_num={page}&page_size={pagesize}'.format(
                   table_name=params.tablename,
                   pkg_name=params.packagename,
                   maintainer=params.maintainer,
                   maintainlevel='',
                   page=1,
                   pagesize=65535).replace(' ', '')
        try:
            response = requests.get(_url)
        except ConnErr as conn_error:
            LOGGER.logger.error(conn_error)
            print(str(conn_error))
        else:
            if response.status_code == 200:
                try:
                    response_data = json.loads(response.text)
                    self.__parse_package(response_data, params.tablename)
                except JSONDecodeError as json_error:
                    LOGGER.logger.error(json_error)
                    print(response.text)

                if getattr(self.table, 'rowcount'):
                    print(self.table)
                else:
                    print('Sorry, no relevant information has been found yet')
            else:
                self.http_error(response)


class UpdatePackageCommand(PkgshipCommand):
    """
    Description: update package data
    Attributes:
        parse: Command line parsing example
        params: Command line parameters
    """

    def __init__(self):
        """
        Description: Class instance initialization
        """
        super(UpdatePackageCommand, self).__init__()

        self.parse = PkgshipCommand.subparsers.add_parser(
            'updatepkg', help='update package data')
        self.params = [
            ('-packagename', 'str', 'Source package name', '', 'store'),
            ('-maintainer', 'str', 'Maintainers name', '', 'store'),
            ('-maintainlevel', 'int', 'database priority', 1, 'store'),
            ('-filefolder', 'str', 'Path of yaml file for batch update', '', 'store'),
            ('--batch', 'str', 'The address of the remote service',
             False, 'store_true'),
        ]

    def register(self):
        """
        Description: Command line parameter injection
        Args:

        Returns:

        Raises:

        """
        super(UpdatePackageCommand, self).register()
        self.parse.set_defaults(func=self.do_command)

    def do_command(self, params):
        """
        Description: Action to execute command
        Args:
            params: Command line parameters
        Returns:

        Raises:
            ConnectionError: Request connection error
        """
        _url = self.write_host + '/lifeCycle/updatePkgInfo'
        try:
            _folder = params.filefolder
            if _folder:
                _folder = os.path.abspath(_folder)
            response = requests.put(
                _url, data=json.dumps({'pkg_name': params.packagename,
                                       'maintainer': params.maintainer,
                                       'maintainlevel': params.maintainlevel,
                                       'batch': params.batch,
                                       'filepath': _folder}),
                headers=self.headers)
        except ConnErr as conn_error:
            LOGGER.logger.error(conn_error)
            print(str(conn_error))
        else:
            if response.status_code == 200:
                try:
                    data = json.loads(response.text)
                except JSONDecodeError as json_error:
                    LOGGER.logger.error(json_error)
                    print(response.text)
                else:
                    if data.get('code') == ResponseCode.SUCCESS:
                        print('Update package data completed')
                    else:
                        LOGGER.logger.error(data.get('msg'))
                        print(data.get('msg'))
            else:
                self.http_error(response)


class BuildDepCommand(PkgshipCommand):
    """
    Description: query the compilation dependencies of the specified package
    Attributes:
        parse: Command line parsing example
        params: Command line parameters
        collection: Is there a collection parameter
        collection_params: Command line collection parameters
    """

    def __init__(self):
        """
        Description: Class instance initialization
        """
        super(BuildDepCommand, self).__init__()
        self.table = PkgshipCommand.create_table(
            ['Binary name', 'Source name', 'Version', 'Database name'])
        self.parse = PkgshipCommand.subparsers.add_parser(
            'builddep', help='query the compilation dependencies of the specified package')
        self.collection = True
        self.params = [
            ('packagename', 'str', 'source package name', '', 'store'),
            ('-remote', 'str', 'The address of the remote service', False, 'store_true')
        ]
        self.collection_params = [
            ('-dbs', 'Operational database collection')
        ]

    def register(self):
        """
        Description: Command line parameter injection
        Args:

        Returns:

        Raises:

        """
        super(BuildDepCommand, self).register()
        # collection parameters

        for cmd_params in self.collection_params:
            self.parse.add_argument(
                cmd_params[0], nargs='*', default=None, help=cmd_params[1])
        self.parse.set_defaults(func=self.do_command)

    def do_command(self, params):
        """
        Description: Action to execute command
        Args:
            params: Command line parameters
        Returns:

        Raises:
            ConnectionError: Request connection error
        """
        self._set_read_host(params.remote)

        _url = self.read_host + '/packages/findBuildDepend'
        try:
            response = requests.post(
                _url, data=json.dumps({'sourceName': params.packagename,
                                       'db_list': params.dbs}),
                headers=self.headers)
        except ConnErr as conn_error:
            LOGGER.logger.error(conn_error)
            print(str(conn_error))
        else:
            if response.status_code == 200:
                try:
                    statistics_table = self.parse_depend_package(
                        json.loads(response.text), params)
                except JSONDecodeError as json_error:
                    LOGGER.logger.error(json_error)
                    print(response.text)
                else:
                    if getattr(self.table, 'rowcount'):
                        self.print_('query {} buildDepend  result display:'.format(
                            params.packagename))
                        print(self.table)
                        self.print_('Statistics')
                        print(statistics_table)
            else:
                self.http_error(response)


class InstallDepCommand(PkgshipCommand):
    """
    Description: query the installation dependencies of the specified package
    Attributes:
        parse: Command line parsing example
        params: Command line parameters
        collection: Is there a collection parameter
        collection_params: Command line collection parameters
    """

    def __init__(self):
        """
        Description: Class instance initialization
        """
        super(InstallDepCommand, self).__init__()

        self.parse = PkgshipCommand.subparsers.add_parser(
            'installdep', help='query the installation dependencies of the specified package')
        self.collection = True
        self.params = [
            ('packagename', 'str', 'source package name', '', 'store'),
            ('-remote', 'str', 'The address of the remote service', False, 'store_true')
        ]
        self.collection_params = [
            ('-dbs', 'Operational database collection')
        ]

    def register(self):
        """
        Description: Command line parameter injection
        Args:

        Returns:

        Raises:

        """
        super(InstallDepCommand, self).register()
        # collection parameters

        for cmd_params in self.collection_params:
            self.parse.add_argument(
                cmd_params[0], nargs='*', default=None, help=cmd_params[1])
        self.parse.set_defaults(func=self.do_command)

    def __parse_package(self, response_data, params):
        """
        Description: Parse the corresponding data of the package
        Args:
            response_data: http response data
            params: Parameters passed in on the command line
        Returns:

        Raises:

        """
        self.table = PkgshipCommand.create_table(
            ['Binary name', 'Source name', 'Version', 'Database name'])
        if getattr(self, 'statistics'):
            setattr(self, 'statistics', dict())
        bin_package_count = 0
        src_package_count = 0
        if response_data.get('code') == ResponseCode.SUCCESS:
            package_all = response_data.get('data')
            if isinstance(package_all, dict):
                if package_all.get("not_found_components"):
                    print("Problem: Not Found Components")
                    for not_found_com in package_all.get("not_found_components"):
                        print("  - nothing provides {} needed by {} ".format(
                            not_found_com, params.packagename))
                for bin_package, package_depend in package_all.get("install_dict").items():
                    # distinguish whether the current data is the data of the root node
                    if isinstance(package_depend, list) and package_depend[-1][0][0] != 'root':

                        row_data = [bin_package,
                                    package_depend[ListNode.SOURCE_NAME],
                                    package_depend[ListNode.VERSION],
                                    package_depend[ListNode.DBNAME]]
                        # Whether the database exists
                        if package_depend[ListNode.DBNAME] not in self.statistics:
                            self.statistics[package_depend[ListNode.DBNAME]] = {
                                'binary': [],
                                'source': []
                            }
                        # Determine whether the current binary package exists
                        if bin_package not in \
                                self.statistics[package_depend[ListNode.DBNAME]]['binary']:
                            self.statistics[package_depend[ListNode.DBNAME]]['binary'].\
                                append(bin_package)
                            bin_package_count += 1
                        # Determine whether the source package exists
                        if package_depend[ListNode.SOURCE_NAME] not in \
                                self.statistics[package_depend[ListNode.DBNAME]]['source']:
                            self.statistics[package_depend[ListNode.DBNAME]]['source'].append(
                                package_depend[ListNode.SOURCE_NAME])
                            src_package_count += 1

                        self.table.add_row(row_data)
        else:
            LOGGER.logger.error(response_data.get('msg'))
            print(response_data.get('msg'))
        # Display of aggregated data
        statistics_table = self.statistics_table(
            bin_package_count, src_package_count)

        return statistics_table

    def do_command(self, params):
        """
        Description: Action to execute command
        Args:
            params: Command line parameters
        Returns:

        Raises:
            ConnectionError: requests connection error
        """
        self._set_read_host(params.remote)

        _url = self.read_host + '/packages/findInstallDepend'
        try:
            response = requests.post(_url, data=json.dumps(
                {
                    'binaryName': params.packagename,
                    'db_list': params.dbs
                }, ensure_ascii=True), headers=self.headers)
        except ConnErr as conn_error:
            LOGGER.logger.error(conn_error)
            print(str(conn_error))
        else:
            if response.status_code == 200:
                try:
                    statistics_table = self.__parse_package(
                        json.loads(response.text), params)
                except JSONDecodeError as json_error:
                    LOGGER.logger.error(json_error)
                    print(response.text)
                else:
                    if getattr(self.table, 'rowcount'):
                        self.print_('query {} InstallDepend result display:'.format(
                            params.packagename))
                        print(self.table)
                        self.print_('Statistics')
                        print(statistics_table)
            else:
                self.http_error(response)


class SelfBuildCommand(PkgshipCommand):
    """
    Description: self-compiled dependency query
    Attributes:
        parse: Command line parsing example
        params: Command line parameters
        collection: Is there a collection parameter
        collection_params: Command line collection parameters
    """

    def __init__(self):
        """
        Description: Class instance initialization
        """
        super(SelfBuildCommand, self).__init__()

        self.parse = PkgshipCommand.subparsers.add_parser(
            'selfbuild', help='query the self-compiled dependencies of the specified package')
        self.collection = True
        self.bin_package_table = self.create_table(
            ['Package name', 'Source Name', 'Version', 'Database'])
        self.src_package_table = self.create_table([
            'Source Name', 'Version', 'Database'])
        self.params = [
            ('packagename', 'str', 'source package name', '', 'store'),
            ('-t', 'str', 'Source of data query', 'binary', 'store'),
            ('-w', 'str', 'whether to include other subpackages of binary', 0, 'store'),
            ('-s', 'str', 'whether it is self-compiled', 0, 'store'),
            ('-remote', 'str', 'The address of the remote service', False, 'store_true')
        ]

        self.collection_params = [
            ('-dbs', 'Operational database collection')
        ]

    def register(self):
        """
        Description: Command line parameter injection
        Args:

        Returns:

        Raises:

        """
        super(SelfBuildCommand, self).register()
        # collection parameters

        for cmd_params in self.collection_params:
            self.parse.add_argument(
                cmd_params[0], nargs='*', default=None, help=cmd_params[1])
        self.parse.set_defaults(func=self.do_command)

    def _parse_bin_package(self, bin_packages):
        """
        Description: Parsing binary result data
        Args:
            bin_packages: Binary package data

        Returns:

        Raises:

        """
        bin_package_count = 0
        if bin_packages:
            for bin_package, package_depend in bin_packages.items():
                # distinguish whether the current data is the data of the root node
                if isinstance(package_depend, list) and package_depend[-1][0][0] != 'root':

                    row_data = [bin_package, package_depend[ListNode.SOURCE_NAME],
                                package_depend[ListNode.VERSION], package_depend[ListNode.DBNAME]]

                    # Whether the database exists
                    if package_depend[ListNode.DBNAME] not in self.statistics:
                        self.statistics[package_depend[ListNode.DBNAME]] = {
                            'binary': [],
                            'source': []
                        }
                    # Determine whether the current binary package exists
                    if bin_package not in \
                            self.statistics[package_depend[ListNode.DBNAME]]['binary']:
                        self.statistics[package_depend[ListNode.DBNAME]]['binary'].\
                            append(bin_package)
                        bin_package_count += 1
                    self.bin_package_table.add_row(row_data)

        return bin_package_count

    def _parse_src_package(self, src_packages):
        """
        Description: Source package data analysis
        Args:
            src_packages: Source package

        Returns:
            Source package data
        Raises:

        """
        src_package_count = 0
        if src_packages:
            for src_package, package_depend in src_packages.items():
                # distinguish whether the current data is the data of the root node
                if isinstance(package_depend, list):

                    row_data = [src_package, package_depend[ListNode.VERSION],
                                package_depend[DB_NAME]]
                    # Whether the database exists
                    if package_depend[DB_NAME] not in self.statistics:
                        self.statistics[package_depend[DB_NAME]] = {
                            'binary': [],
                            'source': []
                        }
                    # Determine whether the current binary package exists
                    if src_package not in self.statistics[package_depend[DB_NAME]]['source']:
                        self.statistics[package_depend[DB_NAME]]['source'].append(src_package)
                        src_package_count += 1

                    self.src_package_table.add_row(row_data)

        return src_package_count

    def __parse_package(self, response_data, params):
        """
        Description: Parse the corresponding data of the package
        Args:
            response_data: http response data
            params: Parameters passed in on the command line
        Returns:
            Summarized data table
        Raises:

        """
        if getattr(self, 'statistics'):
            setattr(self, 'statistics', dict())
        bin_package_count = 0
        src_package_count = 0

        if response_data.get('code') == ResponseCode.SUCCESS:
            package_all = response_data.get('data')
            if isinstance(package_all, dict):
                # Parsing binary result data
                if package_all.get("not_found_components"):
                    print("Problem: Not Found Components")
                    for not_found_com in package_all.get("not_found_components"):
                        print("  - nothing provides {} needed by {} ".format(
                            not_found_com, params.packagename))
                bin_package_count = self._parse_bin_package(
                    package_all.get('binary_dicts'))

                # Source package data analysis
                src_package_count = self._parse_src_package(
                    package_all.get('source_dicts'))
        else:
            LOGGER.logger.error(response_data.get('msg'))
            print(response_data.get('msg'))
        # Display of aggregated data
        statistics_table = self.statistics_table(
            bin_package_count, src_package_count)
        # return (bin_package_table, src_package_table, statistics_table)
        return statistics_table

    def do_command(self, params):
        """
        Description: Action to execute command
        Args:
            params: commands lines params
        Returns:

        Raises:
            ConnectionError: requests connection error
        """
        self._set_read_host(params.remote)
        _url = self.read_host + '/packages/findSelfDepend'
        try:
            response = requests.post(_url,
                                     data=json.dumps({
                                         'packagename': params.packagename,
                                         'db_list': params.dbs,
                                         'packtype': params.t,
                                         'selfbuild': str(params.s),
                                         'withsubpack': str(params.w)}),
                                     headers=self.headers)
        except ConnErr as conn_error:
            LOGGER.logger.error(conn_error)
            print(str(conn_error))
        else:
            if response.status_code == 200:
                try:
                    statistics_table = self.__parse_package(
                        json.loads(response.text), params)
                except JSONDecodeError as json_error:
                    LOGGER.logger.error(json_error)
                    print(response.text)
                else:
                    if getattr(self.bin_package_table, 'rowcount') \
                            and getattr(self.src_package_table, 'rowcount'):
                        self.print_('query {} selfDepend result display :'.format(
                            params.packagename))
                        print(self.bin_package_table)
                        self.print_(character='=')
                        print(self.src_package_table)
                        self.print_('Statistics')
                        print(statistics_table)
            else:
                self.http_error(response)


class BeDependCommand(PkgshipCommand):
    """
    Description: dependent query
    Attributes:
        parse: Command line parsing example
        params: Command line parameters
    """

    def __init__(self):
        """
        Description: Class instance initialization
        """
        super(BeDependCommand, self).__init__()
        self.table = PkgshipCommand.create_table(
            ['Binary name', 'Source name', 'Version', 'Database name'])
        self.parse = PkgshipCommand.subparsers.add_parser(
            'bedepend', help='dependency query for the specified package')
        self.params = [
            ('packagename', 'str', 'source package name', '', 'store'),
            ('db', 'str', 'name of the database operated', '', 'store'),
            ('-w', 'str', 'whether to include other subpackages of binary', 0, 'store'),
            ('-remote', 'str', 'The address of the remote service', False, 'store_true')
        ]

    def register(self):
        """
        Description: Command line parameter injection
        Args:

        Returns:

        Raises:

        """
        super(BeDependCommand, self).register()
        self.parse.set_defaults(func=self.do_command)

    def do_command(self, params):
        """
        Description: Action to execute command
        Args:
            params: command lines params
        Returns:

        Raises:
            ConnectionError: requests connection error
        """
        self._set_read_host(params.remote)
        _url = self.read_host + '/packages/findBeDepend'
        try:
            response = requests.post(_url, data=json.dumps(
                {
                    'packagename': params.packagename,
                    'dbname': params.db,
                    'withsubpack': str(params.w)
                }
            ), headers=self.headers)
        except ConnErr as conn_error:
            LOGGER.logger.error(conn_error)
            print(str(conn_error))
        else:
            if response.status_code == 200:
                try:
                    statistics_table = self.parse_depend_package(
                        json.loads(response.text))
                except JSONDecodeError as json_error:
                    LOGGER.logger.error(json_error)
                    print(response.text)
                else:
                    if getattr(self.table, 'rowcount'):
                        self.print_('query {} beDepend result display :'.format(
                            params.packagename))
                        print(self.table)
                        self.print_('Statistics')
                        print(statistics_table)

            else:
                self.http_error(response)


class SingleCommand(PkgshipCommand):
    """
    Description: query single package information
    Attributes:
        parse: Command line parsing example
        params: Command line parameters
    """

    def __init__(self):
        """
        Description: Class instance initialization
        """
        super(SingleCommand, self).__init__()

        self.parse = PkgshipCommand.subparsers.add_parser(
            'single', help='query the information of a single package')
        self.params = [
            ('packagename', 'str', 'source package name', '', 'store'),
            ('tablename', 'str', 'name of the database operated', '', 'store'),
            ('-remote', 'str', 'The address of the remote service', False, 'store_true')
        ]
        self.provides_table = self.create_table(['Symbol', 'Required by'])
        self.requires_table = self.create_table(['Symbol', 'Provides by'])

    def register(self):
        """
        Description: Command line parameter injection
        Args:

        Returns:

        Raises:

        """
        super(SingleCommand, self).register()
        self.parse.set_defaults(func=self.do_command)

    # pylint: disable=too-many-branches
    def __parse_package_detail(self, response_data):
        """
        Description: Parse the detail data of the package
        Args:
            response_data: http response data
        Returns:

        Raises:

        """
        _show_field_name = {'pkg_name': "Package Name", 'version': "Version", 'release': "Release",
                            'url': "Url", 'license': "License", 'feature': "Feature",
                            'maintainer': "Maintainer", 'maintainlevel': "Maintain Level",
                            'gitee_url': "Gitee Url", 'issue': "Issue", 'summary': "Summary",
                            'description': "Description", 'buildrequired': "Build Required"}
        _package_detail_info = response_data.get('data')
        _line_content = []
        if _package_detail_info:
            for key, name_value in _show_field_name.items():
                value = _package_detail_info.get(key)
                if value is None:
                    value = ''
                if isinstance(value, list):
                    value_s = self.show_separation(value, LIST_LEN, separation_str=',')
                    for idx, con in enumerate(value_s):
                        if idx != 0:
                            name_value = " "
                        _line_content.append("%-15s:%s" % (name_value, con))
                if key == "description":
                    value = _package_detail_info.get(key).split()
                    value_d = self.show_separation(value, DEPRECATION_LEN)
                    for idx, con in enumerate(value_d):
                        if idx != 0:
                            name_value = " "
                        _line_content.append("%-15s:%s" % (name_value, con))
                if not isinstance(value, list) and key != "description":
                    _line_content.append('%-15s:%s' % (name_value, value))
        for content in _line_content:
            self.print_(content=content)

    def __parse_provides(self, provides):
        """
            Data analysis of provides package
        """
        if provides and isinstance(provides, list):
            for _provide in provides:
                _required_by = '\n'.join(
                    _provide['requiredby']) if _provide['requiredby'] else ''
                self.provides_table.add_row(
                    [_provide['name'], _required_by])
        self.print_('Provides')
        if getattr(self.provides_table, 'rowcount'):
            print(self.provides_table)
        else:
            print('No relevant dependent data')
        self.provides_table.clear_rows()

    def __parse_requires(self, requires):
        """
            Data analysis of requires package
        """
        if requires and isinstance(requires, list):
            for _require in requires:
                _provide_by = '\n'.join(
                    _require['providedby']) if _require['providedby'] else ''
                self.requires_table.add_row(
                    [_require['name'], _provide_by])
        self.print_('Requires')
        if getattr(self.requires_table, 'rowcount'):
            print(self.requires_table)
        else:
            print('No related components')
        self.requires_table.clear_rows()

    def __parse_subpack(self, subpacks):
        """
            Data analysis of binary package
        """
        for subpack_item in subpacks:
            print('-' * 50)
            self.print_(subpack_item['name'])

            self.__parse_provides(subpack_item['provides'])
            self.__parse_requires(subpack_item['requires'])

    def __parse_package(self, response_data):
        """
        Description: Parse the corresponding data of the package
        Args:
            response_data: http response data
        Returns:

        Raises:

        """
        if response_data.get('code') == ResponseCode.SUCCESS:

            self.__parse_package_detail(response_data)
            try:
                _subpacks = response_data['data']['subpack']
                self.__parse_subpack(_subpacks)
            except KeyError as key_error:
                LOGGER.logger.error(key_error)
        else:
            print(response_data.get('msg'))

    def do_command(self, params):
        """
        Description: Action to execute command
        Args:
            params: command lines params
        Returns:

        Raises:
            ConnectionError: requests connection error
        """
        self._set_read_host(params.remote)
        _url = self.read_host + \
               '/packages/packageInfo?table_name={db_name}&pkg_name={packagename}' \
                   .format(db_name=params.tablename, packagename=params.packagename)
        try:
            response = requests.get(_url)
        except ConnErr as conn_error:
            LOGGER.logger.error(conn_error)
            print(str(conn_error))
        else:
            if response.status_code == 200:
                try:
                    self.__parse_package(json.loads(response.text))
                except JSONDecodeError as json_error:
                    LOGGER.logger.error(json_error)
                    print(response.text)

            else:
                self.http_error(response)


class IssueCommand(PkgshipCommand):
    """
    Description: Get the issue list
    Attributes:
        parse: Command line parsing example
        params: Command line parameters
    """

    def __init__(self):
        """
        Description: Class instance initialization
        """
        super(IssueCommand, self).__init__()

        self.parse = PkgshipCommand.subparsers.add_parser(
            'issue', help='Query the issue list of the specified package')
        self.params = [
            ('-packagename', 'str', 'Query source package name', '', 'store'),

            ('-issue_type', 'str', 'Type of issue', '', 'store'),
            ('-issue_status', 'str', 'the status of the issue', '', 'store'),
            ('-maintainer', 'str', 'Maintainer\'s name', '', 'store'),
            ('-page', 'int',
             'Need to query the data on the first few pages', 1, 'store'),
            ('-pagesize', 'int',
             'The size of the data displayed on each page', 65535, 'store'),
            ('-remote', 'str', 'The address of the remote service', False, 'store_true')
        ]
        self.table = self.create_table(
            ['Issue ID', 'Package Name', 'Issue Title',
             'Issue Status', 'Issue Type', 'Maintainer'])

    def register(self):
        """
        Description: Command line parameter injection

        """
        super(IssueCommand, self).register()
        self.parse.set_defaults(func=self.do_command)

    def __parse_package(self, response_data):
        """
        Description: Parse the corresponding data of the package

        Args:
            response_data: http response data
        """
        if response_data.get('code') == ResponseCode.SUCCESS:
            issue_all = response_data.get('data')
            if isinstance(issue_all, list):
                for issue_item in issue_all:
                    _row_data = [
                        issue_item.get('issue_id'),
                        issue_item.get('pkg_name') if issue_item.get(
                            'pkg_name') else '',
                        issue_item.get('issue_title')[:20] + '...' if issue_item.get(
                            'issue_title') else '',
                        issue_item.get('issue_status') if issue_item.get(
                            'issue_status') else '',
                        issue_item.get('issue_type') if issue_item.get(
                            'issue_type') else '',
                        issue_item.get('maintainer') if issue_item.get('maintainer') else '']
                    self.table.add_row(_row_data)
        else:
            print(response_data.get('msg'))

    def do_command(self, params):
        """
        Description: Action to execute command
        Args:
            params: command lines params
        Returns:

        Raises:
            ConnectionError: requests connection error
        """
        if "," in params.issue_type or "," in params.issue_status:
            print('Params issue_type or issue_status are error! Please check and try it again')
            return
        self._set_read_host(params.remote)
        _url = self.read_host + \
               '/lifeCycle/issuetrace?page_num={page_num}&\
               page_size={page_size}&pkg_name={pkg_name}&issue_type={issue_type}\
               &issue_status={issue_status}&maintainer={maintainer}' \
                   .format(page_num=params.page,
                           page_size=params.pagesize,
                           pkg_name=params.packagename,
                           issue_type=params.issue_type,
                           issue_status=params.issue_status,
                           maintainer=params.maintainer).replace(' ', '')
        try:
            response = requests.get(_url)
        except ConnErr as conn_error:
            LOGGER.logger.error(conn_error)
            print(str(conn_error))
        else:
            if response.status_code == 200:
                try:
                    response_data = json.loads(response.text)
                    self.__parse_package(response_data)
                except JSONDecodeError as json_error:
                    LOGGER.logger.error(json_error)
                    print(response.text)
                if getattr(self.table, "rowcount"):
                    print('total count : %d' % response_data['total_count'])
                    print('total page : %d' % response_data['total_page'])
                    print('current page : %s ' % params.page)
                    print(self.table)
                else:
                    print("Sorry, no relevant information has been found yet")
            else:
                self.http_error(response)


class AllTablesCommand(PkgshipCommand):
    """
    Description: Get all data tables in the current life cycle
    Attributes:
        parse: Command line parsing example
        params: Command line parameters
    """

    def __init__(self):
        """
        Description: Class instance initialization
        """
        super(AllTablesCommand, self).__init__()

        self.parse = PkgshipCommand.subparsers.add_parser(
            'tables', help='Get all data tables in the current life cycle')
        self.params = [
            ('-remote', 'str', 'The address of the remote service', False, 'store_true')
        ]

    def register(self):
        """
        Description: Command line parameter injection

        """
        super(AllTablesCommand, self).register()
        self.parse.set_defaults(func=self.do_command)

    def do_command(self, params):
        """
        Description: Action to execute command
        Args:
            params: command lines params
        Returns:

        Raises:
            ConnectionError: requests connection error
        """
        self._set_read_host(params.remote)
        _url = self.read_host + '/lifeCycle/tables'
        try:
            response = requests.get(_url, headers=self.headers)
        except ConnErr as conn_error:
            LOGGER.logger.error(conn_error)
            print(str(conn_error))
        else:
            if response.status_code == 200:
                try:
                    _response_content = json.loads(response.text)
                    if _response_content.get('code') == ResponseCode.SUCCESS:
                        print(
                            'The version libraries that exist in the ',
                            'current life cycle are as follows:')
                        for table in _response_content.get('data', []):
                            print(table)
                    else:
                        print('Failed to get the lifecycle repository')
                except JSONDecodeError as json_error:
                    LOGGER.logger.error(json_error)
                    print(response.text)
            else:
                self.http_error(response)


class BatchTaskCommand(PkgshipCommand):
    """
    Description: Issue and life cycle information involved in batch processing packages
    Attributes:
        parse: Command line parsing example
        params: Command line parameters
    """

    def __init__(self):
        """
        Description: Class instance initialization
        """
        super(BatchTaskCommand, self).__init__()

        self.parse = PkgshipCommand.subparsers.add_parser(
            'update',
            help='Issue and life cycle information involved in batch processing packages')
        self.params = [
            ('--issue', 'str', 'Batch operation on issue', False, 'store_true'),
            ('--package', 'str', 'Package life cycle information processing',
             False, 'store_true'),
        ]

    def register(self):
        """
        Description: Command line parameter injection

        """
        super(BatchTaskCommand, self).register()
        self.parse.set_defaults(func=self.do_command)

    def do_command(self, params):
        """
        Description: Action to execute command
        Args:
            params: command lines params
        Returns:

        Raises:
            ConnectionError: requests connection error
        """
        if not params.issue and not params.package:
            print('Please select the way to operate')
        if params.issue:
            issue_thread = threading.Thread(
                target=update_pkg_info, args=(False,))
            issue_thread.start()
        if params.package:
            update_pkg_thread = threading.Thread(
                target=update_pkg_info)
            update_pkg_thread.start()


class GetFilelistInfoCommand(PkgshipCommand):
    """
    Description: get binary package info
    Attributes:
        params: Command line parameters
    """

    def __init__(self):
        """
        Description: Class instance initialization
        """
        super(GetFilelistInfoCommand, self).__init__()
        self.columns = 30

        self.parse = PkgshipCommand.subparsers.add_parser(
            'info', help='Query filelist info')
        self.params = [
            ('--dbname', 'str', 'Database name', 'openEuler', 'store'),
        ]

    def register(self):
        """
        Description: Command line parameter injection
        Args:

        Returns:

        Raises:

        """
        super(GetFilelistInfoCommand, self).register()
        self.parse.set_defaults(func=self.do_command)
        self.parse.add_argument('--packagename', nargs='*', required=True, default=None,
                                help='Package name')

    @staticmethod
    def create_table(title=None):
        """
        Description: Create printed forms
        Args:
            title: Table title
        Returns:
            ASCII format table
        Raises:
            """
        table = super(GetFilelistInfoCommand, GetFilelistInfoCommand).create_table(title)
        table.horizontal_char = '-'
        table.left_padding_width = 0
        return table

    def print_filelist_info(self, filelist_dict):
        """
        Description: Print filelist information on the command line
        Args:

        Returns:

        Raises:

        """
        if filelist_dict:
            for each_packagename, package_info in filelist_dict.items():
                self.print_(each_packagename, dividing_line=True)

                for key, values in package_info.items():
                    if values:
                        table = self.create_table([key])
                        for value in values:
                            table.add_row([value])
                        print(table, '\n')

    def do_command(self, params):
        """
        Description: Action to execute command
        Args:
            params: Command line parameters
        Returns:

        Raises:
            ConnectionError: Request connection error
        """
        packagenames = "$".join(params.packagename)
        _url = self.read_host + \
               '/packages/packageInfo/file?db_name={db_name}&pkg_name={packagename}' \
                   .format(db_name=params.dbname, packagename=packagenames)
        try:
            response = requests.get(_url)
        except ConnErr as conn_error:
            LOGGER.logger.error(conn_error)
            print(str(conn_error))
        else:
            if response.status_code == 200:
                try:
                    response_data = json.loads(response.text)

                    self.print_filelist_info(response_data['data'])

                except JSONDecodeError as json_error:
                    LOGGER.logger.error(json_error)
                    print(response.text)
                else:
                    if response_data.get('code') == ResponseCode.SUCCESS:
                        print('query completed')
                    else:
                        LOGGER.logger.error(response_data.get('msg'))
                        print(response_data.get('msg'))
            else:
                self.http_error(response)


if __name__ == '__main__':
    main()
