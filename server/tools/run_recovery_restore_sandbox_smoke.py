from __future__ import annotations

import asyncio
import base64
import json
import os
import secrets
import signal
import socket
import subprocess
import tempfile
import time
import uuid
from pathlib import Path

import httpx
import redis
import websockets
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from websockets.exceptions import ConnectionClosed, InvalidHandshake, InvalidStatus


ROOT = Path(__file__).resolve().parents[1]
PYTHON_BIN = ROOT / ".venv_tmpcheck" / "bin" / "python"
CHECK_ALERT_PROVISIONING = ROOT / "tools" / "check_alert_provisioning_artifacts.py"
POST_RESTORE_RUNTIME_SMOKE = ROOT / "tools" / "run_post_restore_runtime_validation_smoke.py"

REQUEST_TIMEOUT_SECONDS = 5
HEALTH_TIMEOUT_SECONDS = 30
REDIS_TIMEOUT_SECONDS = 20


class RecoverySandboxSmokeError(RuntimeError):
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
) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        cmd,
        cwd=str(cwd),
        env=env,
        text=True,
        capture_output=True,
    )
    if check and completed.returncode != 0:
        raise RecoverySandboxSmokeError(
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
    raise RecoverySandboxSmokeError(f"Redis did not become ready on port {redis_port}: {last_error}")


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
    raise RecoverySandboxSmokeError(
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
            raise RecoverySandboxSmokeError(f"Expected system.connected, got: {message}")


async def _ws_expect_rejected(ws_url: str) -> None:
    try:
        async with websockets.connect(ws_url, open_timeout=5, close_timeout=2) as ws:
            try:
                await asyncio.wait_for(ws.recv(), timeout=2)
                raise RecoverySandboxSmokeError("WS invalid-token path unexpectedly produced a message")
            except ConnectionClosed as close_exc:
                if close_exc.code != 1008:
                    raise RecoverySandboxSmokeError(
                        f"Expected WS close code 1008, got {close_exc.code}"
                    )
                return
    except InvalidStatus as exc:
        status_code = getattr(exc, "status_code", None)
        if status_code is None:
            response = getattr(exc, "response", None)
            status_code = getattr(response, "status_code", None)
        if status_code == 403:
            return
        raise RecoverySandboxSmokeError(
            f"Expected status 403 for rejected WS handshake, got {status_code}"
        ) from exc
    except InvalidHandshake as exc:
        if "403" in str(exc):
            return
        raise RecoverySandboxSmokeError(f"Expected rejected WS handshake, got: {exc}") from exc


def _phase_canonical_input_checks() -> None:
    if not CHECK_ALERT_PROVISIONING.exists():
        raise RecoverySandboxSmokeError(f"Missing checker: {CHECK_ALERT_PROVISIONING}")
    result = _run([str(PYTHON_BIN), str(CHECK_ALERT_PROVISIONING)], cwd=ROOT)
    if "alert-provisioning-artifacts-check: OK" not in result.stdout:
        raise RecoverySandboxSmokeError(
            "Canonical input checks did not report success marker\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )
    print("Canonical input checks: OK")


def _phase_post_restore_runtime_proof() -> None:
    if not POST_RESTORE_RUNTIME_SMOKE.exists():
        raise RecoverySandboxSmokeError(f"Missing runtime smoke harness: {POST_RESTORE_RUNTIME_SMOKE}")
    result = _run([str(PYTHON_BIN), str(POST_RESTORE_RUNTIME_SMOKE)], cwd=ROOT)
    if "Post-restore runtime validation smoke: OK" not in result.stdout:
        raise RecoverySandboxSmokeError(
            "Step 21.4 runtime proof set did not report success marker\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )
    print("Post-restore runtime proof set (21.4): OK")


def _phase_redis_bounded_loss_rehearsal() -> None:
    server_port = _pick_free_port()
    redis_port = _pick_free_port()
    redis_container = f"flexphone-recovery-redis-{uuid.uuid4().hex[:8]}"

    backend_log_file = tempfile.NamedTemporaryFile(
        prefix="flexphone-recovery-backend-",
        suffix=".log",
        delete=False,
    )
    backend_log_path = Path(backend_log_file.name)
    backend_log_file.close()

    backend_process: subprocess.Popen[str] | None = None

    def _start_redis_container() -> None:
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

    try:
        _start_redis_container()

        backend_env = os.environ.copy()
        backend_env.update(
            {
                "FLEXPHONE_AUTH_CHALLENGE_REDIS_URL": f"redis://127.0.0.1:{redis_port}/0",
                "FLEXPHONE_SIGNALING_REDIS_URL": f"redis://127.0.0.1:{redis_port}/0",
                "FLEXPHONE_AUTH_JWT_SECRET": "recovery-sandbox-auth-secret-32-bytes-minimum",
                "FLEXPHONE_OTEL_EXPORTER": "none",
                "FLEXPHONE_SIGNALING_INSTANCE_ID": f"recovery-sandbox-{uuid.uuid4().hex[:8]}",
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
        _wait_http_status(f"{base_url}/health", 200)
        _wait_http_status(f"{base_url}/ready", 200)

        private_key, public_key_spki_base64, device_id = _generate_identity()
        nickname = "@recovery_rehearsal"

        register_response = httpx.post(
            f"{base_url}/devices/register",
            json={
                "nickname": nickname,
                "device_id": device_id,
                "public_key_spki_base64": public_key_spki_base64,
            },
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        if register_response.status_code != 200:
            raise RecoverySandboxSmokeError(
                f"Device register failed: {register_response.status_code} {register_response.text}"
            )

        challenge_response = httpx.post(
            f"{base_url}/auth/challenge",
            json={"nickname": nickname, "device_id": device_id},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        if challenge_response.status_code != 200:
            raise RecoverySandboxSmokeError(
                f"Initial challenge issue failed: {challenge_response.status_code} {challenge_response.text}"
            )
        challenge_payload = challenge_response.json()
        old_signature = _sign_canonical_payload(private_key, challenge_payload["canonical_payload"])

        # Simulate transient Redis loss.
        _run(["docker", "stop", redis_container], cwd=ROOT, check=False)

        verify_while_down = httpx.post(
            f"{base_url}/auth/verify",
            json={
                "challenge_id": challenge_payload["challenge_id"],
                "nickname": nickname,
                "device_id": device_id,
                "signature": old_signature,
            },
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        if verify_while_down.status_code != 503:
            raise RecoverySandboxSmokeError(
                "Expected fail-closed verify while Redis is down (503), got "
                f"{verify_while_down.status_code} {verify_while_down.text}"
            )

        # Start fresh Redis (transient state lost), verify old challenge must stay fail-closed.
        _start_redis_container()
        _wait_http_status(f"{base_url}/ready", 200)

        verify_old_after_restart = httpx.post(
            f"{base_url}/auth/verify",
            json={
                "challenge_id": challenge_payload["challenge_id"],
                "nickname": nickname,
                "device_id": device_id,
                "signature": old_signature,
            },
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        if verify_old_after_restart.status_code != 404:
            raise RecoverySandboxSmokeError(
                "Expected old challenge to be rejected after Redis restart (404), got "
                f"{verify_old_after_restart.status_code} {verify_old_after_restart.text}"
            )

        # Fresh re-auth path should converge successfully.
        fresh_challenge_response = httpx.post(
            f"{base_url}/auth/challenge",
            json={"nickname": nickname, "device_id": device_id},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        if fresh_challenge_response.status_code != 200:
            raise RecoverySandboxSmokeError(
                f"Fresh challenge issue failed after Redis restart: {fresh_challenge_response.status_code} {fresh_challenge_response.text}"
            )
        fresh_challenge_payload = fresh_challenge_response.json()
        fresh_signature = _sign_canonical_payload(private_key, fresh_challenge_payload["canonical_payload"])

        fresh_verify_response = httpx.post(
            f"{base_url}/auth/verify",
            json={
                "challenge_id": fresh_challenge_payload["challenge_id"],
                "nickname": nickname,
                "device_id": device_id,
                "signature": fresh_signature,
            },
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        if fresh_verify_response.status_code != 200:
            raise RecoverySandboxSmokeError(
                f"Fresh verify failed after Redis restart: {fresh_verify_response.status_code} {fresh_verify_response.text}"
            )

        access_token = fresh_verify_response.json().get("access_token")
        if not isinstance(access_token, str) or not access_token:
            raise RecoverySandboxSmokeError("Fresh verify response missing access_token")

        ws_valid_url = f"ws://127.0.0.1:{server_port}/ws/signaling/{nickname}?access_token={access_token}"
        asyncio.run(_ws_expect_connected(ws_valid_url))

        ws_invalid_url = f"ws://127.0.0.1:{server_port}/ws/signaling/{nickname}?access_token=invalid-token"
        asyncio.run(_ws_expect_rejected(ws_invalid_url))

        print("Redis bounded-loss convergence rehearsal: OK")

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
            print(f"Recovery rehearsal backend log path: {backend_log_path}")


def run_recovery_restore_sandbox_smoke() -> int:
    if not PYTHON_BIN.exists():
        raise RecoverySandboxSmokeError(f"Python runtime not found: {PYTHON_BIN}")

    _phase_canonical_input_checks()
    _phase_post_restore_runtime_proof()
    _phase_redis_bounded_loss_rehearsal()

    print("Sandbox restore smoke rehearsal: OK")
    return 0


def main() -> int:
    try:
        return run_recovery_restore_sandbox_smoke()
    except RecoverySandboxSmokeError as exc:
        print(f"Sandbox restore smoke rehearsal: FAILED - {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
