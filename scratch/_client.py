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
import logging
import os
from functools import cache
from typing import Any, Optional

import requests

from scratch._types import CacheError, CacheTTL, CacheUnavailableError, RateLimitedError, ScratchNotEnabledError

LOGGER = logging.getLogger(__name__)

SCRATCH_TOKEN = "SCRATCH_TOKEN"


@cache
def _get_default_client() -> "ScratchClient":
    if not os.environ.get(SCRATCH_TOKEN):
        raise ScratchNotEnabledError(
            "Scratch cache is not enabled for this compute module. "
            "Enable the scratch feature flag for this deployment to use it."
        )
    return ScratchClient()


class ScratchClient:
    """Low-level HTTP client for the Scratch Conjure API.

    Identity is extracted server-side from the HMAC token in the Authorization header.
    """

    _CA_PATH_ENV = "CONNECTIONS_TO_OTHER_PODS_CA_PATH"

    def __init__(self) -> None:
        self._service_url = self._resolve_service_url().rstrip("/")

        if not self._service_url:
            raise CacheError(
                "Scratch service URL not configured. Ensure FOUNDRY_SERVICE_DISCOVERY_V2 is set."
            )

        self._cert_path = os.environ.get(self._CA_PATH_ENV, "")
        self._session = requests.Session()
        self._session.verify = self._cert_path if self._cert_path else True

    @staticmethod
    def _resolve_service_url() -> str:
        try:
            import yaml  # type: ignore[import-untyped]
        except ImportError:
            raise ImportError(
                "the scratch extras is not installed. Please install it with "
                "`pip install foundry-compute-modules[scratch]`"
            )

        discovery_path = os.environ.get("FOUNDRY_SERVICE_DISCOVERY_V2", "")
        if discovery_path and os.path.exists(discovery_path):
            try:
                with open(discovery_path, "r") as f:
                    service_discovery = yaml.safe_load(f)
                    uris: list[str] = service_discovery.get("contour_backend_multiplexer", [])
                    if uris:
                        return uris[0]
            except Exception as e:
                LOGGER.warning("Failed to parse service discovery file %s: %s", discovery_path, e)
        return ""

    def _headers(self) -> dict:
        return {
            "Authorization": os.environ.get(SCRATCH_TOKEN, ""),
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _handle_response(self, resp: requests.Response) -> Any:
        if resp.status_code == 429:
            raise RateLimitedError()
        if resp.status_code == 403:
            raise CacheError("Scratch cache is disabled or the auth token is invalid.")
        if resp.status_code == 404:
            raise CacheError("Scratch cache is disabled. The cache endpoint was not found.")
        if resp.status_code >= 500:
            raise CacheUnavailableError(f"Cache service error: {resp.status_code}")
        resp.raise_for_status()
        if resp.status_code == 204 or not resp.content:
            return None
        return resp.json()

    def _url(self, path: str) -> str:
        return f"{self._service_url}/scratch/api{path}"

    # ── Cache operations ──

    def get(self, key: str) -> Optional[str]:
        resp = self._session.post(self._url("/v1/cache/get"), headers=self._headers(), data=json.dumps({"key": key}))
        data = self._handle_response(resp)
        if data is None:
            return None
        return data.get("value")

    def put(self, key: str, value: str, ttl: Optional[CacheTTL] = None) -> None:
        body = {"key": key, "value": {"value": value}}
        if ttl is not None:
            body["ttl"] = ttl.value
        resp = self._session.post(self._url("/v1/cache"), headers=self._headers(), data=json.dumps(body))
        self._handle_response(resp)

    def delete(self, key: str) -> None:
        resp = self._session.post(
            self._url("/v1/cache/delete"), headers=self._headers(), data=json.dumps({"key": key})
        )
        self._handle_response(resp)

    def exists(self, key: str) -> bool:
        resp = self._session.post(
            self._url("/v1/cache/exists"), headers=self._headers(), data=json.dumps({"key": key})
        )
        data = self._handle_response(resp)
        if data is None:
            return False
        return data.get("exists", False)

    def batch_get(self, keys: list[str]) -> dict[str, str]:
        if len(keys) > 100:
            raise ValueError(f"batch_get supports at most 100 keys, got {len(keys)}")
        resp = self._session.post(
            self._url("/v1/cache/batch-get"), headers=self._headers(), data=json.dumps({"keys": keys})
        )
        data = self._handle_response(resp)
        if data is None:
            return {}
        entries = data.get("entries", {})
        return {k: v["value"] for k, v in entries.items()}

    # ── Lock operations ──

    def try_lock(self, lock_name: str) -> Optional[dict]:
        resp = self._session.post(
            self._url("/v1/lock/try-lock"), headers=self._headers(), data=json.dumps({"lockName": lock_name})
        )
        data = self._handle_response(resp)
        if data is not None and "acquired" in data:
            return data["acquired"]
        return None

    def unlock(self, handle: dict) -> None:
        resp = self._session.post(
            self._url("/v1/lock/unlock"), headers=self._headers(), data=json.dumps({"handle": handle})
        )
        self._handle_response(resp)

    def refresh_lock(self, handle: dict) -> bool:
        resp = self._session.post(
            self._url("/v1/lock/refresh"), headers=self._headers(), data=json.dumps({"handle": handle})
        )
        data = self._handle_response(resp)
        if data is None:
            return False
        return data.get("success", False)
