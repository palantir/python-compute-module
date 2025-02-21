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

import ast
import importlib
import inspect
import json
import logging
import pkgutil
import sys
import types
from typing import Iterator, List, Set

import compute_modules.startup
from compute_modules.function_registry.function import Function
from compute_modules.function_registry.function_registry import add_function, add_functions

LOGGER = logging.getLogger(__name__)


def serialise(src_dir: str) -> str:
    # Disables automatically starting compute module upon importing function annotations
    compute_modules.startup.DISABLE_STARTUP = True

    if src_dir not in sys.path:
        sys.path.append(src_dir)

    py_modules: Set[types.ModuleType] = set(_import_python_modules(src_dir))
    cm_functions: List[Function] = list(_discover_functions(py_modules))
    _validate_functions(cm_functions)
    return _serialise_functions(cm_functions)


def _import_python_modules(directory: str) -> Iterator[types.ModuleType]:
    for module in pkgutil.walk_packages([directory]):
        LOGGER.debug(f"Found {repr(module)}")
        if not module.ispkg:
            LOGGER.debug(f"Importing module {module.name}")
            yield importlib.import_module(module.name)


def _discover_functions(py_modules: Set[types.ModuleType]) -> Iterator[Function]:
    for module in py_modules:
        yield from _discover_decorated_functions(module)
        yield from _discover_manually_registered_functions(module)


def _discover_decorated_functions(py_module: types.ModuleType) -> Iterator[Function]:
    module_attrs = [getattr(py_module, attr) for attr in dir(py_module)]
    for attr in module_attrs:
        if inspect.getmodule(attr) is py_module and isinstance(attr, Function):
            LOGGER.debug(f"Located function {attr.__name__} in module {py_module.__name__}")
            yield attr


def _discover_manually_registered_functions(py_module: types.ModuleType) -> Iterator[Function]:
    try:
        source = inspect.getsource(py_module)
    except OSError:
        LOGGER.warning(f"Could not read source for module {py_module.__name__}")
        # https://stackoverflow.com/questions/13243766/how-to-define-an-empty-generator-function
        return
        yield

    syntax_tree = ast.parse(source)

    for node in ast.walk(syntax_tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name):
            continue
        # Manual function registration entry points
        if not (node.func.id == add_function.__name__ or node.func.id == add_functions.__name__):
            continue
        LOGGER.debug(f"Found call to {node.func.id} in module {py_module.__name__}")

        for arg in node.args:
            if not isinstance(arg, ast.Name):
                continue
            fn = getattr(py_module, arg.id, None)
            if not callable(fn):
                continue

            LOGGER.debug(f"Located function {fn.__name__} in module {py_module.__name__}")
            yield Function(fn)


def _validate_functions(functions: List[Function]) -> None:
    seen_functions: Set[str] = set()
    duplicate_functions: List[str] = []

    for f in functions:
        if f.__name__ in seen_functions:
            duplicate_functions.append(f.__name__)
        else:
            seen_functions.add(f.__name__)

    if len(duplicate_functions) > 0:
        raise ValueError(f"Duplicate function(s) found: {duplicate_functions}")


def _serialise_functions(functions: List[Function]) -> str:
    parsed_schemas = []
    for function in functions:
        LOGGER.debug(f"Serialising function {function.__name__}")
        parsed_schemas.append(function.get_function_schema())
    return json.dumps(parsed_schemas)
