#  Copyright 2026 Palantir Technologies, Inc.
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
from pathlib import Path
from typing import Any, Optional
from unittest import mock
from unittest.mock import MagicMock, patch

import pytest
import requests

from scratch._client import ScratchClient, _get_default_client
from scratch._types import CacheError, CacheTTL, CacheUnavailableError, RateLimitedError, ScratchNotEnabledError


def _make_response(status_code: int = 200, body: Optional[dict[str, Any]] = None) -> MagicMock:
    resp = MagicMock(spec=requests.Response)
    resp.status_code = status_code
    if body is not None:
        resp.content = json.dumps(body).encode()
        resp.json.return_value = body
    else:
        resp.content = b""
    return resp


@pytest.fixture
def client() -> ScratchClient:
    with patch.object(ScratchClient, "_resolve_service_url", return_value="https://scratch.local"):
        return ScratchClient()


def _stub_post(client: ScratchClient, resp: MagicMock) -> MagicMock:
    post_mock = MagicMock(return_value=resp)
    client._session.post = post_mock  # type: ignore[method-assign]
    return post_mock


def _posted_body(post_mock: MagicMock) -> Any:
    return post_mock.call_args[1]["json"]


def test_get_default_client_no_token() -> None:
    with mock.patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ScratchNotEnabledError, match="not enabled"):
            _get_default_client()


def test_get_default_client_caches() -> None:
    with mock.patch.dict(os.environ, {"SCRATCH_TOKEN": "test-token"}, clear=True):
        with patch.object(ScratchClient, "_resolve_service_url", return_value="https://scratch.local"):
            assert _get_default_client() is _get_default_client()


def test_resolve_service_url_from_yaml(tmp_path: Path) -> None:
    service_file = tmp_path / "sd.yaml"
    service_file.write_text("contour_backend_multiplexer:\n  - https://scratch.local\n  - https://backup.local\n")

    mock_yaml = MagicMock()
    mock_yaml.safe_load.return_value = {
        "contour_backend_multiplexer": ["https://scratch.local", "https://backup.local"]
    }

    with mock.patch.dict(os.environ, {"FOUNDRY_SERVICE_DISCOVERY_V2": str(service_file)}):
        with patch.dict("sys.modules", {"yaml": mock_yaml}):
            assert ScratchClient._resolve_service_url() == "https://scratch.local"


def test_resolve_service_url_missing_file() -> None:
    mock_yaml = MagicMock()
    with mock.patch.dict(os.environ, {"FOUNDRY_SERVICE_DISCOVERY_V2": "/nonexistent/path.yaml"}):
        with patch.dict("sys.modules", {"yaml": mock_yaml}):
            assert ScratchClient._resolve_service_url() == ""


def test_resolve_service_url_no_env() -> None:
    mock_yaml = MagicMock()
    with mock.patch.dict(os.environ, {}, clear=True):
        with patch.dict("sys.modules", {"yaml": mock_yaml}):
            assert ScratchClient._resolve_service_url() == ""


def test_init_raises_without_service_url() -> None:
    with patch.object(ScratchClient, "_resolve_service_url", return_value=""):
        with pytest.raises(CacheError, match="Scratch service URL not configured"):
            ScratchClient()


@pytest.mark.parametrize(
    "status_code, exception_type",
    [
        (429, RateLimitedError),
        (403, CacheError),
        (404, CacheError),
        (500, CacheUnavailableError),
    ],
)
def test_handle_response_errors(client: ScratchClient, status_code: int, exception_type: type) -> None:
    with pytest.raises(exception_type):
        client._handle_response(_make_response(status_code))


def test_handle_response_204(client: ScratchClient) -> None:
    assert client._handle_response(_make_response(204)) is None


def test_handle_response_200_json(client: ScratchClient) -> None:
    assert client._handle_response(_make_response(200, {"key": "val"})) == {"key": "val"}


def test_url_construction(client: ScratchClient) -> None:
    assert client._url("/v1/cache/get") == "https://scratch.local/scratch/api/v1/cache/get"


def test_get(client: ScratchClient) -> None:
    post = _stub_post(client, _make_response(200, {"value": "hello"}))

    assert client.get("my-key") == "hello"
    assert "/v1/cache/get" in post.call_args[0][0]
    assert _posted_body(post) == {"key": "my-key"}


def test_get_miss(client: ScratchClient) -> None:
    _stub_post(client, _make_response(204))
    assert client.get("missing") is None


def test_put_with_ttl(client: ScratchClient) -> None:
    post = _stub_post(client, _make_response(204))
    client.put("k", "v", CacheTTL.FIVE_MINUTES)
    assert _posted_body(post) == {"key": "k", "value": {"value": "v"}, "ttl": "FIVE_MINUTES"}


def test_put_without_ttl(client: ScratchClient) -> None:
    post = _stub_post(client, _make_response(204))
    client.put("k", "v")
    assert "ttl" not in _posted_body(post)


def test_delete(client: ScratchClient) -> None:
    post = _stub_post(client, _make_response(204))
    client.delete("k")
    assert _posted_body(post) == {"key": "k"}


@pytest.mark.parametrize("exists", [True, False])
def test_exists(client: ScratchClient, exists: bool) -> None:
    _stub_post(client, _make_response(200, {"exists": exists}))
    assert client.exists("k") is exists


def test_batch_get(client: ScratchClient) -> None:
    _stub_post(client, _make_response(200, {"entries": {"a": {"value": "1"}, "b": {"value": "2"}}}))
    assert client.batch_get(["a", "b"]) == {"a": "1", "b": "2"}


def test_batch_get_over_100(client: ScratchClient) -> None:
    with pytest.raises(ValueError, match="at most 100"):
        client.batch_get([f"key-{i}" for i in range(101)])


def test_try_lock_acquired(client: ScratchClient) -> None:
    handle = {"lockName": "my-lock", "lockId": "abc123"}
    _stub_post(client, _make_response(200, {"acquired": handle}))
    assert client.try_lock("my-lock") == handle


def test_try_lock_not_acquired(client: ScratchClient) -> None:
    _stub_post(client, _make_response(200, {"notAcquired": {}}))
    assert client.try_lock("my-lock") is None


def test_unlock(client: ScratchClient) -> None:
    handle = {"lockName": "my-lock", "lockId": "abc123"}
    post = _stub_post(client, _make_response(204))
    client.unlock(handle)
    assert _posted_body(post) == {"handle": handle}


@pytest.mark.parametrize("success", [True, False])
def test_refresh_lock(client: ScratchClient, success: bool) -> None:
    _stub_post(client, _make_response(200, {"success": success}))
    assert client.refresh_lock({"lockName": "l", "lockId": "i"}) is success
