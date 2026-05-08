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

"""Low-level HTTP client for the Caching Service Conjure API."""

import json
import os
from functools import cache
from typing import Any, Optional
from urllib.parse import quote

import requests

from foundrycache._types import CacheError, CacheTTL, CacheUnavailableError, RateLimitedError

EPHEMERAL_CACHE_URL = "EPHEMERAL_CACHE_URL"
EPHEMERAL_CACHE_TOKEN = "EPHEMERAL_CACHE_TOKEN"
FOUNDRY_COMPUTE_MODULE_RID = "FOUNDRY_COMPUTE_MODULE_RID"


@cache
def _get_default_client() -> "CachingServiceClient":
    """Lazily create a shared client from environment variables."""
    return CachingServiceClient()


class CachingServiceClient:
    """HTTP client that calls the Caching Service Conjure API."""

    def __init__(
        self,
        service_url: Optional[str] = None,
        compute_rid: Optional[str] = None,
    ) -> None:
        self._service_url = (service_url or os.environ.get(EPHEMERAL_CACHE_URL, "")).rstrip("/")
        self._compute_rid = compute_rid or os.environ.get(FOUNDRY_COMPUTE_MODULE_RID, "")
        self._auth_token = os.environ.get(EPHEMERAL_CACHE_TOKEN, "Bearer prototype")

        if not self._service_url:
            raise CacheError(
                f"Cache service URL not configured. Set {EPHEMERAL_CACHE_URL} environment variable or pass service_url."
            )
        if not self._compute_rid:
            raise CacheError(
                f"Compute RID not configured. Set {FOUNDRY_COMPUTE_MODULE_RID} environment variable or pass compute_rid."
            )

    @property
    def compute_rid(self) -> str:
        return self._compute_rid

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": self._auth_token,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _handle_response(self, resp: requests.Response) -> Any:
        if resp.status_code == 429:
            raise RateLimitedError(self._compute_rid)
        if resp.status_code >= 500:
            raise CacheUnavailableError(f"Cache service error: {resp.status_code}")
        resp.raise_for_status()
        if resp.status_code == 204 or not resp.content:
            return None
        return resp.json()

    def _url(self, path: str) -> str:
        return f"{self._service_url}/ephemeral-cache/api{path}"

    # -- Cache operations --

    def get(self, key: str) -> Optional[str]:
        rid = quote(self._compute_rid, safe="")
        k = quote(key, safe="")
        resp = requests.get(self._url(f"/v1/cache/{rid}/{k}"), headers=self._headers())
        if resp.status_code == 204 or not resp.content:
            return None
        data = self._handle_response(resp)
        if data is None:
            return None
        return data.get("value")  # type: ignore[no-any-return]

    def put(self, key: str, value: str, ttl: Optional[CacheTTL] = None) -> None:
        body: dict[str, Any] = {"computeRid": self._compute_rid, "key": key, "value": {"value": value}}
        if ttl is not None:
            body["ttl"] = ttl.value
        resp = requests.post(self._url("/v1/cache"), headers=self._headers(), data=json.dumps(body))
        self._handle_response(resp)

    def get_or_compute(self, key: str, fallback_value: str, ttl: Optional[CacheTTL] = None) -> tuple[str, bool]:
        body: dict[str, Any] = {"computeRid": self._compute_rid, "key": key, "fallbackValue": {"value": fallback_value}}
        if ttl is not None:
            body["ttl"] = ttl.value
        resp = requests.post(self._url("/v1/cache/get-or-compute"), headers=self._headers(), data=json.dumps(body))
        data = self._handle_response(resp)
        return data["value"]["value"], data["wasComputed"]  # type: ignore[no-any-return]

    def put_expected(self, key: str, expected: Optional[str], new_value: str, ttl: Optional[CacheTTL] = None) -> bool:
        body: dict[str, Any] = {"computeRid": self._compute_rid, "key": key, "newValue": {"value": new_value}}
        if expected is not None:
            body["expected"] = {"value": expected}
        if ttl is not None:
            body["ttl"] = ttl.value
        resp = requests.post(self._url("/v1/cache/put-expected"), headers=self._headers(), data=json.dumps(body))
        data = self._handle_response(resp)
        return data.get("success", False)  # type: ignore[no-any-return]

    def delete(self, key: str) -> None:
        rid = quote(self._compute_rid, safe="")
        k = quote(key, safe="")
        resp = requests.delete(self._url(f"/v1/cache/{rid}/{k}"), headers=self._headers())
        self._handle_response(resp)

    def exists(self, key: str) -> bool:
        rid = quote(self._compute_rid, safe="")
        k = quote(key, safe="")
        resp = requests.get(self._url(f"/v1/cache/{rid}/{k}/exists"), headers=self._headers())
        return self._handle_response(resp) is True

    def batch_get(self, keys: list[str]) -> dict[str, str]:
        body: dict[str, Any] = {"computeRid": self._compute_rid, "keys": keys}
        resp = requests.post(self._url("/v1/cache/batch-get"), headers=self._headers(), data=json.dumps(body))
        data = self._handle_response(resp)
        if data is None:
            return {}
        entries: dict[str, Any] = data.get("entries", {})
        return {k: v["value"] for k, v in entries.items()}

    # -- Lock operations --

    def try_lock(self, lock_name: str) -> Optional[dict[str, Any]]:
        body: dict[str, Any] = {"computeRid": self._compute_rid, "lockName": lock_name}
        resp = requests.post(self._url("/v1/lock/try-lock"), headers=self._headers(), data=json.dumps(body))
        data = self._handle_response(resp)
        if data is None:
            return None
        if "acquired" in data:
            return data["acquired"]  # type: ignore[no-any-return]
        return None

    def unlock(self, handle: dict[str, Any]) -> None:
        body: dict[str, Any] = {"computeRid": self._compute_rid, "handle": handle}
        resp = requests.post(self._url("/v1/lock/unlock"), headers=self._headers(), data=json.dumps(body))
        self._handle_response(resp)

    def refresh_lock(self, handle: dict[str, Any]) -> bool:
        body: dict[str, Any] = {"computeRid": self._compute_rid, "handle": handle}
        resp = requests.post(self._url("/v1/lock/refresh"), headers=self._headers(), data=json.dumps(body))
        data = self._handle_response(resp)
        if data is None:
            return False
        return data.get("success", False)  # type: ignore[no-any-return]
