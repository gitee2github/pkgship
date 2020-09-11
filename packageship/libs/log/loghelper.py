#!/usr/bin/python3
"""
Logging related
"""
import os
import threading
import pathlib
import logging
from concurrent_log_handler import ConcurrentRotatingFileHandler
from packageship import system_config
from packageship.libs.configutils.readconfig import ReadConfig


READCONFIG = ReadConfig(system_config.SYS_CONFIG_PATH)


def setup_log(config=None):
    """
        Log logging in the context of flask
    """
    if config:
        logging.basicConfig(level=config.LOG_LEVEL)
    else:
        _level = READCONFIG.get_config('LOG', 'log_level')
        if _level is None:
            _level = 'INFO'
        logging.basicConfig(level=_level)
    path = READCONFIG.get_config('LOG', 'log_path')
    log_name = READCONFIG.get_config('LOG', 'log_name')
    backup_count = READCONFIG.get_config('LOG', 'backup_count')
    if not backup_count or not isinstance(backup_count, int):
        backup_count = 10
    max_bytes = READCONFIG.get_config('LOG', 'max_bytes')
    if not max_bytes or not isinstance(max_bytes, int):
        max_bytes = 314572800
    if not log_name:
        log_name = 'log_info.log'
    if not path:
        path = os.path.join(system_config.LOG_FOLDER_PATH, log_name)
    else:
        path = os.path.join(path, log_name)
    if not os.path.exists(path):
        try:
            os.makedirs(os.path.split(path)[0])
        except FileExistsError:
            pathlib.Path(path).touch()

    file_log_handler = ConcurrentRotatingFileHandler(
        path, maxBytes=max_bytes, backupCount=backup_count)

    formatter = logging.Formatter(
        '%(levelname)s %(filename)s:%(lineno)d %(message)s')

    file_log_handler.setFormatter(formatter)

    return file_log_handler


class Log():
    """
        General log operations
    """
    _instance_lock = threading.Lock()

    def __init__(self, name=__name__, path=None):
        self.__name = name

        self.__file_handler = None

        log_name = READCONFIG.get_config('LOG', 'log_name')
        if not log_name:
            log_name = 'log_info.log'
        if path:
            self.__path = os.path.join(system_config.LOG_FOLDER_PATH, path)
        else:
            self.__path = READCONFIG.get_config('LOG', 'log_path')
            if not self.__path:
                self.__path = os.path.join(
                    system_config.LOG_FOLDER_PATH, log_name)
            else:
                self.__path = os.path.join(self.__path, log_name)

        if not os.path.exists(self.__path):
            try:
                os.makedirs(os.path.split(self.__path)[0])
            except FileExistsError:
                pathlib.Path(self.__path).touch()
        self.__level = READCONFIG.get_config('LOG', 'log_level')
        if self.__level is None:
            self.__level = 'INFO'
        self.__logger = logging.getLogger(self.__name)
        self.__logger.setLevel(self.__level)
        self.backup_count = READCONFIG.get_config('LOG', 'backup_count') or 10
        self.max_bytes = READCONFIG.get_config('LOG', 'max_bytes') or 314572800
        try:
            self.backup_count = int(self.backup_count)
            self.max_bytes = int(self.max_bytes)
        except ValueError:
            self.backup_count = 10
            self.max_bytes = 314572800
        self.__init_handler()
        self.__set_handler()
        self.__set_formatter()

    def __new__(cls, *args, **kwargs):  # pylint: disable=unused-argument
        """
            Use the singleton pattern to create a thread-safe producer pattern
        """
        if not hasattr(cls, "_instance"):
            with cls._instance_lock:
                if not hasattr(cls, "_instance"):
                    cls._instance = object.__new__(cls)
        return cls._instance

    def __init_handler(self):
        self.__file_handler = ConcurrentRotatingFileHandler(
            self.__path, maxBytes=self.max_bytes, backupCount=self.backup_count, encoding="utf-8")

    def __set_handler(self):
        self.__file_handler.setLevel(self.__level)
        self.__logger.addHandler(self.__file_handler)

    def __set_formatter(self):
        formatter = logging.Formatter('%(asctime)s-%(name)s-%(filename)s-[line:%(lineno)d]'
                                      '-%(levelname)s-[ log details ]: %(message)s',
                                      datefmt='%a, %d %b %Y %H:%M:%S')
        self.__file_handler.setFormatter(formatter)

    def info(self, message):
        """General information printing of the log"""
        self.__logger.info(message)

    def debug(self, message):
        """Log debugging information printing"""
        self.__logger.debug(message)

    def warning(self, message):
        """Log warning message printing"""
        self.__logger.warning(message)

    def error(self, message):
        """Log error message printing"""
        self.__logger.error(message)

    @property
    def logger(self):
        """
            Get logs
        """
        return self.__logger
