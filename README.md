# RapidMiner Python package

This Python package allows you to interact with Altair AI Studio and Altair AI Hub. You can collaborate using the Altair AI repository and leverage the scalable Altair AI Hub infrastructure to run processes. This document shows examples on how to use the package. Additional notebook files provide more advanced examples. There is an API document for each of the classes: [Project](docs/api/Project.md), [Studio](docs/api/Studio.md), [Server](docs/api/Server.md), [Connections](docs/api/Connections.md), [Scoring](docs/api/Scoring.md). You can find the [changelog for the package here](CHANGES.md).

## Table of contents

- [RapidMiner Python package](#rapidminer-python-package)
  - [Table of contents](#table-of-contents)
  - [Requirements](#requirements)
  - [Known current limitations](#known-current-limitations)
  - [Overview](#overview)
  - [Installation](#installation)
  - [Project](#project)
        - [Reading ExampleSet](#reading-exampleset)
        - [Writing ExampleSet](#writing-exampleset)
        - [Running a process](#running-a-process)
  - [Connections](#connections)
  - [Studio](#studio)
        - [Reading ExampleSet](#reading-exampleset-1)
        - [Writing ExampleSet](#writing-exampleset-1)
        - [Running a process](#running-a-process-1)
  - [Server](#server)
    - [Usage of Server API](#usage-of-server-api)
    - [Running a process](#running-a-process-2)
    - [Getting information about projects, queues and connections](#getting-information-about-projects-queues-and-connections)
      - [Projects](#projects)
      - [Connections](#connections-1)
      - [Queues](#queues)
  - [Web Api Endpoints](#web-api-endpoints)
  - [Scoring](#scoring)

## Requirements

* Altair AI Studio *2024.0* (*10.4.0*) for Studio class
* Altair AI Hub *2024.0* (*10.4.0*) for Server class
* Python Scripting extension *10.0.0* or later installed for both Studio and Server, download it from the [Marketplace](https://marketplace.rapidminer.com/UpdateServer/faces/product_details.xhtml?productId=rmx_python_scripting)

## Known current limitations

* Python version: 
  * Extensive tests were only carried out using *Python 3.10.9*, but earlier versions are expected to work as well.
  * Python 2 is not supported.
* Altair AI Studio and AI Hub processes guarantee reproducibility. That means you should always get the same result after a version update. The same feature *cannot be guaranteed* when using this Python library (the library depends on other libraries that are not in our control).
* Altair AI Hub with [SAML authentication](https://redirects.rapidminer.com/web/saml-authentication) is not supported.

## Overview

Studio class provides a read and a write method for reading / writing data and other objects, and both Studio and Server classes provide a run method to run processes. To work with versioned projects, use the Project class that provides read and write methods to the data file format used in them.

Studio class requires a local Studio installation and is suitable in the following cases:
* Implementing certain data science steps in Python using your favorite IDE or notebook implementation. You may even use the resulting code afterwards in an Altair AI process within an *Execute Python* operator.
* You are using coding primarily, but you want to incorporate methods that are impemented in an Altair AI process.
* Creating batch tasks that also interact with the repository and / or run processes.

Server class connects directly to an Altair AI Hub instance without the need of a Studio installation. It is suitable in the following cases:
* Collaborating with Altair AI users, sharing data easily.
* Calling, running, scheduling processes on the Altair AI Hub platform from a local script.

Project class is required to work with the git-based versioned repositories called projects. Projects can be shared using Altair AI Hub. The shared data format allows Python coders and Altair AI users to easily work on the same data. To summarize, this class is suitable in the following cases:
* Using versioned projects to collaborate with RapidMiner users and share data easily.

Connections class can be used to access connections defined in a project. This way, Python coders can use the same external connections that are used by Altair AI users. The connection fields are accessible, you only need an appropriate Python package to use those values.
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

Projects are a new feature of Altair AI Hub 9.7.0 that allows you to have versioned repositories as the storage layer shared between Altair AI users and Python coders. You can use any kind of git client, e.g. git commands, to clone, checkout a repository from Altair AI Hub, and push your modifications there. Use the Project class to read and write the common data file format (HDF5).

Let's say you have cloned your versioned project into the local `myproject` folder using the git clone command. After that, point the Project class to this folder:

```python
import rapidminer
project = rapidminer.Project("myproject")
```

##### Reading ExampleSet

Once you have a project instance, you can read an Altair AI ExampleSet in Python by running the following line (let's assume your data set called `mydata` is inside the `data` folder):

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

For more examples with projects, see the [Project examples notebook](examples/project_examples.ipynb).

##### Running a process

Use Studio or Server classes to run a process from a project, see examples below.

## Connections

Connections in Altair AI allow you to access external systems like databases, cloud services, social media, etc. With the Connections class, you can reuse connections defined in Altair AI in an easy and secure way. Access all connections in a project, by pointing to a local project folder:

```python
import rapidminer
connections = rapidminer.Connections("myproject", server=rapidminer.Server("https://myserver.mycompany.com:8080", authentication_server="https:///myserver.mycompany.com:8081/auth", offline_token="qwert12345", client_secret="qwert12345"))
```

Here, we already pointed to a [Server](#server) instance. That is only necessary if you have encrypted connection fields or use the AI Hub Vault to store certain sensitive values.

It is also possible to use connections from an AI Hub repository. Assuming here that we have a [Server](#server) instance, you can retrieve the connections defined in its repository:

```python
connections = server.get_connections()
```

You can read the values of the connection fields by either using the connection name or an index. Use these field values to establish a connection using an appropriate Python package. The following code shows several different ways to access these values. Encryption or value injection (e.g. from AI Hub Vault) is handled transparently:

```python
myconn = connections["my_db_connection"]
mydb = myconn.values["database"]
myuser = myconn.user
mypass = connections[0].password
myhost = myconn.find_first("host")
myport = connections[0].values["port"]
```

Note when reading connections directly from an AI Hub project, encrypted values are not available (values are None). You are advised to use AI Hub Vault for these values, or clone the project with the connection in it.

## Studio

You need to have a locally installed Altair AI Studio instance to use this class. The only thing you need to provide is your installation path. Once that is specified, you can read from and write data or other objects to any configured repository. You can also run processes from files or from the repository. In this section, we show you some examples on how to read and write repository data and run processes. For more advanced scenarios see the included [IPython notebook](examples/studio_examples.ipynb) and the [documentation of the `Studio` class](docs/api/Studio.md).

Note that each `Studio` method starts a Studio instance in the background and stops it when it is done. It is not recommended to run multiple instances in parallel, e.g. on different Notebook tabs. If you have several Altair AI extensions installed, all of them will be loaded each time, that may lead to longer runtime. Provide multiple parameters to a read or write call, if possible, to avoid the startup overhead. 

First you need a `Connector` object to interact with Studio. Once you have that, you can read and write data or run a process with a single line. To create a `Studio` `Connector` object, run the following code:

```python
connector = rapidminer.Studio("/path/to/you/studio/installation")
```

where you replace `"/path/to/you/studio/installation"` with the location of your Studio installation. In case of Windows, a typical path is `"C:/Program Files/Altair/Rapidminer/AI Studio"` - note that you should either use forward "/" as separators or put an `r` before the first quote character to indicate raw string
. In case of Mac, the path is usually `"/Applications/AI Studio.app/Contents/Resources/AI-Studio"`. Alternatively you can define this location via the `RAPIDMINER_HOME` environment variable.

##### Reading ExampleSet

Once you have a connector instance, you can read an Altair AI ExampleSet in Python by running the following line:

```python
df = connector.read_resource("//Samples/data/Iris")
```

The resulting `df` is a `pandas` `DataFrame` object, which you can use in the conventional way.

##### Writing ExampleSet

You can save any `pandas` `DataFrame` object to an Altair AI repository (or file) with the following command:

```python
connector.write_resource(df, "//Local Repository/data/mydata")
```

where `df` is the `DataFrame` object you want to write to the repository, and `"//Local Repository/data/mydata"` is the location where you want to store it.

##### Running a process

To run a process execute the following line:

```python
df = connector.run_process("//Samples/processes/02_Preprocessing/01_Normalization")
```

You will get the results as `pandas` `DataFrames`. You can also define inputs, and many more. For more examples, see the [Studio examples notebook](examples/studio_examples.ipynb).

## Server

With `Server` class, you can directly connect to a local or remote Altair AI Hub instance without the need for any local Altair AI Studio installation. You can execute processes using the scalable Job Agent architecture. In this section, we show you some examples on how to run processes. For more advanced scenarios see the included [IPython notebook](examples/server_examples.ipynb) and the [documentation of the `Server` class](docs/api/Server.md).

### Usage of Server API

To create a `Server` `Connector` object, run the following code:

```python
connector = rapidminer.Server("https://myserver.mycompany.com:8080")
```

It will ask you for further input to be able to authenticate. The input required from the user:
 - authentication_server: the url of the Keycloak authentication server with the /auth postfix
 - offline_token: after logging to the AI Hub instance, with the correct permissions you should be able to reach your {AI Hub url}/get-token page, where you can find the value of the offline token
 - client_secret: on the above page you should be able to see the client secret for this token-tool client

It is also possible to configure it using the constructor arguments: 

```python
connector = rapidminer.Server("https://myserver.mycompany.com:8080", authentication_server="https:///myserver.mycompany.com:8081/auth", offline_token="qwert12345", client_secret="qwert12345")
```

### Running a process

You may want to run a process that resides in a versioned project. Note that inputs and outputs are not allowed, as the process can only directly read from the project and potentially write back using an automatic commit and push. To run the latest version of a process in project, use the following code:

```python
connector = rapidminer.Server("https://myserver.mycompany.com:8080", authentication_server="https:///myserver.mycompany.com:8081/auth", offline_token="qwert12345", client_secret="qwert12345")
connector.run_process("processes/normalize_iris.rmp", project="sample-dev")
```

You can add the `project` name and `path` to the process to the run_process method too. You can also define `macros` and the `queue`, like the following way:

```python
connector.run_process(project='test-project', path='test-process.rmp', queue="default", macros={"sample_size" : 100})
```

### Getting information about projects, queues and connections

#### Projects

You can also get the available projects in the Server the following way:

```python
connector.get_projects()
```

This method returns a JSON array of objects representing each repository with its properties.

#### Connections

You can also get the available connections in a given project:

```python
connector.get_connections('project')
```

It returns a Connections object listing connections from the AI Hub project.

#### Queues

You can also get the queues in a Server:

```python
connector.get_queues()
```

It returns a JSON array of objects representing each queue with its properties.


## Web Api Endpoints

As AiHub Version 10.2 introduced a new possibility of having deployed endpoints next to the Real-Time-Scoring AiHub had offered, rapidminer package also introduces a new interface for that feature from version 10.4.

You can read the details of the advantages having Web Api endpoints and check the differences with the already existing Real-Time-Scoring at [Web Api Endpoints](https://docs.rapidminer.com/latest/hub/endpoints/index.html)

The WebApi class allows you to easily score a deployed service. You only need to provide the Altair AI Hub URL and the particular service endpoint to create a class instance. After that, you can use the predict method to do scoring and get the result in pandas DataFrame format, or in JSON format (depending on the value of return_json flag). For instructions on how to deploy Web Api endpoint on Altair AI Hub, please refer to its documentation.

```python
data = [
  {
   "a1": 5.1,
   "a2": 3.5,
   "a3": 1.4,
   "a4": 0.2
  }
 ]
macros = {
    'macro1': 1,
    'macro2': 'value'
}
wa = rapidminer.WebApi("https://myserver.mycompany.com:8090", "score-sales/score1")
prediction = wa.predict(data, macros, return_json=True)
```

where the Web Api endpoint is at `"score-sales/score1"` that can be applied to pandas DataFrame `data`, or list of JSON objects, with macros as parameters, and the resulting `prediction` is a pandas DataFrame as well (or JSON object). You can also define the Web Api group by defining the `web_api_group` parameter, by default it uses the `DEFAULT` one.

It can work without any authentication. However, there are three different options for authentication. It depends on the endpoint configuration, but the three different method is the basic authentication, the other one is the OAuth2 authentication with Keycloak and the last one is Long Living Token.

If basic authentication is configured, it is needed to add three extra arguments to define the `authentication` method, `username` and `password`.
The value of the authentication parameter in this case is `"basic"`.

```python
wa = rapidminer.WebApi("https://myserver.mycompany.com:8090", "score-sales/score1", authentication='basic', username="my_user", password="my_password")
prediction = wa.predict(data)
```

If the oauth authentication is configured, it is needed to add three more extra arguments compared to the basic authentication to define the `authentication server`, the `offline_token` and the `client_secret`.
The value of the authentication parameter in this case is `"oauth"`. The extra parameters details:
 - authentication_server: the url of the Keycloak authentication server with the /auth postfix
 - offline_token: after logging to the AI hub instance, with the correct permissions you should be able to reach your {AI Hub url}/get-token endpoint, where you can find the value of the offline token
 - client_secret: on the above page you should be able to see the client secret for this token-tool client

```python
wa = rapidminer.WebApi("https://myserver.mycompany.com:8090", "score-sales/score1", authentication='oauth', authentication_server="https:///myserver.mycompany.com:8090/auth", offline_token="qwert12345", client_secret="qwert12345")
prediction = wa.predict(data)
```

If the apitoken authentication is configured, it is needed to add your apitoken. The value of the authentication parameter in this case is `"apitoken"`.

```python
wa = rapidminer.WebApi("https://myserver.mycompany.com:8090", "score-sales/score1", authentication='apitoken', apitoken="my_token")
prediction = wa.predict(data)
```

## Scoring

This class allows you to easily use a deployed [Real-Time Scoring](https://docs.rapidminer.com/server/scoring-agent/) service. You only need to provide the Altair AI Hub url and the particular scoring service endpoint to create a class instance. After that, you can use the predict method to do scoring on a pandas DataFrame and get the result in a pandas DataFrame as well. For instructions on how to deploy Real-Time Scoring on Altair AI Hub, please refer to its documentation.

```python
sc = rapidminer.Scoring("http://myserver.mycompany.com:8090", "score-sales/score1")
prediction = sc.predict(df)
```

where the scoring endpoint is at `"score-sales/score1"` that can be applied to the dataset `df`, and the resulting `prediction` is a `pandas` `DataFrame` object. You can find the `Scoring` class [documentation here](docs/api/Scoring.md). Note that the scoring endpoint should not have a leading `"/"`.

It can work without any authentication. However, there are two different options for authentication. It depends on the RTS server configuration, but the two different method is the basic authentication and the other one is the OAuth2 authentication with Keycloak.

If basic authentication is configured, it is needed to add three extra arguments to define the `authentication` method, `username` and `password`.
The value of the authentication parameter in this case is `"basic"`.

```python
sc = rapidminer.Scoring("http://myserver.mycompany.com:8090", "score-sales/score1", authentication='basic', username="your_user", password="your_password")
prediction = sc.predict(df)
```

If the oauth authentication is configured, it is needed to add three more extra arguments compared to the basic authentication to define the `authentication server`, the `realm` and the `client-id`.
The value of the authentication parameter in this case is `"oauth"`.

```python
sc = rapidminer.Scoring("http://myserver.mycompany.com:8090", "score-sales/score1", authentication='basic', username="your_user", password="your_password", authentication_server='http://auth-server.mycompany.com:8081', realm='MyCompanyRealm', client_id='real-time-scoring-client')
prediction = sc.predict(df)
```
