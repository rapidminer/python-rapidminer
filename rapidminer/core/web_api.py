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
import pandas as pd
import requests
import json
from io import StringIO
from .oauthenticator import OAuthenticator
from .utilities import ServerException
from .utilities import extract_json
from .config import API_CONTEXT
from .config import WEB_API_GROUP_PREFIX
from .config import AUTHENTICATION_TYPE_OAUTH
from .config import AUTHENTICATION_TYPE_BASIC
from .config import AUTHENTICATION_LONG_LIVING_TOKEN
import base64


class WebApi:
    """
    Class that allows you to use the Web Api endpoints on a dataset with authentication available. 
    You can authenticate via the basic authentication method and via OAuth2, Keycloak server.
    """

    def __init__(self, hostname, endpoint, web_api_group='DEFAULT', authentication=None, username=None, password=None, authentication_server=None, realm=None, client_id=None, apitoken=None):
        """
        Arguments:
        :param hostname: Server url (together with the port).
        :param endpoint: endpoint to use.
        :param web_api_group: defines the Web API Group of the deployment.
        :param authentication: optional, it can have two different values "basic" or "oauth" or "apitoken".
        :param username: optional username for authentication in case of both authentication method.
        :param password: optional password for authentication in case of both authentication method.
        :param authentication_server: Authentication Server url (together with the port).
        :param realm: defines the Realm in case of OAuth authentication.
        :param client_id: defines the client in the Realm in case of OAuth authentication.
        :param apitoken: Long Living Token.
        """
        if hostname.endswith("/"):
            hostname = hostname[:-1]
        if authentication and authentication == AUTHENTICATION_TYPE_BASIC:
            self.authentication = authentication
            self.username = username
            self.__password = password
        elif authentication and authentication == AUTHENTICATION_TYPE_OAUTH:
            self.authentication = authentication
            self.oauthenticator = OAuthenticator(url=authentication_server, realm=realm,
                                                 client_id=client_id, username=username, password=password)
        elif authentication and apitoken and authentication == AUTHENTICATION_LONG_LIVING_TOKEN:
            self.authentication = authentication
            self.token = apitoken
        elif authentication:
            raise ValueError(
                f'The authentication parameter is defined then the value must be {AUTHENTICATION_TYPE_BASIC} or {AUTHENTICATION_TYPE_OAUTH} or {AUTHENTICATION_LONG_LIVING_TOKEN}.')
        else:
            self.authentication = None
        self.url = hostname + "/" + WEB_API_GROUP_PREFIX + "/" + \
            web_api_group + "/" + API_CONTEXT + "/services/" + endpoint

    def predict(self, data=None, macros=None, return_json=False):
        """
        Calls the Web Api endpoint on the specified dataset and macros and returns the result.

        Arguments:
        :param dataframe: pandas DataFrame, or list of JSON objects.
        :param macros: dictionary.
        :param return_json: if it is set to True it will return the response data and not trying to convert it to pandas DataFrame.
        :return: the result as pandas DataFrame, or a list of JSON objects.
        """

        if self.authentication == AUTHENTICATION_TYPE_BASIC and self.username and self.__password:
            userAndPass = base64.b64encode(
                bytes(self.username + ":" + self.__password, "utf-8")).decode("ascii")
            headers = {
                'Content-type': 'application/json',
                'Authorization': 'Basic %s' % userAndPass
            }
        elif self.authentication == AUTHENTICATION_TYPE_OAUTH and self.oauthenticator:
            headers = {
                'Content-type': 'application/json',
                'Authorization': 'Bearer %s' % self.oauthenticator.get_token()
            }
        elif self.authentication == AUTHENTICATION_LONG_LIVING_TOKEN and self.token:
            headers = {
                'Content-type': 'application/json',
                'Authorization': 'apitoken %s' % self.token
            }
        else:
            headers = {
                'Content-type': 'application/json'
            }

        # Mapping the data and macros to the correct format
        body = {}
        if data is not None and type(data) is pd.DataFrame:
            body = data.to_json(orient="table")
        else:
            body = json.dumps({
                'data': [{}] if data is None else data
            })
        if macros is not None:
            url = self.url + self.create_macros(macros)
        else:
            url = self.url
        r = requests.post(url, data=body, headers=headers)
        response = extract_json(r)
        if r.status_code != 200:
            message = "Could not score data, status: " + str(r.status_code)
            try:
                message += ". Message: " + response["message"]
            except KeyError:
                message += ""
            raise ServerException(message)

        if return_json:
            return response["data"]
        else:
            json_string = json.dumps(response["data"])
            df_out = pd.read_json(StringIO(json_string))

            return df_out

    def create_macros(self, macros):
        url_parameters = '?'
        for k, v in macros.items():
            if url_parameters[-1] != '?':
                url_parameters += '&'
            url_parameters += f'{k}={v}'
        return url_parameters
