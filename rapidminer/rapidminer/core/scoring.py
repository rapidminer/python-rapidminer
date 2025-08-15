#
# This file is part of the RapidMiner Python package.
#
# Copyright (C) 2018-2025 RapidMiner GmbH
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
from .oauthenticator import OAuthenticator
from .utilities import ServerException
from .utilities import extract_json
from .config import API_CONTEXT
from .config import AUTHENTICATION_TYPE_OAUTH
from .config import AUTHENTICATION_TYPE_BASIC
from .config import AUTHENTICATION_TYPE_OAUTH_OFFLINE_TOKEN
import base64


class Scoring:
    """
    Class that allows you to use the Real-Time Scoring agent directly on a dataset with authentication available.
    You can authenticate via the basic authentication method and via OAuth2, Keycloak server.
    """

    def __init__(self, hostname, endpoint, authentication=None, username=None, password=None,
                 client_secret=None, offline_token=None, authentication_server=None, realm=None, client_id=None):
        """
        Arguments:
        :param hostname: Server url (together with the port).
        :param endpoint: scoring service endpoint to use.
        :param authentication: optional, it can have three different values "basic" or "oauth" or "oauth_token".
        :param username: optional username for authentication in case of both authentication method.
        :param password: optional password for authentication in case of both authentication method.
        :param client_secret: Client secret for OAuth authentication via a non-public keycloak client, used with "oauth_token" authentication
        :param offline_token: Offline token for authentication acquired via the /get-token endpoint, used with "oauth_token" authentication
        :param authentication_server: Authentication Server url (together with the port).
        :param realm: defines the Realm in case of OAuth authentication.
        :param client_id: defines the client in the Realm in case of OAuth authentication.
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
        elif authentication and authentication == AUTHENTICATION_TYPE_OAUTH_OFFLINE_TOKEN:
            self.authentication = authentication
            self.oauthenticator = OAuthenticator(url=authentication_server, realm='master',
                                                 client_id='token-tool', client_secret=client_secret, offline_token=offline_token)
        elif authentication:
            raise ValueError(f'The authentication parameter is defined then the value must be '
                             f'{AUTHENTICATION_TYPE_BASIC} or {AUTHENTICATION_TYPE_OAUTH} or '
                             f'{AUTHENTICATION_TYPE_OAUTH_OFFLINE_TOKEN}.')
        else:
            self.authentication = None
        self.url = hostname + "/" + API_CONTEXT + "/services/" + endpoint

    def predict(self, dataframe):
        """
        Calls the Real-Time Scoring agent on the specified dataset and returns the result.

        Arguments:
        :param dataframe: the pandas DataFrame.
        :return: the result as a pandas DataFrame.
        """
        df_json = dataframe.to_json(orient="table")

        if self.authentication == AUTHENTICATION_TYPE_BASIC and self.username and self.__password:
            userAndPass = base64.b64encode(bytes(self.username + ":" + self.__password, "utf-8")).decode("ascii")
            headers = {
                'Content-type': 'application/json',
                'Authorization': 'Basic %s' % userAndPass
            }
        elif (self.authentication == AUTHENTICATION_TYPE_OAUTH or self.authentication == AUTHENTICATION_TYPE_OAUTH_OFFLINE_TOKEN) and self.oauthenticator:
            headers = {
                'Content-type': 'application/json',
                'Authorization': 'Bearer %s' % self.oauthenticator.get_token()
            }
        else:
            headers = {
                'Content-type': 'application/json'
            }
        r = requests.post(self.url, data=df_json, headers=headers)
        response = extract_json(r)
        if r.status_code != 200:
            message = "Could not score data, status: " + str(r.status_code)
            try:
                message += ". Message: " + response["message"]
            except KeyError:
                message += ""
            raise ServerException(message)

        json_string = json.dumps(response["data"])
        df_out = pd.read_json(json_string)

        return df_out
