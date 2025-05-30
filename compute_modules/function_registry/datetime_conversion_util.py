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


from datetime import datetime, timezone


class DatetimeConversionUtil:
    DATETIME_FORMAT_STRING = "%Y-%m-%dT%H:%M:%SZ"

    @staticmethod
    def datetime_to_string(datetime_obj: datetime) -> str:
        obj = datetime_obj.astimezone(timezone.utc)
        # Format as ISO 8601 string with 'Z' suffix
        return obj.strftime(DatetimeConversionUtil.DATETIME_FORMAT_STRING)

    @staticmethod
    def string_to_datetime(datetime_string: str) -> datetime:
        return datetime.strptime(datetime_string, DatetimeConversionUtil.DATETIME_FORMAT_STRING)
