"""
LLM Trust & Safety Framework
Configurações globais - Enterprise Edition
"""
from pydantic import field_validator
from pydantic_settings import BaseSettings
from typing import Optional, List, Any


class Settings(BaseSettings):
    # Segurança
    SECRET_KEY: str = "llm-trust-safety-super-secret-key-enterprise-2025"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480  # 8 horas
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Banco de dados
    DATABASE_URL: str = "sqlite+aiosqlite:///./llm_trust_enterprise.db"

    # LLM
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    LLM_PROVIDER: str = "mock"  # mock | openai | anthropic
    LLM_MODEL: str = "gpt-4o-mini"
    LLM_TIMEOUT: int = 30

    # Aplicação
    APP_NAME: str = "Plataforma de Segurança e Governança para LLMs"
    APP_SUBTITLE: str = "Firewall semântico, auditoria e conformidade para sistemas com modelos de linguagem"
    VERSION: str = "2.0.0"
    DEBUG: bool = True
    ENVIRONMENT: str = "development"

    # CORS — Origens permitidas (vírgula-separadas no .env)
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"

    # Limites
    MAX_PROMPT_LENGTH: int = 10000
    MAX_HISTORY_TURNS: int = 50
    RATE_LIMIT_PER_MINUTE: int = 100
    BLOCK_THRESHOLD: float = 75.0
    ALERT_THRESHOLD: float = 50.0

    # Webhooks
    WEBHOOK_TIMEOUT: int = 5
    WEBHOOK_RETRY_COUNT: int = 3

    # Feature flags
    ENABLE_WEBSOCKET: bool = True
    ENABLE_THREAT_INTEL: bool = True
    ENABLE_COMPLIANCE_ENGINE: bool = True
    ENABLE_DATA_EXPOSURE_MIRROR: bool = True
    ENABLE_GEOLOCATION: bool = False

    # Idioma padrão
    DEFAULT_LANGUAGE: str = "pt-BR"

    @field_validator("DEBUG", mode="before")
    @classmethod
    def parse_debug_value(cls, value: Any) -> Any:
        """Accept common deployment labels for DEBUG coming from the shell."""
        if isinstance(value, bool) or value is None:
            return value
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"1", "true", "yes", "on", "debug", "dev", "development"}:
                return True
            if normalized in {"0", "false", "no", "off", "release", "prod", "production", "staging"}:
                return False
        return value

    @property
    def cors_origins(self) -> List[str]:
        """Retorna lista de origens CORS a partir da string separada por vírgulas."""
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    class Config:
        env_file = ".env"


settings = Settings()

# ── Validação de ambiente no boot ───────────────────────────────────────────────
_DEFAULT_KEY = "llm-trust-safety-super-secret-key-enterprise-2025"
if settings.SECRET_KEY == _DEFAULT_KEY and settings.is_production:
    import warnings
    warnings.warn(
        "⚠️  SECRET_KEY padrão em uso em ENVIRONMENT=production! "
        "Defina uma chave forte no .env antes de implantar.",
        stacklevel=1,
    )
