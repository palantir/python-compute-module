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

from scripts.infer.infer import infer
from scripts.ontology._config_path import get_ontology_config_file


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
    config_file_path = get_ontology_config_file(arguments.ontology_metadata_config_file)
    config_file_arg_provided = arguments.ontology_metadata_config_file is not None
    api_name_type_id_mapping = _get_api_name_type_id_mapping(config_file_path, config_file_arg_provided)
    print(
        json.dumps(
            infer(
                src_dir=arguments.source,
                api_name_type_id_mapping=api_name_type_id_mapping,
            )
        )
    )


def _get_api_name_type_id_mapping(config_file_path: str, config_file_arg_provided: bool) -> dict[str, str]:
    if not os.path.isfile(config_file_path):
        if config_file_arg_provided:
            raise ValueError(f"No file found at {config_file_arg_provided}")
        return {}
    with open(config_file_path) as f:
        config_data = json.load(f)
    return config_data.get("apiNameToTypeId", {})  # type: ignore[no-any-return]


if __name__ == "__main__":
    main()
