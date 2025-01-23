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
import threading
from typing import TYPE_CHECKING, Any, Dict, MutableMapping, Optional, Tuple, Union

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
    "%(levelname)-8s PID: %(process_id)-6s JOB: %(job_id)-36s LOC: %(filename)s:%(lineno)d - %(message)s"
)

LOG_FORMATTER = None


def _setup_logger_formatter(
    formatter: logging.Formatter,
) -> None:
    if formatter:
        global LOG_FORMATTER
        LOG_FORMATTER = formatter

    for adapter in COMPUTE_MODULES_ADAPTER_MANAGER.adapters.values():
        for handler in adapter.logger.handlers:
            handler.setFormatter(LOG_FORMATTER)


# TODO: support for log file output (need access to selected log output location)
def _create_logger(name: str) -> logging.Logger:
    """Creates a logger that can have its log level set ... and actually work.

    See: https://stackoverflow.com/a/59705351
    """
    logger = logging.getLogger(name)
    handler = logging.StreamHandler()
    formatter = LOG_FORMATTER if LOG_FORMATTER else logging.Formatter(DEFAULT_LOG_FORMAT)
    handler.setFormatter(formatter)
    logger.handlers.clear()
    logger.addHandler(handler)

    return logger


THREAD_LOCAL = threading.local()


def set_thread_local_data(key: str, value: str) -> None:
    setattr(THREAD_LOCAL, key, value)


def get_thread_local_data(key: str, default: str) -> str:
    return getattr(THREAD_LOCAL, key, default)


# Custom LoggerAdapter to inject job- & thread/process-specific information into log lines
#
# See: https://docs.python.org/3/howto/logging-cookbook.html#using-loggeradapters-to-impart-contextual-information
class ComputeModulesLoggerAdapter(_LoggerAdapter):
    """Wrapper around Python's `logging.LoggerAdapter` class.
    This can be used like a normal `logging.Logger` instance
    """

    def __init__(
        self,
        logger_name: str,
    ) -> None:
        # Need to pass empty dict as `extra` param for 3.9 support
        super().__init__(_create_logger(logger_name), dict())

    def process(self, msg: str, kwargs: MutableMapping[str, Any]) -> Tuple[str, MutableMapping[str, Any]]:
        custom_data = {
            "process_id": str(get_thread_local_data("process_id", "-1")),
            "job_id": str(get_thread_local_data("job_id", "")),
        }
        kwargs["extra"] = kwargs.get("extra", {})
        kwargs["extra"].update(custom_data)
        return msg, kwargs


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
        set_thread_local_data("process_id", str(process_id))

    def update_job_id(self, job_id: str) -> None:
        """Update job_id for all registered adapters"""
        set_thread_local_data("job_id", str(job_id))


COMPUTE_MODULES_ADAPTER_MANAGER = ComputeModulesAdapterManager()


__all__ = [
    "COMPUTE_MODULES_ADAPTER_MANAGER",
    "ComputeModulesLoggerAdapter",
    "_setup_logger_formatter",
]
