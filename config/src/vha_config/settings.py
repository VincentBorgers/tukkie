from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT_DIR = Path(__file__).resolve().parents[3]


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Tukkie"
    environment: str = "development"
    host: str = "127.0.0.1"
    port: int = 8000
    default_language: str = "nl-NL"
    db_path: Path = ROOT_DIR / "config" / "data" / "tukkie.db"
    chroma_path: Path = ROOT_DIR / "config" / "chroma"
    models_path: Path = ROOT_DIR / "config" / "models"
    dashboard_dist_path: Path = ROOT_DIR / "dashboard" / "dist"
    prompt_path: Path = ROOT_DIR / "config" / "prompts" / "dutch_system_prompt.txt"
    assistant_config_path: Path = ROOT_DIR / "config" / "assistant.yaml"
    profile_config_path: Path = ROOT_DIR / "config" / "profile.yaml"
    rooms_config_path: Path = ROOT_DIR / "config" / "rooms.yaml"
    devices_config_path: Path = ROOT_DIR / "config" / "devices.yaml"
    scenes_config_path: Path = ROOT_DIR / "config" / "scenes.yaml"
    automations_config_path: Path = ROOT_DIR / "config" / "automations.yaml"
    ollama_host: str = "http://127.0.0.1:11434"
    ollama_model: str = "llama3.1:8b"
    allow_fallback_integrations: bool = False
    use_sample_seed_data: bool = False
    memory_encryption_key: str | None = None
    tool_timeout_seconds: int = 10
    telemetry_enabled: bool = False
    enable_voice_blueprint: bool = True
    voice_input_enabled: bool = True
    voice_auto_speak: bool = False
    vosk_model_path: Path = ROOT_DIR / "config" / "models" / "vosk-model-small-nl-0.22"
    piper_binary_path: Path | None = None
    piper_voice_model_path: Path | None = ROOT_DIR / "config" / "models" / "piper" / "nl_NL-ronnie-medium.onnx"
    piper_voice_config_path: Path | None = ROOT_DIR / "config" / "models" / "piper" / "nl_NL-ronnie-medium.onnx.json"
    voice_cache_path: Path = ROOT_DIR / "config" / "data" / "voice-cache"
    device_refresh_interval_seconds: int = 30
    critical_confirmation_window_seconds: int = 300
    cors_origins: str = "http://127.0.0.1:5173,http://localhost:5173,http://127.0.0.1:8000,http://localhost:8000"
    default_profile_name: str = "Household"
    default_home_city: str = ""
    default_wake_word: str = "tukkie"
    ring_username: str | None = None
    ring_password: str | None = None
    ring_2fa_code: str | None = None
    ring_token_cache_path: Path = ROOT_DIR / "config" / "data" / "ring-token.json"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @field_validator("piper_binary_path", "piper_voice_model_path", "piper_voice_config_path", mode="before")
    @classmethod
    def empty_path_to_none(cls, value):
        if value in {"", None}:
            return None
        return value

    @field_validator(
        "db_path",
        "chroma_path",
        "models_path",
        "dashboard_dist_path",
        "prompt_path",
        "assistant_config_path",
        "profile_config_path",
        "rooms_config_path",
        "devices_config_path",
        "scenes_config_path",
        "automations_config_path",
        "vosk_model_path",
        "piper_binary_path",
        "piper_voice_model_path",
        "piper_voice_config_path",
        "voice_cache_path",
        "ring_token_cache_path",
        mode="after",
    )
    @classmethod
    def resolve_relative_paths(cls, value):
        if value is None:
            return None
        path = Path(value)
        if path.is_absolute():
            return path
        return ROOT_DIR / path

    def ensure_directories(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.chroma_path.mkdir(parents=True, exist_ok=True)
        self.models_path.mkdir(parents=True, exist_ok=True)
        self.voice_cache_path.mkdir(parents=True, exist_ok=True)
