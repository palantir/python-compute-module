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
import uuid

import pytest

from compute_modules.logging import get_logger, internal
from compute_modules.logging.common import (
    COMPUTE_MODULES_ADAPTER_MANAGER,
    DEFAULT_LOG_FORMAT,
    ComputeModulesLoggerAdapter,
)

from .logging_test_utils import CLIENT_INFO_STR, CLIENT_WARNING_STR, INFO_STR

logging.basicConfig(format=DEFAULT_LOG_FORMAT)


def logger_fixtures() -> tuple[ComputeModulesLoggerAdapter, ComputeModulesLoggerAdapter, ComputeModulesLoggerAdapter]:
    """Initializes & configures loggers"""
    internal_logger = internal.get_internal_logger()
    internal_logger.setLevel(logging.INFO)
    logger_1 = get_logger("test.logger.1")
    logger_1.setLevel(logging.INFO)
    logger_2 = get_logger("test.logger.2")
    logger_2.setLevel(logging.INFO)
    return (internal_logger, logger_1, logger_2)


def format_log_context(pid: int, job_id: str) -> str:
    return f"PID: {pid:<2} JOB: {job_id:<37}"


def test_initial_log_format(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Verify initial state of logger context"""
    internal_logger, logger_1, logger_2 = logger_fixtures()
    internal_logger.info(INFO_STR)
    logger_1.info(CLIENT_INFO_STR)
    logger_2.info(CLIENT_WARNING_STR)
    captured = capsys.readouterr()
    parsed_out = list(filter(lambda x: x, captured.err.split("\n")))
    assert len(parsed_out) == 3
    for log in parsed_out:
        assert format_log_context(pid=-1, job_id="") in log


def test_updated_pid_log_format(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Verify state of logger context after updating process_id"""
    internal_logger, logger_1, logger_2 = logger_fixtures()
    COMPUTE_MODULES_ADAPTER_MANAGER.update_process_id(process_id=2)
    internal_logger.info(INFO_STR)
    logger_1.info(CLIENT_INFO_STR)
    logger_2.info(CLIENT_WARNING_STR)
    captured = capsys.readouterr()
    parsed_out = list(filter(lambda x: x, captured.err.split("\n")))
    assert len(parsed_out) == 3
    for log in parsed_out:
        assert format_log_context(pid=2, job_id="") in log


def test_updated_jobid_log_format(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Verify state of logger context after updating job_id"""
    internal_logger, logger_1, logger_2 = logger_fixtures()
    job_id = str(uuid.uuid4())
    COMPUTE_MODULES_ADAPTER_MANAGER.update_job_id(job_id=job_id)
    internal_logger.info(INFO_STR)
    logger_1.info(CLIENT_INFO_STR)
    logger_2.info(CLIENT_WARNING_STR)
    captured = capsys.readouterr()
    parsed_out = list(filter(lambda x: x, captured.err.split("\n")))
    assert len(parsed_out) == 3
    for log in parsed_out:
        assert format_log_context(pid=-1, job_id=job_id) in log
    # Test clearing now
    COMPUTE_MODULES_ADAPTER_MANAGER.update_job_id(job_id="")
    internal_logger.info(INFO_STR)
    logger_1.info(CLIENT_INFO_STR)
    logger_2.info(CLIENT_WARNING_STR)
    captured = capsys.readouterr()
    parsed_out = list(filter(lambda x: x, captured.err.split("\n")))
    assert len(parsed_out) == 3
    for log in parsed_out:
        assert format_log_context(pid=-1, job_id="") in log
