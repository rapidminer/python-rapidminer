
# rapidminer


## Server

Class for using a local or remote RapidMiner Server instance directly. You can read from and write to the Server repository and you can execute processes using the scalable Job Agent architecture.



```python
Server(url='http://localhost:8080',
            username=None,
            password=None,
            size_limit_kb=50000,
            webservice='Repository Service',
            processpath=None,
            tempfolder=None,
            install=True,
            verifySSL=True,
            logger=None,
            loglevel=logging.INFO)
```

Initializes a new connector to a local or remote Rapidminer Server instance. It also installs the auxiliary web service required by this library to be able to interact with the Server repository directly.

Arguments:
- `url`: Server url path (hostname and port as well)
- `username`: user to use Server with
- `password`: password for the username. If not provided, you will need to enter it.
- `size_limit_kb`: maximum number of kilobytes that are allowed to be read from or writing to Server. Reading or writing large objects may degrade Server's performance or lead to out of memory errors. Default value is 50000.
- `webservice`: this API requires an auxiliary process installed as a web service on the Server instance. This parameter specifies the name for this web service. The web service is automatically installed if it has not been.
- `processpath`: path in the repository where the process behind the web service will be saved. If not specified, a user prompt asks for the path, but proposes a default value. Note that you may want to make this process executable for all users.
- `tempfolder`: repository folder on Server that can be used for storing temporary objects by run_process method. Default value is "tmp" inside the user home folder. Note that in case of certain failures, you may need to delete remaining temporary objects from this folder manually.
- `install`: boolean. If set to false, web service installation step is completely skipped. Default value is True.
- `verifySSL`: either a boolean, in which case it controls whether we verify the server's TLS certificate, or a string, in which case it must be a path to a CA bundle to use. Default value is True.
- `logger`: a Logger object to use. By default a very simple logger is used, with INFO level, logging to stdout.
- `loglevel`: the loglevel, as an int value. Common values are defined in the standard logging module. Only used, if logger is not defined.


### read_resource
```python
Server.read_resource(path, project=None)
```

Reads one or more resources from the specified Server repository locations. Does not allow the retrieval of objects larger than the limit settings allow (size_limit_kb, limit in kilobytes).

Arguments:
- `path`: the path(s) to the resource(s) inside Server repository. Multiple paths can be specified as list or tuple. A path can be a string, a rapidminer.RepositoryLocation or a rapidminer.ProjectLocation object.
- `project`: optional project name. If this argument is defined, the specified paths are resolved in this project. If rapidminer.ProjectLocation objects are specified in the first argument, their project settings override the project set by this argument.



Returns:


- the requested resource(s). Datasets are returned as pandas DataFrames. Python native objects are returned as Python objects, other object types may be returned as bytes or BytesIO. If multiple inputs are specified, the same number of inputs will be returned in a tuple. Otherwise, the return value is a single object.


### write_resource
```python
Server.write_resource(resource, path)
```

Writes pandas DataFrame(s) or other objects to the Server repository.

Arguments:
- `resource`: a resource can be a pandas DataFrame, a pickle-able python object or a file-like object. Multiple DataFrames or other objects can be specified as list or tuple. A path can be a string or a rapidminer.RepositoryLocation object.
- `path`: the target path(s) to the resource(s) inside Server repository. The same number of path values are required as the number of resources.


### run_process
```python
Server.run_process(path,
                   inputs=[],
                   macros={},
                   queue='DEFAULT',
                   ignore_cleanup_errors=True,
                   project=None)
```

Runs a RapidMiner process and returns the result(s).

Arguments:
- `path`: path to the RapidMiner process in the Server repository. It can be a string or a rapidminer.RepositoryLocation object.
- `inputs`: inputs used by the RapidMiner process, an input can be a pandas DataFrame, a pickle-able python object or a file-like object.
- `macros`: optional dict that sets the macros in the process context according to the key-value pairs, e.g. macros={"macro1": "value1", "macro2": "value2"}
- `queue`: the name of the queue to submit the process to. Default is DEFAULT.
- `ignore_cleanup_errors`: boolean. Determines if any error during temporary data cleanup should be ignored or not. Default value is True.
- `project`: optional project name. If this argument is defined, the specified paths are resolved in this project. If rapidminer.ProjectLocation objects are specified in the first argument, their project settings override the project set by this argument. Note that when using projects, the inputs parameter is ignored, as direct write is not supported for versioned projects. Also, the method does not return outputs in this case.



Returns:


- the results of the RapidMiner process. It can be None, or a single object, or a tuple. One result may be a pandas DataFrame, a pickle-able Python object or a file-like object. When a project is used, no output is returned, as that would need direct write to a versioned project that is not supported.


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

Gets information of the available projects in the Server instance.




Returns:


- a JSON array of objects representing each repository with its properties
