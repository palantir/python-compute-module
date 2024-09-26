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


from typing import TypedDict


# Failure case 1
class BadClassNoTypeHints:
    def __init__(self, arg1: str, arg2: int):
        self.arg1 = arg1
        self.arg2 = arg2


class NoTypeHintsWrapper(TypedDict):
    param: BadClassNoTypeHints


def dummy_no_type_hints(context, event: NoTypeHintsWrapper) -> int:  # type: ignore[no-untyped-def]
    return 1


# Failure case 2
class BadClassNoInitHints:
    arg1: str
    arg2: int

    def __init__(self, arg1, arg2) -> None:  # type: ignore[no-untyped-def]
        self.arg1 = arg1
        self.arg2 = arg2


class NoInitHintsWrapper(TypedDict):
    param: BadClassNoInitHints


def dummy_no_init_hints(context, event: NoInitHintsWrapper) -> int:  # type: ignore[no-untyped-def]
    return 1


# Failure case 3
class BadClassArgsInit:
    arg1: str
    arg2: int

    def __init__(self, arg1: str, arg2: int, *args) -> None:  # type: ignore[no-untyped-def]
        self.arg1 = arg1
        self.arg2 = arg2


class ArgsInitWrapper(TypedDict):
    param: BadClassArgsInit


def dummy_args_init(context, event: ArgsInitWrapper) -> int:  # type: ignore[no-untyped-def]
    return 1


# Failure case 4
class BadClassKwargsInit:
    arg1: str
    arg2: int

    def __init__(self, arg1: str, arg2: int, **kwargs) -> None:  # type: ignore[no-untyped-def]
        self.arg1 = kwargs["arg1"]
        self.arg2 = kwargs["arg2"]


class KwargsInitWrapper(TypedDict):
    param: BadClassKwargsInit


def dummy_kwargs_init(context, event: KwargsInitWrapper) -> int:  # type: ignore[no-untyped-def]
    return 1
