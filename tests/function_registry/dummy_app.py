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
from datetime import date, datetime
from decimal import Decimal
from typing import Dict, Optional, Set, Union

from compute_modules.context import QueryContext


@dataclass
class ChildClass:
    timestamp: datetime
    some_value: float
    another_optional_field: Union[str, None]


class ParentClass:
    some_flag: bool
    some_value: int
    child: ChildClass

    def __init__(self, some_flag: bool, some_value: int, child: ChildClass) -> None:
        self.some_flag = some_flag
        self.some_value = some_value
        self.child = child


@dataclass
class DummyInput:
    parent_class: ParentClass
    optional_field: Optional[str]
    set_field: Set[date]
    map_field: Dict[bytes, Decimal]
    some_flag: bool


@dataclass
class DummyOutput:
    res1: bool
    res2: Dict[str, float]


@dataclass
class ClassWithBareDict:
    dict_field: dict  # type: ignore[type-arg]


def dummy_func_1(context, event: DummyInput) -> DummyOutput:  # type: ignore[no-untyped-def]
    """Example function with type hints"""
    key_value = event.optional_field or "default"
    return DummyOutput(res1=True, res2={key_value: event.parent_class.child.some_value})


def dummy_func_2(context, event):  # type: ignore[no-untyped-def]
    """No type hints example"""
    return event["blah"]


def dummy_func_3(context: QueryContext, event) -> int:  # type: ignore[no-untyped-def]
    """Example function with type hint for context & return type only"""
    return 1


def dummy_func_4(context: QueryContext, event: ClassWithBareDict) -> int:
    """Example function with type hint for context & return type only"""
    return 1
