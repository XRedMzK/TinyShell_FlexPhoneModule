# Step 14 Auth Session Hardening Blueprint

## Goal
Bind signaling access to proof-of-possession of the device private key.

Flow:
1. Client requests one-time challenge for `(nickname, device_id)`.
2. Client signs canonical payload with local ECDSA P-256 private key.
3. Backend verifies signature against registered public key.
4. Backend issues short-lived signaling access token.
5. WebSocket signaling accepts only valid token bound to path nickname/device.

## Security Invariants
- Challenge is one-time and TTL-bounded.
- Challenge is bound to exact `(nickname, device_id)`.
- Signed payload is canonical and includes identity context, not just nonce.
- Replay of challenge is blocked by `consumed=true` after successful verify.
- Signaling session is rejected before registration if token is missing/invalid.
- Token audience is restricted to `signaling`.
- Token subject is bound to `nickname + device_id`.
- Token lifetime is short (`5-10m`).
- Backend clock is source of truth; small skew window is allowed.

## Data Model (Server)
Challenge record (in-memory for MVP):
- `challenge_id: str` (UUIDv4)
- `nickname: str`
- `device_id: str`
- `nonce_b64url: str` (>= 16 bytes random, recommended 32 bytes)
- `issued_at_unix: int`
- `expires_at_unix: int`
- `consumed: bool`
- `consumed_at_unix: int | null`

Token config:
- `JWT_ISSUER = "flexphone-backend"`
- `JWT_AUDIENCE = "signaling"`
- `JWT_ALG = "HS256"` (MVP)
- `JWT_TTL_SECONDS = 300..600`
- `JWT_CLOCK_SKEW_SECONDS = 30`
- `JWT_SECRET` must be set from env, no hardcoded default.

## Canonical Signed Payload (v1)
String payload, UTF-8, LF separators, exact field order:

```text
flexphone-auth-v1
challenge_id=<challenge_id>
nickname=<nickname>
device_id=<device_id>
nonce=<nonce_b64url>
issued_at=<issued_at_unix>
expires_at=<expires_at_unix>
```

Client signs payload bytes with ECDSA P-256 SHA-256.
Signature transport encoding: `base64url` of raw signature bytes returned by Web Crypto `sign()`.

## API Contracts

### 1) POST `/auth/challenge`
Request:
```json
{
  "nickname": "@alice",
  "device_id": "hex-device-id"
}
```

Response `200`:
```json
{
  "challenge_id": "uuid",
  "nickname": "@alice",
  "device_id": "hex-device-id",
  "nonce": "base64url",
  "issued_at_unix": 1760000000,
  "expires_at_unix": 1760000060,
  "algorithm": "ECDSA_P256_SHA256",
  "payload_version": "flexphone-auth-v1"
}
```

Validation:
- nickname format (`@...`)
- device exists and matches nickname registration
- issue challenge with TTL `30-120s`

### 2) POST `/auth/verify`
Request:
```json
{
  "challenge_id": "uuid",
  "nickname": "@alice",
  "device_id": "hex-device-id",
  "signature": "base64url"
}
```

Response `200`:
```json
{
  "access_token": "jwt",
  "token_type": "Bearer",
  "expires_at_unix": 1760000360
}
```

Validation order:
1. challenge exists, else `challenge_not_found`
2. challenge not expired, else `challenge_expired`
3. challenge not consumed, else `challenge_consumed`
4. `(nickname, device_id)` equals challenge binding, else `wrong_nickname_or_device`
5. registered public key exists, else `device_not_registered`
6. signature decoding/parsing valid, else `invalid_signature`
7. ECDSA verify succeeds, else `invalid_signature`
8. mark challenge `consumed=true`
9. issue JWT

## JWT Claims
Required claims:
- `iss`: `flexphone-backend`
- `sub`: `<nickname>:<device_id>`
- `nickname`
- `device_id`
- `aud`: `signaling`
- `iat`
- `exp`
- `jti`

MVP policy:
- Use `iat + exp` (no `nbf`).
- Re-auth on expiration by repeating challenge/verify flow.
- No refresh token in Step 14.

## WebSocket Auth Gate
Endpoint:
- `/ws/signaling/{nickname}?access_token=<jwt>` (MVP transport choice)

Reject before hub/session registration if token fails checks:
- missing token -> `token_missing`
- invalid signature/format -> `token_invalid`
- expired -> `token_expired`
- wrong `aud` -> `token_wrong_audience`
- token nickname != path nickname -> `token_wrong_nickname`
- token device does not match bound subject -> `token_wrong_device`

Suggested close behavior:
- close code `1008` with short reason code string.

## Reason Codes (Canonical)
- `challenge_not_found`
- `challenge_expired`
- `challenge_consumed`
- `wrong_nickname_or_device`
- `invalid_signature`
- `device_not_registered`
- `token_missing`
- `token_invalid`
- `token_expired`
- `token_wrong_audience`
- `token_wrong_nickname`
- `token_wrong_device`

## Tests

### API tests
- challenge success
- challenge device mismatch
- verify success
- verify `challenge_not_found`
- verify `challenge_expired`
- verify `challenge_consumed`
- verify `wrong_nickname_or_device`
- verify `invalid_signature`
- verify `replay_challenge` (2nd verify fails)

### WebSocket tests (FastAPI TestClient)
- `ws_without_token` -> reject
- `ws_with_invalid_token` -> reject
- `ws_with_expired_token` -> reject
- `ws_with_wrong_audience` -> reject
- `ws_with_wrong_nickname` -> reject
- `ws_with_wrong_device` -> reject
- valid token -> connect succeeds

### Client flow tests (manual + build)
- challenge request -> sign -> verify -> WS connect
- reconnect with expired token -> challenge/verify repeated
- two clients authenticated and call flow still works

## Implementation Sequence
1. Server models + settings for auth challenge/JWT.
2. Implement `/auth/challenge` and `/auth/verify`.
3. Add JWT helper and token validator.
4. Apply WS auth gate before `hub.connect()`.
5. Add automated tests for API + WS negative paths.
6. Update client auth bootstrap before signaling connect.
7. Manual desktop e2e for auth + call flow.
