from typing import List, Tuple

import requests

from ._types import OntologyMetadataLinkTypeOuter, OntologyMetadataObjectTypeOuter


class OntologyMetadataClient:
    bulk_load_entities_path = "{foundry_url}/ontology-metadata/api/ontology/ontology/bulkLoadEntities"

    def __init__(self, foundry_url: str, token: str):
        self.foundry_url = foundry_url
        self.token = token

    def bulk_load_entities(
        self,
        object_type_rids: List[str],
        link_type_rids: List[str],
    ) -> Tuple[List[OntologyMetadataObjectTypeOuter], List[OntologyMetadataLinkTypeOuter]]:
        payload = {
            "objectTypes": [
                {"identifier": {"objectTypeRid": rid, "type": "objectTypeRid"}} for rid in object_type_rids
            ],
            "linkTypes": [{"identifier": {"linkTypeRid": rid, "type": "linkTypeRid"}} for rid in link_type_rids],
            "loadRedacted": True,
            "includeObjectTypesWithoutSearchableDatasources": True,
            "includeEntityMetadata": False,
        }
        response = requests.post(
            self.bulk_load_entities_path.format(foundry_url=self.foundry_url),
            headers={
                "Authorization": f"Bearer {self.token}",
            },
            json=payload,
        )
        result = response.json()
        return result["objectTypes"], result["linkTypes"]
