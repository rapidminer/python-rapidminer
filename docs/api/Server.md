
# rapidminer


## Server

Class for using a local or remote RapidMiner Server instance directly. You can execute processes using the scalable Job Agent architecture.



```python
Server(url=None,
            authentication_server=None,
            username=None,
            password=None,
            realm=None,
            client_id=None,
            verifySSL=True,
            logger=None,
            loglevel=logging.INFO)
```

Initializes a new connector to a local or remote Rapidminer Server instance.

Arguments:
- `url`: Server url path (hostname and port as well)
- `authentication_server`: Authentication Server url (together with the port).
- `username`: optional username for authentication.
- `password`: optional password for authentication.
- `realm`: defines the Realm in case of OAuth authentication.
- `client_id`: defines the client in the Realm.
- `verifySSL`: either a boolean, in which case it controls whether we verify the server's TLS certificate, or a string, in which case it must be a path to a CA bundle to use. Default value is True.
- `logger`: a Logger object to use. By default a very simple logger is used, with INFO level, logging to stdout.
- `loglevel`: the loglevel, as an int value. Common values are defined in the standard logging module. Only used, if logger is not defined.


### run_process
```python
Server.run_process(path, project=None, macros={}, queue='DEFAULT')
```

Runs a RapidMiner process.

Arguments:
- `path`: path to the RapidMiner process in the Project. It can be a string or a rapidminer.ProjectLocation object.
- `project`: optional project name. If the path parameter is a rapidminer.ProjectLocation, then it is not needed to be defined.
- `macros`: optional dict that sets the macros in the process context according to the key-value pairs, e.g. macros={"macro1": "value1", "macro2": "value2"}
- `queue`: the name of the queue to submit the process to. Default is DEFAULT.


### get_queues
```python
Server.get_queues()
```

Gets information of the available queues in the Server instance.


Returns:
- a JSON array of objects representing each queue with its properties


### get_projects
```python
Server.get_projects()
```

Gets information of the available projects in the AI Hub instance.


Returns:
- a JSON array of objects representing each repository with its properties


### get_connections
```python
Server.get_connections(project)
```

Read the connections from the AI Hub repository.


Returns:
- Connections object listing connections from the AI Hub repository. Note that values of encrypted fields are not available (values will be None). Use AI Hub Vault to securely store and retrieve these values instead
