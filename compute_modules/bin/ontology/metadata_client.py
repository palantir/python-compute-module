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


from typing import List, Tuple
from urllib.parse import urlparse

import requests

from compute_modules.bin.ontology._types import OntologyMetadataLinkTypeOuter, OntologyMetadataObjectTypeOuter


def _clean_url(url: str) -> str:
    parsed_url = urlparse(url)
    if not parsed_url.scheme:
        parsed_url = urlparse(f"https://{url}")
    return f"https://{parsed_url.netloc}"


class OntologyMetadataClient:
    bulk_load_entities_path = "{foundry_url}/ontology-metadata/api/ontology/ontology/bulkLoadEntities"

    def __init__(self, foundry_url: str, token: str):
        self.foundry_url = _clean_url(foundry_url)
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
        response.raise_for_status()
        result = response.json()
        return result["objectTypes"], result["linkTypes"]
