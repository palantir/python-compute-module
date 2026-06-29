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


from typing import Optional

from scratch._client import ScratchClient, _get_default_client


class Lock:
    """A held distributed lock. Expires after 20 seconds unless ``refresh()`` is called.

    **Important:** The lock starts expiring immediately after acquisition. If your work
    takes longer than 20 seconds, you must call ``refresh()`` periodically to keep it alive.

    For example::

        lock = lock_service.try_lock("my-lock")
        if lock:
            try:
                for item in items:
                    process(item)
                    if not lock.refresh():  # call before 20s expires
                        raise RuntimeError("Lost lock")
            finally:
                lock.unlock()
    """

    def __init__(self, client: ScratchClient, handle: dict) -> None:
        self._client = client
        self._handle = handle
        self._released = False

    @property
    def lock_name(self) -> str:
        return self._handle["lockName"]

    @property
    def lock_id(self) -> str:
        return self._handle["lockId"]

    def unlock(self) -> None:
        """Release the lock. No-op if already released."""
        if not self._released:
            self._client.unlock(self._handle)
            self._released = True

    def refresh(self) -> bool:
        """Extend the lease by another 20 seconds. Call this before the current lease expires.

        Returns True if the lease was extended, False if the lock was lost (e.g. it expired
        before this call reached the server). Always check the return value.
        """
        if self._released:
            return False
        return self._client.refresh_lock(self._handle)

    def __enter__(self) -> "Lock":
        return self

    def __exit__(self, *_args: object) -> None:
        self.unlock()


class DistributedLock:
    """Distributed locking for cross-replica coordination.

    Locks auto-expire after 20 seconds if not refreshed. Only one replica
    can hold a given lock at a time.

    **Lock safety:** A lock does not guarantee mutual exclusion forever. If a
    replica acquires a lock but then stalls (GC pause, network hiccup, slow I/O),
    the lock will expire after the TTL and another replica can acquire it.
    The lock TTL is short by design (20s) to avoid situations where the holder dies
    (e.g. OOM) and the lock cannot be acquired by any other living replica.
    Call ``refresh()`` periodically for long-running work, and always check its
    return value — ``False`` means the lock was lost.

    For example:

        lock = lock_service.try_lock("process-batch")
        if lock:
            try:
                for chunk in get_chunks():
                    process(chunk)
                    if not lock.refresh():
                        raise RuntimeError("Lost lock — another replica took over")
            finally:
                lock.unlock()
    """

    def __init__(self) -> None:
        self._client = _get_default_client()

    def try_lock(self, lock_name: str) -> Optional[Lock]:
        """Attempt to acquire a named lock.

        Returns a ``Lock`` if acquired, ``None`` if the lock is held by another client.
        The lock starts its 20-second TTL immediately, so you must call ``lock.refresh()`` for
        long-running work
        """
        handle = self._client.try_lock(lock_name)
        if handle is None:
            return None
        return Lock(self._client, handle)
