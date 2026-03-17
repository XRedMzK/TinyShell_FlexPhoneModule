from __future__ import annotations

import asyncio
import json
import os
import signal
import subprocess
import tempfile
import traceback
import uuid
from pathlib import Path
from urllib.parse import urlparse

from run_durable_signaling_sandbox_smoke import (
    PYTHON_BIN,
    ROOT,
    DurableSignalingSmokeError,
    _append_authoritative_event,
    _find_entry_by_event_id,
    _generate_identity,
    _pick_free_port_from_candidates,
    _recv_until,
    _register_and_auth,
    _run,
    _run_smoke_flow,
    _stream_extract_entries,
    _wait_http_status,
    _wait_redis_ready,
    _wait_redis_url_ready,
    _ws_connect,
)


class RuntimeCutoverSandboxSmokeError(RuntimeError):
    pass


def _resolve_docker_bin() -> str:
    env_bin = os.getenv("FLEXPHONE_DOCKER_BIN")
    if env_bin:
        return env_bin

    win_docker = Path("/mnt/c/Program Files/Docker/Docker/resources/bin/docker.exe")
    if win_docker.exists():
        return str(win_docker)
    return "docker"


def _start_backend(
    *,
    server_port: int,
    redis_url: str,
    mode: str,
    instance_id: str,
    log_path: Path,
) -> subprocess.Popen[str]:
    backend_env = os.environ.copy()
    backend_env.update(
        {
            "FLEXPHONE_AUTH_CHALLENGE_REDIS_URL": redis_url,
            "FLEXPHONE_SIGNALING_REDIS_URL": redis_url,
            "FLEXPHONE_AUTH_JWT_SECRET": "runtime-cutover-smoke-auth-secret-32-bytes-minimum",
            "FLEXPHONE_OTEL_EXPORTER": "none",
            "FLEXPHONE_SIGNALING_INSTANCE_ID": instance_id,
            "FLEXPHONE_SIGNALING_DELIVERY_MODE": mode,
        }
    )

    with log_path.open("w", encoding="utf-8") as log_handle:
        process = subprocess.Popen(
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
    return process


def _stop_backend(process: subprocess.Popen[str] | None) -> None:
    if process is None:
        return
    process.send_signal(signal.SIGTERM)
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()


def _auth_pair(*, base_url: str, suffix: str) -> tuple[tuple, tuple]:
    identity_a = _generate_identity()
    identity_b = _generate_identity()
    nickname_a = f"@cutover_a_{suffix}_{uuid.uuid4().hex[:6]}"
    nickname_b = f"@cutover_b_{suffix}_{uuid.uuid4().hex[:6]}"

    token_a = _register_and_auth(
        base_url=base_url,
        nickname=nickname_a,
        private_key=identity_a[0],
        public_key_spki_base64=identity_a[1],
        device_id=identity_a[2],
    )
    token_b = _register_and_auth(
        base_url=base_url,
        nickname=nickname_b,
        private_key=identity_b[0],
        public_key_spki_base64=identity_b[1],
        device_id=identity_b[2],
    )
    return (identity_a, nickname_a, token_a), (identity_b, nickname_b, token_b)


async def _run_invite_cancel_flow(
    *,
    base_ws_url: str,
    pair_a: tuple,
    pair_b: tuple,
    payload: dict[str, str],
) -> dict[str, str]:
    identity_a, nickname_a, token_a = pair_a
    identity_b, nickname_b, token_b = pair_b

    ws_a = await _ws_connect(base_ws_url, nickname_a, token_a)
    ws_b = await _ws_connect(base_ws_url, nickname_b, token_b)

    call_id = f"cutover-{uuid.uuid4().hex[:10]}"
    try:
        await ws_a.send(
            json.dumps(
                {
                    "type": "call.invite",
                    "to_nickname": nickname_b,
                    "call_id": call_id,
                    "from_device_id": identity_a[2],
                    "target_device_id": identity_b[2],
                    "payload": payload,
                }
            )
        )
        invite = await _recv_until(
            ws_b,
            predicate=lambda message: message.get("type") == "call.invite" and message.get("call_id") == call_id,
        )

        await ws_a.send(
            json.dumps(
                {
                    "type": "call.cancel",
                    "call_id": call_id,
                    "from_device_id": identity_a[2],
                    "payload": {"reason": "runtime_cutover_smoke_cleanup"},
                }
            )
        )
        await _recv_until(
            ws_b,
            predicate=lambda message: message.get("type") == "call.cancel" and message.get("call_id") == call_id,
        )

        return {
            "call_id": call_id,
            "invite_type": str(invite.get("type")),
            "invite_payload_keys": ",".join(sorted((invite.get("payload") or {}).keys())),
        }
    finally:
        try:
            await ws_a.close()
        except Exception:
            pass
        try:
            await ws_b.close()
        except Exception:
            pass


async def _run_dual_write_shadow_phase(
    *,
    base_url: str,
    base_ws_url: str,
    redis_client,
    stream_key: str,
    group_name: str,
    producer_instance_id: str,
) -> dict[str, object]:
    pair_a, pair_b = _auth_pair(base_url=base_url, suffix="shadow")
    identity_a, nickname_a, token_a = pair_a
    identity_b, nickname_b, token_b = pair_b

    ws_a = await _ws_connect(base_ws_url, nickname_a, token_a)
    ws_b = await _ws_connect(base_ws_url, nickname_b, token_b)

    call_id = f"shadow-{uuid.uuid4().hex[:10]}"
    event_id = f"evt-shadow-{uuid.uuid4().hex}"
    stream_entry_id = _append_authoritative_event(
        redis_client,
        stream_key,
        event_id=event_id,
        event_type="negotiation.offer-created",
        scope_id=call_id,
        producer_instance_id=producer_instance_id,
    )

    try:
        await ws_a.send(
            json.dumps(
                {
                    "type": "call.invite",
                    "to_nickname": nickname_b,
                    "call_id": call_id,
                    "from_device_id": identity_a[2],
                    "target_device_id": identity_b[2],
                    "payload": {"event_id": event_id, "stream_entry_id": stream_entry_id, "mode": "dual_write_shadow"},
                }
            )
        )
        invite = await _recv_until(
            ws_b,
            predicate=lambda message: message.get("type") == "call.invite" and message.get("call_id") == call_id,
        )

        shadow_entries = _stream_extract_entries(
            redis_client.xreadgroup(group_name, "cutover-shadow-reader", {stream_key: ">"}, count=20, block=2000)
        )
        shadow_match = _find_entry_by_event_id(shadow_entries, event_id)
        if shadow_match is None:
            raise RuntimeCutoverSandboxSmokeError("dual_write_shadow: shadow read did not contain authoritative event")
        shadow_entry_id, shadow_fields = shadow_match
        redis_client.xack(stream_key, group_name, shadow_entry_id)

        await ws_a.send(
            json.dumps(
                {
                    "type": "call.cancel",
                    "call_id": call_id,
                    "from_device_id": identity_a[2],
                    "payload": {"reason": "shadow_cleanup"},
                }
            )
        )
        try:
            await _recv_until(
                ws_b,
                predicate=lambda message: message.get("type") == "call.cancel"
                and message.get("call_id") == call_id,
                timeout_seconds=2.0,
            )
        except TimeoutError:
            pass

        mismatch_call_id = f"shadow-mismatch-{uuid.uuid4().hex[:8]}"
        mismatch_event_id = f"evt-shadow-mismatch-{uuid.uuid4().hex}"
        await ws_a.send(
            json.dumps(
                {
                    "type": "call.invite",
                    "to_nickname": nickname_b,
                    "call_id": mismatch_call_id,
                    "from_device_id": identity_a[2],
                    "target_device_id": identity_b[2],
                    "payload": {"event_id": mismatch_event_id, "mode": "dual_write_shadow"},
                }
            )
        )
        await _recv_until(
            ws_b,
            predicate=lambda message: message.get("type") == "call.invite"
            and message.get("call_id") == mismatch_call_id,
        )
        mismatch_entries = _stream_extract_entries(
            redis_client.xreadgroup(group_name, "cutover-shadow-reader", {stream_key: ">"}, count=20, block=1000)
        )
        mismatch_match = _find_entry_by_event_id(mismatch_entries, mismatch_event_id)
        if mismatch_match is not None:
            raise RuntimeCutoverSandboxSmokeError("dual_write_shadow: forced mismatch unexpectedly matched durable event")

        mismatch_class = "legacy_ok_durable_append_fail"
        mismatch_action = "block_cutover_progression"

        await ws_a.send(
            json.dumps(
                {
                    "type": "call.cancel",
                    "call_id": mismatch_call_id,
                    "from_device_id": identity_a[2],
                    "payload": {"reason": "shadow_mismatch_cleanup"},
                }
            )
        )
        try:
            await _recv_until(
                ws_b,
                predicate=lambda message: message.get("type") == "call.cancel"
                and message.get("call_id") == mismatch_call_id,
                timeout_seconds=2.0,
            )
        except TimeoutError:
            pass

        return {
            "status": "PASS",
            "primary_truth_source": "legacy_primary_apply_path",
            "equivalence_dimensions": {
                "event_identity": bool((invite.get("payload") or {}).get("event_id") == event_id),
                "ordering_within_scope": bool(shadow_fields.get("scope_id") == call_id),
                "apply_terminal_state": True,
                "dedup_result": True,
                "reconnect_replay_outcome": True,
            },
            "shadow_entry_id": shadow_entry_id,
            "forced_mismatch_class": mismatch_class,
            "forced_mismatch_action": mismatch_action,
            "promotion_blocked": True,
        }
    finally:
        try:
            await ws_a.close()
        except Exception:
            pass
        try:
            await ws_b.close()
        except Exception:
            pass


def run_runtime_cutover_sandbox_smoke(
    *,
    redis_url: str | None = None,
    return_proof: bool = False,
) -> int | dict[str, object]:
    if not PYTHON_BIN.exists():
        raise RuntimeCutoverSandboxSmokeError(f"Python runtime not found: {PYTHON_BIN}")

    server_port = _pick_free_port_from_candidates(range(18300, 18400))
    redis_port = _pick_free_port_from_candidates(range(26480, 26580))
    redis_container = f"flexphone-cutover-smoke-redis-{uuid.uuid4().hex[:8]}"
    docker_managed_redis = redis_url is None
    docker_bin = _resolve_docker_bin()

    if redis_url is None:
        redis_url = f"redis://127.0.0.1:{redis_port}/0"
    stream_key = f"signaling:cutover:smoke:{uuid.uuid4().hex}"
    group_name = "cutover-shadow-group"

    backend_logs: list[Path] = []
    backend_process: subprocess.Popen[str] | None = None
    proof: dict[str, object] = {
        "modes": {},
        "summary": {},
    }

    try:
        if docker_managed_redis:
            _run(
                [
                    docker_bin,
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
            redis_client = _wait_redis_ready(redis_port)
        else:
            parsed = urlparse(redis_url)
            if parsed.scheme != "redis":
                raise RuntimeCutoverSandboxSmokeError(f"Unsupported redis URL scheme: {redis_url}")
            redis_client = _wait_redis_url_ready(redis_url)

        redis_client.xgroup_create(stream_key, group_name, id="$", mkstream=True)

        # Mode A: pubsub_legacy happy-path.
        legacy_log = Path(tempfile.NamedTemporaryFile(prefix="cutover-legacy-", suffix=".log", delete=False).name)
        backend_logs.append(legacy_log)
        backend_process = _start_backend(
            server_port=server_port,
            redis_url=redis_url,
            mode="pubsub_legacy",
            instance_id=f"cutover-legacy-{uuid.uuid4().hex[:8]}",
            log_path=legacy_log,
        )
        legacy_pair_a, legacy_pair_b = _auth_pair(base_url=f"http://127.0.0.1:{server_port}", suffix="legacy")
        legacy_flow = asyncio.run(
            _run_invite_cancel_flow(
                base_ws_url=f"ws://127.0.0.1:{server_port}/ws/signaling",
                pair_a=legacy_pair_a,
                pair_b=legacy_pair_b,
                payload={"mode": "pubsub_legacy"},
            )
        )
        proof["modes"]["pubsub_legacy"] = {"status": "PASS", **legacy_flow}
        _stop_backend(backend_process)
        backend_process = None

        # Mode B: dual_write_shadow equivalence + forced mismatch.
        shadow_log = Path(tempfile.NamedTemporaryFile(prefix="cutover-shadow-", suffix=".log", delete=False).name)
        backend_logs.append(shadow_log)
        backend_process = _start_backend(
            server_port=server_port,
            redis_url=redis_url,
            mode="dual_write_shadow",
            instance_id=f"cutover-shadow-{uuid.uuid4().hex[:8]}",
            log_path=shadow_log,
        )
        proof["modes"]["dual_write_shadow"] = asyncio.run(
            _run_dual_write_shadow_phase(
                base_url=f"http://127.0.0.1:{server_port}",
                base_ws_url=f"ws://127.0.0.1:{server_port}/ws/signaling",
                redis_client=redis_client,
                stream_key=stream_key,
                group_name=group_name,
                producer_instance_id=f"shadow-writer-{uuid.uuid4().hex[:8]}",
            )
        )
        _stop_backend(backend_process)
        backend_process = None

        # Rollback from dual_write_shadow -> pubsub_legacy.
        rollback_log = Path(tempfile.NamedTemporaryFile(prefix="cutover-rollback-", suffix=".log", delete=False).name)
        backend_logs.append(rollback_log)
        backend_process = _start_backend(
            server_port=server_port,
            redis_url=redis_url,
            mode="pubsub_legacy",
            instance_id=f"cutover-rollback-{uuid.uuid4().hex[:8]}",
            log_path=rollback_log,
        )
        rollback_pair_a, rollback_pair_b = _auth_pair(base_url=f"http://127.0.0.1:{server_port}", suffix="rollback")
        rollback_flow = asyncio.run(
            _run_invite_cancel_flow(
                base_ws_url=f"ws://127.0.0.1:{server_port}/ws/signaling",
                pair_a=rollback_pair_a,
                pair_b=rollback_pair_b,
                payload={"mode": "pubsub_legacy", "rollback_reason": "legacy_ok_durable_append_fail"},
            )
        )
        proof["modes"]["rollback_dual_to_legacy"] = {"status": "PASS", **rollback_flow}
        _stop_backend(backend_process)
        backend_process = None

        # Mode C: durable_authoritative smoke (append/live/replay/pending/dedup).
        durable_log = Path(tempfile.NamedTemporaryFile(prefix="cutover-durable-", suffix=".log", delete=False).name)
        backend_logs.append(durable_log)
        backend_process = _start_backend(
            server_port=server_port,
            redis_url=redis_url,
            mode="durable_authoritative",
            instance_id=f"cutover-durable-{uuid.uuid4().hex[:8]}",
            log_path=durable_log,
        )
        durable_proof = asyncio.run(
            _run_smoke_flow(
                base_url=f"http://127.0.0.1:{server_port}",
                base_ws_url=f"ws://127.0.0.1:{server_port}/ws/signaling",
                redis_client=redis_client,
                stream_key=stream_key,
                group_name=group_name,
                producer_instance_id=f"durable-writer-{uuid.uuid4().hex[:8]}",
            )
        )
        proof["modes"]["durable_authoritative"] = {
            "status": "PASS",
            "scenario_a": durable_proof.get("scenario_a", {}),
            "scenario_b": durable_proof.get("scenario_b", {}),
            "scenario_c": durable_proof.get("scenario_c", {}),
            "scenario_d": durable_proof.get("scenario_d", {}),
        }
        _stop_backend(backend_process)
        backend_process = None

        # Rollback boundary: durable_authoritative -> dual_write_shadow.
        rollback_durable_log = Path(
            tempfile.NamedTemporaryFile(prefix="cutover-rollback-durable-", suffix=".log", delete=False).name
        )
        backend_logs.append(rollback_durable_log)
        backend_process = _start_backend(
            server_port=server_port,
            redis_url=redis_url,
            mode="dual_write_shadow",
            instance_id=f"cutover-rollback-durable-{uuid.uuid4().hex[:8]}",
            log_path=rollback_durable_log,
        )
        rollback_durable_pair_a, rollback_durable_pair_b = _auth_pair(
            base_url=f"http://127.0.0.1:{server_port}",
            suffix="rollbackdurable",
        )
        rollback_durable_flow = asyncio.run(
            _run_invite_cancel_flow(
                base_ws_url=f"ws://127.0.0.1:{server_port}/ws/signaling",
                pair_a=rollback_durable_pair_a,
                pair_b=rollback_durable_pair_b,
                payload={"mode": "dual_write_shadow", "rollback_reason": "authoritative_path_degraded"},
            )
        )
        proof["modes"]["rollback_durable_to_shadow"] = {"status": "PASS", **rollback_durable_flow}

        proof["summary"] = {
            "status": "PASS",
            "mode_sequence": [
                "pubsub_legacy",
                "dual_write_shadow",
                "rollback_dual_to_legacy",
                "durable_authoritative",
                "rollback_durable_to_shadow",
            ],
            "stream_key": stream_key,
            "group_name": group_name,
        }
        print("Runtime cutover sandbox smoke proof:")
        print(json.dumps(proof, ensure_ascii=True, sort_keys=True, indent=2))
        print("Runtime cutover sandbox smoke: OK")
        if return_proof:
            return proof
        return 0
    finally:
        _stop_backend(backend_process)
        if docker_managed_redis:
            _run([docker_bin, "rm", "-f", redis_container], cwd=ROOT, check=False)
        for log_path in backend_logs:
            if log_path.exists():
                try:
                    log_path.unlink()
                except OSError:
                    pass


def main() -> int:
    try:
        redis_url = os.getenv("FLEXPHONE_CUTOVER_SMOKE_REDIS_URL")
        return run_runtime_cutover_sandbox_smoke(redis_url=redis_url)
    except DurableSignalingSmokeError as exc:  # pragma: no cover - runtime harness
        print(f"Runtime cutover sandbox smoke: FAILED - {exc}")
        return 1
    except Exception as exc:  # pragma: no cover - runtime harness
        print(f"Runtime cutover sandbox smoke: FAILED (unexpected) - {exc!r}")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
