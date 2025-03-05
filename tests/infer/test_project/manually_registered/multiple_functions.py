#  Copyright 2025 Palantir Technologies, Inc.
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
from dataclasses import dataclass
from typing import List

from compute_modules.context import QueryContext
from compute_modules.function_registry.function_registry import add_functions
from compute_modules.startup import start_compute_module


@dataclass
class Point:
    x: float
    y: float
    z: float


@dataclass
class Message:
    message: str
    from_id: int
    to_id: int
    timestamp: datetime.datetime


@dataclass
class Messages:
    messages: List[Message]


@dataclass
class MultipleEventWrapper:
    points: List[Point]
    messages: Messages


@dataclass
class Number:
    value: int


def return_complex_in_main(context: QueryContext, event: MultipleEventWrapper) -> str:
    return f"Points: {event.points}, Messages: {event.messages}"


def return_number_in_main(context: QueryContext, number: Number) -> Number:
    return number.value  # type: ignore[return-value]


if __name__ == "__main__":
    add_functions(return_complex_in_main, return_number_in_main)
    start_compute_module()
