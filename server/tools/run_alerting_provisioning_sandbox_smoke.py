from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]

RENDERED_ALERTMANAGER = ROOT / "generated" / "alertmanager" / "alertmanager.rendered.yml"
RENDERED_GRAFANA_DIR = ROOT / "generated" / "grafana" / "provisioning" / "alerting"

REQUIRED_GRAFANA_FILES = (
    "contact-points.rendered.yml",
    "policies.rendered.yml",
    "mute-timings.rendered.yml",
    "templates.rendered.yml",
)

SANDBOX_ALERTMANAGER_PORT = 19093
SANDBOX_GRAFANA_PORT = 13000


def _run(cmd: list[str], *, cwd: Path | None = None, timeout: int = 180) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
    )


def _require_command(name: str) -> None:
    if shutil.which(name) is None:
        raise RuntimeError(
            f"Required command is not available in current environment: {name}. "
            "For WSL, enable Docker Desktop WSL integration first."
        )


def _prepare_docker_config() -> None:
    docker_config = ROOT / ".tmp-docker-config"
    docker_config.mkdir(parents=True, exist_ok=True)
    config_file = docker_config / "config.json"
    if not config_file.exists():
        config_file.write_text("{}", encoding="utf-8")
    os.environ["DOCKER_CONFIG"] = str(docker_config)


def _ensure_inputs() -> None:
    if not RENDERED_ALERTMANAGER.exists():
        raise RuntimeError(f"Missing rendered Alertmanager artifact: {RENDERED_ALERTMANAGER}")

    for filename in REQUIRED_GRAFANA_FILES:
        file_path = RENDERED_GRAFANA_DIR / filename
        if not file_path.exists():
            raise RuntimeError(f"Missing rendered Grafana artifact: {file_path}")


def _prepare_sandbox_layout(base_dir: Path) -> None:
    alertmanager_dir = base_dir / "alertmanager"
    grafana_alerting_dir = base_dir / "grafana" / "provisioning" / "alerting"

    alertmanager_dir.mkdir(parents=True, exist_ok=True)
    grafana_alerting_dir.mkdir(parents=True, exist_ok=True)

    shutil.copy2(RENDERED_ALERTMANAGER, alertmanager_dir / "alertmanager.yml")
    for filename in REQUIRED_GRAFANA_FILES:
        shutil.copy2(RENDERED_GRAFANA_DIR / filename, grafana_alerting_dir / filename)


def _write_compose_file(base_dir: Path) -> Path:
    compose_path = base_dir / "compose.yml"
    compose_text = f"""services:
  alertmanager:
    image: prom/alertmanager:latest
    command:
      - --config.file=/etc/alertmanager/alertmanager.yml
      - --web.listen-address=:9093
    ports:
      - "127.0.0.1:{SANDBOX_ALERTMANAGER_PORT}:9093"
    volumes:
      - ./alertmanager:/etc/alertmanager:ro

  grafana:
    image: grafana/grafana:latest
    environment:
      - GF_SECURITY_ADMIN_USER=admin
      - GF_SECURITY_ADMIN_PASSWORD=admin
      - GF_AUTH_DISABLE_LOGIN_FORM=false
      - GF_LOG_LEVEL=info
    ports:
      - "127.0.0.1:{SANDBOX_GRAFANA_PORT}:3000"
    volumes:
      - ./grafana/provisioning:/etc/grafana/provisioning:ro
"""
    compose_path.write_text(compose_text, encoding="utf-8")
    return compose_path


def _wait_http_ok(url: str, *, timeout_seconds: int = 120) -> None:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        try:
            request = Request(url, method="GET")
            with urlopen(request, timeout=3) as response:  # nosec B310 - local sandbox endpoint
                status = getattr(response, "status", None)
                if status and 200 <= status < 300:
                    return
        except Exception:
            pass
        time.sleep(1.5)
    raise RuntimeError(f"Timed out waiting for endpoint: {url}")


def _docker_compose_cmd() -> list[str]:
    docker_compose = _run(["docker", "compose", "version"])
    if docker_compose.returncode == 0:
        return ["docker", "compose"]

    legacy = _run(["docker-compose", "--version"])
    if legacy.returncode == 0:
        return ["docker-compose"]

    raise RuntimeError("Neither `docker compose` nor `docker-compose` is available.")


def _check_amtool_in_container(base_dir: Path) -> None:
    cmd = [
        "docker",
        "run",
        "--rm",
        "--entrypoint",
        "amtool",
        "-v",
        f"{(base_dir / 'alertmanager').resolve()}:/cfg:ro",
        "prom/alertmanager:latest",
        "check-config",
        "/cfg/alertmanager.yml",
    ]
    result = _run(cmd, timeout=240)
    if result.returncode != 0:
        raise RuntimeError(
            "amtool check-config failed.\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )
    print("amtool check-config: OK")


def _check_logs_for_errors(compose_cmd: list[str], compose_path: Path) -> None:
    cmd = [*compose_cmd, "-f", str(compose_path), "logs", "--no-color"]
    result = _run(cmd, timeout=120)
    if result.returncode != 0:
        raise RuntimeError(f"Failed to read sandbox logs: {result.stderr}")

    log_text = (result.stdout or "").lower()
    suspicious_markers = (
        "provisioning failed",
        "error parsing",
        "failed to parse",
        "invalid configuration",
    )
    matches = [marker for marker in suspicious_markers if marker in log_text]
    if matches:
        raise RuntimeError(f"Provisioning/config errors detected in sandbox logs: {', '.join(matches)}")


def _alertmanager_reload() -> None:
    request = Request(
        f"http://127.0.0.1:{SANDBOX_ALERTMANAGER_PORT}/-/reload",
        method="POST",
    )
    try:
        with urlopen(request, timeout=5) as response:  # nosec B310 - local sandbox endpoint
            status = getattr(response, "status", None)
            if status is None or status < 200 or status >= 300:
                raise RuntimeError(f"Unexpected Alertmanager reload status: {status}")
    except URLError as exc:
        raise RuntimeError(f"Alertmanager reload failed: {exc}") from exc
    print("Alertmanager reload: OK")


def _compose_up(compose_cmd: list[str], compose_path: Path) -> None:
    cmd = [*compose_cmd, "-f", str(compose_path), "up", "-d"]
    result = _run(cmd, timeout=300)
    if result.returncode != 0:
        raise RuntimeError(
            "Failed to start sandbox services.\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )


def _compose_down(compose_cmd: list[str], compose_path: Path) -> None:
    cmd = [*compose_cmd, "-f", str(compose_path), "down", "-v", "--remove-orphans"]
    _run(cmd, timeout=180)


def run_sandbox_smoke() -> int:
    _require_command("docker")
    _prepare_docker_config()
    _ensure_inputs()
    compose_cmd = _docker_compose_cmd()

    with tempfile.TemporaryDirectory(prefix="flexphone-alerting-sandbox-") as tmp:
        base_dir = Path(tmp)
        _prepare_sandbox_layout(base_dir)
        compose_path = _write_compose_file(base_dir)

        _check_amtool_in_container(base_dir)
        _compose_up(compose_cmd, compose_path)
        try:
            _wait_http_ok(f"http://127.0.0.1:{SANDBOX_ALERTMANAGER_PORT}/-/ready")
            print("Alertmanager ready: OK")
            _wait_http_ok(f"http://127.0.0.1:{SANDBOX_GRAFANA_PORT}/api/health")
            print("Grafana ready: OK")
            _alertmanager_reload()
            _check_logs_for_errors(compose_cmd, compose_path)
            print("Sandbox provisioning smoke: OK")
        finally:
            _compose_down(compose_cmd, compose_path)

    return 0


def main() -> int:
    try:
        return run_sandbox_smoke()
    except Exception as exc:  # pragma: no cover - runtime harness
        print(f"Sandbox provisioning smoke: FAILED - {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
