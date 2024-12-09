import json
import logging

import pytest


class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "level": record.levelname,
            "process_id": record.process_id,
            "job_id": record.job_id,
            "location": f"{record.filename}:{record.lineno}",
            "message": record.getMessage(),
            "custom_text": "custom-message",
        }
        return json.dumps(log_record)


@pytest.fixture
def custom_formatter():
    return JsonFormatter()
