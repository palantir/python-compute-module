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
import inspect
import typing

from compute_modules.context.types import QueryContext

from .types import (
    AllowedKeyTypes,
    Byte,
    ComputeModuleFunctionSchema,
    DataTypeDict,
    Double,
    FunctionInputType,
    FunctionOutputType,
    Long,
    ParseFunctionSchemaResult,
    PythonClassNode,
    Short,
)

CONTEXT_KEY = "context"
RETURN_KEY = "return"
RESERVED_KEYS = {CONTEXT_KEY, RETURN_KEY}


def parse_function_schema(
    function_ref: typing.Callable[..., typing.Any], function_name: str
) -> ParseFunctionSchemaResult:
    """Convert function name, input(s) & output into ComputeModuleFunctionSchema"""
    type_hints = typing.get_type_hints(function_ref, globalns={})
    inputs, root_class_node = _extract_inputs(type_hints)
    is_context_typed = _check_is_context_typed(type_hints)
    output = _extract_output(type_hints)
    function_schema = ComputeModuleFunctionSchema(
        functionName=function_name,
        inputs=inputs,
        output=output,
    )
    return ParseFunctionSchemaResult(
        function_schema=function_schema,
        class_node=root_class_node,
        is_context_typed=is_context_typed,
    )


def _extract_inputs(
    type_hints: typing.Dict[str, typing.Any],
) -> typing.Tuple[typing.List[FunctionInputType], typing.Optional[PythonClassNode]]:
    non_reserved_keys = iter([key for key in type_hints.keys() if key not in RESERVED_KEYS])
    payload_key = next(non_reserved_keys, None)
    if not payload_key:
        return [], None
    payload = type_hints[payload_key]
    inputs = []
    root_node_children: typing.Dict[str, PythonClassNode] = {}
    _assert_is_valid_custom_type(payload)
    field_hints = typing.get_type_hints(payload, globalns={})
    for field_name, value_type_hint in field_hints.items():
        # TODO: self-referencing classes??
        value_data_type, value_class_node = _extract_data_type(value_type_hint)
        root_node_children[field_name] = value_class_node
        inputs.append(
            FunctionInputType(
                name=field_name,
                required=True,
                constraints=[],
                dataType=value_data_type,
            )
        )
    root_class_node = PythonClassNode(
        constructor=payload,
        children=root_node_children,
    )
    return inputs, root_class_node


def _default_unknown_output() -> FunctionOutputType:
    """
    The UI for compute modules throws an error when registering a function without output, or with an output type that
    it does not recognize. To align with the behavior of other services, we should default the output type to a string.
    """
    return FunctionOutputType(
        type="single",
        single={
            "dataType": {
                "type": "string",
            },
        },
    )


def _check_is_context_typed(type_hints: typing.Dict[str, typing.Any]) -> bool:
    if CONTEXT_KEY not in type_hints:
        return False
    if type_hints[CONTEXT_KEY] is not QueryContext:
        raise ValueError("context can only be typed as compute_modules.context.QueryContext!")
    return True


def _extract_output(type_hints: typing.Dict[str, typing.Any]) -> FunctionOutputType:
    if RETURN_KEY not in type_hints:
        return _default_unknown_output()
    output_data_type, _ = _extract_data_type(type_hints[RETURN_KEY])
    return FunctionOutputType(
        type="single",
        single={
            "dataType": output_data_type,
        },
    )


def _extract_data_type(type_hint: typing.Any) -> typing.Tuple[DataTypeDict, PythonClassNode]:
    # TODO: not sure how to actually test the Byte/Long/Short/etc. DataTypes here...
    # As in how someone would actually define a Pyhton CM with those types
    if type_hint is bytes:
        return {
            "type": "binary",
            "binary": {},
        }, PythonClassNode(constructor=lambda x: bytes(x, encoding="utf8"), children=None)
    if type_hint is bool:
        return {
            "type": "boolean",
            "boolean": {},
        }, PythonClassNode(constructor=bool, children=None)
    if type_hint is Byte:
        return {
            "type": "byte",
            "byte": {},
        }, PythonClassNode(constructor=Byte, children=None)
    if type_hint is datetime.date:
        return {
            "type": "date",
            "date": {},
        }, PythonClassNode(constructor=datetime.date.fromisoformat, children=None)
    if type_hint is decimal.Decimal:
        return {
            "type": "decimal",
            "decimal": {},
        }, PythonClassNode(constructor=decimal.Decimal, children=None)
    if type_hint is Double:
        return {
            "type": "double",
            "double": {},
        }, PythonClassNode(constructor=Double, children=None)
    if type_hint is float:
        return {
            "type": "float",
            "float": {},
        }, PythonClassNode(constructor=float, children=None)
    if type_hint is int:
        return {
            "type": "integer",
            "integer": {},
        }, PythonClassNode(constructor=int, children=None)
    if type_hint is Long:
        return {
            "type": "long",
            "long": {},
        }, PythonClassNode(constructor=Long, children=None)
    if type_hint is Short:
        return {
            "type": "short",
            "short": {},
        }, PythonClassNode(constructor=Short, children=None)
    if type_hint is str:
        return {
            "type": "string",
            "string": {},
        }, PythonClassNode(constructor=str, children=None)
    if type_hint is datetime.datetime:
        # TODO: datetime.fromtimestamp(timestamp, datetime.UTC) instead once python version upgraded
        return {
            "type": "timestamp",
            "timestamp": {},
        }, PythonClassNode(constructor=lambda d: datetime.datetime.utcfromtimestamp(d / 1e3), children=None)
    if typing.get_origin(type_hint) is list:
        element_hint = typing.get_args(type_hint)[0]
        element_type, element_class_node = _extract_data_type(element_hint)
        return {
            "type": "list",
            "list": {
                "elementsType": element_type,
            },
        }, PythonClassNode(constructor=list, children={"list": element_class_node})
    if type_hint is dict or typing.get_origin(type_hint) is dict:
        dict_type_hints = typing.get_args(type_hint)
        if not len(dict_type_hints):
            raise ValueError("dict type hints must have type parameters provided (e.g. dict[str, str])")
        key_type, value_type = dict_type_hints
        if not (
            key_type in typing.get_args(AllowedKeyTypes)
            or issubclass(key_type, tuple(cls for cls in typing.get_args(AllowedKeyTypes) if inspect.isclass(cls)))
        ):
            raise ValueError(
                "Map key must be of type: ",
                AllowedKeyTypes,
                ", but it is of type: ",
                key_type,
            )
        key_data_type, key_class_node = _extract_data_type(key_type)
        value_data_type, value_class_node = _extract_data_type(value_type)
        return {
            "type": "map",
            "map": {
                "keysType": key_data_type,
                "valuesType": value_data_type,
            },
        }, PythonClassNode(constructor=dict, children={"key": key_class_node, "value": value_class_node})
    if typing.get_origin(type_hint) is typing.Union:
        type_args = typing.get_args(type_hint)
        if len(type_args) == 2 and type(None) in type_args:
            optional_type = next(arg for arg in type_args if arg is not type(None))
            optional_data_type, optional_class_node = _extract_data_type(optional_type)
            return {
                "type": "optionalType",
                "optionalType": {
                    "wrappedType": optional_data_type,
                },
            }, PythonClassNode(constructor=typing.Optional, children={"optional": optional_class_node})
        else:
            raise ValueError("Only unions with two types where one of the types is `None` are supported")
    if typing.get_origin(type_hint) is set:
        element_hint = typing.get_args(type_hint)[0]
        element_type, element_class_node = _extract_data_type(element_hint)
        return {
            "type": "set",
            "set": {
                "elementsType": element_type,
            },
        }, PythonClassNode(constructor=set, children={"set": element_class_node})
    # will throw error if it is not valid
    _assert_is_valid_custom_type(type_hint)
    custom_type_fields = {}
    child_class_nodes = {}
    for field_name, field_type_hint in typing.get_type_hints(type_hint, globalns={}).items():
        custom_type_fields[field_name], child_class_node = _extract_data_type(field_type_hint)
        if child_class_node:
            child_class_nodes[field_name] = child_class_node
    return {
        "type": "anonymousCustomType",
        "anonymousCustomType": {
            "fields": custom_type_fields,
        },
    }, PythonClassNode(constructor=type_hint, children=child_class_nodes)


def _assert_is_valid_custom_type(item: typing.Any) -> None:
    # If using a TypedDict, _assert_is_valid_custom_type will raise an erroneous exception
    # So we only want to validate if this is a true class
    if issubclass(item, dict):
        return
    type_hints = typing.get_type_hints(item, globalns={})
    init_spec: inspect.FullArgSpec = inspect.getfullargspec(item.__init__)
    init_args = init_spec.args
    init_args.remove("self")
    if set(type_hints) != set(init_args):
        raise ValueError(
            "Custom Type %s found but invalid, type_hints %s must match init args %s"
            % (item.__name__, set(type_hints), set(init_args))
        )
    _check_restrictions_on__init__(init_spec, item)


def _check_restrictions_on__init__(init_spec: inspect.FullArgSpec, item: typing.Any) -> None:
    annotations = init_spec.annotations
    annotations.pop(RETURN_KEY, None)
    # Check that the init args have type annotations that match the fields
    if typing.get_type_hints(item, globalns={}) != annotations:
        raise ValueError(
            "Custom Type {} should have init args type annotations {}"
            " that match the fields type annotations {}".format(
                item.__name__, typing.get_type_hints(item, globalns={}), annotations
            )
        )

    # special argument **kwargs or *args isn't used in the init method
    init_signature = inspect.signature(item.__init__)
    if annotations != {}:
        if "args" in init_signature.parameters:
            raise ValueError("The __init__ method should not use *args")
        if "kwargs" in init_signature.parameters:
            raise ValueError("The __init__ method should not use **kwargs")
