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

from dataclasses import dataclass
from typing import Set, TypedDict

from compute_modules.context import QueryContext
from compute_modules.function_registry.function_registry import add_function, add_functions
from compute_modules.function_registry.types import Byte
from compute_modules.startup import start_compute_module


@dataclass
class Mixed1Wrapper:
    value: int


@dataclass
class Mixed2Wrapper:
    value: Set[int]


@dataclass
class Mixed3Wrapper:
    value: Byte


class Mixed4Wrapper(TypedDict):
    name: str


def mixed_1(context: QueryContext, wrapper: Mixed1Wrapper) -> int:
    return wrapper.value


def mixed_2(context: QueryContext, wrapper: Mixed2Wrapper) -> Set[int]:
    return wrapper.value


def mixed_3(context: QueryContext, wrapper: Mixed3Wrapper) -> Byte:
    return wrapper.value


def mixed_4(context: QueryContext, wrapper: Mixed4Wrapper) -> str:
    return wrapper["name"]


if __name__ == "__main__":
    add_function(mixed_1)
    add_functions(mixed_2, mixed_3, mixed_4)
    start_compute_module()
