
# rapidminer


## Connections
```python
Connections()
```

Class for using connections from a Project or Repository.



```python
Connections(path='.',
                 server=None,
                 project_name=None,
                 show_parameter_groups=False,
                 macros=None)
```

Initializes a reference to a locally cloned project or to an AI Hub repository. You either need to clone a project from AI Hub first (e.g. via git commands), or point to an AI Hub repository to be able to use the methods of this class.

- `path`: path to the local project repository root folder. It can be a relative path from the current working directory or an absolute path. The default value points to the working directory. Set it to None to read connections from AI Hub repository (server parameter needs to be set in this case)
- `server`: Server object; required when values are encrypted or when values are injected from the AI Hub Vault
- `project_name`: name of the project to which these connections belong; if not specified, it is set to the parent directory name of the specified path parameter. Ignored if AI Hub repository connections are used
- `show_parameter_groups`: when set to True (default if False), parameter keys include the group as well in group.key format; otherwise, group is only added if there is a name collision among the keys
- `macros`: a dictionary or method defining the values for the macro injected parameters. If a connection has a prefix defined for macro keys, the prefix is added before the key. If a method is used here, it should accept connection_name and macro_name parameters, and should return the macro value for those


## Connection
```python
Connection()
```

Class that represents a single connection.


### config

The raw internal JSON configuration of the connection.


### name

The name of the connection.


### password

Quick way to access the first field that probably contains a password, e.g. the field name contains the string password.


### type

Type of the connection, i.e. what kind of system or service it connects to.


### user

Quick way to access the first field that probably contains a user name, e.g. the field name contains the string username.


### values

Dictionary with all the connection fields. Injected and encrypted fields are all handled transparently provided that the appropriate information is accessible. Otherwise, an error is thrown for the first problem encountered. Note that encrypted values from an AI Hub repository are not available (values will be None) - use AI Hub Vault in this case. When accessing multiple fields, you may want to first create a copy from the returned dictionary to avoid retrieving values stored in AI Hub vault or decrypting values multiple times (all such values are refreshed in each call).



```python
Connection(location, config, connections)
```

Initializes a connection instance based on a location and a config dictionary.

- `location`: path to the connection file in the project or in the AI Hub repository
- `config`: dictionary containing all the connection details; can be directly created from the JSON content of the connection
- `connections`: reference to the parent Connections object


### find_first
```python
Connection.find_first(*words)
```

Returns the value of the first connection parameter that has one of the specified arguments in its key as a substring. Useful for looking up parameters if the key is not known accurately.

- `words`: arbitrary number of words to look for - the functions stops at the very first word for which it successfully finds a parameter that has the word in its key
