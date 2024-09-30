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


import logging

import pytest

from compute_modules.logging import get_logger, set_internal_log_level

from .logging_test_utils import (
    CLIENT_CRITICAL_STR,
    CLIENT_DEBUG_STR,
    CLIENT_ERROR_STR,
    CLIENT_INFO_STR,
    CLIENT_WARNING_STR,
    CRITICAL_STR,
    DEBUG_STR,
    ERROR_STR,
    INFO_STR,
    WARNING_STR,
    emit_internal_logs,
)

# TODO: update docs


def test_default_log_levels(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test default log level is ERROR"""
    emit_internal_logs()
    assert DEBUG_STR not in caplog.text
    assert INFO_STR not in caplog.text
    assert WARNING_STR not in caplog.text
    assert ERROR_STR in caplog.text
    assert CRITICAL_STR in caplog.text


def test_log_level_override(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test calling set_internal_log_level to change CM log level"""
    set_internal_log_level(logging.INFO)
    emit_internal_logs()
    assert DEBUG_STR not in caplog.text
    assert INFO_STR in caplog.text
    assert WARNING_STR in caplog.text
    assert ERROR_STR in caplog.text
    assert CRITICAL_STR in caplog.text


def test_log_level_override_with_client_level_lower(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test calling set_internal_log_level to change CM log level,
    while having public logger at a different level
    """
    set_internal_log_level(logging.WARNING)
    client_logger = get_logger("twinkle")
    client_logger.setLevel(logging.DEBUG)
    client_logger.debug(CLIENT_DEBUG_STR)
    client_logger.info(CLIENT_INFO_STR)
    client_logger.warning(CLIENT_WARNING_STR)
    client_logger.error(CLIENT_ERROR_STR)
    client_logger.critical(CLIENT_CRITICAL_STR)
    emit_internal_logs()
    assert DEBUG_STR not in caplog.text
    assert INFO_STR not in caplog.text
    assert WARNING_STR in caplog.text
    assert ERROR_STR in caplog.text
    assert CRITICAL_STR in caplog.text

    assert CLIENT_DEBUG_STR in caplog.text
    assert CLIENT_INFO_STR in caplog.text
    assert CLIENT_WARNING_STR in caplog.text
    assert CLIENT_ERROR_STR in caplog.text
    assert CLIENT_CRITICAL_STR in caplog.text


def test_log_level_override_with_client_level_higher(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test calling set_internal_log_level to change CM log level,
    while having public logger at a different level
    """
    set_internal_log_level(logging.DEBUG)
    client_logger = get_logger("twinkle")
    client_logger.setLevel(logging.ERROR)
    client_logger.debug(CLIENT_DEBUG_STR)
    client_logger.info(CLIENT_INFO_STR)
    client_logger.warning(CLIENT_WARNING_STR)
    client_logger.error(CLIENT_ERROR_STR)
    client_logger.critical(CLIENT_CRITICAL_STR)
    emit_internal_logs()
    assert DEBUG_STR in caplog.text
    assert INFO_STR in caplog.text
    assert WARNING_STR in caplog.text
    assert ERROR_STR in caplog.text
    assert CRITICAL_STR in caplog.text

    assert CLIENT_DEBUG_STR not in caplog.text
    assert CLIENT_INFO_STR not in caplog.text
    assert CLIENT_WARNING_STR not in caplog.text
    assert CLIENT_ERROR_STR in caplog.text
    assert CLIENT_CRITICAL_STR in caplog.text
    assert CRITICAL_STR in caplog.text

    assert CLIENT_DEBUG_STR not in caplog.text
    assert CLIENT_INFO_STR not in caplog.text
    assert CLIENT_WARNING_STR not in caplog.text
    assert CLIENT_ERROR_STR in caplog.text
    assert CLIENT_CRITICAL_STR in caplog.text
    assert CLIENT_CRITICAL_STR in caplog.text
    assert CLIENT_INFO_STR not in caplog.text
    assert CLIENT_WARNING_STR not in caplog.text
    assert CLIENT_ERROR_STR in caplog.text
    assert CLIENT_CRITICAL_STR in caplog.text
    assert CRITICAL_STR in caplog.text

    assert CLIENT_DEBUG_STR not in caplog.text
    assert CLIENT_INFO_STR not in caplog.text
    assert CLIENT_WARNING_STR not in caplog.text
    assert CLIENT_ERROR_STR in caplog.text
    assert CLIENT_CRITICAL_STR in caplog.text
    assert CLIENT_CRITICAL_STR in caplog.text
