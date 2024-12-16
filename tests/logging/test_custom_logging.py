import json
import logging
from typing import Dict
import pytest

from compute_modules.logging import get_logger, setup_logger
from slslogging import SlsServiceFormatter, UnsafeArg, SafeArg

from compute_modules.logging.common import COMPUTE_MODULES_ADAPTER_MANAGER

from .logging_test_utils import CLIENT_DEBUG_STR, CLIENT_INFO_STR


class CustomSls(SlsServiceFormatter):

   

    def formatted_fields(self) -> Dict[str, str]:
        return {
            "level": "%(levelname)s",
            "jobID": "%(job_id)s",
            "processID": "%(process_id)s",
            "origin": f"{self.origin_prefix}%(name)s",
            "thread": "%(threadName)s",
            "message": "%(msg)s",  # msg contains the unformatted message
        }


def test_log_custom_format(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """
    Test if SlsServiceFormatter is correctly setup
    """

    #setup_logger(formatter= CustomSls())
    client_logger = get_logger("twinkle")
    COMPUTE_MODULES_ADAPTER_MANAGER.update_process_id(process_id=13)
    COMPUTE_MODULES_ADAPTER_MANAGER.update_job_id("world")

    client_logger.setLevel(logging.INFO)
    client_logger.debug(CLIENT_DEBUG_STR)
    client_logger.info(CLIENT_INFO_STR) #SafeArg("safe-arg", "green"), UnsafeArg("unsafe-arg", "oliver"))

    logged = caplog.text

    assert logged !=''

    try:
        log_js = json.loads(logged)
        valid_json = True
    except ValueError:
        valid_json = False

    assert valid_json, "SLS Formatted logs should be json"
    assert log_js["level"] == "INFO", "SLS Log has wrong level"
    assert log_js["message"] == CLIENT_INFO_STR, "SLS Log has wrong message"
    assert log_js["origin"] == "python:twinkle", "SLS Log has wrong origin"
    assert log_js["params"] == {"safe-arg": "green"}
    assert log_js["unsafeParams"] == {"unsafe-arg": "oliver"}
