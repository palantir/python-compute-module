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


from collections import defaultdict
from typing import Dict, List

from compute_modules.bin.ontology._types import (
    ObjectTypeMetadata,
    OntologyMetadataLinkTypeOuter,
    OntologyMetadataObjectTypeOuter,
    RuntimeMetadata,
)
from compute_modules.bin.ontology.metadata_client import OntologyMetadataClient


def load_object_type_metadata(
    foundry_url: str,
    token: str,
    object_type_rids: List[str],
    link_type_rids: List[str],
) -> RuntimeMetadata:
    client = OntologyMetadataClient(foundry_url=foundry_url, token=token)
    object_types, link_types = client.bulk_load_entities(
        object_type_rids=object_type_rids,
        link_type_rids=link_type_rids,
    )
    link_types_for_object = _get_link_types(link_types=link_types)
    object_type_metadata = _get_object_type_metadata(
        object_types=object_types, link_types_for_object=link_types_for_object
    )
    return RuntimeMetadata(objectMetadata=object_type_metadata)


def _get_object_type_metadata(
    object_types: List[OntologyMetadataObjectTypeOuter],
    link_types_for_object: Dict[str, Dict[str, str]],
) -> Dict[str, ObjectTypeMetadata]:
    object_type_metadata = {}
    for object_type in object_types:
        object_type_details = object_type["objectType"]
        if object_type_details["apiName"] in object_type_metadata:
            raise ValueError(f"Duplicate api name found in ontology metadata: {object_type_details['apiName']}")
        primary_key_id = object_type_details["propertyTypes"][object_type_details["primaryKeys"][0]]["id"]
        object_rid = object_type_details["rid"]
        object_type_metadata[object_type_details["apiName"]] = ObjectTypeMetadata(
            objectTypeApiName=object_type_details["apiName"],
            objectTypeId=object_type_details["id"],
            primaryKeyPropertyId=primary_key_id,
            properties={value["apiName"]: value["id"] for _, value in object_type_details["propertyTypes"].items()},
            links=link_types_for_object[object_rid],
        )
    return object_type_metadata


def _get_link_types(link_types: List[OntologyMetadataLinkTypeOuter]) -> Dict[str, Dict[str, str]]:
    link_types_for_object: Dict[str, Dict[str, str]] = defaultdict(dict)
    for link_type in link_types:
        link_type_id = link_type["linkType"]["id"]
        link_type_definition = link_type["linkType"]["definition"].get("manyToMany")
        # AFAIK oneToMany link edits are expressed as direct edits
        # on the ontology object so not implementing oneToMany for now
        if not link_type_definition:
            continue
        object_a_api_name = link_type_definition["objectTypeAToBLinkMetadata"].get("apiName")
        if object_a_api_name:
            link_types_for_object[link_type_definition["objectTypeRidA"]][object_a_api_name] = link_type_id
        object_b_api_name = link_type_definition["objectTypeBToALinkMetadata"].get("apiName")
        if object_b_api_name:
            link_types_for_object[link_type_definition["objectTypeRidB"]][object_b_api_name] = link_type_id
    return link_types_for_object
