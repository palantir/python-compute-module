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


from .common import ComputeModulesLoggerAdapter, create_logger


def get_logger() -> ComputeModulesLoggerAdapter:
    """Creates a logger instance for use within a compute module"""
    return PUBLIC_LOGGER_ADAPTER


# DO NOT USE PUBLIC_LOGGER DIRECTLY. You will get an error
# Use `create_log_adapter`; this will create a wrapper that provides contextural information to the logs
# See: https://docs.python.org/3/howto/logging-cookbook.html#using-loggeradapters-to-impart-contextual-information
PUBLIC_LOGGER = create_logger("compute_modules")
PUBLIC_LOGGER_ADAPTER = ComputeModulesLoggerAdapter(logger=PUBLIC_LOGGER)


__all__ = [
    "get_logger",
]
