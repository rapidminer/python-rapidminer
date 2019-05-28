#
# This file is part of the RapidMiner Python package.
#
# Copyright (C) 2018-2019 RapidMiner GmbH
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
import pandas as pd
from collections import OrderedDict
from .utilities import __DEFAULT_ENCODING__

class Connector(object):
    """
    Base class for interacting with RapidMiner. The subclasses of this class should be used.
    """
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
        :param macros: optional dict that sets the macros in the process context according to the key-value pairs.
        :return: the results of the RapidMiner process. It can be None, or a single object, or a tuple.
        """
        raise NotImplementedError("Method not implemented in base class.")

    def _suppress_pandas_warning(self, f):
        try:
            import warnings
        except:
            f()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            f()

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

    # TODO refactor this method to reduce its cognitivy complexity (44->15)
    def _write_metadata(self, data, text_file):
        """
        Writes the meta data to a stream (a file object with text type)
        uses the meta data from rm_metadata attribute if present
        otherwise deduces the type from the data and sets no special role.

        Taken -- with some modification -- from the legacy wrapper.py code (handleMetaData).

        :param data: the pandas DataFrame.
        :param text_file: the file object representing a text resource (e.g. the result of 'open("myfile.txt", "r", encoding="utf-8")')
        :return:
        """
        metadata = OrderedDict()
        #check if rm_metadata attribute is present and a dictionary
        try:
            if isinstance(data.rm_metadata, dict):
                meta_isdict = True
            else:
                meta_isdict = False
                if data.rm_metadata is not None:
                    self.log("'rm_metadata' must be a dictionary.", level=logging.WARNING)
        except:
            meta_isdict = False

        for name in data.columns.values:
            try:
                meta = data.rm_metadata[name]
                if isinstance(meta, tuple) and len(meta) == 2 and meta_isdict:
                    meta_type, meta_role = meta
                else:
                    if meta_isdict and meta is not None:
                        self.log("'rm_metadata[" + name + "]' must be a tuple of length 2, e.g. data.rm_metadata['column1']=('binominal','label')", level=logging.WARNING)
                    if isinstance(meta, tuple) or isinstance(meta, list) and len(meta) > 0:
                        meta_type = meta[0]
                    else:
                        try:
                            meta_type = str(meta)
                        except:
                            meta_type = None
                    if isinstance(meta, tuple) or isinstance(meta, list) and len(meta) > 1:
                        meta_role = meta[1]
                    else:
                        meta_role = None
            except:
                meta_type = None
                meta_role = None

            if meta_role is None:
                meta_role = 'attribute'
            #choose type by dtype of the column
            if meta_type is None:
                kind_char = data.dtypes[name].kind
                if kind_char in ('i','u'):
                    meta_type = 'integer'
                elif kind_char in ('f'):
                    meta_type = 'real'
                elif kind_char in ('M'):
                    meta_type = 'date_time'
                elif kind_char in ('b'):
                    meta_type = 'binominal'
                else:
                    meta_type = 'polynomial'
            metadata[name] = [meta_type, meta_role]
        #store as json
        try:
            json.dump(metadata, text_file)
        except Exception as e:
            self.log("Failed to send meta data from Python script to RapidMiner (reason: " + str(e) + ").", level=logging.WARNING)

    def _set_metadata(self, df, metadata):
        df.rm_metadata = metadata

    def _copy_dataframe(self, df):
        """
        Returns a copy of the metadata. Handles the special 'rm_metadata' attribute as well.

        :param df: a pandas DataFrame.
        :return: copy of the pandas DataFrame.
        """
        copy = df.copy()
        if hasattr(df, "rm_metadata"):
            self._suppress_pandas_warning(lambda: self._set_metadata(copy, df.rm_metadata))
        return copy;

    def _serialize_dataframe(self, df, streams):
        """
        Serializes a pandas DataFrame to CSV, using the format required by RapidMiner Read CSV operator.

        :param df: the pandas DataFrame.
        :param streams: list of (text) file objects. The list should contain to objects, the first is foir the actual data (csv), the second for the metadata (pmd).
        :return:
        """
        dfc = self._copy_dataframe(df) # make a copy, as the column names may be modified
        dfc.columns = self._rename_invalid_columns(dfc.columns)
        dfc.to_csv(streams[0], index=False, encoding=__DEFAULT_ENCODING__)
        self._write_metadata(dfc, streams[1])

    def _deserialize_dataframe(self, csv_stream, md_stream):
        """
        Reads a csv file into a pandas Dataframe. Code --with slight modifications -- taken from wrapper.py (readExampleSet).

        :param csv_stream: the -seekable- csv stream to read from. Must have special format (which is created by the corresponding Java
                code in the Studio part.
        :param md_stream: metadata stream, containing additional column type infos created by Studio.
        :return: pandas DataFrame object, with special rm_metadata attribute present (this stores the metadata).
        """
        original_position = None
        try:
            metadata = json.load(md_stream)
            date_set = set(['date','time','date_time'])
            date_columns = []
            meta_dict={}
            #different iteration methods for python 2 and 3
            try:
                items = metadata.iteritems()
            except AttributeError:
                items = metadata.items()
            for key, value in items:
                #convert to tuple
                meta_dict[key]=(value[0],None if value[1]=="attribute" else value[1])
                #store date columns for parsing
                if value[0] in date_set:
                    date_columns.append(key)
            #read example set from csv
            original_position = csv_stream.tell()
            try:
                data = pd.read_csv(csv_stream,index_col=None,encoding=__DEFAULT_ENCODING__,parse_dates=date_columns,infer_datetime_format=True)
            except TypeError:
                #if the argument inter_datetime_format is not allowed in the current version do without
                csv_stream.seek(original_position)
                data = pd.read_csv(csv_stream,index_col=None,encoding=__DEFAULT_ENCODING__,parse_dates=date_columns)
            self._suppress_pandas_warning(lambda: self._set_metadata(data, meta_dict))
        except:
            #reading with meta data failed
            self.log("Failed to use the meta data.", level=logging.WARNING)
            if original_position is not None:
                csv_stream.seek(original_position)
            data = pd.read_csv(csv_stream,index_col=None,encoding=__DEFAULT_ENCODING__)
            self._suppress_pandas_warning(lambda: self._set_metadata(data, None))
        return data
