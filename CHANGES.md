## Release notes for `rapidminer` Python package

Note that this list is meant to track the main changes and does not provide an exhaustive list of changes in the package.

The first 3 numbers in the version always indicate the RapidMiner platform (Studio and AI Hub) version that the package is meant to be used with. This does not mean that the package is always incompatible with a different platform version. We aim to add explicit error messages when there is an incompatibility between versions, but it is generally recommended to always use the same version of the package and the RapidMiner platform.

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

