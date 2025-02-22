from collections import defaultdict
from typing import Dict, List

from ._types import ObjectTypeMetadata, OntologyMetadataLinkTypeOuter, OntologyMetadataObjectTypeOuter
from .metadata_client import OntologyMetadataClient


def load_object_type_metadata(
    foundry_url: str,
    token: str,
    object_type_rids: List[str],
    link_type_rids: List[str],
) -> Dict[str, ObjectTypeMetadata]:
    client = OntologyMetadataClient(foundry_url=foundry_url, token=token)
    object_types, link_types = client.bulk_load_entities(
        object_type_rids=object_type_rids,
        link_type_rids=link_type_rids,
    )
    link_types_for_object = _get_link_types(link_types=link_types)
    return _get_object_type_metadata(object_types=object_types, link_types_for_object=link_types_for_object)


def _get_object_type_metadata(
    object_types: List[OntologyMetadataObjectTypeOuter],
    link_types_for_object: Dict[str, Dict[str, str]],
) -> Dict[str, ObjectTypeMetadata]:
    object_type_metadata = {}
    for object_type in object_types:
        object_type_details = object_type["objectType"]
        primary_key_id = object_type_details["propertyTypes"][object_type_details["primaryKeys"][0]]["id"]
        object_rid = object_type_details["rid"]
        object_type_metadata[object_rid] = ObjectTypeMetadata(
            api_name=object_type_details["apiName"],
            type_id=object_type_details["id"],
            primary_key_id=primary_key_id,
            property_api_name_to_id={
                value["apiName"]: value["id"] for _, value in object_type_details["propertyTypes"].items()
            },
            link_type_api_name_to_id=link_types_for_object[object_rid],
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
