
# rapidminer


## Connections


```python
Connections(path='.',
                 server=None,
                 project_name=None,
                 show_parameter_groups=False,
                 macros=None)
```

Initializes a reference to a locally cloned project. You need to clone a project from RapidMiner Server first (e.g. via git commands) to be able to use the methods of this instance.

- `path`: path to the local project repository root folder. It can be a relative path from the current working directory or an absolute path, . The default value points to the working directory.
- `server`: Server object; required when values are encrypted or when values are injected from the Server Vault
- `project_name`: name of the project to which these connections belong; if not specified, it is set to the parent directory name of the specified path parameter
- `show_parameter_groups`: when set to True (default if False), parameter keys include the group as well in <group>.<key> format; otherwise, group is only added if there is a name collision
- `macros`: a dictionary or method, defining the values for the macro injected parameters. If a connection has a <prefix> defined for macro keys, the prefix is used before the key in <prefi><original key> format. If a method is used here, it should accept the connection_name and macro_name parameters, and should return the macro value for those.


## Connection

Class that represents a single connection.



```python
Connection(filepath, config, connections)
```

Initializes a connection instance based on a path and a config dictionary.

- `filepath`: path to the connection file
- `config`: dictionary containing all the connection details; can be directly created from the JSON content of the connection
- `connections`: reference to the parent Connections object


### find_first
```python
Connection.find_first(*words)
```

Returns the value of the first connection parameter that has one of the specified arguments in its key as a substring. Useful for looking up parameters if the key is not known accurately.

- `words`: arbitrary number of words to look for - the functions stops at the very first word for which it successfully finds a parameter that has the word in its key
