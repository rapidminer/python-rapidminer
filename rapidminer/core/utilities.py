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
import sys

if sys.version_info.major > 2:
    def __open__(file, mode):
        return open(file, mode, encoding="utf-8")
else:
    raise GeneralException("Python 2 is not supported. Use Python 3.")

__STDOUT_ENCODING__ = os.getenv("PYTHONIOENCODING") # encoding in python should be the same as in Studio (with -Dfile.encoding param or system global), in order to handle special characters well
if __STDOUT_ENCODING__ is None or __STDOUT_ENCODING__ == "":
    __STDOUT_ENCODING__ = "utf-8"

class GeneralException(Exception):
    """
    General exception class to errors related to the rapidminer package.
    """
    def __init__(self, msg=""):
        super(GeneralException, self).__init__(msg)

class ServerException(Exception):
    def __init__(self, msg=""):
        super(ServerException, self).__init__(msg)

class ProjectException(Exception):
    def __init__(self, msg=""):
        super(ProjectException, self).__init__(msg)

class TooManyBinomialValuesError(ProjectException):
    def __init__(self, msg=""):
        super(TooManyBinomialValuesError, self).__init__(msg)

class ValueConversionError(ProjectException):
    def __init__(self, msg=""):
        super(ValueConversionError, self).__init__(msg)

class VersionException(Exception):
    def __init__(self, product, upgrade_to):
        super(VersionException, self).__init__("You are using an older version of Python Scripting Extension in "
                                        + product + ". Upgrade to "
                                        + upgrade_to + " version to use this version of the package.")

def extract_json(res):
    """
    Returns the JSON contained in the response object, or an empty JSON.

    If the JSON contains an 'error' attribute, an exception is raised with the extracted error message.
    """
    response = {}
    if hasattr(res, 'content') and len(res.text.strip()) > 0:
        try:
            response = res.json()
        except:
            return {}
        if "error" in response:
            s = ""
            error = response["error"]
            if "type" in error:
                s += error["type"] + ": "
            if "message" in error:
                s += error["message"]
            if s == "":
                s = "Unkown error: " + str(response)
            raise ServerException(str)
    return response


class Version:
    def __init__(self, version):
        v = version.split(".")
        # cut -BETA, -SNAPSHOT from last component, etc.
        [self.major, self.minor, self.patch] = [int(v[0]), int(v[1]), int(v[2].rsplit('-', 1)[0])]
 
    def is_at_least(self, other):
        selflist = [self.major, self.minor, self.patch]
        otherlist = [other.major, other.minor, other.patch]
        for i in range(len(selflist)):
            if selflist[i] > otherlist[i]:
                return True
            elif selflist[i] < otherlist[i]:
                return False
        return True

def _is_docker_based_deployment():
    return all([var in os.environ for var in ["JUPYTERHUB_API_TOKEN", "JUPYTERHUB_API_URL", "JUPYTERHUB_USER"]])
