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
import shutil
import os
import subprocess
import tempfile
import glob
import sys
import logging
from threading import Thread
import threading
import platform
import io
import pandas
try:
    import cPickle as pickle
except:
    import pickle
from .utilities import __STDOUT_ENCODING__
from .connector import Connector
from .resources import Resource
from .resources import File
from .resources import RepositoryLocation
from .utilities import GeneralException
from .utilities import __open__

class StudioException(Exception):
    def __init__(self, msg=""):
        super(Exception, self).__init__(msg)

class Studio(Connector):
    """
    Class for using a locally installed RapidMiner Studio instance. You can read from and write to the repositories defined in Studio (and use even remote repositories this way) and you can execute processes.
    """
    __TMP_OUTPUT_DIR_PREFIX= "rapidminer-scripting-output-"
    __TMP_INPUT_DIR_PREFIX="rapidminer-scripting-inputs-"
    ___EXIT_CODE_MSG="EXIT_CODE="
    __RAPIDMINER_ERROR_MSG="RAPIDMINER_ERROR_MSG="
    __RAPIDMINER_ERROR_MSG_FIRST_LINE="RAPIDMINER_ERROR_MSG_FIRST_LINE="
    __SCRIPTS_SUBDIR="scripts"

    def __init__(self, studio_home=None, logger=None, loglevel=logging.INFO, rm_stdout=None, override_python_binary=False):
        """
        Initializes a new connector to a local Rapidminer Studio instance. Every command will launch a new Studio instance, executing the required operations in batch mode.

        Arguments:
        :param studio_home: path to installation directory of the Rapidminer Studio. If None, the location will be taken from the RAPIDMINER_HOME environment variable if defined, or the current directory, if RAPIDMINER_HOME is not defined.
        :param logger: a Logger object to use. By default a very simple logger is used, with INFO level, logging to stdout.
        :param loglevel: the loglevel, as an int value. Common values are defined in the standard logging module. Only used, if logger is not defined.
        :param rm_stdout: the output stream to redirect the output of underlying Studio launches. By default, the output is directed to the logger associated with this connector. Log records from Studio are labeled with new element 'key'='studio', while the logs from Python with 'key'='python'.
        :param override_python_binary: if set to True, any Execute Python operator in a process called via run_process will use the current Python interpreter instead of the one configured in the Studio installation, except if the process explicitly defines the Python binary. Default value is False.
        """
        super(Studio, self).__init__(logger, loglevel)
        if studio_home is not None:
            self.studio_home = studio_home
        elif os.getenv("RAPIDMINER_HOME") is not None and not os.getenv("RAPIDMINER_HOME") == "":
            self.studio_home = os.getenv("RAPIDMINER_HOME")
        else:
            # OS specific default home exists
            self.studio_home = Studio.__get_default_rmhome()
        self.__rm_stdout__ = rm_stdout
        self.override_python_binary = override_python_binary
        self.__last_exception_msg__ = {} # ensures proper multithreading: this maps last exception message for every thread
        self.__last_exit_code__ = {} # ensures proper multithreading: this maps last exit code for every thread
        if not os.path.isdir(self.studio_home):
            raise StudioException("Specified or default RapidMiner Home does not exist: " + self.studio_home)
        scripts_dir = os.path.join(self.studio_home, self.__SCRIPTS_SUBDIR)
        if not os.path.isdir(scripts_dir):
            raise StudioException("Specified or default RapidMiner Home does not contain required scripts: " + scripts_dir)

####################
# Public functions #
####################

    def read_resource(self, path):
        """
        Reads one or more resources from the given repository locations / files

        Arguments:
        :param path: the path(s) to the resource(s). Multiple paths can be specified as list or tuple. A path can be a string, in that case it is interpreted as a repository location. By using rapidminer.File and rapidminer.RepositoryLocation objects, you can specify explicitly whether you want to use local files or RapidMiner repository entries.
        :return: the resource(s) as pandas DataFrame(s), a pickle-able python object(s) or a file-like object(s). If multiple inputs are specified, the same number of inputs will be returned, as a tuple of objects.
         """
        if not ((isinstance(path, tuple) or isinstance(path, list))):
            path = [path]
            single_input = True
        else:
            if len(path) == 0:
                return None
            single_input = False
        output_dirs = [tempfile.mkdtemp(prefix=self.__TMP_OUTPUT_DIR_PREFIX) for _ in path]
        try:
            self.__run_rapidminer(input_files=list(path), output_files=[File(output_dir) for output_dir in output_dirs], command_type="READ_RESOURCE")
            output_files = []
            for output_dir in output_dirs:
                csv_files = glob.glob(output_dir + "/*.csv")
                if (len(csv_files) == 1):
                    output_files.append(csv_files[0])
                else:
                    output_files.append(glob.glob(output_dir + "/*")[0])
            result = tuple(self.__deserialize_from_file(output_file) for output_file in output_files)
            if single_input:
                return result[0]
            else:
                return result
        finally:
            for dir in output_dirs:
                shutil.rmtree(dir, ignore_errors=True)

    def write_resource(self, resource, path):
        """
        Writes pandas DataFrame(s) or other objects to RapidMiner repository locations / regular files.

        Arguments:
        :param resource: resource(s) to save: a resource can be a pandas DataFrame, a pickle-able python object or a file-like object. Multiple DataFrames or other objects can be specified as list or tuple.
        :param path: the target path(s) for the resource(s). The same number of path values are required as the number of resources. A path can be a string, in that case it is interpreted as a repository location. By using rapidminer.File and rapidminer.RepositoryLocation objects, you can specify explicitly whether you want to use local files or RapidMiner repository entries.
        """
        if not ((isinstance(resource, tuple) or isinstance(resource, list))):
            resource = [resource]
        if not ((isinstance(path, tuple) or isinstance(path, list))):
            path = [path]

        if len(resource) != len(path):
            raise ValueError("Resource and path must contain the same number of values.")
        input_dirs = [tempfile.mkdtemp(prefix=self.__TMP_INPUT_DIR_PREFIX) for _ in resource]
        try:
            input_files = [self.__serialize_to_file(obj, os.path.join(dir, "input0")) for (dir, obj) in zip(input_dirs, resource)]
            self.__run_rapidminer(input_files=[File(f) for f in input_files], output_files=path, command_type="WRITE_RESOURCE")
        finally:
            for input_dir in input_dirs:
                shutil.rmtree(input_dir, ignore_errors=True)

    def run_process(self, path, inputs=[], macros={}, operator=None):
        """
        Runs a RapidMiner process and returns the result(s).

        Arguments:
        :param path: path to the RapidMiner process in a repository or an .rmp file. It can be a string, in that case it is interpreted as a repository location. It can also be a rapidminer.File or rapidminer.RepositoryLocation object representing a local file or a RapidMiner repository entry, respectively.
        :param inputs: inputs used by the RapidMiner process, an input can be a pandas DataFrame, a pickle-able python object or a file-like object.
        :param operator: the name of the RapidMiner operator of the process to execute. If None (default) the whole process is executed.
        :return: the results of the RapidMiner process. It can be None, or a single object, or a tuple. One result may be a pandas DataFrame, a pickle-able python object or a file-like object.
        """
        if inputs is not None and not (isinstance(inputs, tuple) or isinstance(inputs, list)):
            inputs = [inputs]
        output_dir = tempfile.mkdtemp(prefix=self.__TMP_OUTPUT_DIR_PREFIX)
        remove_dirs = [output_dir]
        try:
            input_files = []
            if inputs:
                input_dir = tempfile.mkdtemp(prefix=self.__TMP_INPUT_DIR_PREFIX)
                remove_dirs.append(input_dir)
                for i in range(len(inputs)):
                    input_files.append(File(self.__serialize_to_file(inputs[i], os.path.join(input_dir, "input" + str(i)))))
            return self.__run_process_with_output_dir(path, input_files, operator, output_dir, macros, command_type="RUN_PROCESS")
        finally:
            for dir in remove_dirs:
                shutil.rmtree(dir, ignore_errors=True)

#####################
# Private functions #
#####################

    def __get_default_rmhome():
        if platform.system() == "Windows":
            return "C:/Program Files/RapidMiner Studio"
        elif platform.system() == "Darwin":
            return "/Applications/RapidMiner Studio.app/Contents/Resources/RapidMiner-Studio"
        else:
            # no default on other systems
            return os.getcwd()

    def __extract_log_level(self, msg):
        # LogLevels: https://docs.python.org/2/library/logging.html#logging-levels
        if msg.startswith("FINEST: "):
            lglevel = logging.DEBUG
            msg = msg[8:]
        elif msg.startswith("FINER: "):
            lglevel = logging.DEBUG
            msg = msg[7:]
        elif msg.startswith("DEBUG: "):
            lglevel = logging.DEBUG
            msg = msg[7:]
        elif msg.startswith("CONFIG: "):
            lglevel = logging.DEBUG
            msg = msg[8:]
        elif msg.startswith("INFO: "):
            lglevel = logging.INFO
            msg = msg[6:]
        elif msg.startswith("WARNING: "):
            lglevel = logging.WARNING
            msg = msg[9:]
        elif msg.startswith("SEVERE: "):
            lglevel = logging.ERROR
            msg = msg[8:]
        elif msg.startswith(self.__RAPIDMINER_ERROR_MSG_FIRST_LINE):
            lglevel = -1
        elif msg.startswith(self.__RAPIDMINER_ERROR_MSG):
            lglevel = logging.ERROR
            msg = msg[len(self.__RAPIDMINER_ERROR_MSG):]
        elif msg.startswith(self.___EXIT_CODE_MSG):
            lglevel = -1
        else:
            lglevel = logging.INFO
        return (msg, lglevel)

    def __update_error_and_exit_code_fields(self, msg, threadid):
        if msg.startswith(self.__RAPIDMINER_ERROR_MSG_FIRST_LINE):
            msg = msg[len(self.__RAPIDMINER_ERROR_MSG_FIRST_LINE):]
            self.__last_exception_msg__[threadid] = msg
        elif msg.startswith(self.___EXIT_CODE_MSG):
            try:
                self.__last_exit_code__[threadid] = int(msg[10:])
            except ValueError:
                self.__last_exit_code__[threadid] = 0

    def __print_to_console(self, process, close_process_stdout=False, threadid = -1):
        for line in iter(process.stdout.readline, b''):
            try:
                msg = line.decode(encoding=__STDOUT_ENCODING__, errors='ignore')
                self.__update_error_and_exit_code_fields(msg, threadid)
                if self.__rm_stdout__ is not None:
                    self.__rm_stdout__.write(msg)
                else:
                    (msg, lglevel) = self.__extract_log_level(msg)
                    self.log(msg, level=lglevel, source="studio")
            except UnicodeEncodeError:
                self.log("<could not decode row>", level=logging.DEBUG, source="studio")
        if close_process_stdout:
            process.stdout.close()

    def __start_printer_thread(self, process):
        t = Thread(target = self.__print_to_console, args=(process, False, threading.currentThread().ident))
        t.daemon = True
        t.start()

    def __quote_params(self, param, prefix=""):
        if platform.system() == "Windows":
            return prefix + param
        else:
            return '\"' + prefix + param + '\"'

    def __encode_params(self, param):
        encoded = ""
        for character in param:
            if ord(character) < 128:
                if character == "\\":
                    # replace \ with \\
                    encoded = encoded + "\\\\"
                elif character == "\"":
                    # replace " with \a
                    encoded = encoded + "\\a"
                else:
                    encoded = encoded + character
            else:
                #replace non ASCII with \nxHHHH, where n is the length og HHHH, HHHH is the hex code
                code = hex(ord(character))[2:]
                encoded = encoded + "\\" + str(len(code)) + "x" + code
        return encoded

    def __append_param(self, params, param, prefix):
        params.append(self.__quote_params(self.__encode_params(param), prefix=prefix))

    def __get_script_suffix(self):
        if platform.system() == "Windows":
            return ".bat"
        elif platform.system() == "Darwin":
            return "-osx.sh"
        else:
            return ".sh"

    def __needs_temp_dir(self, input_file):
        '''
        Returns true, if the given input file will need a temporary directory on the RapidMiner side.

        :param input_file: the file to be inspected. Files with .fo extension needs a temp dir. (file-object)
        :return: true, if the given input file will need a temporary directory on the RapidMiner side.
        '''
        if isinstance(input_file, Resource):
            input_file = input_file.to_string()
        return input_file.endswith(".fo")

    # TODO refactor this method to reduce its cognitive complexity from 26 to the allowed 15...
    def __run_rapidminer(self, process=None, input_files=[], output_files=[], output_dir=None, macros={}, operator=None, command_type=None):
        kwargs = {"stdout": subprocess.PIPE,
                  "stderr": subprocess.STDOUT,
                  "bufsize": 10}
        params = []
        params.append(os.path.join(self.studio_home, self.__SCRIPTS_SUBDIR, "rapidminer-batch" + self.__get_script_suffix()))
        self.__append_param(params, "rmx_python_scripting:com.rapidminer.extension.pythonscripting.launcher.ExtendedCmdLauncher", prefix="-C")
        if (process is not None):
            if not isinstance(process, Resource):
                process = RepositoryLocation(name=process)
            self.__append_param(params, process.to_string(), prefix="-P")
        for input_file in input_files:
            if not isinstance(input_file, Resource):
                input_file = RepositoryLocation(name=input_file)
            self.__append_param(params, input_file.to_string(), prefix="-I")
        for output_file in output_files:
            if not isinstance(output_file, Resource):
                output_file = RepositoryLocation(name=output_file)
            self.__append_param(params, output_file.to_string(), prefix="-O")
        if output_dir is not None:
            self.__append_param(params, output_dir, prefix="-D")
        if operator is not None:
            self.__append_param(params, operator, prefix="-N")
        if len(macros) > 0:
            for key in macros:
                self.__append_param(params, str(key) + "=" + str(macros[key]), prefix="-M")
        if any(self.__needs_temp_dir(input) for input in input_files):
            temp_dir = tempfile.mkdtemp(prefix=self.__TMP_OUTPUT_DIR_PREFIX)
            self.__append_param(params, temp_dir, prefix="-T")
        else:
            temp_dir = None
        if self.override_python_binary:
            self.__append_param(params, sys.executable, prefix="-B")
        if command_type is not None:
            self.__append_param(params, command_type, prefix="-A")
        threadid = threading.currentThread().ident
        if threadid in self.__last_exit_code__:
            del self.__last_exit_code__[threadid]
        if threadid in self.__last_exception_msg__:
            del self.__last_exception_msg__[threadid]
        try:
            p = subprocess.Popen(params, **kwargs)
            try:
                self.__start_printer_thread(p)
                p.wait()
                if not threadid in self.__last_exit_code__ or self.__last_exit_code__[threadid] != 0:
                    if threadid in self.__last_exception_msg__:
                        raise StudioException("Error while executing studio: " + self.__last_exception_msg__[threadid])
                    elif threadid in self.__last_exit_code__:
                        raise StudioException("Error while executing studio - unkown error. (error code: " + str(self.__last_exit_code__) + ")")
                    else:
                        raise StudioException("Error while executing studio - unkown error.")
            finally:
                p.stdout.close()
        finally:
            if temp_dir is not None:
                shutil.rmtree(temp_dir, ignore_errors=True)

    def __run_process_with_output_dir(self, path, input_files, operator, output_dir, macros, command_type):
        self.__run_rapidminer(process=path, input_files=input_files, output_dir=output_dir, macros=macros, operator=operator, command_type=command_type)
        outputs = glob.glob(os.path.join(output_dir, "*.*"))
        outputs.sort()
        result = []
        for output in outputs:
            if not output.endswith(".pmd"):
                result.append(self.__deserialize_from_file(output))
        if len(result) == 0:
            return None
        elif len(result) == 1:
            return result[0]
        return tuple(result)

    def __serialize_dataframe_to_file(self, df, basename):
        """
        Serializes a pandas DataFrame to CSV, using the format reuqired by RapidMiner Read CSV operator.

        :param df: the pandas DataFrame.
        :param basename: the base filename, without extension.
        :return:
        """
        with __open__(basename + ".csv", "w") as csv_file:
            with __open__(basename + ".pmd", "w") as meta_file:
                self._serialize_dataframe(df, [csv_file, meta_file])
        return basename + ".csv"

    def __serialize_to_file(self, object, basename):
        """
        Serializes a python object to the appropriate file.

        :param object, a python object.
        :param basename: the base filename, without extension.
        :return:
        """
        if isinstance(object, pandas.DataFrame):
            return self.__serialize_dataframe_to_file(object, basename)
        else:
            # try to write out as a file like object first
            try:
                with open(basename + ".fo", "w", encoding=object.encoding) as outf:
                    shutil.copyfileobj(object, outf)
                return basename + ".fo"
            except AttributeError:
                try:
                    with open(basename + ".fo", "wb") as outf:
                        shutil.copyfileobj(object, outf)
                    return basename + ".fo"
                except AttributeError:
                    shutil.rmtree(basename + ".fo", ignore_errors=True)
                    with open(basename + ".bin", 'wb') as dump_file:
                        pickle.dump(object, dump_file)
                    return basename + ".bin"

    def __deserialize_dataframe_from_file(self, csv_file, md_file):
        """
        Reads a csv file into a pandas Dataframe. Code -- with slight modifications -- taken from wrapper.py (readExampleSet).

        :param csv_file: the csv file to read from. Must have special format (which is created by the corresponding Java
                code in the Studio part.
        :param md_file: metadata file, containing additional column type infos created by Studio.
        :return: pandas DataFrame object, with special rm_metadata attribute present (this stores the metadata).
        """
        try:
            with __open__(md_file,'r') as md_stream:
                with __open__(csv_file,'r') as csv_stream:
                    return self._deserialize_dataframe(csv_stream, md_stream)
        except:
            #no metadata found
            with __open__(csv_file,'r') as csv_stream:
                return self._deserialize_dataframe(csv_stream, None)

    def __deserialize_from_file(self, filename):
        """
        Reads the given file. The actual method depends on the file extension

        :param filename: name of the file
        :return: an arbitrary python object (DataFrame, file object or any other python type pickled out)
        """
        extension = os.path.splitext(filename)[1]
        if(extension=='.csv'):
            md_file = os.path.splitext(filename)[0] + ".pmd"
            return self.__deserialize_dataframe_from_file(filename, md_file)
        elif extension=='.bin':
            with open(filename, 'rb') as f:
                try:
                    return pickle.load(f)
                except Exception as exc:
                    raise GeneralException("Error while trying to load pickled object:" + str(exc))
        elif extension=='.fo':
            with open(filename, 'rb') as f:
                return io.BytesIO(f.read()) # reads the file to memory
        else:
            raise ValueError("Cannot handle files with '" + str(extension) + "' extension.")
