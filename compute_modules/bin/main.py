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
import json
import os
from typing import Optional

from compute_modules.bin.serialise import serialise

DEFAULT_ONTOLOGY_METADATA_CONFIG_FILENAME = "ontology_metadata_config.json"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source")
    parser.add_argument(
        "--ontology-metadata-config",
        required=False,
        dest="ontology_metadata_config_file",
        default=None,
    )
    arguments = parser.parse_args()
    api_name_type_id_mapping = _get_api_name_type_id_mapping(arguments.ontology_metadata_config_file)
    print(
        serialise(
            src_dir=arguments.source,
            api_name_type_id_mapping=api_name_type_id_mapping,
        )
    )


def _get_api_name_type_id_mapping(ontology_metadata_config_file: Optional[str]) -> dict[str, str]:
    if not ontology_metadata_config_file:
        ontology_metadata_config_file = os.path.join(os.getcwd(), DEFAULT_ONTOLOGY_METADATA_CONFIG_FILENAME)
    if not os.path.isfile(ontology_metadata_config_file):
        return {}
    with open(ontology_metadata_config_file) as f:
        config_data = json.load(f)
    return config_data.get("apiNameToTypeId", {})  # type: ignore[no-any-return]


if __name__ == "__main__":
    main()
