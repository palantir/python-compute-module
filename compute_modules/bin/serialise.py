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
from typing import Dict, Iterator, List, Optional, Set

import compute_modules.startup
from compute_modules.function_registry.function import Function
from compute_modules.function_registry.function_registry import add_function, add_functions

from .ontology._types import ObjectTypeMetadata
from .ontology.metadata_loader import load_object_type_metadata

LOGGER = logging.getLogger(__name__)


def serialise(
    src_dir: str,
    foundry_url: Optional[str],
    token: Optional[str],
    object_type_rids: List[str],
    link_type_rids: List[str],
) -> str:
    # Disables automatically starting compute module upon importing function annotations
    compute_modules.startup.DISABLE_STARTUP = True

    if src_dir not in sys.path:
        sys.path.append(src_dir)

    # TODO: use ontology_metadata to write ... something. Initially thought add to each function schema but now not sure since it'll be the same for every function in a CM
    onntology_metadata = _maybe_load_metadata(
        foundry_url=foundry_url,
        token=token,
        object_type_rids=object_type_rids,
        link_type_rids=link_type_rids,
    )
    api_name_type_id_mapping = _get_api_name_type_id_mapping(onntology_metadata)
    py_modules: Set[types.ModuleType] = set(_import_python_modules(src_dir))
    cm_functions: List[Function] = list(_discover_functions(py_modules))
    _validate_functions(cm_functions)
    return _serialise_functions(cm_functions, api_name_type_id_mapping)


def _get_api_name_type_id_mapping(
    ontology_metadata: Dict[str, ObjectTypeMetadata],
) -> Dict[str, str]:
    res = {}
    for metadata in ontology_metadata.values():
        if metadata.api_name in res:
            raise ValueError(f"Duplicate api name found in ontology metadata: {metadata.api_name}")
        res[metadata.api_name] = metadata.type_id
    return res


def _maybe_load_metadata(
    foundry_url: Optional[str],
    token: Optional[str],
    object_type_rids: List[str],
    link_type_rids: List[str],
) -> Dict[str, ObjectTypeMetadata]:
    if not (object_type_rids or link_type_rids):
        return {}
    if not foundry_url:
        raise RuntimeError("Missing foundry_url param; cannot load ontology metadata")
    if not token:
        raise RuntimeError("Missing token param; cannot load ontology metadata")
    return load_object_type_metadata(
        foundry_url=foundry_url,
        token=token,
        object_type_rids=object_type_rids,
        link_type_rids=link_type_rids,
    )


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
            parsed_edits = set()
            if edits_arg and isinstance(edits_arg, ast.keyword) and isinstance(edits_arg.value, ast.List):
                for edit in edits_arg.value.elts:
                    if not isinstance(edit, ast.Name):
                        continue
                    parsed_edit = getattr(py_module, edit.id, None)
                    if parsed_edit and hasattr(parsed_edit, "api_name") and callable(parsed_edit.api_name):
                        parsed_edits.add(parsed_edit)
            yield Function(fn, parsed_edits)


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


def _serialise_functions(
    functions: List[Function],
    api_name_type_id_mapping: Dict[str, str],
) -> str:
    parsed_schemas = []
    for function in functions:
        LOGGER.debug(f"Serialising function {function.__name__}")
        parsed_schemas.append(function.get_function_schema(api_name_type_id_mapping))
    return json.dumps(parsed_schemas)
