#  Copyright 2024 Palantir Technologies, Inc.
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


from argparse import ArgumentParser, Namespace
from sys import argv
from typing import List


def get_raw_arguments() -> List[str]:
    """Get command line arguments passed into the compute module as-is"""
    return argv[1:]


def get_parsed_arguments() -> Namespace:
    """Get command line arguments passed into the compute module, parsed into an `argparse.Namespace` object.

    Note: for this to work properly you must pass args in a standard format, e.g. `--some-flag=test` or `-flag hello`.
    If you are using a non-standard format for args then use `get_raw_arguments` instead.
    """
    # Source: https://stackoverflow.com/a/37367814
    parser = ArgumentParser()
    _, unknown = parser.parse_known_args()
    for arg in unknown:
        if arg.startswith(("-", "--")):
            parser.add_argument(arg.split("=")[0])
    args = parser.parse_args()
    return args
