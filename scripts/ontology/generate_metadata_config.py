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

from compute_modules.ontology._config_path import get_ontology_config_file
from compute_modules.ontology.generate_metadata_config import generate_metadata_config


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source")
    parser.add_argument(
        "--object-type-rid",
        required=False,
        nargs="*",
        dest="object_type_rids",
        default=[],
    )
    parser.add_argument(
        "--link-type-rid",
        required=False,
        nargs="*",
        dest="link_type_rids",
        default=[],
    )
    parser.add_argument(
        "-t",
        "--token",
        required=False,
        default=None,
    )
    parser.add_argument(
        "--foundry-url",
        required=False,
        default=None,
    )
    parser.add_argument(
        "--ontology-metadata-config",
        required=False,
        dest="ontology_metadata_config_file",
        default=None,
    )
    arguments = parser.parse_args()
    output_file = get_ontology_config_file(arguments.ontology_metadata_config_file)
    print("Generating config file...")
    generate_metadata_config(
        foundry_url=arguments.foundry_url,
        token=arguments.token,
        object_type_rids=arguments.object_type_rids,
        link_type_rids=arguments.link_type_rids,
        output_file=output_file,
    )
    print(f"Wrote config file to {output_file}")


if __name__ == "__main__":
    main()
