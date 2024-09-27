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
from typing import Any
from uuid import UUID

# TODO: add replica ID to default log format
DEFAULT_LOG_FORMAT = (
    "%(levelname)-8s PID: %(process_id)-2s JOB: %(job_id)-36s LOC: %(filename)s:%(lineno)d - %(message)s"
)


# TODO: support for SLS logging format
def create_logger(name: str) -> logging.Logger:
    """Creates a logger that can have its log level set ... and actually work.

    See: https://stackoverflow.com/a/59705351
    """
    logger = logging.getLogger(name)
    # TODO: need a way to inspect the selected container log source so we can modify here accordingly to use a FileHandler
    handler = logging.StreamHandler()
    formatter = logging.Formatter(DEFAULT_LOG_FORMAT)
    handler.setFormatter(formatter)
    logger.handlers.clear()
    logger.addHandler(handler)
    return logger


def create_log_adapter(
    logger: logging.Logger,
    process_id: str = "-1",
    job_id: str = str(UUID(int=0)),
) -> logging.LoggerAdapter[Any]:
    return logging.LoggerAdapter(
        logger=logger,
        extra=dict(
            process_id=process_id,
            job_id=job_id,
        ),
    )


# Wrapper around a logging.LoggerAdapter instance.
# This allows us to obtain a ComputeModulesLoggerAdapter instance just once,
# while having the flexibility to swap out the underlying `logging.LoggerAdapter` being used.
# The use case here is that we want to update the `logging.LoggerAdapter`
# based on the process_id or job_id so that information is emitted as part of the log context
# Technically, this class does not actually extend `logging.LoggerAdapter` but I put that as the
# base class for this so intellisense shows up for normal Logger APIs (e.g., `info`, `debug`, etc.)
class ComputeModulesLoggerAdapter(logging.LoggerAdapter[logging.Logger]):
    "`logging.LoggerAdapter`. This can be used like a normal `logging.Logger` instance"

    def __init__(
        self,
        logger: logging.Logger,
        process_id: int = -1,
        job_id: str = "",
    ) -> None:
        self._logger = logger
        self._process_id = process_id
        self._job_id = job_id
        self._set_log_adapter()

    def _set_log_adapter(self) -> logging.LoggerAdapter[Any]:
        self.adapter = logging.LoggerAdapter(
            logger=self._logger,
            extra=dict(
                process_id=str(self._process_id),
                job_id=self._job_id,
            ),
        )
        return self.adapter

    def _update_process_id(self, process_id: int) -> None:
        self._process_id = process_id
        self._set_log_adapter()

    def _update_job_id(self, job_id: str) -> None:
        self._job_id = job_id
        self._set_log_adapter()

    def __getattr__(self, name: str) -> Any:
        if name.startswith("_"):
            return getattr(self, name)
        return getattr(self.adapter, name)


__all__ = [
    "create_logger",
    "create_log_adapter",
    "DEFAULT_LOG_FORMAT",
    "ComputeModulesLoggerAdapter",
]
