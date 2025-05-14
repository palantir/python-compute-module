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

import os
from datetime import datetime
from functools import cache
from typing import Any, Optional

from ._api import DEFAULT_CA_BUNDLE, JAVA_OFFSET_DATETIME_FORMAT, SERVICE_DISCOVERY_PATH, MountedSourceConfig
from ._back_compat import get_mounted_sources


def __get_on_prem_proxy_service_uris() -> list[str]:
    try:
        import yaml  # type: ignore[import-untyped]
    except ImportError:
        raise ImportError(
            "the sources extras is not installed. Please install it with `pip install foundry-compute-modules[sources]`"
        )

    with open(os.environ[SERVICE_DISCOVERY_PATH], "r") as f:
        service_discovery = yaml.safe_load(f)
        on_prem_proxy_uris: list[str] = service_discovery.get("on_prem_proxy", [])
        return on_prem_proxy_uris


@cache
def get_source(source_api_name: str):  # type: ignore[no-untyped-def]
    try:
        from external_systems.sources import (
            AwsCredentials,
            ClientCertificate,
            HttpsConnectionParameters,
            Source,
            SourceCredentials,
            SourceParameters,
        )
    except ImportError:
        raise ImportError(
            "the sources extras is not installed. Please install it with `pip install foundry-compute-modules[sources]`"
        )

    def convert_resolved_source_credentials(
        credentials: Optional[Any],
    ) -> Optional[SourceCredentials]:
        if credentials is None:
            return None

        cloud_credentials = credentials.get("cloudCredentials", None)
        if cloud_credentials is None:
            return None

        aws_credentials = cloud_credentials.get("awsCredentials", None)
        if aws_credentials is None:
            return None

        session_credentials = aws_credentials.get("sessionCredentials", None)
        if session_credentials is not None:
            return AwsCredentials(
                access_key_id=session_credentials.get("accessKeyId"),
                secret_access_key=session_credentials.get("secretAccessKey"),
                session_token=session_credentials.get("sessionToken"),
                expiration=datetime.strptime(session_credentials.get("expiration"), JAVA_OFFSET_DATETIME_FORMAT),
            )

        basic_credentials = aws_credentials.get("basicCredentials", None)
        if basic_credentials is not None:
            return AwsCredentials(
                access_key_id=basic_credentials.get("accessKeyId"),
                secret_access_key=basic_credentials.get("secretAccessKey"),
            )

        return None

    mounted_source: Optional[MountedSourceConfig] = get_mounted_sources().get(source_api_name, None)
    if mounted_source is None:
        raise ValueError(f"Source {source_api_name} not found")

    client_certificate = (
        ClientCertificate(
            pem_certificate=mounted_source.client_certificate.pem_certificate,
            pem_private_key=mounted_source.client_certificate.pem_private_key,
        )
        if mounted_source.client_certificate is not None
        else None
    )

    source_parameters = SourceParameters(
        secrets=mounted_source.secrets,
        proxy_token=mounted_source.proxy_token,
        https_connections=(
            {
                "http_connection": HttpsConnectionParameters(
                    url=mounted_source.http_connection_config.url,
                    headers=mounted_source.http_connection_config.auth_headers,
                    query_params=mounted_source.http_connection_config.query_parameters,
                )
            }
            if mounted_source.http_connection_config is not None
            else {}
        ),
        server_certificates=mounted_source.server_certificates,
        client_certificate=client_certificate,
        resolved_source_credentials=convert_resolved_source_credentials(mounted_source.resolved_credentials),
    )

    on_prem_proxy_service_uris = __get_on_prem_proxy_service_uris()

    return Source(
        source_parameters=source_parameters,
        source_configuration=mounted_source.source_configuration,
        on_prem_proxy_service_uris=on_prem_proxy_service_uris,
        egress_proxy_service_uris=[],
        egress_proxy_token=None,
        ca_bundle_path=os.environ.get(DEFAULT_CA_BUNDLE),
    )
