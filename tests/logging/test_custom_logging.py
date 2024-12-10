import json
import logging
import pytest

from compute_modules.logging import get_logger, setup_logger
from slslogging import SlsServiceFormatter, UnsafeArg, SafeArg

from .logging_test_utils import CLIENT_DEBUG_STR, CLIENT_INFO_STR


def test_log_custom_format(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """
    TODO
    """

    setup_logger(None, SlsServiceFormatter())
    client_logger = get_logger("twinkle")

    client_logger.setLevel(logging.INFO)
    client_logger.debug(CLIENT_DEBUG_STR)
    client_logger.info(CLIENT_INFO_STR, SafeArg("safe-arg", "green"), UnsafeArg("unsafe-arg", "oliver"))

    logged = capsys.readouterr().err

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
