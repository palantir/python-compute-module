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


from dataclasses import dataclass, field
from typing import Any, Optional

# Env var constants
SOURCE_CONFIGURATIONS_PATH = "SOURCE_CONFIGURATIONS_PATH"
SOURCE_CREDENTIALS_PATH = "SOURCE_CREDENTIALS"
SERVICE_DISCOVERY_PATH = "FOUNDRY_SERVICE_DISCOVERY_V2"
DEFAULT_CA_BUNDLE = "DEFAULT_CA_PATH"


JAVA_OFFSET_DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


@dataclass
class MountedClientCertificate:
    pem_certificate: str
    pem_private_key: str

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "MountedClientCertificate":
        return MountedClientCertificate(pem_certificate=data["pemCertificate"], pem_private_key=data["pemPrivateKey"])


@dataclass
class MountedHttpConnectionConfig:
    url: str
    auth_headers: dict[str, str] = field(default_factory=dict)
    query_parameters: dict[str, str] = field(default_factory=dict)

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "MountedHttpConnectionConfig":
        return MountedHttpConnectionConfig(
            url=data["url"], auth_headers=data.get("authHeaders", {}), query_parameters=data.get("queryParameters", {})
        )


@dataclass
class MountedSourceConfig:
    secrets: dict[str, str] = field(default_factory=dict)
    http_connection_config: Optional[MountedHttpConnectionConfig] = None
    proxy_token: Optional[str] = None
    source_configuration: Any = None
    resolved_credentials: Any = None
    client_certificate: Optional[MountedClientCertificate] = None
    server_certificates: dict[str, str] = field(default_factory=dict)

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "MountedSourceConfig":
        http_conn_config_data = data.get("httpConnectionConfig")
        http_conn_config = (
            MountedHttpConnectionConfig.from_dict(http_conn_config_data) if http_conn_config_data is not None else None
        )

        client_certificate_data = data.get("clientCertificate")
        client_certificate = (
            MountedClientCertificate.from_dict(client_certificate_data) if client_certificate_data is not None else None
        )

        return MountedSourceConfig(
            secrets=data.get("secrets", {}),
            proxy_token=data.get("proxyToken"),
            http_connection_config=http_conn_config,
            source_configuration=data.get("sourceConfiguration"),
            resolved_credentials=data.get("resolvedCredentials"),
            client_certificate=client_certificate,
            server_certificates=data.get("serverCertificates", {}),
        )
