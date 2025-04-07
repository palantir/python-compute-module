#  Copyright 2024 Palantir Technologies, Inc.
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


from typing import Generator, List
from unittest.mock import MagicMock, patch

import pytest

from compute_modules.auth.third_party import RefreshingOauthToken

# Mock data
MOCK_HOSTNAME: str = "example.com"
MOCK_SCOPE: List[str] = ["api:ontologies-read"]
MOCK_TOKEN: str = "mock_token"


@pytest.fixture
def mock_oauth() -> Generator[MagicMock, None, None]:
    with patch("compute_modules.auth.third_party.oauth") as mock_oauth:
        yield mock_oauth


@pytest.fixture
def mock_time() -> Generator[MagicMock, None, None]:
    with patch("time.time") as mock_time:
        yield mock_time


def test_get_token_initial_fetch(mock_oauth: MagicMock, mock_time: MagicMock) -> None:
    mock_oauth.return_value = MOCK_TOKEN
    mock_time.return_value = 1000

    token_refresher = RefreshingOauthToken(MOCK_HOSTNAME, MOCK_SCOPE)
    token: str = token_refresher.get_token()

    assert token == MOCK_TOKEN
    mock_oauth.assert_called_once_with(MOCK_HOSTNAME, MOCK_SCOPE)


def test_get_token_refresh_needed(mock_oauth: MagicMock, mock_time: MagicMock) -> None:
    mock_oauth.return_value = MOCK_TOKEN
    initial_time: int = 1000
    mock_time.side_effect = [initial_time, initial_time + 1900]  # Outside refresh interval

    token_refresher = RefreshingOauthToken(MOCK_HOSTNAME, MOCK_SCOPE)
    token_refresher.get_token()
    token: str = token_refresher.get_token()  # Should trigger refresh

    assert token == MOCK_TOKEN
    assert mock_oauth.call_count == 2


def test_get_token_no_refresh_needed(mock_oauth: MagicMock, mock_time: MagicMock) -> None:
    mock_oauth.return_value = MOCK_TOKEN
    initial_time: int = 1000
    mock_time.side_effect = [initial_time, initial_time + 1700]  # Within refresh interval

    token_refresher = RefreshingOauthToken(MOCK_HOSTNAME, MOCK_SCOPE)
    token_refresher.get_token()
    token: str = token_refresher.get_token()  # Should not trigger refresh

    assert token == MOCK_TOKEN
    assert mock_oauth.call_count == 1
