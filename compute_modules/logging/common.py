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
from typing import TYPE_CHECKING, Any, Dict, Optional, Union

# logging.LoggerAdapter was made generic in 3.11 so we need to determine at runtime
# whether this should be generic or not.
#
# See: https://mypy.readthedocs.io/en/stable/runtime_troubles.html#using-classes-that-are-generic-in-stubs-but-not-at-runtime
#
if TYPE_CHECKING:
    _LoggerAdapter = logging.LoggerAdapter[logging.Logger]
else:
    _LoggerAdapter = logging.LoggerAdapter


# TODO: add replica ID to default log format
DEFAULT_LOG_FORMAT = (
    "%(levelname)-8s PID: %(process_id)-2s JOB: %(job_id)-36s LOC: %(filename)s:%(lineno)d - %(message)s"
)


# TODO: support for log file output (need access to selected log output location)
def _create_logger(name: str) -> logging.Logger:
    """Creates a logger that can have its log level set ... and actually work.

    See: https://stackoverflow.com/a/59705351
    """
    logger = logging.getLogger(name)
    handler = logging.StreamHandler()
    formatter = logging.Formatter(DEFAULT_LOG_FORMAT)
    handler.setFormatter(formatter)
    logger.handlers.clear()
    logger.addHandler(handler)
    return logger


# Wrapper around a logging.LoggerAdapter instance.
# This allows us to obtain a ComputeModulesLoggerAdapter instance just once,
# while having the flexibility to swap out the underlying `logging.LoggerAdapter` being used.
# The use case here is that we want to update the `logging.LoggerAdapter`
# based on the process_id or job_id so that information is emitted as part of the log context
#
# Technically, this class does not actually extend `logging.LoggerAdapter` but I put that as the
# base class for this so intellisense shows up for normal Logger APIs (e.g., `info`, `debug`, etc.).
#
# See: https://docs.python.org/3/howto/logging-cookbook.html#using-loggeradapters-to-impart-contextual-information
class ComputeModulesLoggerAdapter(_LoggerAdapter):
    """Wrapper around Python's `logging.LoggerAdapter` class.
    This can be used like a normal `logging.Logger` instance
    """

    def __init__(
        self,
        logger_name: str,
        process_id: int = -1,
        job_id: str = "",
    ) -> None:
        self._p_logger = _create_logger(logger_name)
        self._p_process_id = process_id
        self._p_job_id = job_id
        self._p_set_log_adapter()

    def _p_set_log_adapter(self) -> None:
        self.adapter = logging.LoggerAdapter(
            logger=self._p_logger,
            extra=dict(
                process_id=str(self._p_process_id),
                job_id=self._p_job_id,
            ),
        )

    def _p_update_process_id(self, process_id: int) -> None:
        self._p_process_id = process_id
        self._p_set_log_adapter()

    def _p_update_job_id(self, job_id: str) -> None:
        self._p_job_id = job_id
        self._p_set_log_adapter()

    def __getattr__(self, name: str) -> Any:
        if name.startswith("_p_"):
            return getattr(self, name)
        return getattr(self.adapter, name)


class ComputeModulesAdapterManager(object):
    adapters: Dict[str, ComputeModulesLoggerAdapter] = {}

    def get_logger(self, name: str, default_level: Optional[Union[str, int]] = None) -> ComputeModulesLoggerAdapter:
        """Get a logger by name. If it does not already exist, creates it first"""
        if name not in self.adapters:
            self.adapters[name] = ComputeModulesLoggerAdapter(name)
            if default_level:
                self.adapters[name].setLevel(default_level)
        return self.adapters[name]

    def update_process_id(self, process_id: int) -> None:
        """Update process_id for all registered adapters"""
        for adapter in self.adapters.values():
            adapter._p_update_process_id(process_id=process_id)

    def update_job_id(self, job_id: str) -> None:
        """Update job_id for all registered adapters"""
        for adapter in self.adapters.values():
            adapter._p_update_job_id(job_id=job_id)


COMPUTE_MODULES_ADAPTER_MANAGER = ComputeModulesAdapterManager()


__all__ = [
    "COMPUTE_MODULES_ADAPTER_MANAGER",
    "ComputeModulesLoggerAdapter",
]
