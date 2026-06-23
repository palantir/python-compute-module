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


from dataclasses import dataclass
from typing import Optional, Union

import pytest

from compute_modules.context import QueryContext
from compute_modules.function_registry.function_schema_parser import parse_function_schema
from compute_modules.function_registry.types import ComputeModuleFunctionSchema, FunctionOutputType
from tests.function_registry.dummy_app import (
    DummyInput,
    ParentClass,
    dummy_func_1,
    dummy_func_2,
    dummy_func_3,
    dummy_func_4,
    dummy_func_5,
)
from tests.function_registry.dummy_app_with_issues import (
    dummy_args_init,
    dummy_kwargs_init,
    dummy_no_init_hints,
    dummy_no_type_hints,
)

EXPECTED_STRING = {"string": {}, "type": "string"}
EXPECTED_OPTIONAL_STRING = {"optionalType": {"wrappedType": EXPECTED_STRING}, "type": "optionalType"}


@dataclass
class SimpleInput:
    x: str


@dataclass
class Pep604Input:
    error: str | None = None


@dataclass
class Pep604Inner:
    name: str
    error: str | None = None


@dataclass
class Pep604DirectOuter:
    inner: Pep604Inner


@dataclass
class Pep604ListOuter:
    items: list[Pep604Inner]


@dataclass
class OptionalInner:
    name: str
    error: Optional[str] = None


@dataclass
class OptionalListOuter:
    items: list[OptionalInner]


@dataclass
class UnionInner:
    name: str
    error: Union[str, None] = None


@dataclass
class UnionListOuter:
    items: list[UnionInner]


@dataclass
class UnsupportedPep604UnionInput:
    value: str | int


def pep604_top_level_input(context: QueryContext, event: Pep604Input) -> str:
    return event.error or context.userId or ""


def pep604_nested_direct_output(context: QueryContext, event: SimpleInput) -> Pep604DirectOuter:
    return Pep604DirectOuter(inner=Pep604Inner(name=event.x, error=context.userId))


def pep604_nested_list_output(context: QueryContext, event: SimpleInput) -> Pep604ListOuter:
    return Pep604ListOuter(items=[Pep604Inner(name=event.x, error=context.userId)])


def pep604_nested_input(context: QueryContext, event: Pep604ListOuter) -> str:
    return event.items[0].error or context.userId or ""


def optional_nested_list_output(context: QueryContext, event: SimpleInput) -> OptionalListOuter:
    return OptionalListOuter(items=[OptionalInner(name=event.x, error=context.userId)])


def union_nested_list_output(context: QueryContext, event: SimpleInput) -> UnionListOuter:
    return UnionListOuter(items=[UnionInner(name=event.x, error=context.userId)])


def unsupported_pep604_union_input(context: QueryContext, event: UnsupportedPep604UnionInput) -> str:
    return str(event.value or context.userId or "")


EXPECTED_OUTPUT_1 = {
    "single": {
        "dataType": {
            "anonymousCustomType": {
                "fields": {
                    "res1": {"boolean": {}, "type": "boolean"},
                    "res2": {
                        "map": {
                            "keysType": {"string": {}, "type": "string"},
                            "valuesType": {"float": {}, "type": "float"},
                        },
                        "type": "map",
                    },
                    "res3": {"list": {"elementsType": {"timestamp": {}, "type": "timestamp"}}, "type": "list"},
                }
            },
            "type": "anonymousCustomType",
        }
    },
    "type": "single",
}

EXPECTED_OUTPUT_3 = {
    "single": {
        "dataType": {
            "integer": {},
            "type": "integer",
        }
    },
    "type": "single",
}

EXPECTED_OUTPUT_4 = {
    "single": {
        "dataType": {
            "list": {
                "elementsType": {"string": {}, "type": "string"},
            },
            "type": "list",
        }
    },
    "type": "single",
}

EXPECTED_INPUTS = [
    {
        "name": "parent_class",
        "dataType": {
            "anonymousCustomType": {
                "fields": {
                    "some_flag": {"boolean": {}, "type": "boolean"},
                    "some_value": {"integer": {}, "type": "integer"},
                    "child": {
                        "anonymousCustomType": {
                            "fields": {
                                "timestamp": {"timestamp": {}, "type": "timestamp"},
                                "some_value": {"float": {}, "type": "float"},
                                "another_optional_field": {
                                    "optionalType": {"wrappedType": {"string": {}, "type": "string"}},
                                    "type": "optionalType",
                                },
                            }
                        },
                        "type": "anonymousCustomType",
                    },
                }
            },
            "type": "anonymousCustomType",
        },
        "required": True,
        "constraints": [],
    },
    {
        "name": "optional_field",
        "dataType": {"optionalType": {"wrappedType": {"string": {}, "type": "string"}}, "type": "optionalType"},
        "required": True,
        "constraints": [],
    },
    {
        "name": "set_field",
        "dataType": {"set": {"elementsType": {"date": {}, "type": "date"}}, "type": "set"},
        "required": True,
        "constraints": [],
    },
    {
        "name": "map_field",
        "dataType": {
            "map": {"keysType": {"binary": {}, "type": "binary"}, "valuesType": {"decimal": {}, "type": "decimal"}},
            "type": "map",
        },
        "required": True,
        "constraints": [],
    },
    {
        "name": "datetime_list",
        "dataType": {"list": {"elementsType": {"timestamp": {}, "type": "timestamp"}}, "type": "list"},
        "required": True,
        "constraints": [],
    },
    {"name": "some_flag", "dataType": {"boolean": {}, "type": "boolean"}, "required": True, "constraints": []},
    {
        "name": "optional_default_value_field",
        "dataType": {"optionalType": {"wrappedType": {"string": {}, "type": "string"}}, "type": "optionalType"},
        "required": True,
        "constraints": [],
    },
]


def test_function_schema_parser() -> None:
    """Test the happy path for parse_function_schemas_from_module"""
    parse_result = parse_function_schema(dummy_func_1, "dummy_func_1", [], {})
    assert parse_result.function_schema["functionName"] == "dummy_func_1"
    assert parse_result.function_schema["output"] == EXPECTED_OUTPUT_1
    assert len(parse_result.function_schema["inputs"]) == len(EXPECTED_INPUTS)
    assert parse_result.class_node is not None
    assert parse_result.class_node["constructor"] is DummyInput
    assert parse_result.function_schema["inputs"] == EXPECTED_INPUTS
    assert parse_result.class_node["children"] is not None
    assert parse_result.class_node["children"]["parent_class"]["constructor"] is ParentClass
    assert parse_result.class_node["children"]["optional_field"]["constructor"] is Optional
    assert parse_result.class_node["children"]["set_field"]["constructor"] is set
    assert parse_result.class_node["children"]["map_field"]["constructor"] is dict
    assert parse_result.class_node["children"]["some_flag"]["constructor"] is bool
    assert parse_result.class_node["children"]["some_flag"]["children"] is None
    assert parse_result.class_node["children"]["optional_default_value_field"]["constructor"] is Optional
    assert parse_result.is_context_typed is False


def test_function_schema_parser_pep604_top_level_optional_input() -> None:
    parse_result = parse_function_schema(pep604_top_level_input, "pep604_top_level_input", [], {})

    assert parse_result.function_schema["inputs"] == [
        {
            "name": "error",
            "dataType": EXPECTED_OPTIONAL_STRING,
            "required": True,
            "constraints": [],
        }
    ]
    assert parse_result.class_node is not None
    assert parse_result.class_node["children"] is not None
    assert parse_result.class_node["children"]["error"]["constructor"] is Optional
    assert parse_result.is_context_typed


def test_function_schema_parser_pep604_nested_direct_output() -> None:
    parse_result = parse_function_schema(pep604_nested_direct_output, "pep604_nested_direct_output", [], {})

    output_fields = parse_result.function_schema["output"]["single"]["dataType"]["anonymousCustomType"]["fields"]
    inner_fields = output_fields["inner"]["anonymousCustomType"]["fields"]
    assert inner_fields["name"] == EXPECTED_STRING
    assert inner_fields["error"] == EXPECTED_OPTIONAL_STRING


def test_function_schema_parser_pep604_nested_list_output() -> None:
    parse_result = parse_function_schema(pep604_nested_list_output, "pep604_nested_list_output", [], {})

    output_fields = parse_result.function_schema["output"]["single"]["dataType"]["anonymousCustomType"]["fields"]
    item_fields = output_fields["items"]["list"]["elementsType"]["anonymousCustomType"]["fields"]
    assert item_fields["name"] == EXPECTED_STRING
    assert item_fields["error"] == EXPECTED_OPTIONAL_STRING


def test_function_schema_parser_pep604_nested_input() -> None:
    parse_result = parse_function_schema(pep604_nested_input, "pep604_nested_input", [], {})

    input_data_type = parse_result.function_schema["inputs"][0]["dataType"]
    item_fields = input_data_type["list"]["elementsType"]["anonymousCustomType"]["fields"]
    assert item_fields["name"] == EXPECTED_STRING
    assert item_fields["error"] == EXPECTED_OPTIONAL_STRING


def test_function_schema_parser_optional_union_and_pep604_nested_lists_match() -> None:
    pep604_output = parse_function_schema(
        pep604_nested_list_output, "pep604_nested_list_output", [], {}
    ).function_schema["output"]
    optional_output = parse_function_schema(
        optional_nested_list_output, "optional_nested_list_output", [], {}
    ).function_schema["output"]
    union_output = parse_function_schema(union_nested_list_output, "union_nested_list_output", [], {}).function_schema[
        "output"
    ]

    assert pep604_output == optional_output == union_output


def test_function_schema_parser_unsupported_pep604_union() -> None:
    with pytest.raises(ValueError) as exc_info:
        parse_function_schema(unsupported_pep604_union_input, "unsupported_pep604_union_input", [], {})
    assert "Only unions with two types where one of the types is `None` are supported" in str(exc_info.value)


def test_function_schema_parser_no_type_hints() -> None:
    """Test 'happy' path, but on a function with no type hints"""
    parse_result = parse_function_schema(dummy_func_2, "dummy_func_2", [], {})
    assert parse_result.class_node is None
    assert parse_result.is_context_typed is False
    assert parse_result.function_schema == ComputeModuleFunctionSchema(
        functionName="dummy_func_2",
        inputs=[],
        output=FunctionOutputType(
            type="single",
            single={
                "dataType": {"type": "string", "string": {}},
            },
        ),
        ontologyProvenance=None,
    )


def test_function_schema_parser_context_output_only() -> None:
    """Test 'happy' path for a function that uses type hints only for the context & return type"""
    parse_result = parse_function_schema(dummy_func_3, "dummy_func_3", [], {})
    assert parse_result.class_node is None
    assert parse_result.is_context_typed
    assert parse_result.function_schema["functionName"] == "dummy_func_3"
    assert parse_result.function_schema["inputs"] == []
    assert parse_result.function_schema["output"] == EXPECTED_OUTPUT_3


def test_function_schema_parser_dict_witout_params() -> None:
    """Test 'happy' path for a function that uses type hints only for the context & return type"""
    with pytest.raises(ValueError) as exc_info:
        parse_function_schema(dummy_func_4, "dummy_func_4", [], {})
    assert "dict type hints must have type parameters provided" in str(exc_info.value)


def test_exception_no_type_hints() -> None:
    """CM function params should not have classes without type hints"""
    with pytest.raises(ValueError) as exc_info:
        parse_function_schema(dummy_no_type_hints, "dummy_no_type_hints", [], {})
    assert "type_hints set() must match init args" in str(exc_info.value)


def test_exception_no_init_hints() -> None:
    """CM function params should not have constructors without type hints"""
    with pytest.raises(ValueError) as exc_info:
        parse_function_schema(dummy_no_init_hints, "dummy_no_init_hints", [], {})
    assert "Custom Type BadClassNoInitHints should have init args type annotations" in str(exc_info.value)


def test_exception_args_init() -> None:
    """CM function params should not have constructors that use the `args` keyword"""
    with pytest.raises(ValueError) as exc_info:
        parse_function_schema(dummy_args_init, "dummy_args_init", [], {})
    assert "The __init__ method should not use *args" in str(exc_info.value)


def test_exception_kwargs_init() -> None:
    """CM function params should not have constructors that use the `kwargs` keyword"""
    with pytest.raises(ValueError) as exc_info:
        parse_function_schema(dummy_kwargs_init, "dummy_kwargs_init", [], {})
    assert "The __init__ method should not use **kwargs" in str(exc_info.value)


def test_function_schema_parser_generator_output() -> None:
    """Test 'happy' path for a function that uses type hints for generator return type"""
    parse_result = parse_function_schema(dummy_func_5, "dummy_func_5", [], {})
    assert parse_result.function_schema["functionName"] == "dummy_func_5"
    assert parse_result.function_schema["output"] == EXPECTED_OUTPUT_4
