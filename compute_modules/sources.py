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


import json
import os
from typing import Any

_source_credentials = None


def get_sources() -> Any:
    global _source_credentials
    if _source_credentials is None:
        creds_path = os.environ.get("SOURCE_CREDENTIALS")
        if creds_path:
            with open(creds_path, "r", encoding="utf-8") as fr:
                data = json.load(fr)
            if isinstance(data, dict):
                _source_credentials = data
            else:
                raise ValueError("The JSON content is not a dictionary")
    return _source_credentials


def get_source_secret(source_api_name: str, credential_name: str) -> Any:
    source_credentials = get_sources()
    return source_credentials.get(source_api_name, {}).get(credential_name)
