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

from scratch._cache import DistributedCache
from scratch._types import CacheTTL


@patch("scratch._cache._get_default_client")
class TestDistributedCache:
    def test_get(self, mock_get_client: MagicMock) -> None:
        mock_get_client.return_value.get.return_value = "cached-value"
        assert DistributedCache().get("my-key") == "cached-value"
        mock_get_client.return_value.get.assert_called_once_with("my-key")

    def test_put_default_ttl(self, mock_get_client: MagicMock) -> None:
        DistributedCache().put("k", "v")
        mock_get_client.return_value.put.assert_called_once_with("k", "v", CacheTTL.ONE_HOUR)

    def test_put_custom_ttl(self, mock_get_client: MagicMock) -> None:
        DistributedCache().put("k", "v", CacheTTL.FIVE_MINUTES)
        mock_get_client.return_value.put.assert_called_once_with("k", "v", CacheTTL.FIVE_MINUTES)

    def test_delete(self, mock_get_client: MagicMock) -> None:
        DistributedCache().delete("k")
        mock_get_client.return_value.delete.assert_called_once_with("k")

    def test_exists(self, mock_get_client: MagicMock) -> None:
        mock_get_client.return_value.exists.return_value = True
        assert DistributedCache().exists("k") is True

    def test_batch_get(self, mock_get_client: MagicMock) -> None:
        mock_get_client.return_value.batch_get.return_value = {"a": "1", "b": "2"}
        assert DistributedCache().batch_get(["a", "b"]) == {"a": "1", "b": "2"}
