# Progress Log

## Правило
- Фиксируются только инженерные факты по проекту.
- Формат записи: `YYYY-MM-DD HH:MM (MSK) — <шаг/подшаг>; <что изменено>; <что проверено>. [check: ...]`.
- Тип проверки обязателен: `build check|manual runtime check|API check|desktop e2e manual|automated test`.

## Текущий Статус (2026-03-17 13:54 MSK)
- Структура проекта стабильна: `D:\FlexPhone`, каталоги `client` и `server`.
- Стек: Tauri 2 + React + TypeScript (client), FastAPI + WebSocket signaling (server), WebRTC/coturn, auth `@user_name + device public key`.
- Этапы `13-21` закрыты и подтверждены.
- Этап `22` запущен: `22.1` закрыт build-проверкой.
- GitHub publishing baseline выполнен: `main` отслеживает `origin` (`git@github.com:XRedMzK/TinyShell_FlexPhoneModule.git`).

## Следующая Задача
- [ ] 22.2 — зафиксировать event inventory baseline для signaling delivery hardening (`authoritative durable coordination events` / `ephemeral fan-out hints` / `derived projection events`). [check: build check]

## Этап 20 (Provisioned Alerting Config Artifacts)
- [x] 20.1 — deterministic rendered artifacts + drift contract (`doc↔mapping↔artifact`) и checker. [check: build check]
- [x] 20.2 — sandbox apply/compatibility smoke для Grafana file provisioning + Alertmanager config/reload. [check: manual runtime check]
- [x] 20.3 — CI gate `provisioning-gate` (compile + drift + sandbox smoke). [check: build check]

## Этап 21 (Recovery & Restore Baseline)
- [x] 21.1 — baseline definition (scope/invariants/closure/verification). [check: build check]
- [x] 21.2 — source-of-truth / backup-restore inventory и ownership boundaries. [check: build check]
- [x] 21.3 — Redis loss/restart semantics: fail-closed + bounded-loss convergence (`reconnect/re-auth/startup reconciliation`). [check: build check]
- [x] 21.4 — post-restore runtime checklist (`health/ready/auth/ws/provisioning/observability`). [check: manual runtime check]
- [x] 21.5 — isolated sandbox restore smoke/runbook rehearsal. [check: manual runtime check]
- [x] 21.6 — CI restore simulation gate (`restore-simulation-gate`) поверх `21.1-21.5`. [check: build check]

## Этап 22 (Signaling Delivery Hardening Baseline)
- [x] 22.1 — baseline definition для durable signaling/coordination hardening поверх Pub/Sub bounded-loss модели; doc+module+checker. [check: build check]
- [ ] 22.2 — event inventory baseline (`authoritative durable` / `ephemeral fan-out` / `derived projection`). [check: build check]
- [ ] 22.3 — durable event model baseline (IDs, ordering, dedup, retention, replay/reconciliation). [check: build check]
- [ ] 22.4 — sandbox durable signaling smoke baseline. [check: manual runtime check]
- [ ] 22.5 — CI durable signaling simulation gate baseline. [check: build check]

## Закрытые Этапы (кратко)
- [x] 13 — Security/Testing baseline.
- [x] 14 — Auth Session Hardening.
- [x] 15 — Session Durability.
- [x] 16 — Observability & Release Readiness.
- [x] 17 — Deployment & Operational Hardening.
- [x] 18 — Observability Hardening.
- [x] 19 — Reliability Targets & Alerting Policy.
- [x] 20 — Provisioned Alerting Config Artifacts.
- [x] 21 — Recovery & Restore Baseline.
- [ ] 22 — Signaling Delivery Hardening Baseline.

## Риски И Ограничения
- Backend clock — источник истины для `issued_at`/`expires_at`/`exp`.
- Redis обязателен для auth/signaling state (`FLEXPHONE_AUTH_CHALLENGE_REDIS_URL`, `FLEXPHONE_SIGNALING_REDIS_URL`).
- Cross-instance fan-out использует Redis Pub/Sub (at-most-once); correctness сходится через shared state + reconnect + startup reconciliation.
- `GET /ready` fail-closed по Redis checks (`auth_challenge_redis`, `signaling_redis`) и возвращает `503` при деградации.
- Tracing (`none|console|otlp`) не должен ломать runtime-path при недоступном SDK/endpoint.
- Rendered artifacts (`20.1`) являются производными от mapping (`19.6`); ручное редактирование `server/generated/*.rendered.yml` без render-sync недопустимо.
- Grafana file-provisioning compatibility не эквивалентна HTTP Alerting Provisioning API semantics.
- Stage 21 success = convergence valid clients + rejection stale/invalid state; replay каждого transient key/event не требуется.
- Sandbox/CI restore rehearsal выполняется только в isolated disposable окружении и без production secrets/endpoints.
- До закрытия Stage 22 critical signaling correctness всё ещё опирается на Pub/Sub bounded-loss + reconciliation.

## Журнал Верификаций (последние)
- 2026-03-17 13:52 (MSK) — 22.1; добавлены `docs/step22-signaling-delivery-hardening-baseline.md`, `server/app/signaling_delivery_hardening_baseline.py`, `server/tools/check_signaling_delivery_hardening_baseline.py`; подтверждены checker + compileall. [check: build check]
- 2026-03-17 13:48 (MSK) — 21.6; добавлены `docs/step21-ci-restore-simulation-gate-baseline.md`, `.github/workflows/recovery-restore-ci.yml`; подтверждены compile/checkers + `run_recovery_restore_sandbox_smoke.py`. [check: build check]
- 2026-03-17 13:44 (MSK) — 21.5; добавлены `docs/step21-sandbox-restore-smoke-runbook-baseline.md`, `server/tools/run_recovery_restore_sandbox_smoke.py`; подтверждён isolated sandbox restore rehearsal. [check: manual runtime check]
- 2026-03-17 13:38 (MSK) — 21.4; добавлены `docs/step21-post-restore-runtime-validation-checklist-baseline.md`, `server/tools/run_post_restore_runtime_validation_smoke.py`; подтверждён post-restore runtime proof set. [check: manual runtime check]
- 2026-03-17 13:30 (MSK) — 21.3; добавлены Redis recovery semantics baseline doc/module/checker; подтверждены checker + compileall. [check: build check]
- 2026-03-17 13:25 (MSK) — 21.2; добавлены recovery inventory baseline doc/module/checker; подтверждены checker + compileall. [check: build check]
- 2026-03-17 13:21 (MSK) — 21.1; добавлены recovery baseline definition doc/module/checker; подтверждены checker + compileall. [check: build check]
- 2026-03-17 13:13 (MSK) — GitHub publish; `ssh -T` success, `git push -u origin main` success. [check: manual runtime check]
- 2026-03-17 12:59 (MSK) — 20.3; CI provisioning gate baseline (`.github/workflows/alerting-provisioning-ci.yml`). [check: build check]
- 2026-03-17 12:53 (MSK) — 20.2; sandbox provisioning smoke OK (`amtool`, Alertmanager reload, Grafana provisioning). [check: manual runtime check]
- 2026-03-17 12:41 (MSK) — 20.1; rendered artifacts baseline + checker; подтверждены checker + compileall. [check: build check]
