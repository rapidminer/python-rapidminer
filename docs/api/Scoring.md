
# rapidminer


## Scoring

Class that allows you to use the Real-Time Scoring agent directly on a dataset with authentication available.
You can authenticate via the basic authentication method and via OAuth2, Keycloak server.



```python
Scoring(hostname,
             endpoint,
             authentication=None,
             username=None,
             password=None,
             authentication_server=None,
             realm=None,
             client_id=None)
```

Arguments:
- `hostname`: Server url (together with the port).
- `endpoint`: scoring service endpoint to use.
- `authentication`: optional, it can have two different values "basic" or "oauth".
- `username`: optional username for authentication in case of both authentication method.
- `password`: optional password for authentication in case of both authentication method.
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
