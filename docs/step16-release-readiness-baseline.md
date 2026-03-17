# Step 16.3 - Desktop Release Readiness Baseline

## Scope
- Add a minimal CI scaffold for desktop build/publish.
- Document signing and updater prerequisites for Tauri v2.
- Keep this layer independent from backend runtime closure (Steps 14-16.2).

## CI Scaffold
- Workflow: `.github/workflows/desktop-release-readiness.yml`
- Trigger: `workflow_dispatch`
- Modes:
  - `publish=false` (default): build readiness check only (`npm run build` + `npm run tauri -- build`).
  - `publish=true`: validate release signing secrets and create a draft GitHub Release via `tauri-apps/tauri-action`.

## Required Secrets (publish mode)
- `TAURI_SIGNING_PRIVATE_KEY`
- `TAURI_SIGNING_PRIVATE_KEY_PASSWORD`

## Recommended Windows Signing Secrets
- `WINDOWS_CERTIFICATE` (Base64-encoded `.pfx`)
- `WINDOWS_CERTIFICATE_PASSWORD`

These are not enforced by the baseline workflow yet. They are intentionally documented as a separate hardening step for production distribution.

## Updater Prerequisites (Tauri v2)
- Signed updates are mandatory when updater is enabled.
- Keep signing keys managed as CI secrets; never commit them to repo.
- Enabling updater endpoints/keys in `tauri.conf.json` is a controlled follow-up task after baseline readiness.

## Local PowerShell Build Check
```powershell
Set-Location D:\FlexPhone\client
npm ci
npm run build
npm run tauri -- build
```

## Non-Blocking Boundary
- Desktop release-readiness does not change backend auth/session/reconcile guarantees.
- Backend runtime closure status remains governed by Steps 14-16.2 and corresponding verification logs.
