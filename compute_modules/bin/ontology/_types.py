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
from typing import Dict, List, Optional, TypedDict

# Not all fields are present here because I manually defined these and am lazy;
# Ideally we'd be able to pull in conjure types here but I'm not aware of how to do so while
# staying within the bounds of what is allowed of OSS. Open to suggestions!


@dataclass(frozen=True)
class ObjectTypeMetadata:
    objectTypeApiName: str
    objectTypeId: str
    primaryKeyPropertyId: str
    properties: Dict[str, str]
    links: Dict[str, str]


@dataclass(frozen=True)
class RuntimeMetadata:
    objectMetadata: Dict[str, ObjectTypeMetadata]


# Object types
class ObjectyPropertyType(TypedDict):
    id: str
    rid: str
    apiName: str


class OntologyMetadataObjectType(TypedDict):
    rid: str
    apiName: str
    id: str
    propertyTypes: Dict[str, ObjectyPropertyType]
    primaryKeys: List[str]


class OntologyMetadataObjectTypeOuter(TypedDict):
    objectType: OntologyMetadataObjectType


# Link types
class ManyToManyMetadata(TypedDict):
    apiName: str


class LinkTypeManyToMany(TypedDict):
    objectTypeRidA: str
    objectTypeRidB: str
    objectTypeAToBLinkMetadata: ManyToManyMetadata
    objectTypeBToALinkMetadata: ManyToManyMetadata


class OntologyLinkTypeDefinition(TypedDict):
    type: str
    manyToMany: Optional[LinkTypeManyToMany]


class OntologyMetadataLinkType(TypedDict):
    id: str
    definition: OntologyLinkTypeDefinition


class OntologyMetadataLinkTypeOuter(TypedDict):
    linkType: OntologyMetadataLinkType
