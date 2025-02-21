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

from compute_modules.bin.serialise import serialise


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
    )
    arguments = parser.parse_args()
    print(serialise(src_dir=arguments.source))


if __name__ == "__main__":
    main()
