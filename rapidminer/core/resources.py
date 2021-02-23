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
class Resource(object):
    def to_string(self):
        """
        Returns a string based representation of this resource, which is handled by Rapidminer Studio

        :return: String representation.
        """
        raise NotImplementedError("Method not implemented in base class.")


class File(Resource):
    def __init__(self, filename):
        if not isinstance(filename, str):
            raise ValueError("'filename' must be a string. (now: " + str(type(filename)) +")")
        self.filename = filename

    def to_string(self):
        return "file:" + self.filename


class RepositoryLocation(Resource):
    __SEP__ = "/"

    def __init__(self, parent=None, name="."):
        """
        Creates a new repository location representation.

        :param parent: the parent repository location of this entry. If the value is None, an absolute value should be defined for name.
        :param name: the name of the location, relative to parent or an absolute location, if no parent is defined.
        """
        if parent is not None and not isinstance(parent, RepositoryLocation):
            raise ValueError("'parent' must be a 'rapidminer.RepositoryLocation' object.")
        if name is not None and not isinstance(name, str):
            raise ValueError("'name' must be a string.")
        self.parent = parent
        if name is not None:
            self.name = name
        else:
            self.name = "."

    def __append_with_sep(self, path, relative_path):
        result = path
        if not result.endswith(self.__SEP__):
            result = result + self.__SEP__
        return result + relative_path

    def to_string(self, with_prefix=True):
        if self.parent is not None:
            return self.__append_with_sep(self.parent.to_string(with_prefix=with_prefix), self.name)
        elif with_prefix:
            return "repositorylocation:" + self.name
        else:
            return self.name

class ProjectLocation(Resource):
    
    def __init__(self, project, path):
        """
        Creates a new project location representation.

        :param project: the project base path. It can be an absolute path, or a relative path from the current folder.
        :param path: the relative path inside the project.
        """
        if not project or not path:
            raise ValueError("Both 'project' and 'path' arguments must not be empty.")
        self.project = project
        self.path = path
    
    def to_string(self, with_prefix=True):
        if with_prefix:
            return "git://" + self.project + ".git/" + self.path
        else:
            return self.project + "/" + self.path
    
