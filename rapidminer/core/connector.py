#
# This file is part of the RapidMiner Python package.
#
# Copyright (C) 2018-2021 RapidMiner GmbH
#
# This program is free software: you can redistribute it and/or modify it under the terms of the
# GNU Affero General Public License as published by the Free Software Foundation, either version 3
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without
# even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License along with this program.
# If not, see https://www.gnu.org/licenses/.
#
import json
import logging
import sys
import threading
import datetime
import pandas as pd
from collections import OrderedDict
from .serdeutils import set_metadata_without_warning

class Connector(object):
    """
    Base class for interacting with RapidMiner. The subclasses of this class should be used.
    """
    __date_format_pattern = "%Y-%m-%d %H:%M:%S.%f"
    __id_counter__ = 0
    __lock__ = threading.Lock()

    def __init__(self, logger=None, loglevel=logging.INFO):
        """
        Arguments:
        :param logger: a Logger object to use. By default a very simple logger is used, with INFO level, logging to
                        stdout.
        :param loglevel: the loglevel, as an int value. Common values are defined in the standard logging module. Only
                        used if logger is not defined.
        """
        Connector.__lock__.acquire()
        try:
            self.__id__ = Connector.__id_counter__
            Connector.__id_counter__ = Connector.__id_counter__ + 1
        finally:
            Connector.__lock__.release()
        if logger != None:
            self.logger = logger
        else:
            formatter=logging.Formatter("%(asctime)s [%(levelname)s -- %(source)s]: %(message)s")
            syslog=logging.StreamHandler(sys.stdout)
            syslog.setFormatter(formatter)
            self.logger = logging.getLogger(self.__class__.__name__ + "@" + str(self.__id__))
            self.logger.setLevel(loglevel)
            self.logger.addHandler(syslog)

    def log(self, msg, level=logging.INFO, source="python"):
        """
        Logs a message with the defined log level.

        Arguments:
        :param msg: the message to log.
        :param level: the log level as an integer.
        :param source: source of the message, default is 'python'.
        :return:
        """
        self.logger.log(msg=msg.strip(), level=level, extra={"source": source})

    def read_resource(self, path):
        """
        Reads one or more resources from the given locations.

        Arguments:
        :param path: the path(s) to the resource(s). Multiple paths can be specified as list or tuple.
        :return: the resource(s) read from the path(s). If multiple inputs are specified, the same number of inputs will be returned, as a tuple of objects.
        """
        raise NotImplementedError("Method not implemented in base class.")

    def write_resource(self, resource, path):
        """
        Writes the pandas DataFrame to RapidMiner repository/regular file.

        Arguments:
        :param resource: resource(s) to save. Multiple DataFrames or other objects can be specified as list or tuple.
        :param path: the target path(s) for the resource(s). The same number of path values are required as the number of resources.
        """
        raise NotImplementedError("Method not implemented in base class.")


    def run_process(self, path, inputs=[], macros={}):
        """
        Runs a RapidMiner process and returns the result(s).

        Arguments:
        :param path: path to the RapidMiner process.
        :param inputs: inputs used by the RapidMiner process, as a list of input objects or a single input object.
        :param macros: optional dict that sets the macros in the process context according to the key-value pairs, e.g. macros={"macro1": "value1", "macro2": "value2"}
        :return: the results of the RapidMiner process. It can be None, or a single object, or a tuple.
        """
        raise NotImplementedError("Method not implemented in base class.")

    def _can_convert_to_str(self, value):
        """
        Tests, if the given value can be converted to a string representation.

        Taken from the legacy wrapper.py code (isstringable).

        :param value: value to test.
        :return: True, if value can be converted to string, False otherwise.
        """
        try:
            str(value)
            return True
        except:
            return False

    def _rename_invalid_columns(self, columns):
        """
        Renames the invalid column names. Column names must be not empty and not a single number.

        Taken -- with some modification -- from the legacy wrapper.py code (checkColumNames).

        :param columns: list of DataFrame columns.
        :return:
        """
        if any(self._can_convert_to_str(value) and ((not str(value)) or str(value).isdigit()) for value in columns):
            return ['att'+str(value) if (self._can_convert_to_str(value) and ((not str(value)) or str(value).isdigit())) else str(value) for value in columns]
        else:
            return columns

    def _copy_dataframe(self, df):
        """
        Copies the dataframe, together with rm_metadata
        :param df:
        :return:
        """
        copied = df.copy()
        if hasattr(df, "rm_metadata"):
            set_metadata_without_warning(copied, df.rm_metadata)
        return copied
