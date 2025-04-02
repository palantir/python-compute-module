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

import functools
from typing import Any, Callable, Dict, List

from compute_modules.function_registry.function_schema_parser import parse_function_schema
from compute_modules.function_registry.types import ComputeModuleFunctionSchema


class Function(Callable[..., Any]):  # type: ignore[misc]
    def __init__(
        self,
        function: Callable[..., Any],
        edits: List[Any],
    ):
        self.function = function
        self.edits = edits
        functools.update_wrapper(self, function)

    def __call__(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        return self.function(*args, **kwargs)

    def get_function_schema(
        self,
        api_name_type_id_mapping: Dict[str, str],
    ) -> ComputeModuleFunctionSchema:
        return parse_function_schema(
            function_ref=self.function,
            function_name=self.function.__name__,
            edits=self.edits,
            api_name_type_id_mapping=api_name_type_id_mapping,
            throw_on_missing_type_id=True,
        ).function_schema
