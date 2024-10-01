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


from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class QueryContext:
    """Metadata for the job being executed that is not included in the event payload"""

    authHeader: str
    """Foundry auth token that can be used to call other services within Foundry.
    Only available in certain modes
    """

    jobId: str
    """The unique identifier for the given job"""

    tempCredsAuthToken: Optional[str] = None
    """A temporary token that is used with the Foundry data sidecar."""

    CLIENT_ID: Optional[str] = None
    """Client ID of the third party application associated with this compute module. 
    Present if compute module is configured to have application's permissions. 
    Use this to get a Foundry scoped token from your third party application service user.
    """

    CLIENT_SECRET: Optional[str] = None
    """Client secret of the third party application associated with this compute module. 
    Present if compute module is configured to have application's permissions. 
    Use this to get a Foundry scoped token from your third party application service user.
    """

    sources: Optional[Dict[str, Any]] = None
    """dict containing the metadata of any sources configured for this compute module."""
