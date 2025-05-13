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
import requests
from time import time
import jwt
import re
import os

from .connector import Connector

import logging


class OAuthenticator(Connector):
    def __init__(self, url=None, realm=None, client_id=None, client_secret=None, offline_token=None, username=None,
                 password=None, is_docker_based=False, logger=None, loglevel=logging.DEBUG):
        """
        Initializes a class which is responsible for connecting to a Rapidminer server via OAuth2, Keycloak. It gets the access token and keeps it active.

        Arguments:
        :param url: Server url path (hostname and port as well)
        :param realm: defines the Realm of OAuth authentication.
        :param client_id: defines the client in the Realm in OAuth authentication.
        :param client_secret: Client secret for OAuth authentication via a non-public keycloak client
        :param offline_token: Offline token for authentication acquired via the /get-token endpoint
        :param username: user to use Server with
        :param password: password for the username.
        :param is_docker_based: Boolean flag for Docker-based deployment.
        :param logger: a Logger object to use. By default a very simple logger is used, with INFO level, logging to stdout.
        :param loglevel: the loglevel, as an int value. Common values are defined in the standard logging module. Only used, if logger is not defined.
        """
        super(OAuthenticator, self).__init__(logger, loglevel)
        self.is_docker_based = is_docker_based
        self.offline_token = offline_token
        if is_docker_based:
            api_url = os.getenv("JUPYTERHUB_API_URL")
            self.url = re.sub(r"(https?:/)", r"\g<1>/", re.sub("//*", "/", api_url + '/whoami'))
        elif offline_token:
            self.log(
                f"Using the provided offline token for authentication: authentication url: {url}, realm={realm}, client_id={client_id}")
            if url.endswith("/"):
                url = url[:-1]
            self.url = url
            self.realm = realm
            self.client_id = client_id
            self.client_secret = client_secret
            self.offline_token = offline_token
        else:
            self.log(
                f"Using the following configuration for authentication: authentication url: {url}, realm={realm}, client_id={client_id}, username:{username}")
            if url.endswith("/"):
                url = url[:-1]
            self.url = url
            self.realm = realm
            self.client_id = client_id
            self.username = username
            self.__password = password

        self.tokens = {}

    def get_token(self, force_renew=False):
        if self.tokens and self.__is_token_alive() and not force_renew:
            return self.tokens["access_token"]
        elif self.tokens and not self.__is_token_alive():
            self.log('Token may be expired, requesting new token.', level=logging.DEBUG)
        else:
            self.log('There are no tokens yet.', level=logging.DEBUG)

        if self.is_docker_based:
            return self.__connect_idp()
        else:
            return self.__request_tokens(force_renew)

    def __get_header_and_body(self):
        header = {}
        body = {
            'client_id': self.client_id,
            'username': self.username,
            'password': self.__password,
            'grant_type': 'password'
        }
        return header, body

    def __get_header_and_body_offline_token(self):
        header = {}
        body = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'refresh_token': self.offline_token,
            'grant_type': 'refresh_token'
        }
        return header, body

    def __get_header_and_body_for_refresh(self):
        header = {}
        body = {
            'client_id': self.client_id,
            'grant_type': 'refresh_token',
            'refresh_token': self.tokens['refresh_token']
        }
        return header, body

    def __connect_idp(self):
        api_token = os.getenv("JUPYTERHUB_API_TOKEN")
        self.log("Getting up-to-date access token from: " + self.url, level=logging.DEBUG)
        response = requests.get(self.url, headers={'Authorization': 'token %s' % api_token})
        response .raise_for_status()
        data = response.json()
        access_token = data['auth_state']['access_token']
        try:
            expires = jwt.decode(access_token.encode(), options={"verify_signature": False})['exp']
        except jwt.DecodeError:
            expires = None

        if expires:
            self.tokens = {
                'access_token': access_token,
                'expires_at': expires
            }
        else:
            self.tokens = {
                'access_token': access_token,
            }
        return access_token

    def __request_tokens(self, force_renew: bool = False) -> str:
        token_url = f'{self.url}/realms/{self.realm}/protocol/openid-connect/token'
        self.log(f"\nStarted requesting keycloak token via end-point:\n\t{token_url}", level=logging.DEBUG)

        if 'refresh_token' in self.tokens and self.__is_refresh_token_alive() and not force_renew:
            header, body = self.__get_header_and_body_for_refresh()
        else:
            if self.offline_token:
                header, body = self.__get_header_and_body_offline_token()
            else:
                header, body = self.__get_header_and_body()

        response = requests.post(token_url, headers=header, data=body)
        if response.status_code == 200:
            self.log("Successfully obtained token", level=logging.INFO)
        else:
            self.log(f"Failed to get token: {response.status_code}", level=logging.ERROR)
            self.log(str(response.json()), level=logging.ERROR)
        response.raise_for_status()
        token_data = response.json()

        if 'expires_in' in token_data and 'refresh_expires_in' in token_data:
            expires_at = time() + token_data['expires_in']
            refresh_expires_at = time() + token_data['refresh_expires_in']
            self.tokens = {
                'access_token': token_data['access_token'],
                'expires_at': expires_at,
                'refresh_token': token_data['refresh_token'],
                'refresh_expires_at': refresh_expires_at
            }
        else:
            self.tokens = {
                'access_token': token_data['access_token'],
                'refresh_token': token_data['refresh_token']
            }
        return token_data['access_token']

    def __is_token_alive(self) -> bool:
        if 'expires_at' in self.tokens:
            return self.tokens["expires_at"] - 5 > time()
        else:
            return False

    def __is_refresh_token_alive(self) -> bool:
        if 'refresh_token' in self.tokens and 'refresh_expires_at' in self.tokens:
            return self.tokens["refresh_expires_at"] - 5 > time()
        else:
            return False
