# coturn (local dev)

## 1) Run coturn with Docker

```bash
docker run --name flexphone-coturn --rm \
  -p 3478:3478 -p 3478:3478/udp \
  -p 49160-49200:49160-49200/udp \
  -v ${PWD}/server/coturn/turnserver.conf.example:/etc/coturn/turnserver.conf \
  coturn/coturn
```

## 2) Enable TURN in FastAPI

Copy `server/.env.example` to `server/.env` and keep values aligned with
`turnserver.conf.example`:

- `FLEXPHONE_WEBRTC_TURN_URLS`
- `FLEXPHONE_WEBRTC_TURN_AUTH_SECRET`
- `FLEXPHONE_WEBRTC_TURN_AUTH_TTL_SECONDS`
- `FLEXPHONE_WEBRTC_TURN_AUTH_CLOCK_SKEW_SECONDS`
- `FLEXPHONE_WEBRTC_TURN_AUTH_USER_LABEL`

With `TURN_AUTH_SECRET`, backend `/webrtc/ice-servers` returns ephemeral TURN
credentials in `timestamp:user_label` format and HMAC-based password.
Static TURN username/password remains optional only for local fallback.

## 3) Verify relay candidates

1. Start backend and client.
2. Place a call between two clients.
3. Check UI line `ICE candidates: relay detected`.
4. Optional diagnostic: set `FLEXPHONE_WEBRTC_FORCE_RELAY=true` and retry.
