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
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class MountedHttpConnectionConfig:
    url: str
    auth_headers: Dict[str, str] = field(default_factory=dict)
    query_parameters: Dict[str, str] = field(default_factory=dict)

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "MountedHttpConnectionConfig":
        return MountedHttpConnectionConfig(
            url=data["url"], auth_headers=data.get("authHeaders", {}), query_parameters=data.get("queryParameters", {})
        )


@dataclass
class MountedSourceConfig:
    secrets: Dict[str, str] = field(default_factory=dict)
    http_connection_config: Optional[MountedHttpConnectionConfig] = None
    proxy_token: Optional[str] = None
    source_configuration: Any = None
    resolved_credentials: Any = None

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "MountedSourceConfig":
        http_conn_config_data = data.get("httpConnectionConfig")
        http_conn_config = (
            MountedHttpConnectionConfig.from_dict(http_conn_config_data) if http_conn_config_data is not None else None
        )
        return MountedSourceConfig(
            secrets=data.get("secrets", {}),
            proxy_token=data.get("proxyToken"),
            http_connection_config=http_conn_config,
            source_configuration=data.get("sourceConfiguration"),
            resolved_credentials=data.get("resolvedCredentials"),
        )


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


def get_source_configurations() -> Dict[str, Any]:
    global _source_configurations
    if _source_configurations is None:
        configs_path = os.environ.get("SOURCE_CONFIGURATIONS_PATH")
        if configs_path:
            with open(configs_path, "r", encoding="utf-8") as fr:
                raw_configs = json.load(fr)
            if isinstance(raw_configs, dict):
                _source_configurations = {
                    key: MountedSourceConfig.from_dict(value) for key, value in raw_configs.items()
                }
            else:
                raise ValueError("The JSON content is not a dictionary")
    configs = _source_configurations if _source_configurations is not None else {}
    return {key: value.source_configuration for key, value in configs.items()}


def get_source_secret(source_api_name: str, credential_name: str) -> Any:
    source_credentials = get_sources()
    return source_credentials.get(source_api_name, {}).get(credential_name)


def get_source_config(source_api_name: str) -> Any:
    return get_source_configurations().get(source_api_name)
