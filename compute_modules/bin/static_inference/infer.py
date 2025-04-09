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

import argparse
import ast
import importlib
import inspect
import json
import logging
import os
import pkgutil
import sys
import types
from typing import Any, Dict, Iterator, List, Optional, Set

import compute_modules.startup
from compute_modules.bin.ontology._config_path import get_ontology_config_file
from compute_modules.function_registry.function import Function
from compute_modules.function_registry.function_registry import add_function, add_functions
from compute_modules.function_registry.types import ComputeModuleFunctionSchema

LOGGER = logging.getLogger(__name__)


def infer(
    src_dir: str,
    api_name_type_id_mapping: Dict[str, str],
) -> List[ComputeModuleFunctionSchema]:
    # Disables automatically starting compute module upon importing function annotations
    compute_modules.startup.DISABLE_STARTUP = True

    if src_dir not in sys.path:
        sys.path.append(src_dir)

    py_modules: Set[types.ModuleType] = set(_import_python_modules(src_dir))
    cm_functions: List[Function] = list(_discover_functions(py_modules))
    _validate_functions(cm_functions)
    return _parse_function_schemas(cm_functions, api_name_type_id_mapping)


def _import_python_modules(directory: str) -> Iterator[types.ModuleType]:
    for module in pkgutil.walk_packages([directory]):
        LOGGER.debug(f"Found {repr(module)}")
        if not module.ispkg:
            LOGGER.debug(f"Importing module {module.name}")
            yield importlib.import_module(module.name)


def _discover_functions(
    py_modules: Set[types.ModuleType],
) -> Iterator[Function]:
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
            # Extracting ontology types if `edits=[...]` was provided
            edits_arg = next(filter(lambda k: k.arg == "edits", node.keywords), None)
            parsed_edits: Set[Any] = set()
            _maybe_add_edits(py_module=py_module, edits_arg=edits_arg, parsed_edits=parsed_edits)
            yield Function(fn, list(parsed_edits))


def _maybe_add_edits(
    py_module: types.ModuleType,
    edits_arg: Optional[Any],
    parsed_edits: Set[Any],
) -> None:
    if not edits_arg:
        return
    # edits=[...] literal list syntax
    if isinstance(edits_arg, ast.keyword) and isinstance(edits_arg.value, ast.List):
        for edit in edits_arg.value.elts:
            if not isinstance(edit, ast.Name):
                continue
            parsed_edit = getattr(py_module, edit.id, None)
            if parsed_edit and hasattr(parsed_edit, "api_name") and callable(parsed_edit.api_name):
                parsed_edits.add(parsed_edit)
    # edits=SOME_VAR syntax
    if isinstance(edits_arg, ast.keyword) and isinstance(edits_arg.value, ast.Name):
        edits_list = getattr(py_module, edits_arg.value.id, None)
        if edits_list and isinstance(edits_list, list):
            for edit_type in edits_list:
                if edit_type and hasattr(edit_type, "api_name") and callable(edit_type.api_name):
                    parsed_edits.add(edit_type)


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


def _parse_function_schemas(
    functions: List[Function],
    api_name_type_id_mapping: Dict[str, str],
) -> List[ComputeModuleFunctionSchema]:
    parsed_schemas = []
    for function in functions:
        LOGGER.debug(f"Serialising function {function.__name__}")
        parsed_schemas.append(function.get_function_schema(api_name_type_id_mapping))
    return parsed_schemas


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "source",
        help="Path to the source directory of your compute module",
    )
    parser.add_argument(
        "--ontology-metadata-config",
        required=False,
        help="Path to a configuration file that is used to determine type information for OSDK types. "
        + "Only needed if ontology edits are returned by any functions.",
        dest="ontology_metadata_config_file",
        default=None,
    )
    arguments = parser.parse_args()
    config_file_path = get_ontology_config_file(arguments.ontology_metadata_config_file)
    api_name_type_id_mapping = _get_api_name_type_id_mapping(config_file_path)
    print(
        json.dumps(
            infer(
                src_dir=arguments.source,
                api_name_type_id_mapping=api_name_type_id_mapping,
            )
        )
    )


def _get_api_name_type_id_mapping(config_file_path: str) -> dict[str, str]:
    if not os.path.isfile(config_file_path):
        return {}
    with open(config_file_path) as f:
        config_data = json.load(f)
    return config_data.get("apiNameToTypeId", {})  # type: ignore[no-any-return]


if __name__ == "__main__":
    main()
