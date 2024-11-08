
# rapidminer


## Scoring
```python
Scoring()
```

Class that allows you to use the Real-Time Scoring agent directly on a dataset with authentication available.
You can authenticate via the basic authentication method and via OAuth2, Keycloak server.



```python
Scoring(hostname,
             endpoint,
             authentication=None,
             username=None,
             password=None,
             client_secret=None,
             offline_token=None,
             authentication_server=None,
             realm=None,
             client_id=None)
```

Arguments:
- `hostname`: Server url (together with the port).
- `endpoint`: scoring service endpoint to use.
- `authentication`: optional, it can have three different values "basic" or "oauth" or "oauth_token".
- `username`: optional username for authentication in case of both authentication method.
- `password`: optional password for authentication in case of both authentication method.
- `client_secret`: Client secret for OAuth authentication via a non-public keycloak client, used with "oauth_token" authentication
- `offline_token`: Offline token for authentication acquired via the /get-token endpoint, used with "oauth_token" authentication
- `authentication_server`: Authentication Server url (together with the port).
- `realm`: defines the Realm in case of OAuth authentication.
- `client_id`: defines the client in the Realm in case of OAuth authentication.


### predict
```python
Scoring.predict(dataframe)
```

Calls the Real-Time Scoring agent on the specified dataset and returns the result.

Arguments:
- `dataframe`: the pandas DataFrame.



Returns:


- the result as a pandas DataFrame.
