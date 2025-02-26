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


from typing import Any, NamedTuple, Optional, Union


class DummyOntologyType:
    @staticmethod
    def api_name() -> str:
        return "DummyOntologyType"


class ObjectLocator(NamedTuple):
    object_api_name: str
    primary_key: Any


class AddObject(NamedTuple):
    locator: ObjectLocator
    fields: dict[str, Any]


class ModifyObject(NamedTuple):
    locator: ObjectLocator
    fields: dict[str, Optional[Any]]


class DeleteObject(NamedTuple):
    locator: ObjectLocator


class AddLink(NamedTuple):
    relationship_api_name: str
    source: ObjectLocator
    target: ObjectLocator


class RemoveLink(NamedTuple):
    relationship_api_name: str
    source: ObjectLocator
    target: ObjectLocator


OntologyEdit = Union[AddObject, ModifyObject, DeleteObject, AddLink, RemoveLink]
