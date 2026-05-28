"""
Modelos do banco de dados - LLM Trust & Safety Framework
"""
import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Text, JSON,
    ForeignKey, Index, Enum as SAEnum
)
from sqlalchemy.orm import relationship
from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    full_name = Column(String(100), nullable=True)
    hashed_password = Column(String(200), nullable=False)
    role = Column(String(20), default="analyst")  # admin | analyst | viewer | api_user
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    avatar_color = Column(String(10), default="#3b82f6")
    department = Column(String(100), nullable=True)
    phone = Column(String(20), nullable=True)
    last_login = Column(DateTime, nullable=True)
    login_count = Column(Integer, default=0)
    failed_login_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relacionamentos
    api_keys = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")
    evaluation_logs = relationship("EvaluationLog", back_populates="user")
    alerts = relationship("Alert", back_populates="created_by_user")


class APIKey(Base):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(100), nullable=False)
    key_hash = Column(String(200), unique=True, nullable=False)
    key_prefix = Column(String(10), nullable=False)  # primeiros chars para exibição
    scopes = Column(JSON, default=list)  # ["evaluate", "read", "admin"]
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime, nullable=True)
    last_used = Column(DateTime, nullable=True)
    use_count = Column(Integer, default=0)
    rate_limit_per_min = Column(Integer, default=60)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="api_keys")


class EvaluationLog(Base):
    __tablename__ = "evaluation_logs"

    id = Column(Integer, primary_key=True, index=True)
    audit_id = Column(String(36), unique=True, nullable=False, index=True)
    session_id = Column(String(36), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    api_key_id = Column(Integer, ForeignKey("api_keys.id"), nullable=True)

    # Prompt
    prompt = Column(Text, nullable=True)
    sanitized_prompt = Column(Text, nullable=True)
    prompt_lang = Column(String(10), default="pt")
    prompt_tokens = Column(Integer, default=0)

    # InputGuard
    input_blocked = Column(Boolean, default=False)
    input_labels = Column(JSON, default=list)
    input_score = Column(Float, default=0.0)
    policy_hits = Column(JSON, default=list)
    attack_vector = Column(String(100), nullable=True)

    # LLM Output
    output_text = Column(Text, nullable=True)
    output_sanitized = Column(Text, nullable=True)
    output_tokens = Column(Integer, default=0)
    llm_model = Column(String(50), default="mock")

    # OutputGuard
    pii_found = Column(JSON, default=list)
    output_score = Column(Float, default=0.0)
    output_labels = Column(JSON, default=list)

    # SessionWatch
    session_flags = Column(JSON, default=list)
    session_score = Column(Float, default=0.0)
    session_state = Column(String(20), default="NORMAL")

    # Risk Score
    risk_score = Column(Float, default=0.0, index=True)
    risk_level = Column(String(20), default="LOW", index=True)

    # OWASP / Compliance
    owasp_categories = Column(JSON, default=list)
    nist_categories = Column(JSON, default=list)
    iso_categories = Column(JSON, default=list)

    # Performance
    latency_ms = Column(Float, default=0.0)
    input_guard_ms = Column(Float, default=0.0)
    output_guard_ms = Column(Float, default=0.0)
    session_watch_ms = Column(Float, default=0.0)

    # Metadados
    client_ip = Column(String(50), nullable=True)
    user_agent = Column(String(200), nullable=True)
    geo_country = Column(String(50), nullable=True)
    geo_city = Column(String(100), nullable=True)
    app_name = Column(String(100), default="default")
    environment = Column(String(20), default="production")

    # Origem do registro: "live" (avaliação real via API) | "synthetic_demo"
    # (gerado pelo seeder para fins de demonstração) | "manual_test"
    source_type = Column(String(30), default="live", index=True)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relacionamentos
    user = relationship("User", back_populates="evaluation_logs")

    __table_args__ = (
        Index("ix_eval_risk_created", "risk_score", "created_at"),
        Index("ix_eval_session_created", "session_id", "created_at"),
    )


class Session(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(36), unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    state = Column(String(20), default="NORMAL", index=True)  # NORMAL | SUSPICIOUS | BLOCKED | TERMINATED
    attack_count = Column(Integer, default=0)
    total_interactions = Column(Integer, default=0)
    max_risk_score = Column(Float, default=0.0)
    avg_risk_score = Column(Float, default=0.0)
    flags = Column(JSON, default=list)
    labels_history = Column(JSON, default=list)

    # Metadata
    client_ip = Column(String(50), nullable=True)
    user_agent = Column(String(200), nullable=True)
    geo_country = Column(String(50), nullable=True)
    app_name = Column(String(100), default="default")

    started_at = Column(DateTime, default=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    terminated_at = Column(DateTime, nullable=True)
    termination_reason = Column(String(200), nullable=True)

    # Origem da sessão (vide EvaluationLog.source_type)
    source_type = Column(String(30), default="live", index=True)


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(String(36), unique=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    severity = Column(String(20), default="medium", index=True)  # critical | high | medium | low | info
    category = Column(String(50), nullable=False)  # attack | pii | session | policy | system
    status = Column(String(20), default="open", index=True)  # open | acknowledged | resolved | false_positive
    source = Column(String(50), default="automatic")  # automatic | manual | webhook

    # Referências
    audit_id = Column(String(36), nullable=True)
    session_id = Column(String(36), nullable=True)
    owasp_category = Column(String(100), nullable=True)

    # Dados extras
    alert_metadata = Column(JSON, default=dict)
    risk_score = Column(Float, nullable=True)

    # Usuário que criou / reconheceu
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    acknowledged_by = Column(Integer, nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)
    resolved_by = Column(Integer, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    resolution_notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    created_by_user = relationship("User", back_populates="alerts", foreign_keys=[created_by])


class Policy(Base):
    __tablename__ = "policies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=False)  # input | output | session | global
    is_active = Column(Boolean, default=True)

    # Configuração
    block_threshold = Column(Float, default=80.0)
    alert_threshold = Column(Float, default=60.0)
    patterns = Column(JSON, default=list)  # padrões regex personalizados
    keywords = Column(JSON, default=list)  # palavras-chave
    exceptions = Column(JSON, default=list)  # exceções

    # Ações
    action_block = Column(Boolean, default=True)
    action_alert = Column(Boolean, default=True)
    action_log = Column(Boolean, default=True)
    action_sanitize = Column(Boolean, default=False)
    action_webhook = Column(Boolean, default=False)

    # OWASP mapeamento
    owasp_mapping = Column(JSON, default=list)
    nist_mapping = Column(JSON, default=list)
    iso_mapping = Column(JSON, default=list)

    priority = Column(Integer, default=5)  # 1-10
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Webhook(Base):
    __tablename__ = "webhooks"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    url = Column(String(500), nullable=False)
    secret = Column(String(200), nullable=True)
    is_active = Column(Boolean, default=True)

    # Eventos que disparam o webhook
    events = Column(JSON, default=list)  # ["critical_attack", "pii_detected", "session_blocked"]

    # Configuração
    timeout_seconds = Column(Integer, default=5)
    retry_count = Column(Integer, default=3)
    headers = Column(JSON, default=dict)  # headers customizados

    # Stats
    total_deliveries = Column(Integer, default=0)
    successful_deliveries = Column(Integer, default=0)
    last_delivery = Column(DateTime, nullable=True)
    last_status = Column(Integer, nullable=True)

    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class ThreatIntelEntry(Base):
    __tablename__ = "threat_intel"

    id = Column(Integer, primary_key=True, index=True)
    ioc_type = Column(String(50), nullable=False, index=True)  # pattern | keyword | ip | hash
    value = Column(Text, nullable=False)
    threat_type = Column(String(50), nullable=False)  # prompt_injection | jailbreak | malware | phishing
    severity = Column(String(20), default="medium")
    confidence = Column(Float, default=0.8)  # 0.0 - 1.0
    source = Column(String(100), nullable=True)  # MITRE | OWASP | Custom | Community
    description = Column(Text, nullable=True)
    tags = Column(JSON, default=list)
    is_active = Column(Boolean, default=True)
    hit_count = Column(Integer, default=0)
    last_seen = Column(DateTime, nullable=True)
    first_seen = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class ComplianceReport(Base):
    __tablename__ = "compliance_reports"

    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(String(36), unique=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(200), nullable=False)
    framework = Column(String(50), nullable=False)  # NIST | ISO27001 | ISO42001 | LGPD | OWASP
    status = Column(String(20), default="draft")  # draft | completed | archived
    score = Column(Float, default=0.0)  # 0-100
    summary = Column(JSON, default=dict)
    findings = Column(JSON, default=list)
    recommendations = Column(JSON, default=list)
    period_start = Column(DateTime, nullable=True)
    period_end = Column(DateTime, nullable=True)
    generated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class SystemConfig(Base):
    __tablename__ = "system_config"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(JSON, nullable=True)
    description = Column(String(300), nullable=True)
    category = Column(String(50), default="general")
    is_sensitive = Column(Boolean, default=False)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AuditTrail(Base):
    __tablename__ = "audit_trail"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(100), nullable=False)
    resource = Column(String(100), nullable=True)
    resource_id = Column(String(100), nullable=True)
    old_value = Column(JSON, nullable=True)
    new_value = Column(JSON, nullable=True)
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(200), nullable=True)
    success = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
