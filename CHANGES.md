## Release notes for `rapidminer` Python package

Note that this list is meant to track the main changes and does not provide an exhaustive list of changes in the package.

The first 3 numbers in the version always indicate the RapidMiner platform (Studio and AI Hub) version that the package is meant to be used with. This does not mean that the package is always incompatible with a different platform version. We aim to add explicit error messages when there is an incompatibility between versions, but it is generally recommended to always use the same version of the package and the RapidMiner platform.

Because of multiple reasons (like managing and releasing point of view) from version 10.1.0 we go with the more standardised version numbering. 

### Version 2026.0.1

* Fixed internal core package usability

### Version 2026.0.0

* Switched from setup.py to modern pyproject.toml packaging with flexible dependency version ranges, reducing installation conflicts with other packages

### Version 2025.1.0

* Removed version restrictions for numpy and pandas

### Version 2025.0.0

* Added full support of attribute/column roles

### Version 2024.1.0

* Bugfix: DataFrame reading error in case of integer columns
* Bugfix: Fix reading process details by calling a non-deprecated endpoint

### Version 10.2.0

* Rework authentication to support offline_token authentication method
* Removed possibility of username-password oauth authentication for WebApi and Server classes

### Version 10.1.0

* Introducing new interface for Web Api endpoints

### Version 10.0.0.0

* Added authentication option to `Scoring`
* Adapted authentication to AI Hub 10.0.0 in all classes
* Added support for reading `rmhdf5table` files to `Studio`

### Version 9.10.0.0

* Fixed install problems on Windows and with latest Python versions
* Replaced `tink` dependency with `cryptography` dependency

### Version 9.9.0.0

* Added `Connections` class to allow access to connections in projects
* Added `get_connections()` function to `Server` class to allow access to connections in AI Hub repository
* Adapted `Time` data type handling to how Studio and AI Hub 9.9.0+ handle it 

### Version 9.7.1.1

* Fixed `get_server()` call on docker-based environments

### Version 9.7.1.0

* Fixed the loss of attribute roles when using `read()` of `Project` class
* Explicit error is thrown when a Python Scripting extension with version below 9.7.0 is installed on RapidMiner AI Hub

### Version 9.7.0.1

* Added support for versioned projects via the new `Project` class
* Added support for versioned projects in `read_resource()` and `run_process()` calls of the `Server` class

### Version 9.6.0.0

* Added support for JupyterHub integration with RapidMiner Server
* Package is now published on PyPi

### Version 9.5.0.0

* Improved data handover, requires 9.5.0 version of the platform

### Version 9.3.1.0

* `run_process()` of `Server` now returns just a single value when there is just one output

### Version 9.3.0.0

* First version of the library

