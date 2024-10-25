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
from os import environ
from typing import Dict

from .types import PipelineResource

RESOURCE_ALIAS_MAP = "RESOURCE_ALIAS_MAP"
RESOURCE_ALIAS_NOT_FOUND = """No resource aliases mounted.
 This implies the RESOURCE_ALIAS_MAP environment variable has not been set,
 or your Compute Module is not running in Pipelines mode.
 Please ensure you have set resources mounted on the Compute Module."""


def get_pipeline_resources() -> Dict[str, PipelineResource]:
    """Returns a dictionary of resource alias identifier -> Resource.
    The identifier(s) in this dict correspond to the identifier used for an input/output
    defined in the Configure tab of your 'Pipelines' compute module
    """
    if RESOURCE_ALIAS_MAP not in environ:
        raise RuntimeError(RESOURCE_ALIAS_NOT_FOUND)
    with open(environ[RESOURCE_ALIAS_MAP], encoding="utf-8") as f:
        resource_alias_map_raw = json.load(f)
    return {key: PipelineResource(**value) for key, value in resource_alias_map_raw.items()}
