#
# This file is part of the RapidMiner Python package.
#
# Copyright (C) 2018-2024 RapidMiner GmbH
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
import getpass
from time import sleep
from .connector import Connector
from .connections import Connections
from .oauthenticator import OAuthenticator
from .utilities import ServerException
from .utilities import _is_docker_based_deployment
from .config import API_CONTEXT
from .resources import ProjectLocation
from .project import Project
from functools import partial
import warnings
import logging
import os
from pathlib import Path
import json

from .. import __version__


def get_server():
    if _is_docker_based_deployment():
        default_url = "http://rm-server-svc:8080"
        if "SERVER_BASE_URL" in os.environ:
            default_url = os.environ["SERVER_BASE_URL"]
        return Server(url=default_url)
    else:
        return Server()


class Server(Connector):
    """
    Class for using a local or remote RapidMiner Server instance directly. You can execute processes using the scalable Job Agent architecture.
    """
    __POLL_INTERVAL_SECONDS = 6

    def __init__(self, url=None, authentication_server=None, username=None, password=None, realm=None,
                 client_id=None, verifySSL=True, logger=None, loglevel=logging.INFO):
        """
        Initializes a new connector to a local or remote Rapidminer Server instance.

        Arguments:
        :param url: Server url path (hostname and port as well)
        :param authentication_server: Authentication Server url (together with the port).
        :param username: optional username for authentication.
        :param password: optional password for authentication.
        :param realm: defines the Realm in case of OAuth authentication.
        :param client_id: defines the client in the Realm.
        :param verifySSL: either a boolean, in which case it controls whether we verify the server's TLS certificate, or a string, in which case it must be a path to a CA bundle to use. Default value is True.
        :param logger: a Logger object to use. By default a very simple logger is used, with INFO level, logging to stdout.
        :param loglevel: the loglevel, as an int value. Common values are defined in the standard logging module. Only used, if logger is not defined.
        """
        super(Server, self).__init__(logger, loglevel)
        # URL of the Rapidminer Server
        if not url:
            if "PUBLIC_URL" in os.environ:
                url = os.environ["PUBLIC_URL"]
            else:
                raise ValueError("The url can not be empty!")
        if url.endswith("/"):
            url = url[:-1]
        self.server_url = url
        self.__verifySSL = verifySSL
        self.__user_agent = f"RapidMiner Python Package {str(__version__)}"
        if _is_docker_based_deployment():
            # If there are JUPYTERHUB infos use them, ["JUPYTERHUB_API_TOKEN", "JUPYTERHUB_API_URL", "JUPYTERHUB_USER"]
            self.oauthenticator = OAuthenticator(is_docker_based=True)
        else:
            # if there are no JUPYTERHUB infos ["JUPYTERHUB_API_TOKEN", "JUPYTERHUB_API_URL", "JUPYTERHUB_USER"], try to connect to Keycloak
            if authentication_server is None or realm is None or client_id is None:
                self.log(
                    "Incomplete authentication configuration, trying to fetch it from the server.")
                auth_info = self.__get_auth_info()
                if auth_info:
                    authentication_server = (
                        auth_info['authUrl'] if authentication_server is None else authentication_server)
                    realm = (auth_info['realm'] if realm is None else realm)
                    client_id = (auth_info['clientId'] if client_id is None else client_id)
            # RapidMiner Server Username
            if username is None:
                username = input('Username: ')
            self.username = username
            # RapidMiner Server Password
            if password is None:
                password = getpass.getpass(prompt='Password: ')
            if authentication_server is None:
                authentication_server = input('Authentication server: ')
            if realm is None:
                realm = input('Realm: ')
            if client_id is None:
                client_id = input('Client: ')
            self.oauthenticator = OAuthenticator(url=authentication_server, realm=realm, username=username,
                                                 password=password, client_id=client_id)

        self.__connect()

    ####################
    # Public functions #
    ####################

    def run_process(self, path, project=None, macros={}, queue="DEFAULT"):
        """
        Runs a RapidMiner process.

        Arguments:
        :param path: path to the RapidMiner process in the Project. It can be a string or a rapidminer.ProjectLocation object.
        :param project: optional project name. If the path parameter is a rapidminer.ProjectLocation, then it is not needed to be defined.
        :param macros: optional dict that sets the macros in the process context according to the key-value pairs, e.g. macros={"macro1": "value1", "macro2": "value2"}
        :param queue: the name of the queue to submit the process to. Default is DEFAULT.
        """
        this_project = project
        if isinstance(path, ProjectLocation):
            this_project = path.project
            path = path.path
        elif not isinstance(path, str):
            raise ServerException(
                "Process path should be 'str' or 'rapidminer.RepositoryLocation object, not '" + str(type(path)) + "'.")
        if this_project is None:
            raise ServerException(
                "Project should be defined if the path parameter is a rapidminer.ProjectLocation it can be None.")
        process_xml = self.__read_process_from_project(this_project, path)
        # location will not be submitted
        path = ProjectLocation(this_project, path).to_string()
        context = {}
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
        return None

    def get_queues(self):
        """
        Gets information of the available queues in the Server instance.

        :return: a JSON array of objects representing each queue with its properties
        """
        get_url = self.server_url + "/" + API_CONTEXT + "/queues"
        r = self.__send_request(partial(requests.get, get_url),
                                lambda s: "Failed to get queues, status: " + str(s))
        return r.json()

    def get_projects(self):
        """
        Gets information of the available projects in the AI Hub instance.

        :return: a JSON array of objects representing each repository with its properties
        """
        get_url = self.server_url + "/" + API_CONTEXT + "/repositories"
        r = self.__send_request(partial(requests.get, get_url),
                                lambda s: "Failed to get projects, status: " + str(s))
        return r.json()

    def get_connections(self, project):
        """
        Read the connections from the AI Hub repository.

        :return: Connections object listing connections from the AI Hub repository. Note that values of encrypted fields are not available (values will be None). Use AI Hub Vault to securely store and retrieve these values instead
        """
        return Connections(path=None, server=self, project_name=project)

    #####################
    # Private functions #
    #####################

    def _get_vault_info(self, location):
        """
        Load all server vault entries for a repository location.

        :param location: the location to read the vault information for. Note that there is a different syntax depending on the target repository type. For Projects, use git://reponame.git/Connections/My Connection.conninfo. For AI Hub repository, use /Connections/My Connection
        """
        if isinstance(location, ProjectLocation):
            location = location.to_string(with_prefix=True)
        elif not isinstance(location, str):
            raise ServerException(
                "Location must be a 'str' or 'rapidminer.ProjectLocation object, not '" + str(type(inp)) + "'.")
        get_url = self.server_url + "/" + API_CONTEXT + "/connections/vault?location=" + location
        r = self.__send_request(partial(requests.get, get_url),
                                lambda s: "Failed to get vault info, status: " + str(s))
        return r.json()

    def _get_project_info(self, project_name):
        """
        Read the information for a project from AI Hub.

        :param project_name: specifies the project
        :return: info in JSON format for the project
        """
        get_url = self.server_url + "/" + API_CONTEXT + "/repositories/" + project_name
        r = self.__send_request(partial(requests.get, get_url),
                                lambda s: "Failed to get project info"
                                          + (
                                              ": No project exists with the name '" + project_name + "', provide a valid project name"
                                              if s == 404 else ", status: " + str(s)))
        return r.json()

    def _get_connections_info(self, project_name):
        """
        Read the connections from the given AI Hub project.

        :return: connections in JSON format
        """
        # repositories/{{repositories_first_name}}/contents/{{repositories_first_ref}}?detailed=true&recursive=true&showHidden=true&retrieveFileAttributes=true&retrieveCommits=true
        get_url = self.server_url + "/" + API_CONTEXT + "/repositories/" + project_name + "/contents/master?detailed=true&recursive=true&showHidden=true&retrieveFileAttributes=true&retrieveCommits=true"
        r = self.__send_request(partial(requests.get, get_url),
                                lambda s: "Failed to get connections list, status: " + str(s))
        return r.json()

    def _read_connection_info(self, location):
        get_url = self.server_url + "/" + API_CONTEXT + "/connections/detail?location=" + location
        r = self.__send_request(partial(requests.get, get_url),
                                lambda s: "Failed to get connection details, status: " + str(s))
        return r.json()

    def __get_auth_info(self):
        get_url = get_url = self.server_url + "/" + API_CONTEXT + "/auth/info"
        r = self.__send_request(partial(requests.get, get_url),
                                error_fn=lambda s: "Failed to get auth information from the server: " + str(s),
                                headers_fn=lambda: None)
        response = r.json()
        self.log(
            f"The following authentication information was fetched from the Server:\n{json.dumps(response, indent=4)}")
        if 'jupyter' in response:
            response = response['jupyter']
            self.log("Using jupyter configuration.")
        else:
            response = None
        return response

    def __connect(self, force_renew=False):
        self.auth_header = self.__get_headers(force_renew)
        self.log("Successfully connected to the Server")

    def __submit_process_xml(self, queue, process, location, context):
        post_url = self.server_url + "/" + API_CONTEXT + "/jobs?"
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
            get_url = self.server_url + "/" + API_CONTEXT + "/jobs/" + jobid
            r = self.__send_request(partial(requests.get, get_url),
                                    lambda s: "Error during getting job status, job id: " + jobid + ", status: " + str(
                                        s))
            r = r.json()
            if r["state"] in self.__JOB_STATE_ERROR:
                raise ServerException(
                    "Job finished with error state: " + r["state"] + ", " + Server.__format_job_error(r))
            elif r["state"] in self.__JOB_STATE_SUCCESS:
                return

    def __format_job_error(response):
        # TODO: improve
        return "Unknown error" if "error" not in response else response["error"]["type"] + ": " + response["error"][
            "title"] + ": " + response["error"]["message"]

    def __get_headers(self, force_renew=False):
        head = {'Authorization': 'Bearer %s' % self.oauthenticator.get_token(force_renew)}
        head["User-Agent"] = self.__user_agent
        return head

    def __send_request(self, request, error_fn=None, accepted_status_codes=[200], reconnect=True, headers_fn=None):
        if headers_fn is None:
            headers_fn = self.__get_headers
        try:
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", "Unverified HTTPS request")
                response = request(headers=headers_fn(), verify=self.__verifySSL)
                if reconnect and response.status_code == 401:
                    # token may have expired, try to reconnect:
                    self.log("Session may have expired. Trying to reconnect to the server...")
                    self.__connect(force_renew=True)
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
            try:
                msg = f"{response.status_code}, response: {response.json()}"
            except Exception:
                msg = f"{response.status_code}"
            raise ServerException(error_fn(msg))
        return response

    def __read_process_from_project(self, project, path):
        get_url = self.server_url + "/" + API_CONTEXT + "/repositories/" + project + "/resources/master/" + path
        try:
            r = self.__send_request(partial(requests.get, get_url),
                                    lambda s: "Failed to find process at " + project + "/" + path + ", status: " + str(
                                        s))
        except ServerException as e:
            # re-try with rmp file extension if it has not been specified
            if str(e).endswith("404") and len(Path(path).suffix) == 0:
                r = self.__send_request(partial(requests.get, get_url + Project._RM_RMP_EXTENSION),
                                        lambda
                                            s: "Failed to find process at " + project + "/" + path + ", status: " + str(
                                            s))
            else:
                raise e
        return r.text
