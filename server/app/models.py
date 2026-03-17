from typing import Literal

from pydantic import BaseModel, Field


class DeviceRegisterRequest(BaseModel):
    nickname: str = Field(..., min_length=2, max_length=64)
    device_id: str = Field(..., min_length=16, max_length=128)
    public_key_spki_base64: str = Field(..., min_length=32)


class DeviceRegisterResponse(BaseModel):
    ok: bool
    nickname: str
    device_id: str


class HealthResponse(BaseModel):
    status: str
    app: str


class ReadinessResponse(BaseModel):
    status: Literal["ok", "degraded"]
    app: str
    checks: dict[str, str]


class IceServerConfig(BaseModel):
    urls: list[str]
    username: str | None = None
    credential: str | None = None


class TurnCredentialsMeta(BaseModel):
    mode: Literal["static", "ephemeral"]
    username: str | None = None
    ttl_seconds: int | None = None
    expires_at_unix: int | None = None
    clock_skew_tolerance_seconds: int | None = None
    username_scheme: str | None = None


class IceServersResponse(BaseModel):
    ice_servers: list[IceServerConfig]
    ice_transport_policy: Literal["all", "relay"] = "all"
    turn_credentials: TurnCredentialsMeta | None = None


class AuthChallengeRequest(BaseModel):
    nickname: str = Field(..., min_length=2, max_length=64)
    device_id: str = Field(..., min_length=16, max_length=128)


class AuthChallengeResponse(BaseModel):
    challenge_id: str
    nickname: str
    device_id: str
    nonce: str
    issued_at: int
    expires_at: int
    algorithm: Literal["ECDSA_P256_SHA256"] = "ECDSA_P256_SHA256"
    payload_version: Literal["flexphone-auth-v1"] = "flexphone-auth-v1"
    canonical_payload: str


class AuthVerifyRequest(BaseModel):
    challenge_id: str = Field(..., min_length=36, max_length=64)
    nickname: str = Field(..., min_length=2, max_length=64)
    device_id: str = Field(..., min_length=16, max_length=128)
    signature: str = Field(..., min_length=8)


class AuthVerifyResponse(BaseModel):
    access_token: str
    token_type: Literal["Bearer"] = "Bearer"
    expires_at: int


class ObservabilitySnapshotResponse(BaseModel):
    timestamp: str
    uptime_seconds: int
    counters: dict[str, int]
