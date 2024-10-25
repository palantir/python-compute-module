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


import os

BUILD2_TOKEN = "BUILD2_TOKEN"


def retrieve_pipeline_token() -> str:
    """Produces a bearer token that can be used to make calls to access pipeline resources.
    This is only available in pipeline mode.
    """
    if BUILD2_TOKEN not in os.environ:
        raise RuntimeError("Pipeline token not available. Please make sure you are running in Pipeline mode.")
    with open(os.environ["BUILD2_TOKEN"], encoding="utf-8") as f:
        bearer_token = f.read()
    return bearer_token
