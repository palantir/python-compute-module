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
from typing import Optional, Union


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
    _ROOT_LOGGER.setLevel(level=level)


def get_internal_logger(logger_name: str, parent: Optional[logging.Logger] = None) -> logging.Logger:
    """Produces a Logger that is a child of the parent Logger provided.
    If no parent logger is provided, then _ROOT_LOGGER is used as the parent.
    This is useful because child loggers inherit configurations from their ancestors,
    while also providing additional information about the source of a log in the log itself.

    For internal (within compute_modules library) use only.
    """
    my_parent = parent or _ROOT_LOGGER
    return my_parent.getChild(logger_name)


# TODO: add instance/replica ID to root logger
_ROOT_LOGGER = _create_logger(
    name="compute_modules",
    format="%(levelname)s:%(name)s:%(filename)s:%(lineno)d:%(message)s",
)
_set_log_level(logging.ERROR)


__all__ = [
    "get_internal_logger",
    "_set_log_level",
]
