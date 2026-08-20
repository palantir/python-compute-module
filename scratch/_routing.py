#  Copyright 2026 Palantir Technologies, Inc.
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

"""Inter-pod communication and cache-aware routing for compute module replicas."""

import contextlib
import json
import logging
import os
import socket
import threading
import uuid
from typing import Any, Optional

import requests
from requests.adapters import HTTPAdapter

from scratch._cache import DistributedCache
from scratch._types import CacheTTL

LOGGER = logging.getLogger(__name__)

_ROUTING_KEY_PREFIX = "routing:"
_FORWARDER_PORT = 8945
_EXECUTE_V2_PATH = "/interactive-module/api/interactive-spark-module/execute"
_PASSTHROUGH_PATH = "/interactive-module/api/passthrough"
_VALUE_SEP = "|"
def _pod_ip() -> str:
    ip = os.environ.get("COMPUTE_POD_IP")
    if ip:
        return ip
    try:
        return socket.gethostbyname(socket.gethostname())
    except socket.gaierror:
        return "127.0.0.1"


def _peer_tls_name() -> str:
    """Return the headless Service FQDN for TLS verification.

    Pod certs are namespace wildcards (*.<ns>.svc.cluster.local) with no IP SANs,
    so we connect to the pod IP but verify against the Service hostname.
    COMPUTE_PEER_SERVICE_HOST is injected as the FQDN by compute-service.
    """
    return os.environ.get("COMPUTE_PEER_SERVICE_HOST", "")


class _PeerTLSAdapter(HTTPAdapter):
    """Connects to pod IPs but verifies TLS against the headless Service hostname."""

    def __init__(self, server_hostname: str, **kwargs):
        self._server_hostname = server_hostname
        super().__init__(**kwargs)

    def init_poolmanager(self, connections, maxsize, **kwargs):
        kwargs["assert_hostname"] = self._server_hostname
        kwargs["server_hostname"] = self._server_hostname
        super().init_poolmanager(connections, maxsize, **kwargs)


class PeerNetwork:
    """Peer discovery and inter-pod communication for compute module replicas.

    Discovers peers via headless service DNS. Two forwarding modes depending on the
    peer CM's shape:

    - ``execute_on_peer()``: for @function-based CMs where the Python SDK polls for jobs.
      Calls executeV2 on the peer's forwarder, which queues the job for the polling loop.
    - ``forward_to_peer()``: for Pattern 1 CMs (HTTP server, no @function handlers).
      Calls the peer's passthrough servlet, which proxies to the user's HTTP server.

    Example::

        peers = PeerNetwork()
        # For @function CMs:
        result = peers.execute_on_peer("10.0.1.45", "my_function", {"key": "val"})
        # For HTTP server CMs:
        resp = peers.forward_to_peer("10.0.1.45", "/predict", body=b'...')
    """

    def __init__(
        self,
        service_host: Optional[str] = None,
        port: int = _FORWARDER_PORT,
    ) -> None:
        self._self_ip = _pod_ip()
        self._service_host = service_host or os.environ.get("COMPUTE_PEER_SERVICE_HOST", "")
        self._port = port
        self._ca_path = os.environ.get("CONNECTIONS_TO_OTHER_PODS_CA_PATH", "")
        self._auth_token = _read_module_auth_token()
        self._in_flight: dict[str, int] = {}
        self._lock = threading.Lock()
        self._session = self._build_session()

    def _build_session(self) -> requests.Session:
        session = requests.Session()
        if self._ca_path:
            session.verify = self._ca_path
        tls_name = _peer_tls_name()
        if tls_name:
            session.mount("https://", _PeerTLSAdapter(tls_name))
        return session

    @property
    def self_ip(self) -> str:
        return self._self_ip

    def discover(self) -> list[str]:
        """Return peer pod IPs via headless DNS, excluding self. Empty list on failure."""
        if not self._service_host:
            return []
        try:
            results = socket.getaddrinfo(self._service_host, None, socket.AF_INET)
            return [ip for ip in {r[4][0] for r in results} if ip != self._self_ip]
        except socket.gaierror:
            return []

    def execute_on_peer(
        self,
        target_ip: str,
        query_type: str,
        query: Any,
        timeout: float = 300,
    ) -> bytes:
        """Execute a query on a peer via its forwarder's executeV2 endpoint.

        Submits the query as a job to the peer's forwarder, which queues it for the
        peer's Python replica. Blocks until the result is ready. Returns raw result bytes.
        """
        job_id = str(uuid.uuid4())
        url = f"https://{target_ip}:{self._port}{_EXECUTE_V2_PATH}/{job_id}/v2"

        body = json.dumps({
            "type": "submitJobRequestV3",
            "submitJobRequestV3": {
                "moduleAuthToken": self._auth_token,
                "queryType": query_type,
                "query": query,
                "metrics": {"type": "noTimingPresent", "noTimingPresent": {}},
            },
        }).encode()

        with self._count_in_flight(target_ip):
            resp = self._session.post(
                url, data=body,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self._auth_token}",
                },
                timeout=timeout,
            )

        if resp.status_code >= 400:
            raise RuntimeError(f"execute_on_peer failed: {resp.status_code} {resp.text[:200]}")
        return resp.content

    def forward_to_peer(
        self,
        target_ip: str,
        path: str,
        method: str = "POST",
        body: Optional[bytes] = None,
        headers: Optional[dict] = None,
        timeout: float = 300,
    ) -> requests.Response:
        """Forward an HTTP request to a peer's passthrough servlet.

        For Pattern 1 CMs where the user runs their own HTTP server. Headers pass
        through verbatim (including custom headers like loop-prevention markers).
        """
        url = f"https://{target_ip}:{self._port}{_PASSTHROUGH_PATH}{path}"
        fwd_headers = {**(headers or {})}
        if self._auth_token:
            fwd_headers["Module-Auth-Token"] = self._auth_token

        with self._count_in_flight(target_ip):
            return self._session.request(
                method=method, url=url, data=body, headers=fwd_headers,
                timeout=timeout,
            )

    def in_flight_to(self, target_ip: str) -> int:
        """Number of outstanding forwarded requests to a peer."""
        with self._lock:
            return self._in_flight.get(target_ip, 0)

    @contextlib.contextmanager
    def _count_in_flight(self, target_ip: str):
        with self._lock:
            self._in_flight[target_ip] = self._in_flight.get(target_ip, 0) + 1
        try:
            yield
        finally:
            with self._lock:
                n = self._in_flight.get(target_ip, 1) - 1
                if n <= 0:
                    self._in_flight.pop(target_ip, None)
                else:
                    self._in_flight[target_ip] = n


class ReplicaRouter:
    """Cache-aware routing built on PeerNetwork + Scratch.

    Tracks which replica has which data cached via Scratch, and can execute queries
    on the best peer via the forwarder's executeV2 endpoint.

    Example::

        router = ReplicaRouter()

        needed = ["terrain_01.tiff", "terrain_02.tiff"]
        if router.should_forward(needed):
            best = router.get_best_peer(needed)
            result = router.execute_on_peer(best, "my_function", {"files": needed})
        else:
            execute_locally()
            router.register_local_keys(needed)
    """

    def __init__(
        self,
        peer_network: Optional[PeerNetwork] = None,
        replica_id: Optional[str] = None,
        default_ttl: CacheTTL = CacheTTL.ONE_HOUR,
        max_in_flight_per_peer: int = 5,
    ) -> None:
        self._peers = peer_network or PeerNetwork()
        self._cache = DistributedCache(default_ttl=default_ttl)
        self._replica_id = replica_id or os.environ.get("COMPUTE_POD_NAME", "") or os.environ.get("HOSTNAME", "") or _pod_ip()
        self._default_ttl = default_ttl
        self._max_in_flight = max_in_flight_per_peer

    @property
    def replica_id(self) -> str:
        return self._replica_id

    @property
    def pod_address(self) -> str:
        return self._peers.self_ip

    def register_local_keys(self, keys: list[str], ttl: Optional[CacheTTL] = None) -> None:
        """Record in Scratch that this replica has these keys cached locally."""
        val = _encode(self._replica_id, self._peers.self_ip)
        for key in keys:
            self._cache.put(f"{_ROUTING_KEY_PREFIX}{key}", val, ttl=ttl or self._default_ttl)

    def check_local_coverage(self, needed_keys: list[str]) -> tuple[list[str], list[str]]:
        """Returns (local_keys, missing_keys)."""
        if not needed_keys:
            return [], []

        results = self._batch_lookup(needed_keys)
        local, missing = [], []
        for key in needed_keys:
            raw = results.get(f"{_ROUTING_KEY_PREFIX}{key}")
            if raw and _decode(raw)[0] == self._replica_id:
                local.append(key)
            else:
                missing.append(key)
        return local, missing

    def get_best_peer(self, needed_keys: list[str]) -> Optional[str]:
        """Best peer IP by coverage, or None if local is best. Respects in-flight limits."""
        if not needed_keys:
            return None

        local_count = len(self.check_local_coverage(needed_keys)[0])
        counts, addrs = self._peer_coverage(needed_keys)

        for rid in sorted(counts, key=counts.get, reverse=True):
            if counts[rid] <= local_count:
                break
            addr = addrs.get(rid, "")
            if addr and self._peers.in_flight_to(addr) < self._max_in_flight:
                return addr
        return None

    def should_forward(self, needed_keys: list[str], threshold: float = 0.5) -> bool:
        """True if local coverage is below threshold and a better peer exists."""
        if not needed_keys:
            return False
        local, _ = self.check_local_coverage(needed_keys)
        if len(local) / len(needed_keys) >= threshold:
            return False
        return self.get_best_peer(needed_keys) is not None

    def execute_on_peer(self, target_ip: str, query_type: str, query: Any, **kwargs) -> bytes:
        """Execute a query on a peer via executeV2. For @function-based CMs."""
        return self._peers.execute_on_peer(target_ip, query_type, query, **kwargs)

    def forward_to_peer(self, target_ip: str, path: str, **kwargs) -> requests.Response:
        """Forward an HTTP request to a peer via passthrough. For Pattern 1 CMs (HTTP server)."""
        return self._peers.forward_to_peer(target_ip, path, **kwargs)

    def _peer_coverage(self, needed_keys: list[str]) -> tuple[dict[str, int], dict[str, str]]:
        results = self._batch_lookup(needed_keys)
        counts: dict[str, int] = {}
        addrs: dict[str, str] = {}
        for key in needed_keys:
            raw = results.get(f"{_ROUTING_KEY_PREFIX}{key}")
            if raw:
                rid, addr = _decode(raw)
                if rid != self._replica_id:
                    counts[rid] = counts.get(rid, 0) + 1
                    addrs[rid] = addr
        return counts, addrs

    def _batch_lookup(self, keys: list[str]) -> dict[str, str]:
        prefixed = [f"{_ROUTING_KEY_PREFIX}{k}" for k in keys]
        out: dict[str, str] = {}
        for i in range(0, len(prefixed), 100):
            out.update(self._cache.batch_get(prefixed[i : i + 100]))
        return out


def _encode(replica_id: str, pod_address: str) -> str:
    return f"{replica_id}{_VALUE_SEP}{pod_address}"


def _decode(value: str) -> tuple[str, str]:
    parts = value.split(_VALUE_SEP, 1)
    return (parts[0], parts[1]) if len(parts) == 2 else (parts[0], "")


def _read_module_auth_token() -> str:
    path = os.environ.get("MODULE_AUTH_TOKEN", "")
    if not path or not os.path.exists(path):
        return ""
    try:
        with open(path) as f:
            return f.read().strip()
    except Exception:
        return ""
