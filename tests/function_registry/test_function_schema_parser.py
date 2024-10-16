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


from typing import Optional

import pytest

from compute_modules.function_registry.function_schema_parser import parse_function_schema
from compute_modules.function_registry.types import ComputeModuleFunctionSchema, FunctionOutputType
from tests.function_registry.dummy_app import (
    DummyInput,
    ParentClass,
    dummy_func_1,
    dummy_func_2,
    dummy_func_3,
    dummy_func_4,
)
from tests.function_registry.dummy_app_with_issues import (
    dummy_args_init,
    dummy_kwargs_init,
    dummy_no_init_hints,
    dummy_no_type_hints,
)

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
    {"name": "some_flag", "dataType": {"boolean": {}, "type": "boolean"}, "required": True, "constraints": []},
]


def test_function_schema_parser() -> None:
    """Test the happy path for parse_function_schemas_from_module"""
    parse_result = parse_function_schema(dummy_func_1, "dummy_func_1")
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
    assert parse_result.is_context_typed is False


def test_function_schema_parser_no_type_hints() -> None:
    """Test 'happy' path, but on a function with no type hints"""
    parse_result = parse_function_schema(dummy_func_2, "dummy_func_2")
    assert parse_result.class_node is None
    assert parse_result.is_context_typed is False
    assert parse_result.function_schema == ComputeModuleFunctionSchema(
        functionName="dummy_func_2",
        inputs=[],
        output=FunctionOutputType(
            type="single",
            single={
                "dataType": {
                    "type": "string",
                },
            },
        ),
    )


def test_function_schema_parser_context_output_only() -> None:
    """Test 'happy' path for a function that uses type hints only for the context & return type"""
    parse_result = parse_function_schema(dummy_func_3, "dummy_func_3")
    assert parse_result.class_node is None
    assert parse_result.is_context_typed
    assert parse_result.function_schema["functionName"] == "dummy_func_3"
    assert parse_result.function_schema["inputs"] == []
    assert parse_result.function_schema["output"] == EXPECTED_OUTPUT_3


def test_function_schema_parser_dict_witout_params() -> None:
    """Test 'happy' path for a function that uses type hints only for the context & return type"""
    with pytest.raises(ValueError) as exc_info:
        parse_function_schema(dummy_func_4, "dummy_func_4")
    assert "dict type hints must have type parameters provided" in str(exc_info.value)


def test_exception_no_type_hints() -> None:
    """CM function params should not have classes without type hints"""
    with pytest.raises(ValueError) as exc_info:
        parse_function_schema(dummy_no_type_hints, "dummy_no_type_hints")
    assert "type_hints set() must match init args" in str(exc_info.value)


def test_exception_no_init_hints() -> None:
    """CM function params should not have constructors without type hints"""
    with pytest.raises(ValueError) as exc_info:
        parse_function_schema(dummy_no_init_hints, "dummy_no_init_hints")
    assert "Custom Type BadClassNoInitHints should have init args type annotations" in str(exc_info.value)


def test_exception_args_init() -> None:
    """CM function params should not have constructors that use the `args` keyword"""
    with pytest.raises(ValueError) as exc_info:
        parse_function_schema(dummy_args_init, "dummy_args_init")
    assert "The __init__ method should not use *args" in str(exc_info.value)


def test_exception_kwargs_init() -> None:
    """CM function params should not have constructors that use the `kwargs` keyword"""
    with pytest.raises(ValueError) as exc_info:
        parse_function_schema(dummy_kwargs_init, "dummy_kwargs_init")
    assert "The __init__ method should not use **kwargs" in str(exc_info.value)


def test_exception_kwargs_init() -> None:
    """CM function params should not have constructors that use the `kwargs` keyword"""
    with pytest.raises(ValueError) as exc_info:
        parse_function_schema(dummy_kwargs_init, "dummy_kwargs_init")
    assert "The __init__ method should not use **kwargs" in str(exc_info.value)
