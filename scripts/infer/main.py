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

from scripts.infer.infer import infer


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
    print(
        json.dumps(
            infer(
                src_dir=arguments.source,
            )
        )
    )


if __name__ == "__main__":
    main()
