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
from typing import Any, Optional, Union
from uuid import UUID


def _create_logger(name: str, format: Optional[str] = None) -> logging.Logger:
    """Creates a logger that can have its log level set ... and actually work.

    See: https://stackoverflow.com/a/59705351
    """
    logger = logging.getLogger(name)
    # TODO: need a way to inspect the selected container log source so we can modify here accordingly to use a FileHandler
    handler = logging.StreamHandler()
    formatter = logging.Formatter(format)
    handler.setFormatter(formatter)
    logger.handlers.clear()
    logger.addHandler(handler)
    return logger


def _set_log_level(level: Union[str, int]) -> None:
    """Set the log level of the compute_modules logger"""
    INTERNAL_ROOT_LOGGER.setLevel(level=level)


def create_log_adapter(
    process_id: str = "-1",
    job_id: str = str(UUID(int=0)),
) -> logging.LoggerAdapter[Any]:
    return logging.LoggerAdapter(
        logger=INTERNAL_ROOT_LOGGER,
        extra=dict(
            process_id=process_id,
            job_id=job_id,
        ),
    )


# TODO: add instance/replica ID to root logger
# DO NOT USE INTERNAL_ROOT_LOGGER DIRECTLY. You will get an error
# Use `create_log_adapter`; this will create a wrapper that provides contextural information to the logs
# See: https://docs.python.org/3/howto/logging-cookbook.html#using-loggeradapters-to-impart-contextual-information
INTERNAL_ROOT_LOGGER = _create_logger(
    name="compute_modules",
    format="%(levelname)-8s PID: %(process_id)-2s JOB: %(job_id)-36s LOC: %(filename)s:%(lineno)d - %(message)s",
)
_set_log_level(logging.ERROR)


__all__ = [
    "create_log_adapter",
    "_set_log_level",
]
