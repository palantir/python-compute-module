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


import os
from typing import List

import pytest

from compute_modules.bin.static_inference.infer import infer
from compute_modules.function_registry.types import ComputeModuleFunctionSchema

API_NAME_TYPE_ID_MAPPING = {"DummyOntologyType": "dummy-ontology"}
CURRENT_FILE_PATH = os.path.abspath(__file__)
CURRENT_DIR = os.path.dirname(CURRENT_FILE_PATH)
DECORATED_DIR = os.path.join(CURRENT_DIR, "test_project", "decorated")
MANUALLY_REGISTERED_DIR = os.path.join(CURRENT_DIR, "test_project", "manually_registered")


EXPECTED_DECORATED_RES = [
    {
        "functionName": "ontology_add_function",
        "inputs": [],
        "output": {
            "type": "single",
            "single": {
                "dataType": {"type": "list", "list": {"elementsType": {"ontologyEdit": {}, "type": "ontologyEdit"}}}
            },
        },
        "ontologyProvenance": {"editedObjects": {"dummy-ontology": {}}, "editedLinks": {}},
    },
    {
        "functionName": "return_dict",
        "inputs": [],
        "output": {
            "type": "single",
            "single": {
                "dataType": {
                    "type": "map",
                    "map": {
                        "keysType": {"type": "string", "string": {}},
                        "valuesType": {"type": "string", "string": {}},
                    },
                }
            },
        },
        "ontologyProvenance": None,
    },
    {
        "functionName": "return_list",
        "inputs": [],
        "output": {
            "type": "single",
            "single": {"dataType": {"type": "list", "list": {"elementsType": {"type": "string", "string": {}}}}},
        },
        "ontologyProvenance": None,
    },
    {
        "functionName": "return_set",
        "inputs": [],
        "output": {
            "type": "single",
            "single": {"dataType": {"type": "set", "set": {"elementsType": {"type": "string", "string": {}}}}},
        },
        "ontologyProvenance": None,
    },
    {
        "functionName": "return_byte",
        "inputs": [{"name": "value", "required": True, "constraints": [], "dataType": {"type": "byte", "byte": {}}}],
        "output": {"type": "single", "single": {"dataType": {"type": "byte", "byte": {}}}},
        "ontologyProvenance": None,
    },
    {
        "functionName": "return_double",
        "inputs": [
            {"name": "value", "required": True, "constraints": [], "dataType": {"type": "double", "double": {}}}
        ],
        "output": {"type": "single", "single": {"dataType": {"type": "double", "double": {}}}},
        "ontologyProvenance": None,
    },
    {
        "functionName": "return_long",
        "inputs": [{"name": "value", "required": True, "constraints": [], "dataType": {"type": "long", "long": {}}}],
        "output": {"type": "single", "single": {"dataType": {"type": "long", "long": {}}}},
        "ontologyProvenance": None,
    },
    {
        "functionName": "return_short",
        "inputs": [{"name": "value", "required": True, "constraints": [], "dataType": {"type": "short", "short": {}}}],
        "output": {"type": "single", "single": {"dataType": {"type": "short", "short": {}}}},
        "ontologyProvenance": None,
    },
    {
        "functionName": "return_bool",
        "inputs": [
            {"name": "value", "required": True, "constraints": [], "dataType": {"type": "boolean", "boolean": {}}}
        ],
        "output": {"type": "single", "single": {"dataType": {"type": "boolean", "boolean": {}}}},
        "ontologyProvenance": None,
    },
    {
        "functionName": "return_bytes",
        "inputs": [
            {"name": "value", "required": True, "constraints": [], "dataType": {"type": "binary", "binary": {}}}
        ],
        "output": {"type": "single", "single": {"dataType": {"type": "binary", "binary": {}}}},
        "ontologyProvenance": None,
    },
    {
        "functionName": "return_date",
        "inputs": [{"name": "value", "required": True, "constraints": [], "dataType": {"type": "date", "date": {}}}],
        "output": {"type": "single", "single": {"dataType": {"type": "date", "date": {}}}},
        "ontologyProvenance": None,
    },
    {
        "functionName": "return_datetime",
        "inputs": [
            {"name": "value", "required": True, "constraints": [], "dataType": {"type": "timestamp", "timestamp": {}}}
        ],
        "output": {"type": "single", "single": {"dataType": {"type": "timestamp", "timestamp": {}}}},
        "ontologyProvenance": None,
    },
    {
        "functionName": "return_decimal",
        "inputs": [
            {"name": "value", "required": True, "constraints": [], "dataType": {"type": "decimal", "decimal": {}}}
        ],
        "output": {"type": "single", "single": {"dataType": {"type": "decimal", "decimal": {}}}},
        "ontologyProvenance": None,
    },
    {
        "functionName": "return_float",
        "inputs": [{"name": "value", "required": True, "constraints": [], "dataType": {"type": "float", "float": {}}}],
        "output": {"type": "single", "single": {"dataType": {"type": "float", "float": {}}}},
        "ontologyProvenance": None,
    },
    {
        "functionName": "return_int",
        "inputs": [
            {"name": "value", "required": True, "constraints": [], "dataType": {"type": "integer", "integer": {}}}
        ],
        "output": {"type": "single", "single": {"dataType": {"type": "integer", "integer": {}}}},
        "ontologyProvenance": None,
    },
    {
        "functionName": "return_str",
        "inputs": [
            {"name": "value", "required": True, "constraints": [], "dataType": {"type": "string", "string": {}}}
        ],
        "output": {"type": "single", "single": {"dataType": {"type": "string", "string": {}}}},
        "ontologyProvenance": None,
    },
]

EXPECTED_MANUALLY_REGISTERED_RES = [
    {
        "functionName": "return_dict_length_in_main",
        "inputs": [
            {
                "name": "value",
                "required": True,
                "constraints": [],
                "dataType": {
                    "type": "map",
                    "map": {
                        "keysType": {"type": "string", "string": {}},
                        "valuesType": {"type": "string", "string": {}},
                    },
                },
            }
        ],
        "output": {"type": "single", "single": {"dataType": {"type": "integer", "integer": {}}}},
        "ontologyProvenance": None,
    },
    {
        "functionName": "return_complex_in_main",
        "inputs": [
            {
                "name": "points",
                "required": True,
                "constraints": [],
                "dataType": {
                    "type": "list",
                    "list": {
                        "elementsType": {
                            "type": "anonymousCustomType",
                            "anonymousCustomType": {
                                "fields": {
                                    "x": {"type": "float", "float": {}},
                                    "y": {"type": "float", "float": {}},
                                    "z": {"type": "float", "float": {}},
                                }
                            },
                        }
                    },
                },
            },
            {
                "name": "messages",
                "required": True,
                "constraints": [],
                "dataType": {
                    "type": "anonymousCustomType",
                    "anonymousCustomType": {
                        "fields": {
                            "messages": {
                                "type": "list",
                                "list": {
                                    "elementsType": {
                                        "type": "anonymousCustomType",
                                        "anonymousCustomType": {
                                            "fields": {
                                                "message": {"type": "string", "string": {}},
                                                "from_id": {"type": "integer", "integer": {}},
                                                "to_id": {"type": "integer", "integer": {}},
                                                "timestamp": {"type": "timestamp", "timestamp": {}},
                                            }
                                        },
                                    }
                                },
                            }
                        }
                    },
                },
            },
        ],
        "output": {"type": "single", "single": {"dataType": {"type": "string", "string": {}}}},
        "ontologyProvenance": None,
    },
    {
        "functionName": "return_number_in_main",
        "inputs": [
            {"name": "value", "required": True, "constraints": [], "dataType": {"type": "integer", "integer": {}}}
        ],
        "output": {
            "type": "single",
            "single": {
                "dataType": {
                    "type": "anonymousCustomType",
                    "anonymousCustomType": {"fields": {"value": {"type": "integer", "integer": {}}}},
                }
            },
        },
        "ontologyProvenance": None,
    },
    {
        "functionName": "ontology_edit_function",
        "inputs": [{"name": "name", "required": True, "constraints": [], "dataType": {"type": "string", "string": {}}}],
        "output": {
            "type": "single",
            "single": {
                "dataType": {"type": "list", "list": {"elementsType": {"ontologyEdit": {}, "type": "ontologyEdit"}}}
            },
        },
        "ontologyProvenance": {"editedObjects": {"dummy-ontology": {}}, "editedLinks": {}},
    },
    {
        "functionName": "return_integer_in_main",
        "inputs": [
            {"name": "value", "required": True, "constraints": [], "dataType": {"type": "integer", "integer": {}}}
        ],
        "output": {"type": "single", "single": {"dataType": {"type": "integer", "integer": {}}}},
        "ontologyProvenance": None,
    },
    {
        "functionName": "mixed_1",
        "inputs": [
            {"name": "value", "required": True, "constraints": [], "dataType": {"type": "integer", "integer": {}}}
        ],
        "output": {"type": "single", "single": {"dataType": {"type": "integer", "integer": {}}}},
        "ontologyProvenance": None,
    },
    {
        "functionName": "mixed_2",
        "inputs": [
            {
                "name": "value",
                "required": True,
                "constraints": [],
                "dataType": {"type": "set", "set": {"elementsType": {"type": "integer", "integer": {}}}},
            }
        ],
        "output": {
            "type": "single",
            "single": {"dataType": {"type": "set", "set": {"elementsType": {"type": "integer", "integer": {}}}}},
        },
        "ontologyProvenance": None,
    },
    {
        "functionName": "mixed_3",
        "inputs": [{"name": "value", "required": True, "constraints": [], "dataType": {"type": "byte", "byte": {}}}],
        "output": {"type": "single", "single": {"dataType": {"type": "byte", "byte": {}}}},
        "ontologyProvenance": None,
    },
    {
        "functionName": "mixed_4",
        "inputs": [{"name": "name", "required": True, "constraints": [], "dataType": {"type": "string", "string": {}}}],
        "output": {"type": "single", "single": {"dataType": {"type": "string", "string": {}}}},
        "ontologyProvenance": None,
    },
]
test_cases = [
    # (
    #     DECORATED_DIR,
    #     EXPECTED_DECORATED_RES,
    # ),
    (
        MANUALLY_REGISTERED_DIR,
        EXPECTED_MANUALLY_REGISTERED_RES,
    ),
]


@pytest.mark.parametrize("src_dir, expected_result", test_cases)
def test_infer(src_dir: str, expected_result: List[ComputeModuleFunctionSchema]) -> None:
    res = infer(
        src_dir=src_dir,
        api_name_type_id_mapping=API_NAME_TYPE_ID_MAPPING,
    )
    assert sorted(res, key=lambda x: x["functionName"]) == sorted(expected_result, key=lambda x: x["functionName"])
