from __future__ import annotations

import os

from run_durable_signaling_sandbox_smoke import DurableSignalingSmokeError, run_durable_signaling_sandbox_smoke


def run_ci_simulation() -> int:
    redis_url = os.getenv("FLEXPHONE_DURABLE_SIM_REDIS_URL", "redis://127.0.0.1:6379/0")
    print(f"Durable signaling CI simulation Redis URL: {redis_url}")
    return run_durable_signaling_sandbox_smoke(redis_url=redis_url)


def main() -> int:
    try:
        result = run_ci_simulation()
        if result == 0:
            print("Durable signaling CI simulation: OK")
        return result
    except DurableSignalingSmokeError as exc:  # pragma: no cover - runtime harness
        print(f"Durable signaling CI simulation: FAILED - {exc}")
        return 1
    except Exception as exc:  # pragma: no cover - defensive
        print(f"Durable signaling CI simulation: FAILED (unexpected) - {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
