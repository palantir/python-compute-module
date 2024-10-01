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
from typing import Union

from .common import COMPUTE_MODULES_ADAPTER_MANAGER, ComputeModulesLoggerAdapter

INTERNAL_LOGGER_ADAPTER = None


def set_internal_log_level(level: Union[str, int]) -> None:
    """Set the log level of the compute_modules_internal logger"""
    get_internal_logger().setLevel(level=level)


def get_internal_logger() -> ComputeModulesLoggerAdapter:
    """Provides the internal ComputeModulesLoggerAdapter singleton"""
    global INTERNAL_LOGGER_ADAPTER
    if not INTERNAL_LOGGER_ADAPTER:
        INTERNAL_LOGGER_ADAPTER = COMPUTE_MODULES_ADAPTER_MANAGER.get_logger(
            "compute_modules_internal",
            default_level=logging.ERROR,
        )
    return INTERNAL_LOGGER_ADAPTER


__all__ = [
    "get_internal_logger",
    "set_internal_log_level",
]
