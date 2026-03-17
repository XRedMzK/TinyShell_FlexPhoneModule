# Progress Log

## Правило
- Фиксируются только инженерные факты по проекту.
- Формат записи: `YYYY-MM-DD HH:MM (MSK) — <шаг/подшаг>; <что изменено>; <что проверено>. [check: ...]`.
- Тип проверки обязателен: `build check|manual runtime check|API check|desktop e2e manual|automated test`.

## Текущий Статус (2026-03-17 16:18 MSK)
- Структура проекта стабильна: `D:\FlexPhone`, каталоги `client` и `server`.
- Стек: Tauri 2 + React + TypeScript (client), FastAPI + WebSocket signaling (server), WebRTC/coturn, auth `@user_name + device public key`.
- Этапы `13-24` закрыты и подтверждены (`build` + `manual runtime`).
- Этап `25` запущен: `25.1` закрыт как baseline definition для in-call media control + quality observability.
- GitHub publishing baseline выполнен: `main` отслеживает `origin` (`git@github.com:XRedMzK/TinyShell_FlexPhoneModule.git`).

## Следующая Задача
- [ ] 25.2 — зафиксировать media-control state inventory + ownership matrix baseline. [check: build check]

## Этап 25 (In-Call Media Control and Quality Observability Baseline)
- [x] 25.1 — baseline definition: scope, media-control invariants, mute/switch/parameter ownership boundaries, quality-observability surface (`getStats`) и Stage 25 closure/verification draft. [check: build check]
- [ ] 25.2 — media-control state inventory + ownership matrix baseline. [check: build check]
- [ ] 25.3 — mute/unmute + source-switch + transceiver-direction contract baseline. [check: build check]
- [ ] 25.4 — sender-parameters/bitrate/codec boundary contract baseline. [check: build check]
- [ ] 25.5 — in-call quality observability baseline (`getStats` metrics/sampling/severity mapping). [check: build check]
- [ ] 25.6 — in-call media-control sandbox smoke baseline. [check: manual runtime check]
- [ ] 25.7 — in-call media-control CI gate baseline. [check: build check]

## Закрытые Этапы
- [x] 24 — WebRTC Session Lifecycle Hardening Baseline (`24.1-24.6`: lifecycle baseline, state matrix, negotiation/glare contract, reconnect/restart contract, sandbox smoke, CI gate).
- [x] 23 — Durable Signaling Runtime Cutover Baseline (`23.1-23.6`: baseline, inventory, dual-write contract, sandbox smoke, CI gate, production readiness/rollback contract).
- [x] 22 — Signaling Delivery Hardening Baseline (`22.1-22.5`: baseline, inventory, durable model, sandbox smoke, CI gate).
- [x] 21 — Recovery & Restore Baseline (`21.1-21.6`: definition, inventory, semantics, checklist, sandbox smoke, CI gate).
- [x] 20 — Provisioned Alerting Config Artifacts (`20.1-20.3`: render/drift, compatibility smoke, CI gate).
- [x] 13-19 — Security/Auth/Durability/Observability/Operational hardening и alerting policy baselines.

## Риски И Ограничения
- Backend clock — источник истины для `issued_at`/`expires_at`/`exp`.
- Redis обязателен для auth/signaling state (`FLEXPHONE_AUTH_CHALLENGE_REDIS_URL`, `FLEXPHONE_SIGNALING_REDIS_URL`).
- Cross-instance fan-out использует Redis Pub/Sub (at-most-once); correctness сходится через shared state + reconnect + startup reconciliation.
- `GET /ready` fail-closed по Redis checks (`auth_challenge_redis`, `signaling_redis`) и возвращает `503` при деградации.
- Tracing (`none|console|otlp`) не должен ломать runtime-path при недоступном SDK/endpoint.
- Rendered artifacts (`20.1`) являются производными от mapping (`19.6`); ручное редактирование `server/generated/*.rendered.yml` без render-sync недопустимо.
- Grafana file-provisioning compatibility не эквивалентна HTTP Alerting Provisioning API semantics.

## Журнал Верификаций (последние)
- 2026-03-17 16:18 (MSK) — 25.1; добавлены `docs/step25-incall-media-control-quality-observability-baseline.md`, `server/app/webrtc_incall_media_control_quality_observability_baseline.py`, `server/tools/check_webrtc_incall_media_control_quality_observability_baseline.py`; подтверждены `.venv_tmpcheck/bin/python tools/check_webrtc_session_lifecycle_hardening_baseline.py`, `.venv_tmpcheck/bin/python tools/check_webrtc_lifecycle_ci_gate_baseline.py`, `.venv_tmpcheck/bin/python tools/check_webrtc_incall_media_control_quality_observability_baseline.py` и `.venv_tmpcheck/bin/python -m compileall app tools` (`OK`). [check: build check]
- 2026-03-17 16:12 (MSK) — 24.6; добавлены `docs/step24-lifecycle-ci-gate-baseline.md`, `.github/workflows/webrtc-lifecycle-ci.yml`, `server/app/webrtc_lifecycle_ci_gate_baseline.py`, `server/tools/check_webrtc_lifecycle_ci_gate_baseline.py`, `server/tools/run_webrtc_lifecycle_ci_simulation.py`; подтверждены `.venv_tmpcheck/bin/python -m compileall app tools`, checkers (`24.1/24.2/24.3/24.4/24.6`) и локальный CI-equivalent lifecycle simulation matrix по сценариям `A-F` (`OK`). [check: build check]
- 2026-03-17 16:05 (MSK) — 24.5; добавлены `docs/step24-lifecycle-sandbox-smoke-baseline.md`, `server/tools/run_webrtc_lifecycle_sandbox_smoke.py`; вручную подтверждён lifecycle sandbox smoke по сценариям A-F (happy-path, glare roles, transient recovery, failed->restart recovery, late signaling ignore, close during pending recovery): `.venv_tmpcheck/bin/python tools/run_webrtc_lifecycle_sandbox_smoke.py` (`WebRTC lifecycle sandbox smoke: OK`) и `.venv_tmpcheck/bin/python -m compileall app tools` (`OK`). [check: manual runtime check]
- 2026-03-17 15:58 (MSK) — 24.4; добавлены `docs/step24-reconnect-ice-restart-pending-recovery-contract-baseline.md`, `server/app/webrtc_reconnect_ice_restart_pending_recovery_contract.py`, `server/tools/check_webrtc_reconnect_ice_restart_pending_recovery_contract.py`; подтверждены `tools/check_webrtc_session_lifecycle_hardening_baseline.py`, `tools/check_webrtc_peer_session_state_inventory.py`, `tools/check_webrtc_negotiation_glare_resolution_contract.py`, `tools/check_webrtc_reconnect_ice_restart_pending_recovery_contract.py` и `python -m compileall app tools` (`OK`). [check: build check]
- 2026-03-17 15:51 (MSK) — 24.3; добавлены `docs/step24-negotiation-glare-resolution-contract-baseline.md`, `server/app/webrtc_negotiation_glare_resolution_contract.py`, `server/tools/check_webrtc_negotiation_glare_resolution_contract.py`; подтверждены `tools/check_webrtc_session_lifecycle_hardening_baseline.py`, `tools/check_webrtc_peer_session_state_inventory.py`, `tools/check_webrtc_negotiation_glare_resolution_contract.py` и `python -m compileall app tools` (`OK`). [check: build check]
- 2026-03-17 15:46 (MSK) — 24.2; добавлены `docs/step24-peer-session-state-inventory-transition-matrix-baseline.md`, `server/app/webrtc_peer_session_state_inventory.py`, `server/tools/check_webrtc_peer_session_state_inventory.py`; подтверждены `tools/check_webrtc_session_lifecycle_hardening_baseline.py`, `tools/check_webrtc_peer_session_state_inventory.py` и `python -m compileall app tools` (`OK`). [check: build check]
- 2026-03-17 15:23 (MSK) — 24.1; добавлены `docs/step24-webrtc-session-lifecycle-hardening-baseline.md`, `server/app/webrtc_session_lifecycle_hardening_baseline.py`, `server/tools/check_webrtc_session_lifecycle_hardening_baseline.py`; подтверждены `tools/check_webrtc_session_lifecycle_hardening_baseline.py` (`OK`) и `python -m compileall app tools` (`OK`). [check: build check]
- 2026-03-17 15:17 (MSK) — 23.6; добавлены `docs/step23-production-readiness-rollback-contract-baseline.md`, `server/app/runtime_cutover_production_readiness_rollback_contract.py`, `server/tools/check_runtime_cutover_production_readiness_rollback_contract.py`; обновлён `.github/workflows/runtime-cutover-ci.yml` (добавлен checker шага `23.6`), подтверждены checkers (`23.2/23.3/23.5/23.6`) и `python -m compileall app tools` (`OK`). [check: build check]
