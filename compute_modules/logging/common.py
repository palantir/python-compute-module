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


import json
import logging
import os
import threading
from collections.abc import Mapping, MutableMapping
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

# logging.LoggerAdapter was made generic in 3.11 so we need to determine at runtime
# whether this should be generic or not.
#
# See: https://mypy.readthedocs.io/en/stable/runtime_troubles.html#using-classes-that-are-generic-in-stubs-but-not-at-runtime
#
if TYPE_CHECKING:
    _LoggerAdapter = logging.LoggerAdapter[logging.Logger]
else:
    _LoggerAdapter = logging.LoggerAdapter

DEFAULT_LOG_FORMAT = "%(message)s"
DEFAULT_LOG_STRING_FORMATTER = logging.Formatter(DEFAULT_LOG_FORMAT)
SLS_PARAMS_KEY = "params"
SLS_UNSAFE_PARAMS_KEY = "unsafeParams"


class SlsFormatter(logging.Formatter):
    """Custom SLS formatter for structured logging by sidecar"""

    def __init__(self) -> None:
        super().__init__()
        self.string_formatter = DEFAULT_LOG_STRING_FORMATTER

    def format(self, record: Any) -> str:
        # Use the default string formatter for the message field
        formatted_message = self.string_formatter.format(record)

        unsafe_params = getattr(record, SLS_UNSAFE_PARAMS_KEY, {})
        log_entry = {
            "type": getattr(record, "service_type", "service.1"),
            "level": record.levelname,
            "time": datetime.now(timezone.utc).isoformat(),
            "origin": f"{record.filename}:{record.lineno}",
            "thread": threading.current_thread().name,
            SLS_PARAMS_KEY: getattr(record, SLS_PARAMS_KEY, {}),
            "message": formatted_message,
        }
        if unsafe_params:
            log_entry[SLS_UNSAFE_PARAMS_KEY] = unsafe_params
        else:
            log_entry["safe"] = True
        return json.dumps(log_entry, default=str)


SLS_FORMATTER = SlsFormatter()
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
    formatter = LOG_FORMATTER if LOG_FORMATTER else SLS_FORMATTER
    handler.setFormatter(formatter)
    logger.handlers.clear()
    logger.addHandler(handler)

    return logger


THREAD_LOCAL = threading.local()


def set_thread_local_data(key: str, value: str) -> None:
    setattr(THREAD_LOCAL, key, value)


def get_thread_local_data(key: str, default: str) -> str:
    return getattr(THREAD_LOCAL, key, default)


def _copy_mapping(name: str, value: object) -> dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise TypeError(f"{name} must be a mapping, got {type(value).__name__}")
    return dict(value)


def _pop_mapping(kwargs: MutableMapping[str, Any], name: str) -> dict[str, Any]:
    return _copy_mapping(name, kwargs.pop(name, None))


def _remove_unsafe_keys(params: dict[str, Any], unsafe_params: Mapping[str, Any]) -> None:
    for key in unsafe_params:
        params.pop(key, None)


def _runtime_params() -> dict[str, str]:
    return {
        "process_id": str(get_thread_local_data("process_id", "-1")),
        "job_id": str(get_thread_local_data("job_id", "")),
        "session_id": os.environ.get("COMPUTE_SESSION_ID", ""),
    }


def _log_record_extra(
    extra: object,
    runtime_params: Mapping[str, str],
    params: Mapping[str, Any],
    unsafe_params: Mapping[str, Any],
) -> dict[str, Any]:
    record_extra = _copy_mapping("extra", extra)
    record_extra.update(runtime_params)
    record_extra[SLS_PARAMS_KEY] = dict(params)
    if unsafe_params:
        record_extra[SLS_UNSAFE_PARAMS_KEY] = dict(unsafe_params)
    return record_extra


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
        params: Mapping[str, Any] | None = None,
        unsafe_params: Mapping[str, Any] | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        super().__init__(logger if logger else _create_logger(logger_name), {})
        self._params = _copy_mapping("params", params)
        self._unsafe_params = _copy_mapping("unsafe_params", unsafe_params)

    def bind(
        self,
        params: Mapping[str, Any] | None = None,
        unsafe_params: Mapping[str, Any] | None = None,
    ) -> "ComputeModulesLoggerAdapter":
        """Return a logger adapter with params added to every SLS log entry.

        Bound params are immutable defaults: per-call params with the same key
        take precedence.
        """
        merged_params = {
            **self._params,
            **_copy_mapping("params", params),
        }
        merged_unsafe_params = {
            **self._unsafe_params,
            **_copy_mapping("unsafe_params", unsafe_params),
        }
        return ComputeModulesLoggerAdapter(
            self.logger.name,
            params=merged_params,
            unsafe_params=merged_unsafe_params,
            logger=self.logger,
        )

    def process(self, msg: Any, kwargs: MutableMapping[str, Any]) -> tuple[Any, MutableMapping[str, Any]]:
        runtime_params = _runtime_params()
        params = {
            **runtime_params,
            **self._params,
            **_pop_mapping(kwargs, SLS_PARAMS_KEY),
        }
        unsafe_params = {
            **self._unsafe_params,
            **_pop_mapping(kwargs, "unsafe_params"),
        }
        _remove_unsafe_keys(params, unsafe_params)

        kwargs["extra"] = _log_record_extra(kwargs.get("extra"), runtime_params, params, unsafe_params)

        return msg, kwargs


class ComputeModulesAdapterManager(object):
    adapters: dict[str, ComputeModulesLoggerAdapter] = {}

    def get_logger(self, name: str, default_level: str | int | None = None) -> ComputeModulesLoggerAdapter:
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
