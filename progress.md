# Progress Log

## Правило
- Фиксируются только инженерные факты по проекту.
- Формат записи: `YYYY-MM-DD HH:MM (MSK) — <шаг/подшаг>; <что изменено>; <что проверено>. [check: ...]`.
- Тип проверки обязателен: `build check|manual runtime check|API check|desktop e2e manual|automated test`.

## Текущий Статус (2026-03-17 14:29 MSK)
- Структура проекта стабильна: `D:\FlexPhone`, каталоги `client` и `server`.
- Стек: Tauri 2 + React + TypeScript (client), FastAPI + WebSocket signaling (server), WebRTC/coturn, auth `@user_name + device public key`.
- Этапы `13-22` закрыты и подтверждены.
- Этап `23` запущен: `23.1` закрыт build-проверкой (runtime cutover baseline definition).
- GitHub publishing baseline выполнен: `main` отслеживает `origin` (`git@github.com:XRedMzK/TinyShell_FlexPhoneModule.git`).

## Следующая Задача
- [ ] 23.2 — зафиксировать authoritative runtime path inventory + migration matrix для durable signaling runtime cutover. [check: build check]

## Этап 23 (Durable Signaling Runtime Cutover Baseline)
- [x] 23.1 — runtime cutover baseline definition: scope/invariants/rollout modes (`pubsub_legacy`/`dual_write_shadow`/`durable_authoritative`), rollback boundaries, event migration matrix baseline. [check: build check]
- [ ] 23.2 — authoritative runtime path inventory + migration matrix детализация. [check: build check]
- [ ] 23.3 — dual-write / shadow-read runtime contract baseline. [check: build check]
- [ ] 23.4 — runtime cutover sandbox smoke baseline. [check: manual runtime check]
- [ ] 23.5 — CI/runtime cutover mode gate baseline. [check: build check]
- [ ] 23.6 — production readiness + rollback contract baseline. [check: build check]

## Закрытые Этапы
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
- До runtime cutover на durable transport production signaling correctness частично опирается на Pub/Sub bounded-loss + reconciliation.

## Журнал Верификаций (последние)
- 2026-03-17 14:29 (MSK) — 23.1; добавлены `docs/step23-durable-signaling-runtime-cutover-baseline.md`, `server/app/durable_signaling_runtime_cutover_baseline.py`, `server/tools/check_durable_signaling_runtime_cutover_baseline.py`; подтверждены checker + compileall. [check: build check]
- 2026-03-17 14:23 (MSK) — 22.5; добавлены `docs/step22-ci-durable-signaling-simulation-gate-baseline.md`, `.github/workflows/durable-signaling-ci.yml`, `server/tools/run_durable_signaling_ci_simulation.py`; подтверждены compile/checkers и локальный CI-equivalent simulation (`OK`). [check: build check]
- 2026-03-17 14:16 (MSK) — 22.4; добавлены `docs/step22-sandbox-durable-signaling-smoke-baseline.md`, `server/tools/run_durable_signaling_sandbox_smoke.py`; подтверждён isolated sandbox durable signaling smoke A/B/C/D. [check: manual runtime check]
- 2026-03-17 14:07 (MSK) — 22.3; добавлены durable event model baseline doc/module/checker; подтверждены checker + compileall. [check: build check]
- 2026-03-17 14:01 (MSK) — 22.2; добавлены signaling event inventory baseline doc/module/checker; подтверждены checker + compileall. [check: build check]
- 2026-03-17 13:52 (MSK) — 22.1; добавлены signaling delivery hardening baseline doc/module/checker; подтверждены checker + compileall. [check: build check]
- 2026-03-17 13:48 (MSK) — 21.6; добавлены CI restore simulation gate baseline doc/workflow; подтверждены compile/checkers + restore simulation smoke. [check: build check]
- 2026-03-17 13:13 (MSK) — GitHub publish; `ssh -T` success, `git push -u origin main` success. [check: manual runtime check]
