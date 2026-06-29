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

from typing import Generator
from unittest.mock import MagicMock

import pytest

from scratch._client import ScratchClient, _get_default_client


@pytest.fixture(autouse=True)
def clear_default_client_cache() -> Generator[None, None, None]:
    yield
    _get_default_client.cache_clear()


@pytest.fixture
def mock_client() -> MagicMock:
    return MagicMock(spec=ScratchClient)
