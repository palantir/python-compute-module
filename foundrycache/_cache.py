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

"""DistributedCache — the main user-facing class for caching operations."""

from typing import Callable, Optional

from foundrycache._client import CachingServiceClient, _get_default_client
from foundrycache._types import CacheTTL


class DistributedCache:
    """A distributed cache for deployed compute workloads.

    Data expires after a configurable TTL (default 1 hour, max 24 hours)
    and carries no durability guarantees.

    Example usage::

        from foundrycache import DistributedCache, CacheTTL
        import json

        cache = DistributedCache()

        result = cache.get_or_compute(
            key=f"product:{product_id}",
            fallback=lambda: json.dumps(fetch_product(product_id)),
        )

        cache.put("result:overhead", json.dumps({"total": 42.5}), ttl=CacheTTL.SIX_HOURS)

        cache.put_expected("counter", new_value="6", expected="5")

        results = cache.batch_get(["key1", "key2", "key3"])
    """

    def __init__(self, service_url: Optional[str] = None, compute_rid: Optional[str] = None) -> None:
        if service_url is not None or compute_rid is not None:
            self._client = CachingServiceClient(service_url=service_url, compute_rid=compute_rid)
        else:
            self._client = _get_default_client()

    def get_or_compute(self, key: str, fallback: Callable[[], str], ttl: CacheTTL = CacheTTL.ONE_HOUR) -> str:
        """Return cached value if it exists, otherwise compute, store, and return it.

        The fallback is called client-side, then sent to the server which atomically
        checks-and-stores. Under concurrent access from multiple replicas, the fallback
        may execute more than once but only one value will be stored.
        """
        value = fallback()
        result_value, _was_computed = self._client.get_or_compute(key, value, ttl)
        return result_value

    def put(self, key: str, value: str, ttl: CacheTTL = CacheTTL.ONE_HOUR) -> None:
        """Write a value to the cache."""
        self._client.put(key, value, ttl)

    def put_expected(
        self, key: str, new_value: str, expected: Optional[str] = None, ttl: CacheTTL = CacheTTL.ONE_HOUR
    ) -> bool:
        """Compare-and-swap: atomically update only if current value matches expected.

        If expected is None, acts as put-if-absent (only writes if the key does not exist).

        Returns True if the value was updated, False if the condition was not met.
        """
        return self._client.put_expected(key, expected, new_value, ttl)

    def delete(self, key: str) -> None:
        """Remove a key from the cache. No-op if absent."""
        self._client.delete(key)

    def exists(self, key: str) -> bool:
        """Check if a key exists without retrieving the value."""
        return self._client.exists(key)

    def batch_get(self, keys: list[str]) -> dict[str, str]:
        """Retrieve multiple keys in one call (max 100). Missing keys omitted."""
        return self._client.batch_get(keys)
