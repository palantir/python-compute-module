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

from enum import Enum


class CacheTTL(Enum):
    """Allowed TTL values for cache entries.

    Enforces the maximum 24-hour TTL and prevents runtime errors from invalid durations.
    """

    ONE_MINUTE = "ONE_MINUTE"
    FIVE_MINUTES = "FIVE_MINUTES"
    FIFTEEN_MINUTES = "FIFTEEN_MINUTES"
    ONE_HOUR = "ONE_HOUR"
    SIX_HOURS = "SIX_HOURS"
    TWELVE_HOURS = "TWELVE_HOURS"
    ONE_DAY = "ONE_DAY"


class CacheError(Exception):
    """Base exception for cache operations."""


class ScratchNotEnabledError(CacheError):
    """Raised when scratch cache is not enabled for this compute module."""


class CacheUnavailableError(CacheError):
    """Raised when the cache service is unreachable."""


class RateLimitedError(CacheError):
    """Raised when the rate limit is exceeded."""

    def __init__(self) -> None:
        super().__init__("Rate limit exceeded for this compute module.")
