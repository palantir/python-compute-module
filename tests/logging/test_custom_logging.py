import json
import logging
import pytest
from typing import Dict
from uuid import uuid4

from compute_modules.logging import get_logger, setup_logger_formatter, internal
from compute_modules.logging.common import COMPUTE_MODULES_ADAPTER_MANAGER
from slslogging import SlsServiceFormatter, SafeArg, UnsafeArg

from .logging_test_utils import CLIENT_ERROR_STR, CLIENT_INFO_STR


class CustomSls(SlsServiceFormatter):
    def formatted_fields(self) -> Dict[str, str]:
        return {
            "level": "%(levelname)s",
            "jobId": "%(job_id)s",
            "processId": "%(process_id)s",
            "origin": f"{self.origin_prefix}%(name)s",
            "thread": "%(threadName)s",
            "message": "%(msg)s",  # msg contains the unformatted message
        }


def test_log_custom_format(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """
    Test if library integrates with a custom formatter
    """

    setup_logger_formatter(CustomSls())
    client_logger = get_logger("twinkle")
    client_logger.setLevel(logging.INFO)

    job_id = str(uuid4())
    process_id = 5

    COMPUTE_MODULES_ADAPTER_MANAGER.update_process_id(process_id)
    COMPUTE_MODULES_ADAPTER_MANAGER.update_job_id(job_id)

    client_logger.info(CLIENT_INFO_STR, SafeArg("safe-arg", "green"), UnsafeArg("unsafe-arg", "oliver"))

    logged = capsys.readouterr().err

    try:
        log_js = json.loads(logged)
        valid_json = True
    except ValueError:
        valid_json = False

    # Test external logger
    assert valid_json, "SLS Formatted logs should be json"
    assert log_js["level"] == "INFO", "SLS Log has wrong level"
    assert log_js["message"] == CLIENT_INFO_STR, "SLS Log has wrong message"
    assert log_js["origin"] == "python:twinkle", "SLS Log has wrong origin"
    assert log_js["jobId"] == job_id
    assert log_js["processId"] == str(process_id)
    assert log_js["params"] == {"safe-arg": "green"}
    assert log_js["unsafeParams"] == {"unsafe-arg": "oliver"}

    internal_logger = internal.get_internal_logger()
    internal_logger.error(CLIENT_ERROR_STR)

    internal_logged = capsys.readouterr().err

    try:
        interal_log_js = json.loads(internal_logged)
        internal_valid_json = True
    except ValueError:
        internal_valid_json = False

    # Test internal logger
    assert internal_valid_json, "Internal logs should be SLS formatted json"
    assert interal_log_js["level"] == "ERROR", "Internal Log has wrong level"
    assert interal_log_js["message"] == CLIENT_ERROR_STR, "Internal Log has wrong message"
    assert interal_log_js["origin"] == "python:compute_modules_internal", "Internal Log has wrong origin"
    assert interal_log_js["jobId"] == job_id
    assert interal_log_js["processId"] == str(process_id)
