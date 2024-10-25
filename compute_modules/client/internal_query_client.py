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


import http.client
import json
import multiprocessing
import os
import ssl
import time
import traceback
from contextlib import contextmanager
from typing import Any, Callable, Dict, Generator, List, Optional
from urllib.parse import urlparse

from compute_modules.context.types import QueryContext
from compute_modules.function_registry.function_payload_converter import convert_payload
from compute_modules.function_registry.types import ComputeModuleFunctionSchema, PythonClassNode
from compute_modules.logging.common import COMPUTE_MODULES_ADAPTER_MANAGER
from compute_modules.logging.internal import get_internal_logger

from ..context import get_extra_context_parameters

POST_RESULT_MAX_ATTEMPTS = 5
POST_SCHEMAS_MAX_ATTEMPTS = 5


def _extract_path_from_url(url: str) -> str:
    parsed_url = urlparse(url)
    return parsed_url.path


class InternalQueryService:
    def __init__(
        self,
        registered_functions: Dict[str, Callable[..., Any]],
        function_schemas: List[ComputeModuleFunctionSchema],
        function_schema_conversions: Dict[str, PythonClassNode],
        is_function_context_typed: Dict[str, bool],
    ):
        self.registered_functions = registered_functions
        self.function_schemas = function_schemas
        self.function_schema_conversions = function_schema_conversions
        self.is_function_context_typed = is_function_context_typed
        self.host = os.environ["RUNTIME_HOST"]
        self.port = int(os.environ["RUNTIME_PORT"])
        self.get_job_path = _extract_path_from_url(os.environ["GET_JOB_URI"])
        self.post_result_path = _extract_path_from_url(os.environ["POST_RESULT_URI"])
        self.post_schema_path = _extract_path_from_url(os.environ["POST_SCHEMA_URI"])
        self._initialize_auth_token()
        self._initialize_headers()
        self.certPath = os.environ["CONNECTIONS_TO_OTHER_PODS_CA_PATH"]
        self.context = ssl.create_default_context(cafile=self.certPath)
        self.connection_refused_count: int = 0
        self.concurrency = int(os.environ.get("MAX_CONCURRENT_TASKS", 1))
        self.logger = get_internal_logger()

    def _clear_logger_job_id(self) -> None:
        """Clear the _job_logger until we receive another job"""
        COMPUTE_MODULES_ADAPTER_MANAGER.update_job_id(job_id="")

    def _update_logger_job_id(self, job_id: str) -> None:
        """Create a new LoggerAdapter to provide contextual information in logs"""
        COMPUTE_MODULES_ADAPTER_MANAGER.update_job_id(job_id=job_id)

    def _set_logger_process_id(self, process_id: int) -> None:
        """Set the process_id for internal & public logger"""
        COMPUTE_MODULES_ADAPTER_MANAGER.update_process_id(process_id=process_id)

    def _initialize_auth_token(self) -> None:
        try:
            with open(os.environ["MODULE_AUTH_TOKEN"], "r", encoding="utf-8") as f:
                self.moduleAuthToken = f.read()
        except Exception as e:
            self.logger.error(f"Failed to read auth token: {str(e)}")
            raise

    def _initialize_headers(self) -> None:
        self.get_job_headers = {"Module-Auth-Token": self.moduleAuthToken}
        self.post_result_headers = {
            "Content-Type": "application/octet-stream",
            "Module-Auth-Token": self.moduleAuthToken,
        }
        self.post_schema_headers = {"Content-Type": "application/json", "Module-Auth-Token": self.moduleAuthToken}

    @contextmanager
    def request(
        self,
        method: str,
        url: str,
        headers: Dict[str, Any],
        body: Optional[Any] = None,
    ) -> Generator[http.client.HTTPResponse, Any, None]:
        """Wrapper for using https connection for requests"""
        response: Optional[http.client.HTTPResponse] = None
        connection = http.client.HTTPSConnection(
            host=self.host,
            port=self.port,
            context=self.context,
            timeout=(60 * 5),  # 5 minutes
        )
        try:
            connection.request(
                method=method,
                url=url,
                body=body,
                headers=headers,
            )
            response = connection.getresponse()
            yield response
        finally:
            connection.close()

    def post_query_schemas(self) -> None:
        """Post the function schemas of the Compute Module"""
        body = json.dumps(self.function_schemas)
        self.logger.debug(f"Posting function schemas: {body}")
        for i in range(POST_SCHEMAS_MAX_ATTEMPTS):
            try:
                with self.request(
                    method="POST",
                    url=self.post_schema_path,
                    body=body,
                    headers=self.post_schema_headers,
                ) as response:
                    self.logger.debug(f"POST /schemas response status: {response.status} reason: {response.reason}")
                return
            except ConnectionRefusedError:
                self.logger.warning(f"POST /schemas attempt #{i+1} Connection refused. Sleeping for {2 ** i}s")
                time.sleep(2**i)
            except Exception as e:
                self.logger.error(f"Unknown error posting function schemas: {str(e)}")
                self.logger.error(traceback.format_exc())
                return
        self.logger.error(f"Failed to POST /schemas after {POST_SCHEMAS_MAX_ATTEMPTS} attempts")

    def get_job_or_none(self) -> Any:
        try:
            with self.request(method="GET", url=self.get_job_path, headers=self.get_job_headers) as response:
                response_data = response.read().decode()
                result = None
                if response.status == 200:
                    result = json.loads(response_data)
                elif response.status == 204:
                    self.logger.info("No job found, retrying...")
                else:
                    self.logger.error(f"Unexpected response status: {response.status}")
                self.connection_refused_count = 0
                return result
        except ConnectionRefusedError:
            self.logger.warning(f"Connection refused. Sleeping for {2 ** self.connection_refused_count}s")
            time.sleep(2**self.connection_refused_count)
            self.connection_refused_count += 1
            return None
        except Exception as e:
            self.logger.error(f"Get job request failed, attempting to re-establish connection {str(e)}")
            self.logger.error(traceback.format_exc())
            return None

    def report_job_result(self, job_id: str, result: Any) -> None:
        body = json.dumps(result).encode("utf-8")
        post_result_path = f"{self.post_result_path}/{job_id}"
        self.logger.debug(f"Posting result to {post_result_path}")
        for _ in range(POST_RESULT_MAX_ATTEMPTS):
            try:
                with self.request(
                    method="POST",
                    url=post_result_path,
                    headers=self.post_result_headers,
                    body=body,
                ) as response:
                    if response.status == 204:
                        self.logger.debug("Successfully reported job result")
                        return
                    else:
                        self.logger.error(f"Failed to post result: {response.status} {response.reason}")
            except Exception as e:
                self.logger.error(f"POST of job result failed, attempting to re-establish connection: {str(e)}")
                self.logger.error(traceback.format_exc())
        raise RuntimeError(f"Unable to post job result after {POST_RESULT_MAX_ATTEMPTS} attempts")

    def handle_query(self) -> None:
        job = None
        try:
            job = self.get_job_or_none()
        except Exception as e:
            self.logger.warning(f"Exception occurred while fetching job: {str(e)}")
        if job:
            self.handle_job(job)

    def handle_job(self, job: Dict[str, Any]) -> None:
        v1 = job.get("computeModuleJobV1", {})
        job_id = v1.get("jobId")
        query_type = v1.get("queryType")
        query = v1.get("query")
        tempCredsAuthToken = v1.get("temporaryCredentialsAuthToken", "")
        authHeader = v1.get("authHeader", "")
        query_context = {
            "jobId": job_id,
            "tempCredsAuthToken": tempCredsAuthToken,
            "authHeader": authHeader,
            **get_extra_context_parameters(),
        }
        self._update_logger_job_id(job_id=job_id)
        self.logger.debug(f"Received job; queryType: {query_type}")
        try:
            self.logger.debug("Executing job")
            result = self.get_result(query_type, query, query_context)
            self.logger.debug("Successfully executed job")
        except Exception as e:
            self.logger.error(f"Error executing job: {str(e)}")
            result = self.get_failed_query(f"{str(e)}: {traceback.format_exc()}")
        self.logger.debug("Reporting result for job")
        self.report_job_result(job_id, result)
        self._clear_logger_job_id()

    def get_result(
        self,
        query_type: str,
        query: Dict[str, Any],
        query_context: Dict[str, Any],
    ) -> Any:
        registered_fn_keys = self.registered_functions.keys()
        if query_type in self.registered_functions:
            typed_query = query
            typed_context = query_context
            if query_type in self.function_schema_conversions:
                self.logger.debug(f"Found schema conversion for query {query_type}. Converting to typed payload")
                typed_query = convert_payload(query, self.function_schema_conversions[query_type])
            if self.is_function_context_typed[query_type]:
                typed_context = QueryContext(**query_context)  # type: ignore[assignment]
            return self.registered_functions[query_type](typed_context, typed_query)
        else:
            self.logger.error(f"Unknown query type: {query_type}. Known query runners: {registered_fn_keys}")
            return {"error": "Unknown query type"}

    @staticmethod
    def get_failed_query(message: str) -> Dict[str, str]:
        return {"exception": message}

    def start(self) -> None:
        self.post_query_schemas()
        self.logger.info(f"Starting to poll for jobs with concurrency {self.concurrency}")
        processes = [multiprocessing.Process(target=self.poll_forever, args=(i,)) for i in range(self.concurrency)]
        for p in processes:
            p.start()
        for p in processes:
            p.join()

    def poll_forever(self, process_id: int) -> None:
        self._set_logger_process_id(process_id=process_id)
        while True:
            self.logger.info("Polling for new jobs...")
            self.handle_query()
