from dataclasses import dataclass
from typing import Dict, List, Optional, TypedDict

# Not all fields are present here because I manually defined these and am lazy;
# Ideally we'd be able to pull in conjure types here but I'm not aware of how to do so while
# staying within the bounds of what is allowed of OSS. Open to suggestions!


@dataclass(frozen=True)
class ObjectTypeMetadata:
    api_name: str
    type_id: str
    primary_key_id: str
    property_api_name_to_id: Dict[str, str]
    link_type_api_name_to_id: Dict[str, str]


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
