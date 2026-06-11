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
from compute_modules.logging.common import COMPUTE_MODULES_ADAPTER_MANAGER, ComputeModulesLoggerAdapter, SlsFormatter
from tests.conftest import JsonFormatter

from .logging_test_utils import CLIENT_ERROR_STR, CLIENT_INFO_STR, CLIENT_WARNING_STR, INFO_STR

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


def assert_log_params(log: str, process_id: int, job_id: str, session_id: str = "") -> None:
    """Parse log JSON and verify params field contains expected values"""
    log_json = json.loads(log)
    params = log_json["params"]
    assert params["process_id"] == str(process_id), f"Expected process_id {process_id}, got {params['process_id']}"
    assert params["job_id"] == job_id, f"Expected job_id {job_id}, got {params['job_id']}"
    assert params["session_id"] == session_id, f"Expected session_id {session_id}, got {params['session_id']}"


def test_log_params_can_be_added_per_call(capsys: pytest.CaptureFixture[str]) -> None:
    setup_logger_formatter(SlsFormatter())
    COMPUTE_MODULES_ADAPTER_MANAGER.update_process_id(PROCESS_ID)
    COMPUTE_MODULES_ADAPTER_MANAGER.update_job_id("")

    logger = get_logger("test.logger.params-per-call")
    logger.setLevel(logging.INFO)
    logger.info("with params", params={"event_primary_key": "event-1", "row_count": 5})

    logged = json.loads(capsys.readouterr().err)
    assert logged["safe"] is True
    assert logged["params"]["event_primary_key"] == "event-1"
    assert logged["params"]["row_count"] == 5
    assert logged["params"]["process_id"] == str(PROCESS_ID)
    assert logged["params"]["job_id"] == ""


def test_bound_params_are_added_to_every_log_and_per_call_params_win(
    capsys: pytest.CaptureFixture[str],
) -> None:
    setup_logger_formatter(SlsFormatter())
    COMPUTE_MODULES_ADAPTER_MANAGER.update_process_id(PROCESS_ID)
    COMPUTE_MODULES_ADAPTER_MANAGER.update_job_id("")

    logger = get_logger("test.logger.bound-params")
    logger.setLevel(logging.INFO)
    bound_logger = logger.bind(params={"trace_id": "trace-1", "event_primary_key": "default-event"})

    logger.info("without bound params")
    bound_logger.info("with bound params", params={"event_primary_key": "event-2"})

    logged = [json.loads(line) for line in capsys.readouterr().err.splitlines()]
    assert "trace_id" not in logged[0]["params"]
    assert logged[1]["params"]["trace_id"] == "trace-1"
    assert logged[1]["params"]["event_primary_key"] == "event-2"


def test_unsafe_params_are_written_to_unsafe_params_and_mark_log_unsafe(
    capsys: pytest.CaptureFixture[str],
) -> None:
    setup_logger_formatter(SlsFormatter())
    COMPUTE_MODULES_ADAPTER_MANAGER.update_process_id(PROCESS_ID)
    COMPUTE_MODULES_ADAPTER_MANAGER.update_job_id("")

    logger = get_logger("test.logger.unsafe-params")
    logger.setLevel(logging.INFO)
    logger.info(
        "with unsafe params",
        params={"dataset_rid": "ri.foundry.main.dataset.123", "dataset_name": "should-not-be-safe"},
        unsafe_params={"dataset_name": "Customers"},
    )

    logged = json.loads(capsys.readouterr().err)
    assert "safe" not in logged
    assert logged["params"]["dataset_rid"] == "ri.foundry.main.dataset.123"
    assert "dataset_name" not in logged["params"]
    assert logged["unsafeParams"]["dataset_name"] == "Customers"


def test_log_format(capsys: pytest.CaptureFixture[str], custom_formatter: JsonFormatter) -> None:
    """Verify initial state of logger context"""
    COMPUTE_MODULES_ADAPTER_MANAGER.update_process_id(process_id=-1)
    COMPUTE_MODULES_ADAPTER_MANAGER.update_job_id(job_id="")
    internal_logger, logger_1, logger_2 = logger_fixtures()
    internal_logger.info(INFO_STR)
    logger_1.info(CLIENT_INFO_STR)
    logger_2.info(CLIENT_WARNING_STR)
    captured = capsys.readouterr()
    parsed_out = list(filter(lambda x: x, captured.err.split("\n")))
    assert len(parsed_out) == 3
    for log in parsed_out:
        assert_log_params(log, process_id=-1, job_id="")

    COMPUTE_MODULES_ADAPTER_MANAGER.update_process_id(process_id=PROCESS_ID)
    internal_logger.info(INFO_STR)
    logger_1.info(CLIENT_INFO_STR)
    logger_2.info(CLIENT_WARNING_STR)
    captured = capsys.readouterr()
    parsed_out = list(filter(lambda x: x, captured.err.split("\n")))
    assert len(parsed_out) == 3
    for log in parsed_out:
        assert_log_params(log, process_id=PROCESS_ID, job_id="")

    job_id = str(uuid.uuid4())
    COMPUTE_MODULES_ADAPTER_MANAGER.update_job_id(job_id=job_id)
    internal_logger.info(INFO_STR)
    logger_1.info(CLIENT_INFO_STR)
    logger_2.info(CLIENT_WARNING_STR)
    captured = capsys.readouterr()
    parsed_out = list(filter(lambda x: x, captured.err.split("\n")))
    assert len(parsed_out) == 3
    for log in parsed_out:
        assert_log_params(log, process_id=PROCESS_ID, job_id=job_id)

    # Test clearing now
    COMPUTE_MODULES_ADAPTER_MANAGER.update_job_id(job_id="")
    internal_logger.info(INFO_STR)
    logger_1.info(CLIENT_INFO_STR)
    logger_2.info(CLIENT_WARNING_STR)
    captured = capsys.readouterr()
    parsed_out = list(filter(lambda x: x, captured.err.split("\n")))
    assert len(parsed_out) == 3
    for log in parsed_out:
        assert_log_params(log, process_id=PROCESS_ID, job_id="")

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
    assert log_js["message"] == CLIENT_INFO_STR, "Log has wrong message"
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
