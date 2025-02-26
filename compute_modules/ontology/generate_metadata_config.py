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


import json
from typing import Dict, List

from ._types import ObjectTypeMetadata
from .metadata_loader import load_object_type_metadata


def generate_metadata_config(
    foundry_url: str,
    token: str,
    object_type_rids: List[str],
    link_type_rids: List[str],
    output_file: str,
) -> None:
    ontology_metadata = load_object_type_metadata(
        foundry_url=foundry_url,
        token=token,
        object_type_rids=object_type_rids,
        link_type_rids=link_type_rids,
    )
    config = {"apiNameToTypeId": _get_api_name_type_id_mapping(ontology_metadata)}
    with open(output_file, "w") as f:
        json.dump(config, f)


def _get_api_name_type_id_mapping(
    ontology_metadata: Dict[str, ObjectTypeMetadata],
) -> Dict[str, str]:
    res = {}
    for metadata in ontology_metadata.values():
        if metadata.api_name in res:
            raise ValueError(f"Duplicate api name found in ontology metadata: {metadata.api_name}")
        res[metadata.api_name] = metadata.type_id
    return res
