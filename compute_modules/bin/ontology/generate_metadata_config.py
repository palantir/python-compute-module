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


import argparse
import dataclasses
import json
from typing import Dict

from compute_modules.bin.ontology._config_path import get_ontology_config_file
from compute_modules.bin.ontology._types import ObjectTypeMetadata
from compute_modules.bin.ontology.metadata_loader import load_object_type_metadata


def write_inference_metadata(
    ontology_metadata: Dict[str, ObjectTypeMetadata],
    output_file: str,
) -> None:
    config = {"apiNameToTypeId": {key: value.objectTypeId for key, value in ontology_metadata.items()}}
    with open(output_file, "w") as f:
        json.dump(config, f)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--object-type-rid",
        required=False,
        help="Object type rid of ontology objects to import the metadata for",
        nargs="*",
        dest="object_type_rids",
        default=[],
    )
    parser.add_argument(
        "--link-type-rid",
        required=False,
        help="Link type rid of ontology links to import the metadata for",
        nargs="*",
        dest="link_type_rids",
        default=[],
    )
    parser.add_argument(
        "-t",
        "--token",
        required=True,
        help="Foundry token",
        default=None,
    )
    parser.add_argument(
        "--foundry-url",
        required=True,
        help="Foundry stack url",
        default=None,
    )
    parser.add_argument(
        "--ontology-metadata-config",
        required=False,
        help="Path to file for where to write the output configuration",
        dest="ontology_metadata_config_file",
        default=None,
    )
    arguments = parser.parse_args()
    output_file = get_ontology_config_file(arguments.ontology_metadata_config_file)
    ontology_metadata = load_object_type_metadata(
        foundry_url=arguments.foundry_url,
        token=arguments.token,
        object_type_rids=arguments.object_type_rids,
        link_type_rids=arguments.link_type_rids,
    )
    write_inference_metadata(
        ontology_metadata=ontology_metadata.objectMetadata,
        output_file=output_file,
    )
    print(json.dumps(dataclasses.asdict(ontology_metadata)))


if __name__ == "__main__":
    main()
