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

import os
import glob
import json
import zipfile
from collections import OrderedDict
from tink import aead
from tink import cleartext_keyset_handle
from tink import JsonKeysetReader
import base64
from .utilities import ProjectException
from .utilities import ServerException
from .resources import ProjectLocation
#from .server import get_server, _is_docker_based_deployment


class Connections():
    """
    Class for using connections from a Project or Repository.
    """
    
    CONNECTIONS_SUBDIR = "Connections"
    CONNECTIONS_EXTENSION = ".conninfo"
    
    def __init__(self, path=".", server=None, project_name=None, show_parameter_groups=False, macros=None):
        """
        Initializes a reference to a locally cloned project. You need to clone a project from RapidMiner Server first (e.g. via git commands) to be able to use the methods of this instance.
        
        :param path: path to the local project repository root folder. It can be a relative path from the current working directory or an absolute path, . The default value points to the working directory.
        :param server: Server object; required when values are encrypted or when values are injected from the Server Vault
        :param project_name: name of the project to which these connections belong; if not specified, it is set to the parent directory name of the specified path parameter
        :param show_parameter_groups: when set to True (default if False), parameter keys include the group as well in <group>.<key> format; otherwise, group is only added if there is a name collision
        :param macros: a dictionary or method, defining the values for the macro injected parameters. If a connection has a <prefix> defined for macro keys, the prefix is used before the key in <prefi><original key> format. If a method is used here, it should accept the connection_name and macro_name parameters, and should return the macro value for those.
        """
        if not os.path.exists(path):
            raise ProjectException("Specified path does not exist: '%s'. Please make sure you have a local copy of the project at the specified path." % path)
        path = os.path.abspath(path)
        # if not specified, derive project name from the directory name
        if not project_name:
            project_name = os.path.basename(path)
        path = os.path.join(path, Connections.CONNECTIONS_SUBDIR)
        if not os.path.exists(path):
            raise ProjectException("Connections directory does not exist at the specified path '%s'. Please make sure you have a local copy of the project." % (os.path.dirname(path)))
        self.path = path
        aead.register()
        conn_files = glob.glob(os.path.join(self.path, "*" + Connections.CONNECTIONS_EXTENSION))

        self.server = server
        self.project_name = project_name
        self._show_parameter_groups = show_parameter_groups
        self.macros = macros
        self.__cached_project_primitive = None
        self.__list = []
        for z in conn_files:
            with zipfile.ZipFile(z) as zf:
                with zf.open("Config") as f:
                    self.__list.append(Connection(os.path.join(Connections.CONNECTIONS_SUBDIR, os.path.basename(z)),
                                                  json.loads(f.read(), object_pairs_hook=OrderedDict), self))
        self.__list.sort(key=lambda c: c.name)

    def _get_project_primitive(self):
        # project primitive is not expected to change - initialized once, when first needed
        if self.__cached_project_primitive == None:
            response = self.server.get_project_info(self.project_name)
            content = json.dumps(response["secret"])
            reader = JsonKeysetReader(content)
            keyset_handle = cleartext_keyset_handle.read(reader)
            self.__cached_project_primitive = keyset_handle.primitive(aead.Aead)
        return self.__cached_project_primitive

    def _check_server(self, error_message):
        if not self.server:
            if _is_docker_based_deployment():
                self.server = get_server()
            #else:
            #    raise ServerException(error_message)
    
    def __iter__(self):
        return iter(self.__list)

    def __getitem__(self, item):
        try:
            return self.__list[int(item)]
        except ValueError:
            return next(x for x in self.__list if x.name == item)
        
    def __str__(self):
        return "Connections(%s)" % [x.name for x in self.__list]

    def __repr__(self):
        return repr("Connections(%s)" % [x.name for x in self.__list])


class Connection():
    """
    Class that represents a single connection.
    """

    def __init__(self, filepath, config, connections):
        """
        Initializes a connection instance based on a path and a config dictionary.

        :param filepath: path to the connection file
        :param config: dictionary containing all the connection details; can be directly created from the JSON content of the connection
        :param connecionts: reference to the parent Connections object
        """
        self.__filepath = filepath
        self.__config = config
        self.__connections = connections
        self.__name = config["name"]
        self.__type = config["type"]
        self.__init_constant_values()

    @property
    def config(self):
        return self.__config

    @property
    def name(self):
        return self.__name

    @property
    def type(self):
        return self.__type

    @property
    def values(self):
        self.__refresh_dynamic_values()
        return self.__values

    # Accessing some of the typical fields easily
    @property
    def user(self):
        return self.find_first("username", "user")

    @property
    def password(self):
        return self.find_first("password")

    def find_first(self, *words):
        """
        Returns the value of the first connection parameter that has one of the specified arguments in its key as a substring. Useful for looking up parameters if the key is not known accurately.
        
        :param words: arbitrary number of words to look for - the functions stops at the very first word for which it successfully finds a parameter that has the word in its key
        """
        values_cache = self.values
        for w in words:
            for key in values_cache:
                # don't search in groups
                if w.lower() in key.split(".")[-1].lower():
                    return values_cache[key]
        raise KeyError("Could not find any parameters having the words %s in their key." % str(words))

    def __init_constant_values(self):
        self.__values = OrderedDict()
        self.__lazy_loaded_params = []
        param_keys = set()
        for k in self.__config["keys"]:
            self.__init_constant_values_in_group(k,param_keys)

    def __init_constant_values_in_group(self, group_config, param_keys):
        group = group_config["group"]
        for p in group_config["parameters"]:
            # only add group if there would be a conflict in keys otherwise, or if flag variable is set to True
            if self.__connections._show_parameter_groups or p["name"] in param_keys:
                p["name"] = group + "." + p["name"]
            p["group"] = group
            param_keys.add(p["name"])
            if p["enabled"]:
                if p["injectorName"] or p["encrypted"]:
                    self.__values[p["name"]] = None
                    self.__lazy_loaded_params.append(p)
                else:
                    self.__values[p["name"]] = p["value"]
    
    def __refresh_dynamic_values(self):
        if len(self.__lazy_loaded_params) < 1:
            # nothing to refresh
            return
        for n in self.__lazy_loaded_params:
            self.__refresh_dynamic_value(n)

    def __refresh_dynamic_value(self, parameter):
        self.__refresh_vault_cache()
        name = parameter["name"]
        value = parameter["value"]
        if parameter["injectorName"]:
            value = self.__injected_value(parameter)
            # when injected, there is no encryption
        elif parameter["encrypted"]:
            value = self.__decrypt(value)
        self.__values[name] = value

    def __refresh_vault_cache(self):
        self.__connections._check_server("For accessing a value from the AI Hub Vault, you must provide a Server object.")
        project_loc = ProjectLocation(self.__connections.project_name, self.__filepath)
        self.__cached_vault_info = self.__connections.server.get_vault_info(project_loc)
    
    def __decrypt(self, value):
        if not value:
            return None
        self.__connections._check_server("This connection has encrypted values. Decrypting them is only supported in case of AI Hub (Server) projects/repositories. For decrypting encrypted values, you must provide a Server object.")
        # Use key from Server
        res = self.__connections._get_project_primitive().decrypt(base64.b64decode(value), b'')
        return res.decode("utf-8")

    def __injected_value(self, parameter):
        injector = self.__injector(parameter["injectorName"])
        if injector:
            if injector["type"] == "remote_repository:rapidminer_vault":
                return self.__injected_vault_value(parameter)
            elif injector["type"] == "macro_value_provider":
                return self.__injected_macro_value(parameter, injector)
            else:
                raise ValueError("Unknown injector type %s" % injector["type"])
        return None

    def __injected_vault_value(self, parameter):
        # cut the group if <group>.<key> format is used
        name = parameter["name"].split(".")[-1]
        for v in self.__cached_vault_info:
            if v["parameter"]["name"] == name and v["parameter"]["key"]["group"] == parameter["group"]:
                return v["value"]
        raise ValueError("Parameter with key %s not found in Server Vault" % parameter["name"])

    def __injected_macro_value(self, parameter, injector):
        # cut the group if <group>.<key> format is used
        name = parameter["name"].split(".")[-1]
        if injector["parameters"][0]["value"]:
            # macro prefix is used
            name = str(injector["parameters"][0]["value"]) + "_" + str(name)
        macros = self.__connections.macros
        if macros:
            return self.__get_macro(macros, name)
        raise ValueError("Connection %s uses macros, but macros parameter is set to None." % self.__name)

    def __get_macro(self, macros, key):
        if callable(macros):
            try:
                return macros(self.__name, key)
            except Exception as e:
                raise ValueError("Cannot get macro key %s for connection %s. Reason: %s" % (key, self.__name, str(e)), e)
        else:
            try:
                return macros[key]
            except KeyError:
                raise ValueError("Macro for key %s is not defined in macros dictionary." % key)

    def __injector(self, injector_name):
        for p in self.__config["valueProviders"]:
            if p["name"] == injector_name:
                return p
        raise ValueError("Value provider for injector type %s not found" % injector_name)

    def __str__(self):
        return "Connection(%s)" % self.name

    def __repr__(self):
        return repr("Connection(%s)" % self.name)

