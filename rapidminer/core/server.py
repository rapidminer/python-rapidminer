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
import requests
import base64
import tempfile
import xml.etree.ElementTree as et
import pandas as pd
import getpass
from time import sleep
from .connector import Connector
from .utilities import ServerException
from .utilities import extract_json
from .utilities import Version
from .utilities import VersionException
from .resources import RepositoryLocation
from .serdeutils import read_example_set, write_example_set
from functools import partial
import warnings
import io
import logging
import textwrap
import zeep

from .. import __version__

class Server(Connector):
    """
    Class for using a local or remote RapidMiner Server instance directly. You can read from and write to the Server repository and you can execute processes using the scalable Job Agent architecture.
    """
    __POLL_INTERVAL_SECONDS = 6
    __PROCESS_PATH_TRIES = 3
    __WEBSERVICE_PROCESS_XML = \
        """<?xml version="1.0" encoding="UTF-8"?><process version="9.3.000">
          <context>
            <input/>
            <output/>
            <macros/>
          </context>
          <operator activated="true" class="process" compatibility="9.3.000" expanded="true" name="Process">
            <process expanded="true">
              <operator activated="true" class="python_scripting:repository_service" compatibility="9.3.000" expanded="true" height="68" name="Repository Access" width="90" x="179" y="34"/>
              <connect from_port="input 1" to_op="Repository Access" to_port="file"/>
              <connect from_op="Repository Access" from_port="output" to_port="result 1"/>
              <portSpacing port="source_input 1" spacing="0"/>
              <portSpacing port="source_input 2" spacing="0"/>
              <portSpacing port="sink_result 1" spacing="0"/>
              <portSpacing port="sink_result 2" spacing="0"/>
            </process>
          </operator>
        </process>
        """
    __WEBSERVICE_DESCRIPTOR_XML = \
        """<?xml version="1.0" encoding="UTF-8"?>
        <exported-process>
            <mime-type>application/json</mime-type>
            <output-format>JSON</output-format>
            <process-entry>PROCESS_ENTRY_PATH</process-entry>
            <xslt-entry/>
            <parameter-mappings/>
            <properties>
                <name>service:Repository Service</name>
            </properties>
            <data-source-input>
                <name>service:Repository Service</name>
            </data-source-input>
        </exported-process>
        """
    __WELCOME_INFO = \
"""Web service backend for the Server Python API on this Server is not installed, this
is probably because you are using this API for the first time. This
backend will be installed once and can be used forever afterwards.
Please use either RapidMiner Studio or the RapidMiner Server web interface
to create a dedicated folder for this API backend process that is shared 
among all the users.
Please read the documentation (README) on how to create this folder. If
you are the sole user of this Server, you may skip the creation of this
folder and simply use your home folder. In that case note that if you
want to allow other users later to use the API, you will need to give
them access to the process created by this operation."""
    __WELCOME_LINE_LENGTH = 70
    __TAB = "    "

    def __init__(self, url='http://localhost:8080', username=None, password=None, row_limit=50000, attribute_limit=500,
                 webservice="Repository Service", processpath=None, tempfolder=None, install=True, verifySSL=True,
                 logger=None, loglevel=logging.INFO):
        """
        Initializes a new connector to a local or remote Rapidminer Server instance. It also installs the auxiliary webservice required by this library to be able to interact with the Server repository directly.

        Arguments:
        :param url: Server url path (hostname and port as well)
        :param username: user to use Server with
        :param password: password for the username. If not provided, you will need to enter it.
        :param row_limit: maximum number of rows that are allowed to be read from Server. Reading or writing large objects may degrade Server's performance or lead to out of memory errors. Default value is 50000.
        :param attribute_limit: maximum number of attributes that are allowed to be read from Server. Reading or writing large objects may degrade Server's performance or lead to out of memory errors. Default value is 500.
        :param webservice: this API requires an auxiliary process installed as a webservice on the Server instance. This parameter specifies the name for this webservice. The webservice is automatically installed if it has not been.
        :param processpath: path in the repository where the process behind the webservice will be saved. If not specified, a user prompt asks for the path, but proposes a default value. Note that you may want to make this process executable for all users.
        :param tempfolder: repository folder on Server that can be used for storing temporary objects by run_process method. Default value is "tmp" inside the user home folder. Note that in case of certain failures, you may need to delete remaining temporary objects from this folder manually.
        :param install: boolean. If set to false, webservice installation step is completely skipped. Default value is True.
        :param verifySSL: either a boolean, in which case it controls whether we verify the server's TLS certificate, or a string, in which case it must be a path to a CA bundle to use. Default value is True.
        :param logger: a Logger object to use. By default a very simple logger is used, with INFO level, logging to stdout.
        :param loglevel: the loglevel, as an int value. Common values are defined in the standard logging module. Only used, if logger is not defined.
        """
        super(Server, self).__init__(logger, loglevel)
        # URL of the Rapidminer Server
        self.server_url = url
        # RapidMiner Server Username
        if username is None:
            username = input('Username: ')
        self.username = username
        # RapidMiner Server Password
        if password is None:
            password = getpass.getpass(prompt='Password: ')
        self.__password = password
        self.row_limit = row_limit
        self.attribute_limit = attribute_limit
        self.webservice = webservice
        self.__processpath = processpath
        if tempfolder is None:
            self.__tempfolder = "/home/" + self.username + "/tmp/"
        else:
            self.__tempfolder = tempfolder
            self.__tempfolder += "/" if not self.__tempfolder.endswith("/") else ""
        self.__install = install
        self.__verifySSL = verifySSL

        # Connect to the RM Server
        self.__connect()

        # Test and install required web service if it does not exist
        if self.__install:
            self.__test_and_install()

####################
# Public functions #
####################

    def read_resource(self, path):
        """
        Reads one or more resources from the specified Server repository locations. Only supports reading data sets currently. Does not allow the retrieval of data sets larger that the limit settings allow (row_limit, attribute_limit).

        Arguments:
        :param path: the path(s) to the resource(s) inside Server repository. Multiple paths can be specified as list or tuple. A path can be a string or a rapidminer.RepositoryLocation object.
        :return: the resource(s) as a pandas DataFrame(s). If multiple inputs are specified, the same number of inputs will be returned, as tuple of DataFrame objects. Otherwise, the return value is a single DataFrame.
         """
        if not ((isinstance(path, tuple) or isinstance(path, list))):
            path = [path]
            single_input = True
        else:
            if len(path) == 0:
                return None
            single_input = False
        resources = []
        for inp in path:
            if isinstance(inp, RepositoryLocation):
                inp = inp.to_string(with_prefix=False)
            elif not isinstance(inp, str):
                raise ServerException("Input path should be 'str' or 'rapidminer.RepositoryLocation object, not '" + str(type(inp)) + "'.")
            post_url = self.server_url + "/api/rest/process/" + self.webservice + "?"
            r = self.__send_request(partial(requests.post, post_url, json={"command": "read_resource", "library_version": __version__, "path": inp, "row_limit": self.row_limit, "attribute_limit": self.attribute_limit}),
                                    lambda s: "Failed to read input \"" + inp + "\", status: " + str(s) 
                                    + (". The web service backend may have been deleted, please try to use a new Server class." if s == 404 else ""))
            response = extract_json(r)
            self.__check_extension_version(response, typeColumn="extension", valueColumn="content")
            # in the 9.3.0 version, we expect a list with 2 elements; from 9.3.1 we expect 3 elements
            if not isinstance(response, list) or len(response) not in [2,3]:
                raise ServerException("Invalid response from server. The entry may not be a data set.")
            csv_data = None
            metadata = None
            for row in response:
                try:
                    if row["extension"] == "csv-encoded":
                        csv_data = io.StringIO(row["content"])
                    elif row["extension"] == "pmd-encoded":
                        metadata = io.StringIO(row["content"])
                except KeyError as e:
                    raise ServerException("The response from the server differs from the expected.") from e
            if csv_data is None:
                raise ServerException("No data found.")
            if metadata is None:
                raise ServerException("No metadata found.")
            dataframe = read_example_set(csv_data, metadata)
            resources.append(dataframe)
        if single_input:
            return resources[0]
        else:
            return tuple(resources)

    def write_resource(self, resource, path):
        """
        Writes one or more resources to the Server repository. Only supports writing data sets (pandas DataFrames) currently.

        Arguments:
        :param resource: the pandas DataFrame(s). Multiple DataFrames can be specified as list or tuple. A path can be a string or a rapidminer.RepositoryLocation object.
        :param path: the target path(s) to the resource(s) inside Server repository. The same number of path values are required as the number of resources.
        """
        if not ((isinstance(resource, tuple) or isinstance(resource, list))):
            resource = [resource]
        if not ((isinstance(path, tuple) or isinstance(path, list))):
            path = [path]
        if len(resource) != len(path):
            raise ValueError("resource and path must contain the same number of values")
        for df, out, idx in zip(resource, path, range(len(resource))):
            if isinstance(out, RepositoryLocation):
                out = out.to_string(with_prefix=False)
            elif not isinstance(out, str):
                raise ServerException("Output path should be 'str' or 'rapidminer.RepositoryLocation object, not '" + str(type(out)) + "'.")
            post_url = self.server_url + "/api/rest/process/" + self.webservice + "?"
            if type(df) == pd.DataFrame:
                csv_stream = io.StringIO()
                md_stream = io.StringIO()
                write_example_set(self._copy_dataframe(df), csv_stream, md_stream)
                data = [{"extension": "csv-encoded", "content": csv_stream.getvalue()},
                        {"extension": "pmd-encoded", "content": md_stream.getvalue()}]
            else:
                raise ValueError("resource parameter must be one or more Pandas DataFrames")
            r = self.__send_request(partial(requests.post, post_url, json={"command": "write_resource", "library_version": __version__, "path": out, "data": data}),
                                    lambda s: "Failed to save input no. " + str(idx+1) + ", status: " + str(s)
                                    + (". The web service backend may have been deleted, please try to use a new Server class." if s == 404 else ""))
            response = extract_json(r)
            self.__check_extension_version(response)

    def run_process(self, path, inputs=[], macros={}, queue="DEFAULT", ignore_cleanup_errors=True):
        """
        Runs a RapidMiner process and returns the result(s).

        Arguments:
        :param path: path to the RapidMiner process in the Server repository. It can be a string or a rapidminer.RepositoryLocation object.
        :param inputs: inputs used by the RapidMiner process, as a list of pandas DataFrame objects or a single pandas DataFrame.
        :param macros: optional dict that sets the macros in the process context according to the key-value pairs, e.g. macros={"macro1": "value1", "macro2": "value2"}
        :param queue: the name of the queue to submit the process to. Default is DEFAULT.
        :param ignore_cleanup_errors: boolean. Determines if any error during temporary data cleanup should be ignored or not. Default value is True.
        :return: the results of the RapidMiner process. It can be None, or a single pandas DataFrame object, or a tuple of DataFrames.
        """
        if isinstance(path, RepositoryLocation):
            path = path.to_string(with_prefix=False)
        elif not isinstance(path, str):
            raise ServerException("Process path should be 'str' or 'rapidminer.RepositoryLocation object, not '" + str(type(path)) + "'.")
        if inputs is not None and not ((isinstance(inputs, tuple) or isinstance(inputs, list))):
            inputs = [inputs]
        process_xml = self.__read_process_xml(path)
        root = et.fromstring(process_xml)
        temp_resources = []
        context = {}
        try:
            if inputs:
                input_resources = [self.__tempfolder + next(tempfile._get_candidate_names()) for _ in inputs]
                temp_resources += input_resources
                self.write_resource(inputs, input_resources)
                # add input locations in process xml
                context["inputLocations"] = input_resources
            # find connected output ports, add locations to process xml
            output_resources = []
            for wire in root.find('operator').find('process').findall('connect'):
                if wire.attrib['to_port'].startswith('result '):
                    output_resources.append(self.__tempfolder + next(tempfile._get_candidate_names()))
            if output_resources:
                context["outputLocations"] = output_resources
            temp_resources += output_resources
            # set macros in process xml
            if macros:
                macros_dict = {}
                for key, value in macros.items():
                    macros_dict[key] = value
                context["macros"] = macros_dict
            r = self.__submit_process_xml(queue, process_xml, path, context)
            jobid = r.json()["id"]
            self.log("Submitted process with job id: " + str(jobid))
            self.__wait_for_job(jobid)
            if len(output_resources) == 1:
                output_resources = output_resources[0]
            return self.read_resource(output_resources)
        finally:
            if ignore_cleanup_errors:
                try:
                    self.__delete_resource(temp_resources)
                except Exception as e:
                    strfile = "entry" if len(temp_resources) == 1 else "entries"
                    message = e.message if hasattr(e, 'message') else str(e)
                    self.log("Could not delete the following temporary " + strfile + ", error: " + message, level=logging.WARNING)
                    self.log("\n".join(t for t in temp_resources), level=logging.WARNING)
            else:
                self.__delete_resource(temp_resources)

    def get_queues(self):
        """
        Gets information of the available queues in the Server instance.

        :return: a JSON array of objects representing each queue with its properties
        """
        get_url = self.server_url + "/executions/queues?"
        r = self.__send_request(partial(requests.get, get_url),
                                lambda s: "Failed to get queues, status: " + str(s))
        return r.json()

#####################
# Private functions #
#####################

    def __connect(self):
        # Encode the basic Authorization header
        userAndPass = base64.b64encode(bytes(self.username + ":" + self.__password, "utf-8")).decode("ascii")
        headers = { 'Authorization' : 'Basic %s' %  userAndPass }

        r = self.__send_request(partial(requests.get, url=self.server_url + '/api/rest/tokenservice'),
                                error_fn=lambda s:
                                    "Connection error, status: " + str(s) + "."
                                    + (" Make sure that you entered a valid username and password." if s == 401 else ""),
                                reconnect=False, headers_fn=lambda: headers)
        if "Access denied" in r.text:
            raise ServerException("Connection error: Access denied")

        # JWT idToken for the RM Server
        self.idToken = r.json()['idToken']

        # Bearer Authorization header
        self.auth_header = { 'Authorization' : 'Bearer %s' %  self.idToken }
        self.log("Successfully connected to the Server")

    def __test_and_install(self):
        # test if web service exists
        post_url = self.server_url + "/api/rest/process/" + self.webservice + "?"
        r = self.__send_request(partial(requests.post, post_url, json={"command": "test", "library_version": __version__}))
        if r.status_code == 404:
            print(self.__TAB + ("*" * self.__WELCOME_LINE_LENGTH))
            print(self.__TAB + ("\n" + self.__TAB).join(textwrap.wrap(self.__WELCOME_INFO, self.__WELCOME_LINE_LENGTH)))
            print(self.__TAB + ("*" * self.__WELCOME_LINE_LENGTH))
            self.log("Web service is not installed, installing it with the name '" + self.webservice + "'...")
            default_webservice_path = "/repository_api/" + self.webservice
            # if there is no process path specified, try to get it from user input a couple of times
            tries = self.__PROCESS_PATH_TRIES if self.__processpath is None else 1
            for _ in range(tries):
                processpath_to_test = input("Please enter full repository path for installing the process - it will be accessible by all users"
                                        + " [" + default_webservice_path + "]: ") if self.__processpath is None else self.__processpath
                if processpath_to_test.strip() == "":
                    processpath_to_test = default_webservice_path
                if self.__is_folder(processpath_to_test):
                    processpath_to_test += ("" if processpath_to_test.endswith("/") else "/") + self.webservice
                    self.log("You entered a folder name. Trying to save the process in that folder: " + processpath_to_test, logging.WARNING)
                unauthorized_to_save_msg = "Unauthorized to save. "
                try:
                    self.__install_webservice(processpath_to_test, unauthorized_to_save_msg,
                                              "Your user could not create the web service backend. Please ask an administrator to"
                                              + " create a web service from the following process: " + processpath_to_test + ". ")
                    break
                except ServerException as e:
                    if str(e).startswith(unauthorized_to_save_msg):
                        self.log("Could not save process to location: " + processpath_to_test + ". Please use a path where your user can write to.", logging.ERROR)
                        self.log("Error: " + str(e)[len(unauthorized_to_save_msg):], logging.ERROR)
                    else:
                        raise e
            self.__processpath = processpath_to_test
            # Re-test installed service
            r = self.__send_request(partial(requests.post, post_url, json={"command": "test", "library_version": __version__}),
                                    lambda s: "Test of installed web service failed, status: " + str(s))
            response = extract_json(r)
            self.__check_extension_version(response)
            self.log("Web service backend installed successfully")
        elif r.status_code == 200:
            response = extract_json(r)
            self.__check_extension_version(response)
            self.log("Web service backend exists")
        else:
            raise ServerException("Web service test failed with unexpected error, status: " + r.status_code \
                                  + ". Make sure that the web service with the name '" + self.webservice + ' is installed.')

    def __read_process_xml(self, path):
        get_url = self.server_url + "/api/rest/resources" + path
        r = self.__send_request(partial(requests.get, get_url),
                                lambda s: "Failed to get process \"" + path + "\", status: " + str(s))
        return r.text

    def __submit_process_xml(self, queue, process, location, context):
        post_url = self.server_url + "/executions/jobs?"
        body = {
            "queueName": queue,
            "process": base64.b64encode(bytes(process, "utf-8")).decode("ascii"),
            "location": location,
            "context": context
        }
        return self.__send_request(partial(requests.post, url=post_url, json=body),
                                   lambda s: "Failed to submit process, status: " + str(s))

    __JOB_STATE_ERROR = ("TIMED_OUT", "STOPPED", "ERROR")
    __JOB_STATE_SUCCESS = ("FINISHED")

    def __wait_for_job(self, jobid):
        while True:
            sleep(self.__POLL_INTERVAL_SECONDS)
            get_url = self.server_url + "/executions/jobs/" + jobid
            r = self.__send_request(partial(requests.get, get_url),
                                    lambda s: "Error during getting job status, job id: " + jobid + ", status: " + str(s))
            r = r.json()
            if r["state"] in self.__JOB_STATE_ERROR:
                raise ServerException("Job finished with error state: " + r["state"] + ", " + Server.__format_job_error(r))
            elif r["state"] in self.__JOB_STATE_SUCCESS:
                return

    def __format_job_error(response):
        # TODO: improve
        return "Unknown error" if "error" not in response else response["error"]["type"] + ": " + response["error"]["title"] + ": " + response["error"]["message"]

    def __delete_resource(self, resource_paths):
        post_url = self.server_url + "/api/rest/process/" + self.webservice + "?"
        for path in resource_paths:
            self.__send_request(partial(requests.post, post_url, json={"command": "delete_resource", "library_version": __version__, "path": path}),
                                lambda s: "Failed to delete path \"" + path + "\", status: " + str(s))

    def __install_webservice(self, path, unauthorized_to_save_msg, unauthorized_to_configure_msg):
        self.__post_process(path, self.__WEBSERVICE_PROCESS_XML, unauthorized_to_save_msg)
        self.__make_public(path)
        self.__post_service(self.webservice, self.__WEBSERVICE_DESCRIPTOR_XML.replace("PROCESS_ENTRY_PATH", path), unauthorized_to_configure_msg)

    def __post_process(self, path, process, unauthorized_error_msg):
        post_url = self.server_url + "/api/rest/resources" + path
        return self.__send_request(partial(requests.post, post_url, data=process),
                                   error_fn=lambda s:
                                       (unauthorized_error_msg if s == 403 else "")
                                       + "Failed to save process to repository path '" + path + "', status: " + str(s),
                                   accepted_status_codes=[201], headers_fn=self.__get_headers_with_content_type)

    def __make_public(self, path):
        client = self.__get_soap_client()
        try:
            res = client.service.setAccessRights(path, {
                'execute': 'GRANT',
                'group': 'users',
                'read': 'GRANT',
                'write': 'IGNORE'
            })
        finally:
            self.__destroy_soap_client(client)
        if hasattr(res, "status") and res["status"] != 0:
            self.log("Could not give permission on the backend process to 'users' group, status : " + str(res["status"])
                + ((", error message: " + res["errorMessage"]) if hasattr(res, "errorMessage") else "")
                + ". Please set it manually, or ask an administrator to do it.", logging.WARNING)

    def __post_service(self, service_name, descriptor, unauthorized_error_msg):
        post_url = self.server_url + "/api/rest/service/" + service_name
        return self.__send_request(partial(requests.post, post_url, data=descriptor),
                                   error_fn=lambda s:
                                       (unauthorized_error_msg if s == 403 else "")
                                       + "Failed to install webservice with the name '" + service_name + "', status: " + str(s))

    def __is_folder(self, path):
        client = self.__get_soap_client()
        try:
            res = client.service.getFolderContents(path)
            if hasattr(res, "status") and res["status"] == 0:
                return True
            else:
                return False
        finally:
            self.__destroy_soap_client(client)

    def __get_soap_client(self):
        session = requests.Session()
        session.auth = requests.auth.HTTPBasicAuth(self.username, self.__password)
        client = zeep.Client(self.server_url + "/api/soap/RepositoryService?wsdl", transport=zeep.transports.Transport(session=session))
        return client

    def __destroy_soap_client(self, client):
        client.transport.session.close()

    def __get_headers(self):
        return self.auth_header

    def __get_headers_with_content_type(self):
        head = self.auth_header.copy()
        head['Content-Type'] = 'application/vnd.rapidminer.rmp+xml'
        return head

    def __send_request(self, request, error_fn=None, accepted_status_codes=[200], reconnect=True, headers_fn=None):
        if headers_fn is None:
            headers_fn = self.__get_headers
        try:
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", "Unverified HTTPS request")
                response = request(headers=headers_fn(), verify=self.__verifySSL)
                if reconnect and response.status_code == 401:
                    # token may expired, try to reconnect:
                    self.log("Session expired. Trying to reconnect to the server...")
                    self.__connect()
                    response = request(headers=headers_fn(), verify=self.__verifySSL)
        except requests.exceptions.SSLError as e:
            if "SSL: CERTIFICATE_VERIFY_FAILED" in str(e):
                raise ServerException("SSL verification error while connecting to the server." +
                                      " Probably you did not configured properly the certificate of your RapidMiner Server." +
                                      " By specifying the 'verifySSL=False' or 'verifySSL=/path/to/your/certificate' parameter for the rapidminer.Server object," +
                                      " you can dismiss this error, though this is not recommended." +
                                      " For more details consult the documentation.") from e
            else:
                raise e
        if response.status_code not in accepted_status_codes and error_fn is not None:
            raise ServerException(error_fn(response.status_code))
        return response

    def __check_extension_version(self, response, typeColumn="type", valueColumn="value"):
        extensionVersion = None
        try:
            if isinstance(response, dict):
                if response[typeColumn] == "version_info":
                    extensionVersion = response[valueColumn]
            elif isinstance(response, list):
                for row in response:
                    if row[typeColumn] == "version_info":
                        extensionVersion = row[valueColumn]
                        break
        except (TypeError, KeyError):
            # the response is in the wrong (legacy) format
            pass
        if extensionVersion is None or not Version(extensionVersion).is_at_least(Version("9.5.0")):
            raise VersionException("RapidMiner Server", "to 9.5.0 or newer")


