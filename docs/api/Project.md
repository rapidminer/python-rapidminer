
# rapidminer


## Project

Class for using a project from RapidMiner Server that has been cloned locally. Use git for cloning the repository, then read and write calls can work on local resources. You need to use git commands to push changes that you make locally.



```python
Project(path='.')
```

Initializes a reference to a locally cloned project. You need to clone a project from RapidMiner Server first (e.g. via git commands) to be able to use the methods of this instance.

- `path`: path to the local project repository root folder. It can be a relative path from the current working directory or an absolute path, . The default value points to the working directory.


### read
```python
Project.read(path_or_buffer)
```

Reads a dataset from the local project repository into a pandas DataFrame. Note that only the new HDF5 format is supported, earlier RapidMiner Server data formats are not supported.

- `path_or_buffer`: this can either be a relative path inside the project (e.g. subfolder and file name), an absolute path, or a io.BytesIO stream. If a path is specified, the RapidMiner-specific HDF5 file extension can be omitted.


### write
```python
Project.write(df, path)
```

Writes a pandas DataFrame into the RapidMiner-specific HDF5 file format that the rest of the RapidMiner platform uses. Note that you need to explicitly commit and push your local changes to the remote project repository (e.g. via git commands) to make them available to the platform.

- `path`: relative path inside the project (e.g. subfolder and file name) specifying the target location or an absolute path. The RapidMiner-specific HDF5 file extension is automatically added to the filename, if it is missing.
