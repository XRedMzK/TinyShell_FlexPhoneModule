from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "FlexPhone Server"
    debug: bool = True
    allowed_origins: list[str] = ["http://127.0.0.1:1420", "tauri://localhost"]
    webrtc_stun_urls: list[str] = Field(
        default_factory=lambda: ["stun:stun.l.google.com:19302"]
    )
    webrtc_turn_urls: list[str] = Field(default_factory=list)
    webrtc_turn_auth_secret: str | None = None
    webrtc_turn_auth_ttl_seconds: int = Field(default=600, ge=60, le=86400)
    webrtc_turn_auth_clock_skew_seconds: int = Field(default=30, ge=0, le=300)
    webrtc_turn_auth_user_label: str = "flexphone"
    webrtc_turn_username: str | None = None
    webrtc_turn_password: str | None = None
    webrtc_force_relay: bool = False
    auth_challenge_ttl_seconds: int = Field(default=60, ge=30, le=120)
    auth_challenge_nonce_bytes: int = Field(default=32, ge=16, le=128)
    auth_challenge_redis_url: str = "redis://127.0.0.1:6379/0"
    auth_challenge_store_prefix: str = "auth:challenge"
    auth_challenge_retention_seconds: int = Field(default=300, ge=0, le=86400)
    signaling_redis_url: str = "redis://127.0.0.1:6379/0"
    signaling_presence_key_prefix: str = "signaling:presence"
    signaling_session_key_prefix: str = "signaling:session"
    signaling_pubsub_channel_prefix: str = "signaling:fanout"
    signaling_presence_ttl_seconds: int = Field(default=45, ge=15, le=300)
    signaling_instance_id: str = "flexphone-instance-1"
    auth_clock_skew_seconds: int = Field(default=30, ge=0, le=300)
    auth_jwt_issuer: str = "flexphone-backend"
    auth_jwt_audience: str = "signaling"
    auth_jwt_algorithm: str = "HS256"
    auth_jwt_ttl_seconds: int = Field(default=600, ge=300, le=600)
    auth_jwt_secret: str | None = None
    otel_exporter: str = "none"
    otel_service_name: str = "flexphone-backend"
    otel_otlp_endpoint: str = "http://127.0.0.1:4318/v1/traces"

    @field_validator(
        "allowed_origins", "webrtc_stun_urls", "webrtc_turn_urls", mode="before"
    )
    @classmethod
    def _parse_csv_list(cls, value: object) -> object:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @field_validator("webrtc_turn_auth_user_label")
    @classmethod
    def _validate_turn_user_label(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("webrtc_turn_auth_user_label must not be empty")
        if ":" in normalized:
            raise ValueError("webrtc_turn_auth_user_label must not contain ':'")
        return normalized

    @field_validator("auth_jwt_secret")
    @classmethod
    def _validate_auth_jwt_secret(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        if not normalized:
            raise ValueError("auth_jwt_secret must not be empty when provided")
        return normalized

    @field_validator("otel_exporter")
    @classmethod
    def _validate_otel_exporter(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in {"none", "console", "otlp"}:
            raise ValueError("otel_exporter must be one of: none, console, otlp")
        return normalized

    @field_validator(
        "auth_challenge_redis_url",
        "auth_challenge_store_prefix",
        "signaling_redis_url",
        "signaling_presence_key_prefix",
        "signaling_session_key_prefix",
        "signaling_pubsub_channel_prefix",
        "signaling_instance_id",
        "otel_service_name",
        "otel_otlp_endpoint",
    )
    @classmethod
    def _validate_non_empty_auth_store_settings(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("setting must not be empty")
        return normalized

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="FLEXPHONE_",
        enable_decoding=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
