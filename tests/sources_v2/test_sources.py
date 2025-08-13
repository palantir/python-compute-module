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
from datetime import datetime
from pathlib import Path
from typing import Any
from unittest import mock

import pytest
from external_systems.sources import AwsCredentials, GcpOauthCredentials, OauthCredentials, Source

from compute_modules.sources_v2 import get_source
from compute_modules.sources_v2._api import (
    JAVA_OFFSET_DATETIME_FORMAT,
    SERVICE_DISCOVERY_PATH,
    SOURCE_CONFIGURATIONS_PATH,
    MountedHttpConnectionConfig,
    MountedSourceConfig,
)
from compute_modules.sources_v2._back_compat import get_mounted_sources


@pytest.fixture
def mock_source_config_file(tmp_path: Path) -> Path:
    config_file = tmp_path / "source_config.json"
    return config_file


@pytest.fixture
def mock_service_discovery_file(tmp_path: Path) -> Path:
    service_file = tmp_path / "service_discovery.json"
    service_file.write_text(json.dumps({"on_prem_proxy": ["https://proxy1.example.com", "https://proxy2.example.com"]}))
    return service_file


@pytest.fixture(autouse=True)
def clear_cache() -> Any:
    yield
    get_source.cache_clear()
    get_mounted_sources.cache_clear()


def test_get_source_with_http_connection(mock_source_config_file: Path, mock_service_discovery_file: Path) -> None:
    source_config = {
        "test_source": {
            "secrets": {"SECRET_KEY": "secret_value"},
            "httpConnectionConfig": {
                "url": "https://example.com",
                "authHeaders": {"Authorization": "Bearer token"},
                "queryParameters": {"param": "value"},
            },
            "proxyToken": "proxy_token_123",
            "sourceConfiguration": {"type": "test_type"},
            "resolvedCredentials": {"cloudCredentials": None},
        }
    }

    mock_source_config_file.write_text(json.dumps(source_config))

    with mock.patch.dict(
        os.environ,
        {
            SOURCE_CONFIGURATIONS_PATH: str(mock_source_config_file),
            SERVICE_DISCOVERY_PATH: str(mock_service_discovery_file),
        },
    ):
        source = get_source("test_source")

        assert isinstance(source, Source)
        assert source.get_secret("SECRET_KEY") == "secret_value"
        https_conn = source.get_https_connection()
        assert https_conn.url == "https://example.com"
        assert https_conn.headers == {"Authorization": "Bearer token"}
        assert https_conn.query_params == {"param": "value"}
        assert source.source_configuration == {"type": "test_type"}
        assert source.get_https_proxy_uri() in [
            "https://user:proxy_token_123@proxy1.example.com",
            "https://user:proxy_token_123@proxy2.example.com",
        ]


def test_get_source_without_http_connection(mock_source_config_file: Path, mock_service_discovery_file: Path) -> None:
    source_config = {
        "test_source": {
            "secrets": {"SECRET_KEY": "secret_value"},
            "proxyToken": "proxy_token_123",
            "sourceConfiguration": {"type": "test_type"},
            "resolvedCredentials": {"cloudCredentials": None},
        }
    }

    mock_source_config_file.write_text(json.dumps(source_config))

    with mock.patch.dict(
        os.environ,
        {
            SOURCE_CONFIGURATIONS_PATH: str(mock_source_config_file),
            SERVICE_DISCOVERY_PATH: str(mock_service_discovery_file),
        },
    ):
        source = get_source("test_source")
        assert isinstance(source, Source)
        assert source.get_secret("SECRET_KEY") == "secret_value"
        assert source.get_https_proxy_uri() in [
            "https://user:proxy_token_123@proxy1.example.com",
            "https://user:proxy_token_123@proxy2.example.com",
        ]
        with pytest.raises(ValueError):
            source.get_https_connection()
        with pytest.raises(ValueError):
            source.get_session_credentials()


def test_get_source_get_aws_credentials_with_aws_session_credentials(
    mock_source_config_file: Path, mock_service_discovery_file: Path
) -> None:
    source_config = {
        "test_source": {
            "secrets": {},
            "sourceConfiguration": {"type": "s3"},
            "resolvedCredentials": {
                "cloudCredentials": {
                    "awsCredentials": {
                        "sessionCredentials": {
                            "accessKeyId": "ACCESS_KEY",
                            "secretAccessKey": "SECRET_KEY",
                            "sessionToken": "SESSION_TOKEN",
                            "expiration": "2023-01-01T00:00:00Z",
                        }
                    }
                }
            },
        }
    }

    mock_source_config_file.write_text(json.dumps(source_config))

    with mock.patch.dict(
        os.environ,
        {
            SOURCE_CONFIGURATIONS_PATH: str(mock_source_config_file),
            SERVICE_DISCOVERY_PATH: str(mock_service_discovery_file),
        },
    ):
        source = get_source("test_source")
        assert isinstance(source, Source)
        assert source.get_aws_credentials().get() == AwsCredentials(
            access_key_id="ACCESS_KEY",
            secret_access_key="SECRET_KEY",
            session_token="SESSION_TOKEN",
            expiration=datetime.strptime("2023-01-01T00:00:00Z", JAVA_OFFSET_DATETIME_FORMAT),
        )


def test_get_source_get_aws_credentials_with_aws_basic_credentials(
    mock_source_config_file: Path, mock_service_discovery_file: Path
) -> None:
    source_config = {
        "test_source": {
            "secrets": {},
            "sourceConfiguration": {"type": "s3"},
            "resolvedCredentials": {
                "cloudCredentials": {
                    "awsCredentials": {
                        "basicCredentials": {"accessKeyId": "ACCESS_KEY", "secretAccessKey": "SECRET_KEY"}
                    }
                }
            },
        }
    }

    mock_source_config_file.write_text(json.dumps(source_config))

    with mock.patch.dict(
        os.environ,
        {
            SOURCE_CONFIGURATIONS_PATH: str(mock_source_config_file),
            SERVICE_DISCOVERY_PATH: str(mock_service_discovery_file),
        },
    ):
        source = get_source("test_source")
        assert isinstance(source, Source)
        assert source.get_aws_credentials().get() == AwsCredentials(
            access_key_id="ACCESS_KEY",
            secret_access_key="SECRET_KEY",
        )


def test_get_source_get_session_credentials_with_aws_session_credentials(
    mock_source_config_file: Path, mock_service_discovery_file: Path
) -> None:
    source_config = {
        "test_source": {
            "secrets": {},
            "sourceConfiguration": {"type": "s3"},
            "resolvedCredentials": {
                "cloudCredentials": {
                    "awsCredentials": {
                        "sessionCredentials": {
                            "accessKeyId": "ACCESS_KEY",
                            "secretAccessKey": "SECRET_KEY",
                            "sessionToken": "SESSION_TOKEN",
                            "expiration": "2023-01-01T00:00:00Z",
                        }
                    }
                }
            },
        }
    }

    mock_source_config_file.write_text(json.dumps(source_config))

    with mock.patch.dict(
        os.environ,
        {
            SOURCE_CONFIGURATIONS_PATH: str(mock_source_config_file),
            SERVICE_DISCOVERY_PATH: str(mock_service_discovery_file),
        },
    ):
        source = get_source("test_source")
        assert isinstance(source, Source)
        assert source.get_session_credentials().get() == AwsCredentials(
            access_key_id="ACCESS_KEY",
            secret_access_key="SECRET_KEY",
            session_token="SESSION_TOKEN",
            expiration=datetime.strptime("2023-01-01T00:00:00Z", JAVA_OFFSET_DATETIME_FORMAT),
        )


def test_get_source_get_session_credentials_with_aws_basic_credentials(
    mock_source_config_file: Path, mock_service_discovery_file: Path
) -> None:
    source_config = {
        "test_source": {
            "secrets": {},
            "sourceConfiguration": {"type": "s3"},
            "resolvedCredentials": {
                "cloudCredentials": {
                    "awsCredentials": {
                        "basicCredentials": {"accessKeyId": "ACCESS_KEY", "secretAccessKey": "SECRET_KEY"}
                    }
                }
            },
        }
    }

    mock_source_config_file.write_text(json.dumps(source_config))

    with mock.patch.dict(
        os.environ,
        {
            SOURCE_CONFIGURATIONS_PATH: str(mock_source_config_file),
            SERVICE_DISCOVERY_PATH: str(mock_service_discovery_file),
        },
    ):
        source = get_source("test_source")
        assert isinstance(source, Source)
        assert source.get_session_credentials().get() == AwsCredentials(
            access_key_id="ACCESS_KEY",
            secret_access_key="SECRET_KEY",
        )


def test_get_source_get_session_credentials_with_gcp_oauth_credentials(
    mock_source_config_file: Path, mock_service_discovery_file: Path
) -> None:
    source_config = {
        "test_source": {
            "secrets": {},
            "sourceConfiguration": {"type": "bigquery"},
            "resolvedCredentials": {
                "gcpOauthCredentials": {
                    "accessToken": "ACCESS_TOKEN",
                    "expiration": "2023-01-01T00:00:00Z",
                }
            },
        }
    }

    mock_source_config_file.write_text(json.dumps(source_config))

    with mock.patch.dict(
        os.environ,
        {
            SOURCE_CONFIGURATIONS_PATH: str(mock_source_config_file),
            SERVICE_DISCOVERY_PATH: str(mock_service_discovery_file),
        },
    ):
        source = get_source("test_source")
        assert isinstance(source, Source)
        assert source.get_session_credentials().get() == GcpOauthCredentials(
            access_token="ACCESS_TOKEN",
            expiration=datetime.strptime("2023-01-01T00:00:00Z", JAVA_OFFSET_DATETIME_FORMAT),
        )


def test_get_source_get_session_credentials_with_oauth2_credentials(
    mock_source_config_file: Path, mock_service_discovery_file: Path
) -> None:
    source_config = {
        "test_source": {
            "secrets": {},
            "sourceConfiguration": {"type": "webhooks-rest"},
            "resolvedCredentials": {
                "oauth2Credentials": {"accessToken": "ACCESS_TOKEN", "expiration": "2023-01-01T00:00:00Z"}
            },
        }
    }

    mock_source_config_file.write_text(json.dumps(source_config))

    with mock.patch.dict(
        os.environ,
        {
            SOURCE_CONFIGURATIONS_PATH: str(mock_source_config_file),
            SERVICE_DISCOVERY_PATH: str(mock_service_discovery_file),
        },
    ):
        source = get_source("test_source")
        assert isinstance(source, Source)
        assert source.get_session_credentials().get() == OauthCredentials(
            access_token="ACCESS_TOKEN",
            expiration=datetime.strptime("2023-01-01T00:00:00Z", JAVA_OFFSET_DATETIME_FORMAT),
        )


def test_get_source_not_found(mock_source_config_file: Path, mock_service_discovery_file: Path) -> None:
    source_config = {"existing_source": {"secrets": {}, "sourceConfiguration": {"type": "test_type"}}}

    mock_source_config_file.write_text(json.dumps(source_config))

    with mock.patch.dict(
        os.environ,
        {
            SOURCE_CONFIGURATIONS_PATH: str(mock_source_config_file),
            SERVICE_DISCOVERY_PATH: str(mock_service_discovery_file),
        },
    ):
        with pytest.raises(ValueError, match="Source nonexistent_source not found"):
            get_source("nonexistent_source")


def test_get_source_invalid_config_format(mock_source_config_file: Path, mock_service_discovery_file: Path) -> None:
    source_config = ["test_source", "another_source"]

    mock_source_config_file.write_text(json.dumps(source_config))

    with mock.patch.dict(
        os.environ,
        {
            SOURCE_CONFIGURATIONS_PATH: str(mock_source_config_file),
            SERVICE_DISCOVERY_PATH: str(mock_service_discovery_file),
        },
    ):
        with pytest.raises(ValueError, match="The JSON content is not a dictionary"):
            get_source("test_source")


def test_get_source_missing_config_file(mock_service_discovery_file: Path) -> None:
    with mock.patch.dict(
        os.environ,
        {
            SOURCE_CONFIGURATIONS_PATH: "/nonexistent/path/config.json",
            SERVICE_DISCOVERY_PATH: str(mock_service_discovery_file),
        },
    ):
        with pytest.raises(FileNotFoundError):
            get_source("test_source")


def test_mounted_http_connection_config_from_dict_full() -> None:
    data = {
        "url": "https://example.com",
        "authHeaders": {"Authorization": "Bearer token"},
        "queryParameters": {"param": "value"},
    }

    config = MountedHttpConnectionConfig.from_dict(data)

    assert config.url == "https://example.com"
    assert config.auth_headers == {"Authorization": "Bearer token"}
    assert config.query_parameters == {"param": "value"}


def test_mounted_http_connection_config_from_dict_minimal() -> None:
    data = {"url": "https://example.com"}

    config = MountedHttpConnectionConfig.from_dict(data)

    assert config.url == "https://example.com"
    assert config.auth_headers == {}
    assert config.query_parameters == {}


def test_mounted_source_config_from_dict_full() -> None:
    data = {
        "secrets": {"key": "value"},
        "httpConnectionConfig": {
            "url": "https://example.com",
            "authHeaders": {"Authorization": "Bearer token"},
            "queryParameters": {"param": "value"},
        },
        "proxyToken": "proxy_token_123",
        "sourceConfiguration": {"type": "test_type"},
        "resolvedCredentials": {"data": "value"},
    }

    config = MountedSourceConfig.from_dict(data)

    assert config.secrets == {"key": "value"}
    assert config.proxy_token == "proxy_token_123"
    assert isinstance(config.http_connection_config, MountedHttpConnectionConfig)
    assert config.http_connection_config.url == "https://example.com"
    assert config.source_configuration == {"type": "test_type"}
    assert config.resolved_credentials == {"data": "value"}


def test_mounted_source_config_from_dict_minimal() -> None:
    data: dict[str, Any] = {}

    config = MountedSourceConfig.from_dict(data)

    assert config.secrets == {}
    assert config.proxy_token is None
    assert config.http_connection_config is None
    assert config.source_configuration is None
    assert config.resolved_credentials is None


def test_mounted_source_config_from_dict_without_http_connection() -> None:
    data = {
        "secrets": {"key": "value"},
        "proxyToken": "proxy_token_123",
        "sourceConfiguration": {"type": "test_type"},
    }

    config = MountedSourceConfig.from_dict(data)

    assert config.secrets == {"key": "value"}
    assert config.proxy_token == "proxy_token_123"
    assert config.http_connection_config is None
    assert config.source_configuration == {"type": "test_type"}
