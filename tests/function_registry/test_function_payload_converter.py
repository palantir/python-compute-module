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

import pytest

from compute_modules.function_registry.function_payload_converter import convert_payload
from compute_modules.function_registry.function_schema_parser import parse_function_schema
from tests.function_registry.dummy_app import ChildClass, DummyInput, ParentClass, dummy_func_1

RAW_PAYLOAD = {
    "parent_class": {
        "some_flag": False,
        "some_value": 1234,
        "child": {"timestamp": 1725491095009, "some_value": 1.234, "another_optional_field": "something!"},
    },
    "optional_field": None,
    "set_field": ["2024-09-04", "2024-07-20", "1984-05-19"],
    "map_field": {"dmFsdWU=": "1.0", "dmFsdWUy": "2.0"},
    "some_flag": True,
}

BAD_RAW_PAYLOAD = {
    "parent_class": {
        "some_flag": False,
        "some_value": 1234,
        "child": {"timestamp": 1725491095009, "some_value": 1.234, "another_optional_field": "something!"},
    },
    "optional_field": None,
    "set_field": ["do", "re", "mi"],
    "map_field": {"dmFsdWU=": "1.0", "dmFsdWUy": "2.0"},
    "some_flag": True,
}


@pytest.fixture()
def expected_return_value() -> DummyInput:
    parent_dict = RAW_PAYLOAD["parent_class"]
    child_dict = parent_dict["child"]  # type: ignore[index, call-overload]
    child = ChildClass(
        timestamp=datetime.datetime.utcfromtimestamp(child_dict["timestamp"] / 1e3),  # type: ignore[index]
        some_value=child_dict["some_value"],  # type: ignore[index]
        another_optional_field=child_dict["another_optional_field"],  # type: ignore[index]
    )
    parent = ParentClass(
        some_flag=parent_dict["some_flag"],  # type: ignore[index, call-overload, arg-type]
        some_value=parent_dict["some_value"],  # type: ignore[index, call-overload, arg-type]
        child=child,
    )
    set_field = set([datetime.date.fromisoformat(d) for d in RAW_PAYLOAD["set_field"]])  # type: ignore[union-attr]
    map_field = {bytes(k, encoding="utf8"): decimal.Decimal(v) for k, v in RAW_PAYLOAD["map_field"].items()}  # type: ignore[union-attr, arg-type]
    return DummyInput(
        parent_class=parent,
        optional_field=RAW_PAYLOAD["optional_field"],  # type: ignore[arg-type]
        set_field=set_field,
        map_field=map_field,
        some_flag=RAW_PAYLOAD["some_flag"],  # type: ignore[arg-type]
    )


def test_convert_payload(
    expected_return_value: DummyInput,
) -> None:
    """Test the happy path for convert_payload"""
    parse_result = parse_function_schema(dummy_func_1, "dummy_func_1")
    assert parse_result.class_node
    processed_payload: DummyInput = convert_payload(RAW_PAYLOAD, parse_result.class_node)
    assert processed_payload is not None
    assert processed_payload.parent_class.child.__dict__ == expected_return_value.parent_class.child.__dict__
    assert processed_payload.parent_class.some_flag == expected_return_value.parent_class.some_flag
    assert processed_payload.parent_class.some_value == expected_return_value.parent_class.some_value
    assert processed_payload.optional_field == expected_return_value.optional_field
    assert processed_payload.set_field == expected_return_value.set_field
    assert processed_payload.map_field == expected_return_value.map_field
    assert processed_payload.some_flag == expected_return_value.some_flag


def test_convert_payload_error(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test the error path for convert_payload"""
    parse_result = parse_function_schema(dummy_func_1, "dummy_func_1")
    assert parse_result.class_node
    with pytest.raises(ValueError) as exc_info:
        convert_payload(BAD_RAW_PAYLOAD, parse_result.class_node)
    assert str(exc_info.value) == "Invalid isoformat string: 'do'"
    assert "Error converting do to type <built-in method fromisoformat" in caplog.text
