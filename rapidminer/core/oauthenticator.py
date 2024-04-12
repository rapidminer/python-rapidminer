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
from time import time
import jwt
import re
import os

from .connector import Connector

import logging


class OAuthenticator(Connector):
    def __init__(self, url=None, realm=None, client_id=None, username=None,
                 password=None, is_docker_based=False, logger=None, loglevel=logging.DEBUG):
        """
        Initializes a class which is responsible for connecting to a Rapidminer server via OAuth2, Keycloak. It gets the access token and keeps it active.

        Arguments:
        :param url: Server url path (hostname and port as well)
        :param realm: defines the Realm of OAuth authentication.
        :param client_id: defines the client in the Realm in OAuth authentication.
        :param username: user to use Server with
        :param password: password for the username.
        :param logger: a Logger object to use. By default a very simple logger is used, with INFO level, logging to stdout.
        :param loglevel: the loglevel, as an int value. Common values are defined in the standard logging module. Only used, if logger is not defined.
        """
        super(OAuthenticator, self).__init__(logger, loglevel)
        self.is_docker_based = is_docker_based
        if is_docker_based:
            api_url = os.getenv("JUPYTERHUB_API_URL")
            self.url = re.sub(r"(https?:/)", r"\g<1>/", re.sub("//*", "/", api_url + '/whoami'))
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
            self.log(f'Token may be expired, requesting new token.', level=logging.DEBUG)
        else:
            self.log(f'There are no tokens yet.', level=logging.DEBUG)

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
        r = requests.get(self.url, headers={'Authorization': 'token %s' % api_token})
        r.raise_for_status()
        r = r.json()
        access_token = r['auth_state']['access_token']
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

    def __request_tokens(self, force_renew=False):
        url = f'{self.url}/realms/{self.realm}/protocol/openid-connect/token'
        self.log(f"\nStarted requesting keycloak token via end-point:\n\t{url}", level=logging.DEBUG)
        if 'refresh_token' in self.tokens and self.__is_refresh_token_alive() and not force_renew:
            header, body = self.__get_header_and_body_for_refresh()
        else:
            header, body = self.__get_header_and_body()
        r = requests.post(url, headers=header, data=body)
        r.raise_for_status()
        r = r.json()
        if 'expires_in' in r and 'refresh_expires_in' in r:
            expires_at = time() + r['expires_in']
            refresh_expires_at = time() + r['refresh_expires_in']
            self.tokens = {
                'access_token': r['access_token'],
                'expires_at': expires_at,
                'refresh_token': r['refresh_token'],
                'refresh_expires_at': refresh_expires_at
            }
        else:
            self.tokens = {
                'access_token': r['access_token'],
                'refresh_token': r['refresh_token']
            }
        return r['access_token']

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
