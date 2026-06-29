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

from unittest.mock import MagicMock, patch

from scratch._lock import DistributedLock, Lock

HANDLE = {"lockName": "my-lock", "lockId": "abc123"}


class TestLock:
    def test_properties(self, mock_client: MagicMock) -> None:
        lock = Lock(mock_client, HANDLE)
        assert lock.lock_name == "my-lock"
        assert lock.lock_id == "abc123"

    def test_unlock(self, mock_client: MagicMock) -> None:
        lock = Lock(mock_client, HANDLE)
        lock.unlock()
        mock_client.unlock.assert_called_once_with(HANDLE)

    def test_unlock_idempotent(self, mock_client: MagicMock) -> None:
        lock = Lock(mock_client, HANDLE)
        lock.unlock()
        lock.unlock()
        mock_client.unlock.assert_called_once()

    def test_refresh(self, mock_client: MagicMock) -> None:
        mock_client.refresh_lock.return_value = True
        lock = Lock(mock_client, HANDLE)
        assert lock.refresh() is True
        mock_client.refresh_lock.assert_called_once_with(HANDLE)

    def test_refresh_after_release_returns_false(self, mock_client: MagicMock) -> None:
        lock = Lock(mock_client, HANDLE)
        lock.unlock()
        assert lock.refresh() is False
        mock_client.refresh_lock.assert_not_called()

    def test_context_manager(self, mock_client: MagicMock) -> None:
        with Lock(mock_client, HANDLE):
            pass
        mock_client.unlock.assert_called_once_with(HANDLE)

    def test_context_manager_unlocks_on_exception(self, mock_client: MagicMock) -> None:
        try:
            with Lock(mock_client, HANDLE):
                raise ValueError("boom")
        except ValueError:
            pass
        mock_client.unlock.assert_called_once_with(HANDLE)


class TestDistributedLock:
    @patch("scratch._lock._get_default_client")
    def test_try_lock_acquired(self, mock_get_client: MagicMock) -> None:
        mock_get_client.return_value.try_lock.return_value = HANDLE

        lock = DistributedLock().try_lock("my-lock")

        assert isinstance(lock, Lock)
        assert lock.lock_name == "my-lock"

    @patch("scratch._lock._get_default_client")
    def test_try_lock_not_acquired(self, mock_get_client: MagicMock) -> None:
        mock_get_client.return_value.try_lock.return_value = None
        assert DistributedLock().try_lock("my-lock") is None
