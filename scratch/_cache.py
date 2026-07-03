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

from typing import Optional

from scratch._client import _get_default_client
from scratch._types import CacheTTL


class DistributedCache:
    """A distributed cache shared across all replicas of a compute module. The cache is scoped to the compute module
    so it cannot be accessed by another compute module.

    Note that data expires after a configurable TTL (default 1 hour, max 24 hours)
    and carries no durability guarantees.

    Example of a basic read-through pattern (check cache, fall back to source)::

        from scratch import DistributedCache, CacheTTL
        import json

        cache = DistributedCache(default_ttl=CacheTTL.FIVE_MINUTES)

        key = "expensive-result"
        cached = cache.get(key)
        if cached is None:
            result = expensive_computation()
            cache.put(key, json.dumps(result))
        else:
            result = json.loads(cached)
    """

    def __init__(self, default_ttl: CacheTTL = CacheTTL.ONE_HOUR) -> None:
        self._client = _get_default_client()
        self._default_ttl = default_ttl

    def get(self, key: str) -> Optional[str]:
        """Retrieve a cached value. Returns None if the key does not exist or has expired."""
        return self._client.get(key)

    def put(self, key: str, value: str, ttl: Optional[CacheTTL] = None) -> None:
        """Write a value to the cache. Overwrites if exists.

        Uses the default TTL from the constructor unless overridden with ``ttl``.
        """
        self._client.put(key, value, ttl or self._default_ttl)

    def delete(self, key: str) -> None:
        """Remove a key from the cache. No-op if absent."""
        self._client.delete(key)

    def exists(self, key: str) -> bool:
        """Check if a key exists without retrieving the value."""
        return self._client.exists(key)

    def batch_get(self, keys: list[str]) -> dict[str, str]:
        """Retrieve multiple keys in one call (max 100). Missing keys omitted."""
        return self._client.batch_get(keys)
