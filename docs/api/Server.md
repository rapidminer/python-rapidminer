# rapidminer

## Server

Class for using a local or remote RapidMiner Server instance directly. You can read from and write to the Server repository and you can execute processes using the scalable Job Agent architecture.


```python
Server(self, url='http://localhost:8080', username=None, password=None, row_limit=50000, attribute_limit=500, webservice='Repository Service', processpath=None, tempfolder=None, install=True, verifySSL=True, logger=None, loglevel=logging.INFO)
```

Initializes a new connector to a local or remote Rapidminer Server instance. It also installs the auxiliary webservice required by this library to be able to interact with the Server repository directly.

Arguments:
- `url`: Server url path (hostname and port as well)
- `username`: user to use Server with
- `password`: password for the username. If not provided, you will need to enter it.
- `row_limit`: maximum number of rows that are allowed to be read from Server. Reading or writing large objects may degrade Server's performance or lead to out of memory errors. Default value is 50000.
- `attribute_limit`: maximum number of attributes that are allowed to be read from Server. Reading or writing large objects may degrade Server's performance or lead to out of memory errors. Default value is 500.
- `webservice`: this API requires an auxiliary process installed as a webservice on the Server instance. This parameter specifies the name for this webservice. The webservice is automatically installed if it has not been.
- `processpath`: path in the repository where the process behind the webservice will be saved. If not specified, a user prompt asks for the path, but proposes a default value. Note that you may want to make this process executable for all users.
- `tempfolder`: repository folder on Server that can be used for storing temporary objects by run_process method. Default value is "tmp" inside the user home folder. Note that in case of certain failures, you may need to delete remaining temporary objects from this folder manually.
- `install`: boolean. If set to false, webservice installation step is completely skipped. Default value is True.
- `verifySSL`: either a boolean, in which case it controls whether we verify the server's TLS certificate, or a string, in which case it must be a path to a CA bundle to use. Default value is True.
- `logger`: a Logger object to use. By default a very simple logger is used, with INFO level, logging to stdout.
- `loglevel`: the loglevel, as an int value. Common values are defined in the standard logging module. Only used, if logger is not defined.

### read_resource
```python
Server.read_resource(self, path)
```

Reads one or more resources from the specified Server repository locations. Only supports reading data sets currently. Does not allow the retrieval of data sets larger that the limit settings allow (row_limit, attribute_limit).

Arguments:
- `path`: the path(s) to the resource(s) inside Server repository. Multiple paths can be specified as list or tuple. A path can be a string or a rapidminer.RepositoryLocation object.

Returns:
- the resource(s) as a pandas DataFrame(s). If multiple inputs are specified, the same number of inputs will be returned, as tuple of DataFrame objects. Otherwise, the return value is a single DataFrame.

### write_resource
```python
Server.write_resource(self, resource, path)
```

Writes one or more resources to the Server repository. Only supports writing data sets (pandas DataFrames) currently.

Arguments:
- `resource`: the pandas DataFrame(s). Multiple DataFrames can be specified as list or tuple. A path can be a string or a rapidminer.RepositoryLocation object.
- `path`: the target path(s) to the resource(s) inside Server repository. The same number of path values are required as the number of resources.

### run_process
```python
Server.run_process(self, path, inputs=[], macros={}, queue='DEFAULT', ignore_cleanup_errors=True)
```

Runs a RapidMiner process and returns the result(s).

Arguments:
- `path`: path to the RapidMiner process in the Server repository. It can be a string or a rapidminer.RepositoryLocation object.
- `inputs`: inputs used by the RapidMiner process, as a list of pandas DataFrame objects or a single pandas DataFrame.
- `macros`: optional dict that sets the macros in the process context according to the key-value pairs, e.g. macros={"macro1": "value1", "macro2": "value2"}
- `queue`: the name of the queue to submit the process to. Default is DEFAULT.
- `ignore_cleanup_errors`: boolean. Determines if any error during temporary data cleanup should be ignored or not. Default value is True.

Returns:
- the results of the RapidMiner process. It can be None, or a single pandas DataFrame object, or a tuple of DataFrames.

### get_queues
```python
Server.get_queues(self)
```

Gets information of the available queues in the Server instance.


Returns:
- a JSON array of objects representing each queue with its properties
