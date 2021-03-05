# RapidMiner Python package

This Python package allows you to interact with RapidMiner Studio and AI Hub. You can collaborate using the RapidMiner repository and leverage the scalable RapidMiner AI Hub infrastructure to run processes. This document shows examples on how to use the package. Additional notebook files provide more advanced examples. There is an API document for each classes: [Project](docs/api/Project.md), [Studio](docs/api/Studio.md), [Server](docs/api/Server.md), [Connections](docs/api/Connections.md), [Scoring](docs/api/Scoring.md). You can find the [changelog for the package here](CHANGES.md).

## Table of contents

- [Requirements](#requirements)
- [Known current limitations](#known-current-limitations)
- [Overview](#requirements)
- [Installation](#installation)
- [Project](#project)
- [Connections](#connections)
- [Studio](#studio)
- [Server](#server)
- [Scoring](#scoring)

## Requirements

* RapidMiner Studio *9.7.0* for Studio class
* RapidMiner AI Hub *9.7.0* for Server class
* Python Scripting extension *9.7.0* or later installed for both Studio and RapidMiner AI Hub, download it from the [Marketplace](https://marketplace.rapidminer.com/UpdateServer/faces/product_details.xhtml?productId=rmx_python_scripting)

## Known current limitations

* Python version: 
  * Extensive tests were only carried out using *Python 3.7*, but earlier versions are expected to work as well.
  * Python 2 is not supported.
* RapidMiner Studio and AI Hub processes guarantee reproducibility. That means you should always get the same result after a version update. The same feature *cannot be guaranteed* when using this Python library (the library depends on other libraries that are not in our control).
* RapidMiner AI Hub with [SAML authentication](https://redirects.rapidminer.com/web/saml-authentication) is not supported.

## Overview

Both Studio and Server classes provide a read and a write method for reading / writing data and other objects, and a run method to run processes. The method signatures are the same, with somewhat different extra parameters. To work with versioned projects, a feature that arrives with RapidMiner AI Hub 9.7.0, use the Project class that provides read and write methods to the data file format used in them.

Studio class requires a local Studio installation and is suitable in the following cases:
* Implementing certain data science steps in Python using your favorite IDE or notebook implementation. You may even use the resulting code afterwards in a RapidMiner process within an *Execute Python* operator.
* You are using coding primarily, but you want to incorporate methods that are impemented in a RapidMiner process.
* Creating batch tasks that also interact with the repository and / or run processes.

Server class connects directly to a RapidMiner AI Hub instance without the need of a Studio installation. It is suitable in the following cases:
* Collaborating with RapidMiner users, sharing data easily.
* Calling, running, scheduling processes on the RapidMiner AI Hub platform from a local script.

Project class is required to work with the git-based versioned repositories called projects. Projects can be shared using RapidMiner AI Hub. The shared data format allows Python coders and RapidMiner users to easily work on the same data. To summarize, this class is suitable in the following cases:
* Using versioned projects to collaborate with RapidMiner users and share data easily.

Connections class can be used to access connections defined in a project. This way, Python coders can use the same external connections that are used by RapidMiner users. The connection fields are accessible, you only need an appropriate Python package to use those values.
* Using and sharing connections easily and securely without entering or storing any information redundantly.

## Installation

The library can be installed easily:

- install in one step:

        $ pip install rapidminer

- or clone the repository and install:

        $ git clone https://github.com/rapidminer/python-rapidminer.git
        $ cd python-rapidminer
        $ python setup.py install

## Project

Projects are a new feature of RapidMiner AI Hub 9.7.0 that allows you to have versioned repositories as the storage layer shared between RapidMiner users and Python coders. You can use any kind of git client, e.g. git commands, to clone, checkout a repository from RapidMiner AI Hub, and push your modifications there. Use the Project class to read and write the common data file format (HDF5).

Let's say you have cloned your versioned project into the local `myproject` folder using the git clone command. After that, point the Project class to this folder:

```python
import rapidminer
project = rapidminer.Project("myproject")
```

##### Reading ExampleSet

Once you have a project instance, you can read a RapidMiner ExampleSet in Python by running the following line (let's assume your data set called `mydata` is inside the `data` folder):

```python
df = project.read("data/mydata")
```

The resulting `df` is a `pandas` `DataFrame` object, which you can use in the conventional way.

You can also directly read a file on an arbitrary local path by using a default Project class:

```python
df = rapidminer.Project().read("local/file/path.rmhdf5table")
```

##### Writing ExampleSet

You can save any `pandas` `DataFrame` object to a project with the following command:

```python
project.write(df, "data/mydata_modified")
```

After writing the data set to the disk, you can use git commit and push to publish your changes to the remote project.

##### Running a process

Use Studio or Server classes to run a process from a project, see examples below.

## Connections

Connections in RapidMiner allow you to access external systems like databases, cloud services, social media, etc. With the Connections class, you can reuse connections defined in RapidMiner in an easy and secure way. Access all connections in a project, by pointing to the project folder:

```python
import rapidminer
connections = rapidminer.Connections("myproject", server=rapidminer.Server("https://myserver.mycompany.com:8080", username="myrmuser"))
```

Here, we already pointed to a [Server](#server) instance. That is only necessary if you have encrypted connection fields or use the AI Hub Vault to store certain sensitive values.

You can read the values of the connection fields by either using the connection name or an index. Use these field values to establish a connection using an appropriate Python package. The following code shows several different ways to access these values. Encryption or value injection (e.g. from AI Hub Vault) is handled transparently:

```python
myconn = connections["my_db_connection"]
mydb = myconn.values["database"]
myuser = myconn.user
mypass = connections[0].password
myhost = myconn.find_first("host")
myport = connections[0].values["port"]
```

## Studio

You need to have a locally installed RapidMiner Studio instance to use this class. The only thing you need to provide is your installation path. Once that is specified, you can read from and write data or other objects to any configured repository. You can also run processes from files or from the repository. In this section, we show you some examples on how to read and write repository data and run processes. For more advanced scenarios see the included [IPython notebook](examples/studio_examples.ipynb) and the [documentation of the `Studio` class](docs/api/Studio.md).

Note that each `Studio` method starts a Studio instance in the background and stops it when it is done. It is not recommended to run multiple instances in parallel, e.g. on different Notebook tabs. If you have several RapidMiner extensions installed, all of them will be loaded each time, that may lead to longer runtime. Provide multiple parameters to a read or write call, if possible, to avoid the startup overhead. 

First you need a `Connector` object to interact with Studio. Once you have that, you can read and write data or run a process with a single line. To create a `Studio` `Connector` object, run the following code:

```python
connector = rapidminer.Studio("/path/to/you/studio/installation")
```

where you replace `"/path/to/you/studio/installation"` with the location of your Studio installation. In case of Windows, a typical path is `"C:/Program Files/RapidMiner/RapidMiner Studio"` - note that you should either use forward "/" as separators or put an `r` before the first quote character to indicate raw string
. In case of Mac, the path is usually `"/Applications/RapidMiner Studio.app/Contents/Resources/RapidMiner-Studio"`. Alternatively you can define this location via the `RAPIDMINER_HOME` environment variable.

##### Reading ExampleSet

Once you have a connector instance, you can read a RapidMiner ExampleSet in Python by running the following line:

```python
df = connector.read_resource("//Samples/data/Iris")
```

The resulting `df` is a `pandas` `DataFrame` object, which you can use in the conventional way.

##### Writing ExampleSet

You can save any `pandas` `DataFrame` object to a RapidMiner repository (or file) with the following command:

```python
connector.write_resource(df, "//Local Repository/data/mydata")
```

where `df` is the `DataFrame` object you want to write to the repository, and `"//Local Repository/data/mydata"` is the location where you want to store it.

##### Running a process

To run a process execute the following line:

```python
df = connector.run_process("//Samples/processes/02_Preprocessing/01_Normalization")
```

You will get the results as `pandas` `DataFrames`. You can also define inputs, and many more. For more examples, see the [examples notebook](examples/studio_examples.ipynb)

## Server

With `Server` class, you can directly connect to a local or remote RapidMiner AI Hub instance without the need for any local RapidMiner (Studio) installation. You can read data from and write data to the remote repository and you can execute processes using the scalable Job Agent architecture. In this section, we show you some examples on how to read and write repository data and run processes. For more advanced scenarios see the included [IPython notebook](examples/server_examples.ipynb) and the [documentation of the `Server` class](docs/api/Server.md).

### Installation of Server API

The `Server` class requires a web service backend to be installed on RapidMiner AI Hub. This is done automatically on the first instantiation of the Server class. The repository folder `/shared` is used by default to store the backend process. This folder exists and is accessible by anyone starting from RapidMiner Server 9.6.0.

`Server` class instantiation can be fully automated (thus, no need for user input), if you specify `url`, `username` and `password` parameters.

On the RapidMiner AI Hub web UI you can see the installed web service backend (*Processes*->*Web Services*). It has the name *Repository Service* by default, but you can change that with the optional parameter of `Server` class named `webservice`. You can change the process path location by setting 'processpath', but you need to make sure that it will be executable by all users of the Server API. If the web service is deleted, the next `Server` instantiation will re-create it.

### Usage of Server API

To create a `Server` `Connector` object, run the following code:

```python
connector = rapidminer.Server("https://myserver.mycompany.com:8080", username="myrmuser")
```

where you replace `"https://myserver.mycompany.com:8080"` with the url of your RapidMiner AI Hub instance and `"myrmuser"` with your username.

##### Reading ExampleSet

Once you have a connector instance, you can read a RapidMiner ExampleSet in Python by running the following line:

```python
df = connector.read_resource("/home/myrmuser/data/mydata")
```

You can also read the latest version of a data set from a versioned project by running the following line:

```python
df = connector.read_resource("data/mydata", project="myproject")
```

The resulting `df` in both cases is a `pandas` `DataFrame` object, which you can use in the conventional way.

##### Writing ExampleSet

You can save any `pandas` `DataFrame` object to the RapidMiner AI Hub repository with the following command:

```python
connector.write_resource(df, "/home/myrmuser/data/myresult")
```

where `df` is the `DataFrame` object you want to write to the repository, and `"/home/myrmuser/data/myresult"` is the location where you want to store it.

If you want to write to a versioned project, use the Project class' write method to write to the local disk first (after cloning the project locally), then use git commit and push to publish your changes to RapidMiner AI Hub.

##### Running a process

To run a process execute the following line:

```python
df = connector.run_process("/home/myrmsuer/process/transform_data", inputs=df)
```

You will get the results as `pandas` `DataFrames`. You can also define multiple inputs, and other parameters. For more examples, see the [examples notebook](examples/server_examples.ipynb).

You may want to run a process that resides in a versioned project. Note that in this case, inputs and outputs are not allowed, as the process can only directly read from the project and potentially write back using an automatic commit and push. To run the latest version of a process in project, use the following line:

```python
df = connector.run_process("processes/myprocess", project="myproject")
```

## Scoring

This class allows you to easily use a deployed [Real-Time Scoring](https://docs.rapidminer.com/server/scoring-agent/) service. You only need to provide the RapidMiner AI Hub url and the particular scoring service endpoint to create a class instance. After that, you can use the predict method to do scoring on a pandas DataFrame and get the result in a pandas DataFrame as well. For instructions on how to deploy Real-Time Scoring on RapidMiner AI Hub, please refer to its documentation.

```python
sc = rapidminer.Scoring("http://myserver.mycompany.com:8090", "score-sales/score1")
prediction = sc.predict(df)
```

where the scoring endpoint is at `"score-sales/score1"` that can be applied to the dataset `df`, and the resulting `prediction` is a `pandas` `DataFrame` object. You can find the `Scoring` class [documentation here](docs/api/Scoring.md).


