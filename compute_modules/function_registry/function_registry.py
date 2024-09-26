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


from typing import Any, Callable, Dict, List, Optional

from ..types import ComputeModuleFunctionSchema, PythonClassNode
from .function_schema_parser import parse_function_schema

REGISTERED_FUNCTIONS: Dict[str, Callable[..., Any]] = {}
FUNCTION_SCHEMAS: List[ComputeModuleFunctionSchema] = []
FUNCTION_SCHEMA_CONVERSIONS: Dict[str, PythonClassNode] = {}


def add_functions(*args: Callable[..., Any]) -> None:
    for function_ref in args:
        add_function(function_ref=function_ref)


def add_function(function_ref: Callable[..., Any]) -> None:
    """Parse & register a Compute Module function"""
    function_name = function_ref.__name__
    function_schema, class_node = parse_function_schema(function_ref, function_name)
    _register_parsed_function(
        function_name=function_name,
        function_ref=function_ref,
        function_schema=function_schema,
        function_schema_conversion=class_node,
    )


def _register_parsed_function(
    function_name: str,
    function_ref: Callable[..., Any],
    function_schema: ComputeModuleFunctionSchema,
    function_schema_conversion: Optional[PythonClassNode],
) -> None:
    """Registers a Compute Module function"""
    REGISTERED_FUNCTIONS[function_name] = function_ref
    FUNCTION_SCHEMAS.append(function_schema)
    if function_schema_conversion is not None:
        FUNCTION_SCHEMA_CONVERSIONS[function_name] = function_schema_conversion
