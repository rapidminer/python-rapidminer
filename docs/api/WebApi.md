
# rapidminer


## WebApi

Class that allows you to use the Web Api endpoints on a dataset with authentication available.
You can authenticate via the basic authentication method and via OAuth2, Keycloak server.



```python
WebApi(hostname,
            endpoint,
            web_api_group='DEFAULT',
            authentication=None,
            username=None,
            password=None,
            client_secret=None,
            offline_token=None,
            authentication_server=None,
            apitoken=None)
```

Arguments:
- `hostname`: Server url (together with the port).
- `endpoint`: endpoint to use.
- `web_api_group`: defines the Web API Group of the deployment.
- `authentication`: optional, it can have two different values "basic" or "oauth" or "apitoken".
- `username`: optional username for authentication in case of "basic" authentication method.
- `password`: optional password for authentication in case of "basic" authentication method.
- `authentication_server`: Authentication Server url (together with the port).
- `client_secret`: Client secret for OAuth authentication via a non-public keycloak client
- `offline_token`: Offline token for authentication acquired via the /get-token endpoint
- `apitoken`: Long Living Token.


### predict
```python
WebApi.predict(data=None, macros=None, return_json=False)
```

Calls the Web Api endpoint on the specified dataset and macros and returns the result.

Arguments:
- `dataframe`: pandas DataFrame, or list of JSON objects.
- `macros`: dictionary.
- `return_json`: if it is set to True it will return the response data and not trying to convert it to pandas DataFrame.



Returns:


- the result as pandas DataFrame, or a list of JSON objects.
