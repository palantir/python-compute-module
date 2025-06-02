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
from datetime import date, datetime
from typing import Any

from compute_modules.function_registry.datetime_conversion_util import DatetimeConversionUtil


class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj: Any) -> Any:
        if isinstance(obj, datetime):
            return DatetimeConversionUtil.datetime_to_string(obj)
        if isinstance(obj, date):
            return obj.isoformat()
        if isinstance(obj, list):
            return [self.default(item) for item in obj]
        if isinstance(obj, dict):
            return {k: self.default(v) for k, v in obj.items()}
        return obj
