from __future__ import annotations

import asyncio
import base64
import json
import os
import secrets
import signal
import socket
import subprocess
import sys
import tempfile
import time
import uuid
from pathlib import Path
from typing import Any

import httpx
import redis
import websockets
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from websockets.exceptions import ConnectionClosed, InvalidHandshake, InvalidStatus


ROOT = Path(__file__).resolve().parents[1]
PYTHON_BIN = ROOT / ".venv_tmpcheck" / "bin" / "python"
PROVISIONING_SMOKE = ROOT / "tools" / "run_alerting_provisioning_sandbox_smoke.py"

HEALTH_TIMEOUT_SECONDS = 30
REDIS_TIMEOUT_SECONDS = 20
REQUEST_TIMEOUT_SECONDS = 5


class RuntimeSmokeError(RuntimeError):
    pass


def _pick_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _run(
    cmd: list[str],
    *,
    cwd: Path,
    env: dict[str, str] | None = None,
    check: bool = True,
    capture_output: bool = True,
) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        cmd,
        cwd=str(cwd),
        env=env,
        text=True,
        capture_output=capture_output,
    )
    if check and completed.returncode != 0:
        raise RuntimeSmokeError(
            "Command failed: "
            + " ".join(cmd)
            + f"\nstdout:\n{completed.stdout}\nstderr:\n{completed.stderr}"
        )
    return completed


def _wait_redis_ready(redis_port: int, timeout_seconds: int = REDIS_TIMEOUT_SECONDS) -> None:
    client = redis.Redis(host="127.0.0.1", port=redis_port, decode_responses=True)
    deadline = time.time() + timeout_seconds
    last_error: Exception | None = None
    while time.time() < deadline:
        try:
            if client.ping():
                return
        except Exception as exc:  # pragma: no cover - runtime smoke diagnostic
            last_error = exc
        time.sleep(0.25)
    raise RuntimeSmokeError(f"Redis did not become ready on port {redis_port}: {last_error}")


def _wait_http_status(url: str, expected_status: int, timeout_seconds: int = HEALTH_TIMEOUT_SECONDS) -> httpx.Response:
    deadline = time.time() + timeout_seconds
    last_exc: Exception | None = None
    while time.time() < deadline:
        try:
            response = httpx.get(url, timeout=REQUEST_TIMEOUT_SECONDS)
            if response.status_code == expected_status:
                return response
        except Exception as exc:  # pragma: no cover - runtime smoke diagnostic
            last_exc = exc
        time.sleep(0.3)
    raise RuntimeSmokeError(
        f"Timed out waiting for {url} status={expected_status}; last_exc={last_exc}"
    )


def _generate_identity() -> tuple[ec.EllipticCurvePrivateKey, str, str]:
    private_key = ec.generate_private_key(ec.SECP256R1())
    public_der = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    public_key_spki_base64 = base64.b64encode(public_der).decode("ascii")
    device_id = secrets.token_hex(32)
    return private_key, public_key_spki_base64, device_id


def _sign_canonical_payload(private_key: ec.EllipticCurvePrivateKey, canonical_payload: str) -> str:
    signature = private_key.sign(canonical_payload.encode("utf-8"), ec.ECDSA(hashes.SHA256()))
    return base64.urlsafe_b64encode(signature).decode("ascii").rstrip("=")


async def _ws_expect_connected(ws_url: str) -> None:
    async with websockets.connect(ws_url, open_timeout=5, close_timeout=2) as ws:
        raw_message = await asyncio.wait_for(ws.recv(), timeout=5)
        message = json.loads(raw_message)
        if message.get("type") != "system.connected":
            raise RuntimeSmokeError(f"Expected system.connected, got: {message}")


async def _ws_expect_rejected(ws_url: str) -> None:
    try:
        async with websockets.connect(ws_url, open_timeout=5, close_timeout=2) as ws:
            try:
                await asyncio.wait_for(ws.recv(), timeout=2)
                raise RuntimeSmokeError("WS invalid-token path unexpectedly produced a message")
            except ConnectionClosed as close_exc:
                if close_exc.code != 1008:
                    raise RuntimeSmokeError(f"Expected WS close code 1008, got {close_exc.code}")
                return
    except InvalidStatus as exc:
        status_code = getattr(exc, "status_code", None)
        if status_code is None:
            response = getattr(exc, "response", None)
            status_code = getattr(response, "status_code", None)
        if status_code == 403:
            return
        raise RuntimeSmokeError(f"Expected status 403 for rejected WS handshake, got {status_code}") from exc
    except InvalidHandshake as exc:
        if "403" in str(exc):
            return
        raise RuntimeSmokeError(f"Expected rejected WS handshake, got: {exc}") from exc


def run_post_restore_runtime_validation_smoke() -> int:
    if not PYTHON_BIN.exists():
        raise RuntimeSmokeError(f"Python runtime not found: {PYTHON_BIN}")
    if not PROVISIONING_SMOKE.exists():
        raise RuntimeSmokeError(f"Provisioning smoke harness not found: {PROVISIONING_SMOKE}")

    server_port = _pick_free_port()
    redis_port = _pick_free_port()
    redis_container = f"flexphone-restore-redis-{uuid.uuid4().hex[:8]}"
    backend_log_file = tempfile.NamedTemporaryFile(
        prefix="flexphone-restore-backend-",
        suffix=".log",
        delete=False,
    )
    backend_log_path = Path(backend_log_file.name)
    backend_log_file.close()

    backend_process: subprocess.Popen[str] | None = None

    try:
        _run(
            [
                "docker",
                "run",
                "--rm",
                "-d",
                "--name",
                redis_container,
                "-p",
                f"{redis_port}:6379",
                "redis:7-alpine",
            ],
            cwd=ROOT,
        )
        _wait_redis_ready(redis_port)

        backend_env = os.environ.copy()
        backend_env.update(
            {
                "FLEXPHONE_AUTH_CHALLENGE_REDIS_URL": f"redis://127.0.0.1:{redis_port}/0",
                "FLEXPHONE_SIGNALING_REDIS_URL": f"redis://127.0.0.1:{redis_port}/0",
                "FLEXPHONE_AUTH_JWT_SECRET": "restore-smoke-auth-secret-32-bytes-minimum-value",
                "FLEXPHONE_OTEL_EXPORTER": "otlp",
                "FLEXPHONE_OTEL_OTLP_ENDPOINT": "http://127.0.0.1:65535/v1/traces",
                "FLEXPHONE_SIGNALING_INSTANCE_ID": f"restore-smoke-{uuid.uuid4().hex[:8]}",
            }
        )

        with backend_log_path.open("w", encoding="utf-8") as log_handle:
            backend_process = subprocess.Popen(
                [
                    str(PYTHON_BIN),
                    "-m",
                    "uvicorn",
                    "app.main:app",
                    "--host",
                    "127.0.0.1",
                    "--port",
                    str(server_port),
                ],
                cwd=str(ROOT),
                env=backend_env,
                stdout=log_handle,
                stderr=subprocess.STDOUT,
                text=True,
            )

        base_url = f"http://127.0.0.1:{server_port}"
        health_response = _wait_http_status(f"{base_url}/health", 200)
        if not health_response.headers.get("X-Request-ID"):
            raise RuntimeSmokeError("/health response missing X-Request-ID header")
        ready_response = _wait_http_status(f"{base_url}/ready", 200)
        if not ready_response.headers.get("X-Request-ID"):
            raise RuntimeSmokeError("/ready response missing X-Request-ID header")
        print("Health check: OK")
        print("Readiness check: OK")

        private_key, public_key_spki_base64, device_id = _generate_identity()
        nickname = "@restore_smoke"

        register_payload = {
            "nickname": nickname,
            "device_id": device_id,
            "public_key_spki_base64": public_key_spki_base64,
        }
        register_response = httpx.post(
            f"{base_url}/devices/register",
            json=register_payload,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        if register_response.status_code != 200:
            raise RuntimeSmokeError(
                f"Device register failed: {register_response.status_code} {register_response.text}"
            )

        challenge_response = httpx.post(
            f"{base_url}/auth/challenge",
            json={"nickname": nickname, "device_id": device_id},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        if challenge_response.status_code != 200:
            raise RuntimeSmokeError(
                f"Auth challenge failed: {challenge_response.status_code} {challenge_response.text}"
            )
        challenge_payload = challenge_response.json()

        signature_b64url = _sign_canonical_payload(private_key, challenge_payload["canonical_payload"])

        verify_response = httpx.post(
            f"{base_url}/auth/verify",
            json={
                "challenge_id": challenge_payload["challenge_id"],
                "nickname": nickname,
                "device_id": device_id,
                "signature": signature_b64url,
            },
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        if verify_response.status_code != 200:
            raise RuntimeSmokeError(
                f"Auth verify (fresh challenge) failed: {verify_response.status_code} {verify_response.text}"
            )
        access_token = verify_response.json().get("access_token")
        if not isinstance(access_token, str) or not access_token:
            raise RuntimeSmokeError("Auth verify success response missing access_token")

        invalid_verify = httpx.post(
            f"{base_url}/auth/verify",
            json={
                "challenge_id": str(uuid.uuid4()),
                "nickname": nickname,
                "device_id": device_id,
                "signature": signature_b64url,
            },
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        if invalid_verify.status_code != 404:
            raise RuntimeSmokeError(
                f"Expected challenge_not_found=404, got {invalid_verify.status_code} {invalid_verify.text}"
            )
        print("Auth positive/negative paths: OK")

        ws_valid_url = f"ws://127.0.0.1:{server_port}/ws/signaling/{nickname}?access_token={access_token}"
        asyncio.run(_ws_expect_connected(ws_valid_url))

        ws_invalid_url = f"ws://127.0.0.1:{server_port}/ws/signaling/{nickname}?access_token=invalid-token"
        asyncio.run(_ws_expect_rejected(ws_invalid_url))
        print("WebSocket positive/negative paths: OK")

        snapshot_response = httpx.get(
            f"{base_url}/observability/snapshot",
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        if snapshot_response.status_code != 200:
            raise RuntimeSmokeError(
                f"Observability snapshot failed: {snapshot_response.status_code} {snapshot_response.text}"
            )
        counters: dict[str, Any] = snapshot_response.json().get("counters", {})
        required_counters = {
            "health.ok",
            "ready.ok",
            "auth.challenge.ok",
            "auth.verify.ok",
            "auth.verify.rejected.challenge_not_found",
            "ws.connect.accepted",
            "ws.connect.rejected.token_invalid",
        }
        missing_counters = [key for key in sorted(required_counters) if int(counters.get(key, 0)) < 1]
        if missing_counters:
            raise RuntimeSmokeError(f"Missing expected observability counters: {missing_counters}")
        print("Observability snapshot checks: OK")

        _run(["docker", "stop", redis_container], cwd=ROOT, check=False)

        ready_degraded = _wait_http_status(f"{base_url}/ready", 503)
        health_alive = _wait_http_status(f"{base_url}/health", 200)
        if ready_degraded.status_code != 503 or health_alive.status_code != 200:
            raise RuntimeSmokeError("Readiness fail-closed check after Redis stop failed")
        print("Readiness fail-closed with Redis down: OK")

        provisioning_result = _run(
            [str(PYTHON_BIN), str(PROVISIONING_SMOKE)],
            cwd=ROOT,
            capture_output=True,
        )
        if "Sandbox provisioning smoke: OK" not in provisioning_result.stdout:
            raise RuntimeSmokeError(
                "Provisioning acceptance smoke did not report success marker\n"
                f"stdout:\n{provisioning_result.stdout}\n"
                f"stderr:\n{provisioning_result.stderr}"
            )
        print("Provisioning acceptance smoke: OK")

        print("Post-restore runtime validation smoke: OK")
        return 0

    finally:
        if backend_process is not None:
            if backend_process.poll() is None:
                backend_process.send_signal(signal.SIGTERM)
                try:
                    backend_process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    backend_process.kill()
                    backend_process.wait(timeout=5)

        _run(["docker", "rm", "-f", redis_container], cwd=ROOT, check=False)

        if backend_log_path.exists() and backend_log_path.stat().st_size > 0:
            print(f"Backend log path: {backend_log_path}")


def main() -> int:
    try:
        return run_post_restore_runtime_validation_smoke()
    except RuntimeSmokeError as exc:
        print(f"Post-restore runtime validation smoke: FAILED - {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
