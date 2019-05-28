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

__DEFAULT_ENCODING__ = "utf-8"

if sys.version_info.major > 2:
    def __open__(file, mode):
        return open(file, mode, encoding=__DEFAULT_ENCODING__)
elif sys.version_info.minor > 5:
    import io
    def __open__(file, mode):
        return io.open(file, mode, encoding=__DEFAULT_ENCODING__)
else:
    import codecs
    def __open__(file, mode):
        return codecs.open(file, mode, encoding=__DEFAULT_ENCODING__)
__STDOUT_ENCODING__ = os.getenv("PYTHONIOENCODING") # encoding in python should be the same as in Studio (with -Dfile.encoding param or system global), in order to handle special characters well
if __STDOUT_ENCODING__ is None or __STDOUT_ENCODING__ == "":
    __STDOUT_ENCODING__ = __DEFAULT_ENCODING__

class GeneralException(Exception):
    """
    General exception class to errors related to the rapidminer package.
    """
    def __init__(self, msg=""):
        super(Exception, self).__init__(msg)

class ServerException(Exception):
    def __init__(self, msg=""):
        super(Exception, self).__init__(msg)

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

