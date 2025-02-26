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

from compute_modules.context import QueryContext
from compute_modules.annotations import function
from compute_modules.function_registry.types import Byte, Double, Long, Short

from dataclasses import dataclass
from compute_modules.function_registry.types import Long

@dataclass
class LongPayload:
    value: Long

@function
def return_long(context: QueryContext, event: LongPayload) -> Long:
    return event.value

@dataclass
class ShortPayload:
    value: Short

@function
def return_short(context: QueryContext, event: ShortPayload) -> Short:
    return event.value

@dataclass
class DoublePayload:
    value: Double

@function
def return_double(context: QueryContext, event: DoublePayload) -> Double:
    return event.value

@dataclass
class BytePayload:
    value: Byte

@function
def return_byte(context: QueryContext, event: BytePayload) -> Byte:
    return event.value
