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
import os
from functools import cache

from ._api import SOURCE_CONFIGURATIONS_PATH, SOURCE_CREDENTIALS_PATH, MountedSourceConfig


@cache
def get_mounted_source_secrets() -> dict[str, dict[str, str]]:
    creds_path = os.environ.get(SOURCE_CREDENTIALS_PATH)
    if not creds_path:
        return {}
    data = {}
    with open(creds_path, "r", encoding="utf-8") as fr:
        data.update(json.load(fr))
    if isinstance(data, dict):
        return data
    else:
        raise ValueError("The JSON content is not a dictionary")


@cache
def get_mounted_sources() -> dict[str, MountedSourceConfig]:
    mounted_sources = {}
    configs_path = os.environ.get(SOURCE_CONFIGURATIONS_PATH)
    if configs_path:
        with open(configs_path, "r", encoding="utf-8") as fr:
            raw_configs = json.load(fr)
        if isinstance(raw_configs, dict):
            mounted_sources = {key: MountedSourceConfig.from_dict(value) for key, value in raw_configs.items()}
        else:
            raise ValueError("The JSON content is not a dictionary")
    return mounted_sources
