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


import json
import logging
import uuid

import pytest

from compute_modules.logging import get_logger, internal, setup_logger_formatter
from compute_modules.logging.common import (
    COMPUTE_MODULES_ADAPTER_MANAGER,
    DEFAULT_LOG_FORMAT,
    ComputeModulesLoggerAdapter,
)
from tests.conftest import JsonFormatter

from .logging_test_utils import CLIENT_ERROR_STR, CLIENT_INFO_STR, CLIENT_WARNING_STR, INFO_STR

logging.basicConfig(format=DEFAULT_LOG_FORMAT)

PROCESS_ID = 12345


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
    return f"PID: {pid:<6} JOB: {job_id:<37}"


def test_log_format(capsys: pytest.CaptureFixture[str], custom_formatter: JsonFormatter) -> None:
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
    COMPUTE_MODULES_ADAPTER_MANAGER.update_process_id(process_id=PROCESS_ID)
    internal_logger.info(INFO_STR)
    logger_1.info(CLIENT_INFO_STR)
    logger_2.info(CLIENT_WARNING_STR)
    captured = capsys.readouterr()
    parsed_out = list(filter(lambda x: x, captured.err.split("\n")))
    assert len(parsed_out) == 3
    for log in parsed_out:
        assert format_log_context(pid=PROCESS_ID, job_id="") in log
    job_id = str(uuid.uuid4())
    COMPUTE_MODULES_ADAPTER_MANAGER.update_job_id(job_id=job_id)
    internal_logger.info(INFO_STR)
    logger_1.info(CLIENT_INFO_STR)
    logger_2.info(CLIENT_WARNING_STR)
    captured = capsys.readouterr()
    parsed_out = list(filter(lambda x: x, captured.err.split("\n")))
    assert len(parsed_out) == 3
    for log in parsed_out:
        assert format_log_context(pid=PROCESS_ID, job_id=job_id) in log
    # Test clearing now
    COMPUTE_MODULES_ADAPTER_MANAGER.update_job_id(job_id="")
    internal_logger.info(INFO_STR)
    logger_1.info(CLIENT_INFO_STR)
    logger_2.info(CLIENT_WARNING_STR)
    captured = capsys.readouterr()
    parsed_out = list(filter(lambda x: x, captured.err.split("\n")))
    assert len(parsed_out) == 3
    for log in parsed_out:
        assert format_log_context(pid=PROCESS_ID, job_id="") in log

    # Test Custom Formatting
    # TODO split out into custom test once ComputeModuleLoggingAdapter made fixture to avoid capsys errors

    client_logger = get_logger("twinkle")
    client_logger.setLevel(logging.INFO)
    setup_logger_formatter(custom_formatter)

    job_id = str(uuid.uuid4())
    process_id = 5

    COMPUTE_MODULES_ADAPTER_MANAGER.update_process_id(process_id)
    COMPUTE_MODULES_ADAPTER_MANAGER.update_job_id(job_id)

    client_logger.info(CLIENT_INFO_STR)

    logged = capsys.readouterr().err

    try:
        log_js = json.loads(logged)
        valid_json = True
    except ValueError:
        valid_json = False

    # Test external logger
    assert valid_json, "Logs should be json"
    assert log_js["level"] == "INFO", "Log has wrong level"
    assert log_js["message"] == CLIENT_INFO_STR, "SLS Log has wrong message"
    assert log_js["job_id"] == job_id
    assert log_js["process_id"] == str(process_id)

    internal_logger = internal.get_internal_logger()

    internal_logger.error(CLIENT_ERROR_STR)
    internal_logged = capsys.readouterr().err

    try:
        interal_log_js = json.loads(internal_logged)
        internal_valid_json = True
    except ValueError:
        internal_valid_json = False

    # Test internal logger
    assert internal_valid_json, "Logs should be json"
    assert interal_log_js["level"] == "ERROR", "Log has wrong level"
    assert interal_log_js["message"] == CLIENT_ERROR_STR, "Log has wrong message"
    assert interal_log_js["job_id"] == job_id
    assert interal_log_js["process_id"] == str(process_id)
