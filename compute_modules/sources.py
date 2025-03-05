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
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field


class MountedHttpConnectionConfig(BaseModel):
    model_config = ConfigDict(extra="ignore")

    url: str
    auth_headers: dict[str, str] = Field(alias="authHeaders", default_factory=dict)
    query_parameters: dict[str, str] = Field(alias="queryParameters", default_factory=dict)


class MountedSourceConfig(BaseModel):
    model_config = ConfigDict(extra="ignore")

    secrets: dict[str, str] = Field(alias="secrets", default_factory=dict)
    proxy_token: Optional[str] = Field(alias="proxyToken", default=None)
    http_connection_config: MountedHttpConnectionConfig = Field(alias="httpConnectionConfig")
    source_configuration: Any = Field(alias="sourceConfiguration", default=None)
    resolved_credentials: Any = Field(alias="resolvedCredentials", default=None)


_source_credentials = None
_source_configurations = None


def get_sources() -> Dict[str, Dict[str, str]]:
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
    return _source_credentials if _source_credentials is not None else {}


def get_source_configurations() -> Dict[str, MountedSourceConfig]:
    global _source_configurations
    if _source_configurations is None:
        configs_path = os.environ.get("SOURCE_CONFIGURATIONS_PATH")
        if configs_path:
            with open(configs_path, "r", encoding="utf-8") as fr:
                source_configs: Dict[str, MountedSourceConfig] = {
                    key: MountedSourceConfig.model_validate(value) for key, value in json.load(fr).items()
                }
            if isinstance(source_configs, dict):
                _source_configurations = source_configs
            else:
                raise ValueError("The JSON content is not a dictionary")
    return _source_configurations if _source_configurations is not None else {}


def get_source_secret(source_api_name: str, credential_name: str) -> Any:
    source_credentials = get_sources()
    return source_credentials.get(source_api_name, {}).get(credential_name)


def get_source_config(source_api_name: str) -> Any:
    source_config = get_source_configurations().get(source_api_name)
    return source_config.source_configuration if source_config else None
