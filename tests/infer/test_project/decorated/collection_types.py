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

from typing import Dict, List, Set

from compute_modules.annotations import function
from compute_modules.context import QueryContext
from tests.infer.test_project._types import DummyOntologyType, OntologyEdit


@function
def return_list(context: QueryContext, event) -> List[str]:  # type: ignore[no-untyped-def]
    return ["Hello", "World"]


@function
def return_set(context: QueryContext, event) -> Set[str]:  # type: ignore[no-untyped-def]
    return {"Hello", "World"}


@function
def return_dict(context: QueryContext, event) -> Dict[str, str]:  # type: ignore[no-untyped-def]
    return {"Hello": "World"}


@function(edits=[DummyOntologyType])
def ontology_add_function(context: QueryContext, event) -> list[OntologyEdit]:  # type: ignore[no-untyped-def]
    return []
