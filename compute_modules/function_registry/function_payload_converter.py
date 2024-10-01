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
import typing

from .types import PythonClassNode

logger = logging.getLogger(__name__)


def convert_payload(
    raw_payload: typing.Any,
    class_tree: PythonClassNode,
) -> typing.Any:
    try:
        if raw_payload is None:
            return None
        # No children indicates raw_payload should be a primtive type
        if class_tree["children"] is None:
            return class_tree["constructor"](raw_payload)
        type_constructor = class_tree["constructor"]
        if type_constructor is list:
            child_class_tree = class_tree["children"]["list"]
            return list([convert_payload(el, child_class_tree) for el in raw_payload])
        if type_constructor is dict:
            key_class_tree = class_tree["children"]["key"]
            value_class_tree = class_tree["children"]["value"]
            return {
                convert_payload(key, key_class_tree): convert_payload(value, value_class_tree)
                for key, value in raw_payload.items()
            }
        if type_constructor is typing.Optional:
            return raw_payload
        if type_constructor is set:
            child_class_tree = class_tree["children"]["set"]
            return set([convert_payload(el, child_class_tree) for el in raw_payload])
        # Complex class
        converted_children = {}
        for child_key, child_class_tree in class_tree["children"].items():
            converted_children[child_key] = convert_payload(raw_payload[child_key], child_class_tree)
        return type_constructor(**converted_children)
    except Exception as e:
        logger.error(f"Error converting {raw_payload} to type {class_tree['constructor']}")
        raise e
