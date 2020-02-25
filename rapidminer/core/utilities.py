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
import os
import sys
import pkgutil

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
        super(Exception, self).__init__(msg)

class ServerException(Exception):
    def __init__(self, msg=""):
        super(Exception, self).__init__(msg)

class VersionException(Exception):
    def __init__(self, product, upgrade_to):
        super(Exception, self).__init__("You are using an older version of Python Scripting Extension in " 
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
            str = ""
            error = response["error"]
            if "type" in error:
                str += error["type"] + ": "
            if "message" in error:
                str += error["message"]
            if str == "":
                str = "Unkown error: " + str(response)
            raise ServerException(str)
    return response


def put_docker_notebook_start(path):
    data = pkgutil.get_data(__name__, "notebooks/server_docker_start.ipynb")
    with open(path, "wb") as outf:
        outf.write(data)


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
