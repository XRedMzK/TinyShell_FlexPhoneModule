# Progress Log

## Правило
- Фиксируются только инженерные факты по проекту.
- Формат записи: `YYYY-MM-DD HH:MM (MSK) — <шаг/подшаг>; <что изменено>; <что проверено>. [check: ...]`.
- Тип проверки обязателен: `build check|manual runtime check|API check|desktop e2e manual|automated test`.

## Текущий Статус (2026-03-17 12:59 MSK)
- Структура проекта стабильна: `D:\FlexPhone`, каталоги `client` и `server`.
- Стек: Tauri 2 + React + TypeScript (client), FastAPI + WebSocket signaling (server), WebRTC/coturn, auth на `@user_name + device public key`.
- Этапы `13-20` закрыты и подтверждены.
- Этап `20` (Provisioned Alerting Config Artifacts) закрыт: render + drift + sandbox apply/compatibility smoke + CI gate подтверждены.

## Следующая Задача
- [ ] 21.1 — зафиксировать baseline следующего roadmap-этапа после closure Stage 20 (scope/invariants/closure criteria/verification type). [check: build check]

## Этап 20 (Provisioned Alerting Config Artifacts)
- [x] 20.1 — добавлены `docs/step20-rendered-provisioning-artifacts-baseline.md`, `server/app/reliability_alert_provisioning_artifacts_baseline.py`, `server/app/reliability_alert_provisioning_render.py`, `server/tools/check_alert_provisioning_artifacts.py`; сгенерированы deterministic artifacts в `server/generated/alertmanager` и `server/generated/grafana/provisioning/alerting`; введён drift-check contract (doc↔mapping↔artifact consistency, policy-tree single-root, linkage completeness) без изменения runtime-path. [check: build check]
- [x] 20.2 — зафиксирован provisioning apply/compatibility baseline: добавлены `docs/step20-provisioning-apply-compatibility-baseline.md` и `server/tools/run_alerting_provisioning_sandbox_smoke.py`; вручную подтверждены Grafana file provisioning acceptance (`contact-points/policies/mute-timings/templates`), `amtool check-config`, Alertmanager startup + `POST /-/reload`, sandbox smoke проходит без изменения runtime-path. [check: manual runtime check]
- [x] 20.3 — зафиксирован CI-gate baseline: добавлены `docs/step20-ci-gate-provisioning-baseline.md` и `.github/workflows/alerting-provisioning-ci.yml`, введён отдельный pipeline job `provisioning-gate` (compile check + drift check + sandbox smoke) для rendered provisioning artifacts на isolated CI sandbox без подключения provisioning в production runtime-path. [check: build check]

## Закрытые Этапы (кратко)
- [x] 13 — Security/Testing baseline: ephemeral TURN creds, WS negative-path matrix, call-state enforcement, desktop resilience e2e.
- [x] 14 — Auth Session Hardening: challenge/verify/JWT, WS auth gate, client bootstrap, runtime auth checklist.
- [x] 15 — Session Durability: Redis-backed challenge/presence/session, restart semantics, convergence при transient Pub/Sub loss.
- [x] 16 — Observability & Release Readiness: request-id/counters baseline, OTel tracing baseline, desktop release-readiness CI/signing baseline.
- [x] 17 — Deployment & Operational Hardening: readiness fail-closed, structured operational logging, deployment runbook + manual runtime smoke.
- [x] 18 — Observability Hardening: canonical naming/reason taxonomy, signal correlation/triage, dashboard/alert mapping baseline.
- [x] 19 — Reliability Targets & Alerting Policy: SLO/burn-rate baseline, routing/escalation, suppression/grouping, delivery-template contract, Alertmanager/Grafana policy export baseline.
- [x] 20 — Provisioned Alerting Config Artifacts: deterministic rendered artifacts baseline, sandbox apply/compatibility smoke, CI-gate enforcement baseline.

## Риски И Ограничения
- Backend clock — источник истины для `issued_at`/`expires_at`/`exp`.
- Redis обязателен для auth/signaling state (`FLEXPHONE_AUTH_CHALLENGE_REDIS_URL`, `FLEXPHONE_SIGNALING_REDIS_URL`).
- Cross-instance fan-out использует Redis Pub/Sub (at-most-once); correctness должен сходиться через shared Redis state + reconnect + startup reconciliation.
- `GET /ready` fail-closed по Redis checks (`auth_challenge_redis`, `signaling_redis`) и возвращает `503` при деградации.
- Tracing (`none|console|otlp`) не должен ломать runtime-path при недоступном SDK/endpoint.
- Structured logs: JSON contract + redaction (`token/secret/password/signature/challenge`), `request_id` обязателен, `trace_id/span_id` — при активном span.
- Rendered artifacts (`20.1`) являются производными от mapping (`19.6`); ручное редактирование `server/generated/*.rendered.yml` без render-sync недопустимо.
- Grafana file-provisioning compatibility (20.2) не эквивалентна HTTP Alerting Provisioning API payload semantics; smoke должен валидировать именно file provisioning path.
- Alertmanager apply compatibility требует `amtool check-config` и runtime reload smoke перед фиксацией manual closure.
- CI-gate для provisioning artifacts должен исполняться на isolated sandbox и не должен менять production runtime-path.
- Desktop e2e (screen share) в mixed WSL/Windows требует отдельного QA.

## Журнал Верификаций (последние)
- 2026-03-17 12:59 (MSK) — 20.3; добавлены `docs/step20-ci-gate-provisioning-baseline.md` и `.github/workflows/alerting-provisioning-ci.yml` (job `provisioning-gate`: `python -m compileall app tools`, `python tools/check_alert_provisioning_artifacts.py`, `python tools/run_alerting_provisioning_sandbox_smoke.py`), локально подтверждены `.venv_tmpcheck/bin/python tools/check_alert_provisioning_artifacts.py` (`OK`), `.venv_tmpcheck/bin/python -m compileall app tools` и повторный sandbox smoke `sg docker -c '.venv_tmpcheck/bin/python tools/run_alerting_provisioning_sandbox_smoke.py'` (`OK`). [check: build check]
- 2026-03-17 12:53 (MSK) — 20.2; на окружении с включённым Docker подтверждён локальный sandbox smoke: `sg docker -c '.venv_tmpcheck/bin/python tools/run_alerting_provisioning_sandbox_smoke.py'` -> `amtool check-config: OK`, `Alertmanager ready: OK`, `Grafana ready: OK`, `Alertmanager reload: OK`, `Sandbox provisioning smoke: OK`; compatibility rendered artifacts acceptance подтверждена без изменения runtime-path. [check: manual runtime check]
- 2026-03-17 12:41 (MSK) — 20.1; добавлены Step 20.1 doc/render/baseline/checker файлы, сгенерированы rendered provisioning artifacts (`alertmanager`, `contact-points`, `policies`, `mute-timings`, `templates`), подтверждены `.venv_tmpcheck/bin/python tools/check_alert_provisioning_artifacts.py` (`OK`) и `.venv_tmpcheck/bin/python -m compileall app tools`. [check: build check]
- 2026-03-17 12:30 (MSK) — 19.6; policy export baseline для Alertmanager/Grafana + расширение `tools/check_observability_contract.py`, подтверждены checker + compileall. [check: build check]
- 2026-03-17 12:25 (MSK) — 19.5; alert delivery template baseline + checker validation, подтверждены checker + compileall. [check: build check]
- 2026-03-17 12:20 (MSK) — 19.4; suppression/grouping baseline + checker validation, подтверждены checker + compileall. [check: build check]
- 2026-03-17 12:15 (MSK) — 19.3; routing/escalation baseline + checker validation, подтверждены checker + compileall. [check: build check]
- 2026-03-17 12:10 (MSK) — 19.2; SLO query/alert policy baseline + checker validation, подтверждены checker + compileall. [check: build check]
- 2026-03-17 12:05 (MSK) — 19.1; reliability/SLO baseline + checker validation, подтверждены checker + compileall. [check: build check]
- 2026-03-17 11:04 (MSK) — 17.3; manual runtime smoke (health/ready/auth/ws paths, degraded OTLP endpoint non-fatal). [check: manual runtime check]
- 2026-03-17 09:59 (MSK) — 15.5; manual runtime closure convergence (`valid-token reconnect`, `expired-token fail-closed + re-auth`, no stale/phantom keys). [check: manual runtime check]
- 2026-03-17 02:20 (MSK) — 14 final runtime checklist (`health -> register -> challenge/verify -> ws token paths`) + `pytest`/`compileall`. [check: manual runtime check]
