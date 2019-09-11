# rapidminer

## Studio

Class for using a locally installed RapidMiner Studio instance. You can read from and write to the repositories defined in Studio (and use even remote repositories this way) and you can execute processes.


```python
Studio(self, studio_home=None, logger=None, loglevel=logging.INFO, rm_stdout=None, override_python_binary=False)
```

Initializes a new connector to a local Rapidminer Studio instance. Every command will launch a new Studio instance, executing the required operations in batch mode.

Arguments:
- `studio_home`: path to installation directory of the Rapidminer Studio. If None, the location will be taken from the RAPIDMINER_HOME environment variable if defined, or the current directory, if RAPIDMINER_HOME is not defined.
- `logger`: a Logger object to use. By default a very simple logger is used, with INFO level, logging to stdout.
- `loglevel`: the loglevel, as an int value. Common values are defined in the standard logging module. Only used, if logger is not defined.
- `rm_stdout`: the output stream to redirect the output of underlying Studio launches. By default, the output is directed to the logger associated with this connector. Log records from Studio are labeled with new element 'key'='studio', while the logs from Python with 'key'='python'.
- `override_python_binary`: if set to True, any Execute Python operator in a process called via run_process will use the current Python interpreter instead of the one configured in the Studio installation, except if the process explicitly defines the Python binary. Default value is False.

### read_resource
```python
Studio.read_resource(self, path)
```

Reads one or more resources from the given repository locations / files

Arguments:
- `path`: the path(s) to the resource(s). Multiple paths can be specified as list or tuple. A path can be a string, in that case it is interpreted as a repository location. By using rapidminer.File and rapidminer.RepositoryLocation objects, you can specify explicitly whether you want to use local files or RapidMiner repository entries.

Returns:
- the resource(s) as pandas DataFrame(s), a pickle-able python object(s) or a file-like object(s). If multiple inputs are specified, the same number of inputs will be returned, as a tuple of objects.

### write_resource
```python
Studio.write_resource(self, resource, path)
```

Writes pandas DataFrame(s) or other objects to RapidMiner repository locations / regular files.

Arguments:
- `resource`: resource(s) to save: a resource can be a pandas DataFrame, a pickle-able python object or a file-like object. Multiple DataFrames or other objects can be specified as list or tuple.
- `path`: the target path(s) for the resource(s). The same number of path values are required as the number of resources. A path can be a string, in that case it is interpreted as a repository location. By using rapidminer.File and rapidminer.RepositoryLocation objects, you can specify explicitly whether you want to use local files or RapidMiner repository entries.

### run_process
```python
Studio.run_process(self, path, inputs=[], macros={}, operator=None)
```

Runs a RapidMiner process and returns the result(s).

Arguments:
- `path`: path to the RapidMiner process in a repository or an .rmp file. It can be a string, in that case it is interpreted as a repository location. It can also be a rapidminer.File or rapidminer.RepositoryLocation object representing a local file or a RapidMiner repository entry, respectively.
- `inputs`: inputs used by the RapidMiner process, an input can be a pandas DataFrame, a pickle-able python object or a file-like object.
- `macros`: optional dict that sets the macros in the process context according to the key-value pairs, e.g. macros={"macro1": "value1", "macro2": "value2"}
- `operator`: the name of the RapidMiner operator of the process to execute. If None (default) the whole process is executed.

Returns:
- the results of the RapidMiner process. It can be None, or a single object, or a tuple. One result may be a pandas DataFrame, a pickle-able python object or a file-like object.
