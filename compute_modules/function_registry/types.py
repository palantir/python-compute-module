#  Copyright 2024 Palantir Technologies, Inc.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.


import datetime
import decimal
import typing
from dataclasses import dataclass

DataTypeDict = typing.Dict[str, typing.Any]


class DataType(typing.TypedDict):
    """Data type schema"""

    dataType: DataTypeDict


class PythonClassNode(typing.TypedDict):
    """Represents a Python class constructor with a dict containing refs to any child fields that are also custom classes"""

    constructor: typing.Any
    children: typing.Optional[typing.Dict[str, "PythonClassNode"]]


class FunctionInputType(DataType):
    """Function input schema"""

    name: str
    required: typing.Literal[True]
    constraints: typing.List[typing.Any]


class FunctionOutputType(typing.TypedDict):
    """Function output schema"""

    type: typing.Literal["single"]
    single: DataType


class ComputeModuleFunctionSchema(typing.TypedDict):
    """Represents the function schema for a Compute Module function"""

    # TODO: implement apiName & namespace
    functionName: str
    inputs: typing.List[FunctionInputType]
    output: FunctionOutputType


@dataclass
class ParseFunctionSchemaResult:
    function_schema: ComputeModuleFunctionSchema
    class_node: typing.Optional[PythonClassNode]
    is_context_typed: bool


Byte = typing.NewType("Byte", int)
Double = typing.NewType("Double", float)
Long = typing.NewType("Long", int)
Short = typing.NewType("Short", int)

AllowedKeyTypes = typing.Union[
    bytes,
    bool,
    Byte,
    datetime.date,
    decimal.Decimal,
    Double,
    float,
    int,
    Long,
    # TODO: handle ontology types?
    # OntologyObject
    Short,
    str,
    datetime.datetime,
]
