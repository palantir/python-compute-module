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

import logging
from typing import Any, List, Optional
from unittest.mock import MagicMock

import pytest
import requests

from compute_modules.client.internal_query_client import POST_RESTART_MAX_ATTEMPTS, InternalQueryService


def _make_client() -> Any:
    """Build a bare InternalQueryService for testing report_restart() in isolation.

    The real __init__ requires several environment variables, an auth token
    read from a real file, and a real CA cert path (ssl.create_default_context
    validates it), which is disproportionate to set up just to exercise one
    retry loop. __new__ skips __init__ entirely; we then set only the
    attributes report_restart() actually touches.

    Returns Any (not InternalQueryService): we deliberately assign test
    doubles (a bare Logger instead of ComputeModulesLoggerAdapter, a
    MagicMock instead of a real requests.Session) that don't match the real
    attribute types, and callers need mypy to allow MagicMock-only members
    like `.call_count` on `client.session.request`.
    """
    client: Any = InternalQueryService.__new__(InternalQueryService)
    client.host = "localhost"
    client.port = 1234
    client.post_restart_path = "/restart"
    client.post_restart_headers = {}
    client.certPath = "unused-in-tests"
    client.session = MagicMock()
    client.logger = logging.getLogger("test-internal-query-client")
    return client


def _mock_response(status_code: int, json_body: Optional[List[str]] = None, text: str = "") -> MagicMock:
    response = MagicMock(spec=requests.Response)
    response.status_code = status_code
    response.reason = "mock reason"
    response.text = text
    if json_body is not None:
        response.json.return_value = json_body
    # report_restart() uses `with self.session.request(...) as response:`
    response.__enter__.return_value = response
    response.__exit__.return_value = False
    return response


class TestReportRestart:
    def test_success_on_first_attempt(self) -> None:
        client = _make_client()
        client.session.request.return_value = _mock_response(200, json_body=["job-1", "job-2"])

        client.report_restart()  # should not raise

        assert client.session.request.call_count == 1

    def test_500_stops_retrying_immediately(self) -> None:
        client = _make_client()
        client.session.request.return_value = _mock_response(500, text="internal error")

        with pytest.raises(RuntimeError, match="after 1 attempt"):
            client.report_restart()

        assert client.session.request.call_count == 1

    def test_non_500_failure_status_retries_up_to_max_attempts(self) -> None:
        client = _make_client()
        client.session.request.return_value = _mock_response(404, text="not found")

        with pytest.raises(RuntimeError, match=f"after {POST_RESTART_MAX_ATTEMPTS} attempt"):
            client.report_restart()

        assert client.session.request.call_count == POST_RESTART_MAX_ATTEMPTS

    def test_network_exception_retries_up_to_max_attempts(self) -> None:
        client = _make_client()
        client.session.request.side_effect = requests.ConnectionError("boom")

        with pytest.raises(RuntimeError, match=f"after {POST_RESTART_MAX_ATTEMPTS} attempt"):
            client.report_restart()

        assert client.session.request.call_count == POST_RESTART_MAX_ATTEMPTS

    def test_success_after_a_transient_failure(self) -> None:
        client = _make_client()
        client.session.request.side_effect = [
            _mock_response(503, text="temporarily unavailable"),
            _mock_response(200, json_body=["job-1"]),
        ]

        client.report_restart()  # should not raise

        assert client.session.request.call_count == 2

    def test_500_after_a_transient_failure_still_stops_early(self) -> None:
        """A 500 should stop retries even when it isn't the very first response."""
        client = _make_client()
        client.session.request.side_effect = [
            _mock_response(503, text="temporarily unavailable"),
            _mock_response(500, text="internal error"),
        ]

        with pytest.raises(RuntimeError, match="after 2 attempt"):
            client.report_restart()

        assert client.session.request.call_count == 2

    def test_500_error_is_logged(self, caplog: Any) -> None:
        client = _make_client()
        client.session.request.return_value = _mock_response(500, text="internal error")

        with caplog.at_level(logging.ERROR, logger="test-internal-query-client"):
            with pytest.raises(RuntimeError):
                client.report_restart()

        assert any("not retrying" in message for message in caplog.messages)
