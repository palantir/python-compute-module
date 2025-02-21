#  Copyright 2025 Palantir Technologies, Inc.
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
from typing import Any

import pytest


class JsonFormatter(logging.Formatter):
    def format(self, record: Any) -> str:
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
def custom_formatter() -> JsonFormatter:
    return JsonFormatter()
