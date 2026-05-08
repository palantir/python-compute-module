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

"""DistributedLock — cross-replica coordination primitives."""

from typing import Any, Optional

from foundrycache._client import CachingServiceClient, _get_default_client


class Lock:
    """A held distributed lock. Auto-expires in 5 seconds if not refreshed.

    Can be used as a context manager::

        lock_service = DistributedLock()
        maybe_lock = lock_service.try_lock("my-lock")
        if maybe_lock:
            with maybe_lock:
                do_work()
    """

    def __init__(self, client: CachingServiceClient, handle: dict[str, Any]) -> None:
        self._client = client
        self._handle = handle
        self._released = False

    @property
    def lock_name(self) -> str:
        return self._handle["lockName"]  # type: ignore[no-any-return]

    @property
    def lock_id(self) -> str:
        return self._handle["lockId"]  # type: ignore[no-any-return]

    def unlock(self) -> None:
        """Release the lock synchronously."""
        if not self._released:
            self._client.unlock(self._handle)
            self._released = True

    def refresh(self) -> bool:
        """Extend the lease by another 5 seconds. Returns False if the lock was lost."""
        if self._released:
            return False
        return self._client.refresh_lock(self._handle)

    def __enter__(self) -> "Lock":
        return self

    def __exit__(self, *_args: object) -> None:
        self.unlock()


class DistributedLock:
    """Distributed locking for cross-replica coordination.

    Locks auto-expire after 5 seconds if not refreshed.

    Example usage::

        from foundrycache import DistributedLock

        lock = DistributedLock()
        maybe_lock = lock.try_lock("process-batch")
        if maybe_lock:
            try:
                for chunk in get_chunks():
                    process(chunk)
                    if not maybe_lock.refresh():
                        raise RuntimeError("Lost lock")
            finally:
                maybe_lock.unlock()
    """

    def __init__(self, service_url: Optional[str] = None, compute_rid: Optional[str] = None) -> None:
        if service_url is not None or compute_rid is not None:
            self._client = CachingServiceClient(service_url=service_url, compute_rid=compute_rid)
        else:
            self._client = _get_default_client()

    def try_lock(self, lock_name: str) -> Optional[Lock]:
        """Attempt to acquire a named lock. Returns Lock if acquired, None if contended."""
        handle = self._client.try_lock(lock_name)
        if handle is None:
            return None
        return Lock(self._client, handle)
