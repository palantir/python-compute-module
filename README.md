# Compute Module Lib
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/foundry-compute-modules)
[![PyPI](https://img.shields.io/pypi/v/foundry-compute-modules)](https://pypi.org/project/foundry-compute-modules/)
[![License](https://img.shields.io/badge/License-Apache%202.0-lightgrey.svg)](https://opensource.org/licenses/Apache-2.0)


> [!WARNING]
> This SDK is incubating and subject to change.


An open-source python library for compute modules for performing tasks like service discovery, getting a token, external source credentials, etc



## Functions Mode
Sources can be used to store secrets for use within a Compute Module, they prevent you from having to put secrets in your container or in plaintext in the job specification. 
Retrieving a source credential using this library is simple, if you are in Functions Mode they are passed to the context

### Basic usage

#### Option 1 - `@function` annotation on each endpoint

```python
# app.py
from compute_modules.annotations import function

@function
def add(context, event) -> int:
    return event["x"] + event["y"]

@function
def get_sources(context, event) -> List[str]:
    return context["sources"].keys()
```


#### Option 2 - Explicitly register function(s) & start the Compute Module

You can either add a single function via `add_function` or several at once with `add_functions`.

```python
# functions/add.py
def add(context, event) -> int:
    return event["x"] + event["y"]

# functions/hello.py
def hello(context, event) -> str:
    return "Hello " + event["x"] + "!"

# app.py
from compute_modules import add_functions, start_compute_module

from functions.add import add
from functions.hello import hello

if __name__ == "__main__":
    add_functions(
        hello,
        add,
    )
    start_compute_module()

```

### Advanced Usage - automatic function discovery
This library includes functionality that will inspect the functions registered for the Compute Module, inspect the input/output types of those functions, and then convert those to FunctionSpecs that can be imported as a Foundry Function without any modifications needed. Below are some considerations to ensure this feature works as expected.

#### 1. The Input class must be a complex type
Foundry function specs require the input type of a Function to be a complex type. If your function takes only a single primitive type as input, make sure to wrap that param in a complex type to have your function schema inferred properly. 

#### 2. Input type definition

**✅ TypedDict as input type**

```python
from typing import TypedDict
from compute_modules.annotations import function


class HelloInput(TypedDict):
    planet: str

@function
def hello(context, event: HelloInput) -> str:
    return "Hello " + event["planet"] + "!"
```

**✅ dataclass as input type**
```python
from dataclasses import dataclass
from compute_modules.annotations import function


@dataclass
class TypedInput:
    bytes_value: bytes
    bool_value: bool
    date_value: datetime.date
    decimal_value: decimal.Decimal
    float_value: float
    int_value: int
    str_value: str
    datetime_value: datetime.datetime
    other_date_value: datetime.datetime

@function
def typed_function(context, event: TypedInput) -> str:
    diff = event.other_date_value - event.datetime_value
    return f"The diff between dates provided is {diff}"
```

**✅ regular class with both class AND constructor type hints**
```python
from compute_modules.annotations import function


class GoodExample:
    some_flag: bool
    some_value: int

    def __init__(self, some_flag: bool, some_value: int) -> None:
        self.some_flag = some_flag
        self.some_value = some_value

@function
def typed_function(context, event: GoodExample) -> int:
    return return event.some_value
```

**❌ AVOID python class with no class type hints**
```python
# This will raise an exception
class BadClassNoTypeHints:
    def __init__(self, arg1: str, arg2: int):
        ...
```

**❌ AVOID python class with no constructor type hints**
```python
# This will raise an exception
class BadClassNoInitHints:
    arg1: str
    arg2: int

    def __init__(self, arg1, arg2):
        ...
```

**❌ AVOID python class with `args` in constructor**
```python
# This will raise an exception
class BadClassArgsInit:
    arg1: str
    arg2: int

    def __init__(self, arg1: str, arg2: int, *args):
        ...
```

**❌ AVOID python class with `kwargs` in constructor**
```python
# This will raise an exception
class BadClassKwargsInit:
    arg1: str
    arg2: int

    def __init__(self, arg1: str, arg2: int, **kwargs):
        ...
```

**❌ AVOID using dict/Dict with no type params**
```python
# These both will raise an exception
@dataclass
class MyPayload:
    data: dict

@dataclass
class MyPayload:
    data: typing.Dict
```


#### 3. Serialization/De-serialization of various types

| Python Type         | Foundry Type | Serialized over HTTP as |
| -----------         | ------------ | ----------------------- |
| int                 | Integer      | int                     |
| str                 | Byte         | string                  |
| bool                | Boolean      | boolean                 |
| bytes               | Binary       | string                  |
| datetime.date       | Date         | string                  |
| datetime.datetime   | Timestamp    | int (Unix timestamp)    |
| decimal.Decimal     | Decimal      | string                  |
| float               | Float        | float                   |
| list                | Array        | array                   |
| set                 | Array        | array                   |
| dict                | Map          | JSON                    |
| class/TypedDict     | Struct       | JSON                    |


### `QueryContext` typing

You can annotate the `context` param in any function with the `QueryContext` type to make it statically typed:
```python
from typing import TypedDict

from compute_modules.context import QueryContext
from compute_modules.annotations import function


class HelloInput(TypedDict):
    x: str

@function
def hello(context: QueryContext, event: HelloInput) -> str:
    return f"Hello {event['x']}! Your job ID is: {context.jobId}"
```

If left un-annotated, the `context` param will be a `dict`.


## Pipelines Mode
### Retrieving source credentials

Sources allow you to store secrets securely for use within a Compute Module, eliminating the need to include secrets in your container or in plaintext within the job specification. Retrieving a source credential using this library is straightforward:
```python
from compute_modules.sources import get_sources, get_source_secret

# retrive a dict with all sources
sources = get_sources()

# retrive the credentials of a specific source 
my_creds = get_source_secret("mySourceApiName", "MyCredential")

```

### Retrieving pipeline resources

The SDK offers a convenient method for retrieving information on the resources configured for your pipeline module. This allows you to obtain the rid (& branch, if present) of a Foundry resource via the alias provided for that resource in the Configure tab of your compute module.

```python
from compute_modules.resources import PipelineResource, get_pipeline_resources

resources: dict[str, PipelineResource] = get_pipeline_resources()
print(f"My reource's rid is: {resources['your-alias-name'].rid}")
```

### Retriving pipeline token

To obtain an auth token for interacting with Foundry resources in Pipeline mode use the following function:

```python
from compute_modules.auth import retrieve_pipeline_token
import requests

pipeline_token = retrieve_pipeline_token()
requests.post(..., headers={"Authorization": f"Bearer {pipeline_token}")
```


## Application's permissions/ Third Party App

If you have configured your Compute Module (CM) to use Application's permissions, your application will use a service user for permissions instead of relying on the user's permissions. This configuration requires you to obtain the client ID and credentials to grant permission to the service token. This library facilitates this process:

```python
from compute_modules.auth import retrieve_third_party_id_and_creds, oauth

CLIENT_ID, CLIENT_CREDS = retrieve_third_party_id_and_creds()

# get a scoped token for your 3pa
HOSTNAME = "myenvironment.palantirfoundry.com"
access_token = oauth(HOSTNAME, ["api:datasets-read"])

```

## Retrieving Arguments

This SDK provides utilities for retrieving arguments passed into the compute module. There are two different functions available: `get_raw_arguments` and `get_parsed_arguments`. Below is an example showing the difference between the two.

For a Compute Module with the following arguments configured: ![Compute Module Arguments](./assets/arguments_example.png)

If we log the result of both as such:
```python
# app.py

import logging as log
from compute_modules.annotations import function
from compute_modules.arguments import get_raw_arguments, get_parsed_arguments

log.basicConfig(level=log.INFO)

@function
def hello(context, event) -> str:
    raw_args = get_raw_arguments()
    parsed_args = get_parsed_arguments()
    log.info(f"raw_args: {raw_args}")
    log.info(f"parsed_args: {parsed_args}")
    ...
```

We would then receive the following log output:
```stdout
INFO: raw_args: ['--test', 'hello', '--another-param', 'world']
INFO: parsed_args: Namespace(test='hello' , another_param= 'world' )
```

## Logging

To ensure your logs are emitted to properly we recommend you use the `get_logger` utility function provided by the SDK. This returns a normal `logging.Logger` instance so once you have the logger, you can use it as a drop-in replacement for `logging.getLogger`.

```python
from compute_modules.logging import get_logger

logger = get_logger(__name__)
logger.setLevel(logging.INFO)

logger.debug("Can't see me")
logger.info("Peekaboo!")
logger.warning("Peekaboo!")
logger.error("Peekaboo!")
logger.critical("Peekaboo!")
```

### Surfacing logs from the `compute_modules` library
By default, the logs emitted from within the `compute_modules` library have a level of `ERROR`, meaning only error- or critical-level logs will be emitted. If for any reason you want to see other logs being emitted from within `compute_modules` you can use the `set_internal_log_level` function.

```python
from compute_modules.logging import set_internal_log_level

set_internal_log_level(logging.DEBUG)
```