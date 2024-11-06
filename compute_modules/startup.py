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
from multiprocessing.pool import Pool
from typing import Any, Dict, Optional

from compute_modules.client.internal_query_client import InternalQueryService
from compute_modules.function_registry.function_registry import (
    FUNCTION_SCHEMA_CONVERSIONS,
    FUNCTION_SCHEMAS,
    IS_FUNCTION_CONTEXT_TYPED,
    REGISTERED_FUNCTIONS,
    STREAMING,
)

QUERY_CLIENT: Optional[InternalQueryService] = None

# The main process creates the initial InternalQueryService instance,
# which is used to post the function schema and poll for jobs.
#
# We then spin up a Pool of worker processes that all create their own sessions.
# When a job is received by the main process, that job is delegated to a worker.
# The worker then processes that job and posts the result back to the runtime using its own session.
#
# This library supports streaming responses via generators.
# Python passes data between processes by using `pickle` to serialize the data.
# Generators cannot be pickled, so we cannot pass the result of streaming functions back to the parent process.
# As a workaround, the worker process is given a session only for posting job results back to the runtime.


def _handle_job(job: Dict[str, Any]) -> None:
    """Helper function to be called by pool.apply_async since python can't serialize methods"""
    global QUERY_CLIENT
    assert QUERY_CLIENT, "QUERY_CLIENT is uninitialized"
    QUERY_CLIENT.handle_job(job=job)


def _get_and_schedule_job(pool: Pool) -> None:
    """Try to get a job and schedule to the process pool"""
    global QUERY_CLIENT
    assert QUERY_CLIENT, "QUERY_CLIENT is uninitialized"
    job = None
    try:
        job = QUERY_CLIENT.get_job_or_none()
    except Exception as e:
        QUERY_CLIENT.logger.warning(f"Exception occurred while fetching job: {str(e)}")
    if job:
        QUERY_CLIENT.logger.debug(f"Got a job: {job}")
        pool.apply_async(_handle_job, (job,))


def _worker_init() -> None:
    """Create a new session for each worker"""
    global QUERY_CLIENT
    assert QUERY_CLIENT, "QUERY_CLIENT is uninitialized"
    QUERY_CLIENT.init_session()
    QUERY_CLIENT._set_logger_process_id(os.getpid())


def start_compute_module() -> None:
    """Starts a Compute Module that will Poll for jobs indefinitely"""
    global QUERY_CLIENT
    QUERY_CLIENT = InternalQueryService(
        registered_functions=REGISTERED_FUNCTIONS,
        function_schemas=FUNCTION_SCHEMAS,
        function_schema_conversions=FUNCTION_SCHEMA_CONVERSIONS,
        is_function_context_typed=IS_FUNCTION_CONTEXT_TYPED,
        streaming=STREAMING,
    )
    QUERY_CLIENT.post_query_schemas()
    QUERY_CLIENT.logger.info(f"Starting to poll for jobs with concurrency {QUERY_CLIENT.concurrency}")
    with Pool(QUERY_CLIENT.concurrency, initializer=_worker_init) as pool:
        while True:
            QUERY_CLIENT.logger.info("Polling for new jobs...")
            _get_and_schedule_job(pool)
