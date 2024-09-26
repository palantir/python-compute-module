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


from compute_modules.client.internal_query_client import InternalQueryService
from compute_modules.function_registry.function_registry import (
    FUNCTION_SCHEMA_CONVERSIONS,
    FUNCTION_SCHEMAS,
    IS_FUNCTION_CONTEXT_TYPED,
    REGISTERED_FUNCTIONS,
)


def start_compute_module() -> None:
    """Starts a Compute Module that will Poll for jobs indefinitely"""
    query_client = InternalQueryService(
        registered_functions=REGISTERED_FUNCTIONS,
        function_schemas=FUNCTION_SCHEMAS,
        function_schema_conversions=FUNCTION_SCHEMA_CONVERSIONS,
        is_function_context_typed=IS_FUNCTION_CONTEXT_TYPED,
    )
    query_client.start()
