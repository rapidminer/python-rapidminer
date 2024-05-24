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

import os
import glob
import json
import zipfile
from collections import OrderedDict
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from .utilities import ProjectException, ServerException, _is_docker_based_deployment
from .resources import ProjectLocation


class Connections:
    """
    Class for using connections from a Project or Repository.
    """
    
    _CONNECTIONS_SUBDIR = "Connections"
    _CONNECTIONS_EXTENSION = ".conninfo"
    
    def __init__(self, path=".", server=None, project_name=None, show_parameter_groups=False, macros=None):
        """
        Initializes a reference to a locally cloned project or to an AI Hub repository.
        
        :param path: Path to the local project repository root folder.
        :param server: Server object; required for encrypted values or AI Hub Vault values.
        :param project_name: Name of the project to which these connections belong.
        :param show_parameter_groups: Include the group in parameter keys if set to True.
        :param macros: Dictionary or method defining the values for macro injected parameters.
        """
        if path:
            self._initialize_from_local_path(path, project_name)
        else:
            self._initialize_from_server(server, project_name)

        self.server = server
        self._show_parameter_groups = show_parameter_groups
        self.macros = macros
        self.__cached_project_primitive = None
        self.__list = []

        self._load_connections()
        
    def _initialize_from_local_path(self, path, project_name):
        if not os.path.exists(path):
            raise ProjectException(f"Specified path does not exist: '{path}'. Please ensure you have a local copy of the project at the specified path.")
        path = os.path.abspath(path)
        if not project_name:
            project_name = os.path.basename(path)
        path = os.path.join(path, Connections._CONNECTIONS_SUBDIR)
        if not os.path.exists(path):
            raise ProjectException(f"Connections directory does not exist at the specified path '{os.path.dirname(path)}'. Please ensure you have a local copy of the project.")
        self.path = path
        self.project_name = project_name

    def _initialize_from_server(self, server, project_name):
        self._check_server("You must either provide a project path ('path' parameter) or a Server object ('server' parameter).")
        self.path = None
        self.project_name = project_name

    def _load_connections(self):
        if self.path is None:
            conn_json = self._get_connections_from_project()
            for c in conn_json:
                project_location = ProjectLocation(project=self.project_name, path=c['location'])
                self.__list.append(Connection(c["location"], OrderedDict(self.server._read_connection_info(project_location.to_string())), self))
        else:
            conn_files = glob.glob(os.path.join(self.path, "*" + Connections._CONNECTIONS_EXTENSION))
            for z in conn_files:
                with zipfile.ZipFile(z) as zf:
                    with zf.open("Config") as f:
                        self.__list.append(Connection(os.path.join(Connections._CONNECTIONS_SUBDIR, os.path.basename(z)), json.loads(f.read(), object_pairs_hook=OrderedDict), self))
        self.__list.sort(key=lambda c: c.name)

    def _get_connections_from_project(self):
        files_in_project = self.server._get_connections_info(self.project_name)
        return [{'location': f['path'][len(self.project_name) + 1:]} for f in files_in_project if Connections._CONNECTIONS_EXTENSION in f['name']]

    def _get_project_primitive(self):
        if self.__cached_project_primitive is None:
            response = self.server._get_project_info(self.project_name)
            key_first = next(filter(lambda k: k["status"] == "ENABLED", response["secret"]["key"]))
            key_data = key_first["keyData"]
            if key_data["typeUrl"] != "type.googleapis.com/google.crypto.tink.AesGcmKey":
                raise ServerException(f"Unknown key type is used for encryption: '{key_data["typeUrl"]}'")
            key_str = key_data["value"]
            key = base64.b64decode(key_str)[2:]
            self.__cached_project_primitive = (AESGCM(key), key_first["outputPrefixType"])
        return self.__cached_project_primitive

    def _check_server(self, error_message):
        if not self.server:
            if _is_docker_based_deployment():
                self.server = get_server()
            else:
                raise ServerException(error_message)

    def __iter__(self):
        return iter(self.__list)

    def __getitem__(self, item):
        if isinstance(item, int):
            return self.__list[item]
        return next(x for x in self.__list if x.name == item)

    def __str__(self):
        return f"Connections({[x.name for x in self.__list]})"

    def __repr__(self):
        return repr(f"Connections({[x.name for x in self.__list]})")


class Connection:
    """
    Class that represents a single connection.
    """

    def __init__(self, location, config, connections):
        """
        Initializes a connection instance based on a location and a config dictionary.

        :param location: Path to the connection file in the project or in the AI Hub repository.
        :param config: Dictionary containing all the connection details.
        :param connections: Reference to the parent Connections object.
        """
        self.__location = location
        self.__config = config
        self.__connections = connections
        self.__name = config["name"]
        self.__type = config["type"]
        self.__values = OrderedDict()
        self.__lazy_loaded_params = []
        self.__init_constant_values()

    @property
    def config(self):
        """The raw internal JSON configuration of the connection."""
        return self.__config

    @property
    def name(self):
        """The name of the connection."""
        return self.__name

    @property
    def type(self):
        """Type of the connection."""
        return self.__type

    @property
    def values(self):
        """Dictionary with all the connection fields."""
        self.__refresh_dynamic_values()
        return self.__values

    @property
    def user(self):
        """Quick access to the first field that likely contains a user name."""
        return self.find_first("username", "user")

    @property
    def password(self):
        """Quick access to the first field that likely contains a password."""
        return self.find_first("password")

    def find_first(self, *words):
        """
        Returns the value of the first connection parameter that has one of the specified arguments in its key.
        
        :param words: Words to look for in the parameter keys.
        """
        values_cache = self.values
        for w in words:
            for key in values_cache:
                if w.lower() in key.split(".")[-1].lower():
                    return values_cache[key]
        raise KeyError(f"Could not find any parameters having the words {words} in their key.")

    def __init_constant_values(self):
        param_keys = set()
        for k in self.__config["keys"]:
            self.__init_constant_values_in_group(k, param_keys)

    def __init_constant_values_in_group(self, group_config, param_keys):
        group = group_config["group"]
        for p in group_config["parameters"]:
            if self.__connections._show_parameter_groups or p["name"] in param_keys:
                p["name"] = f"{group}.{p['name']}"
            p["group"] = group
            param_keys.add(p["name"])
            if p["enabled"]:
                if ("injectorName" in p and p["injectorName"]) or p["encrypted"]:
                    self.__values[p["name"]] = None
                    self.__lazy_loaded_params.append(p)
                else:
                    self.__values[p["
