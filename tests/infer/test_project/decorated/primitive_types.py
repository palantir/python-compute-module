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
import decimal

from dataclasses import dataclass
from compute_modules.context import QueryContext
from compute_modules.annotations import function


@dataclass
class BytesWrapper:
    value: bytes

@function
def return_bytes(context: QueryContext, wrapper: BytesWrapper) -> bytes:
    return wrapper.value


@dataclass
class BoolWrapper:
    value: bool

@function
def return_bool(context: QueryContext, wrapper: BoolWrapper) -> bool:
    return wrapper.value


@dataclass
class DateWrapper:
    value: datetime.date

@function
def return_date(context: QueryContext, wrapper: DateWrapper) -> datetime.date:
    return wrapper.value


@dataclass
class DecimalWrapper:
    value: decimal.Decimal

@function
def return_decimal(context: QueryContext, wrapper: DecimalWrapper) -> decimal.Decimal:
    return wrapper.value


@dataclass
class FloatWrapper:
    value: float

@function
def return_float(context: QueryContext, wrapper: FloatWrapper) -> float:
    return wrapper.value


@dataclass
class IntWrapper:
    value: int

@function
def return_int(context: QueryContext, wrapper: IntWrapper) -> int:
    return wrapper.value


@dataclass
class StrWrapper:
    value: str

@function
def return_str(context: QueryContext, wrapper: StrWrapper) -> str:
    return wrapper.value


@dataclass
class DatetimeWrapper:
    value: datetime.datetime

@function
def return_datetime(context: QueryContext, wrapper: DatetimeWrapper) -> datetime.datetime:
    return wrapper.value
