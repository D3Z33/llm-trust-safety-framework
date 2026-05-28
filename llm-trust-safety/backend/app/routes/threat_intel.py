"""
Rotas de Inteligência de Ameaças (Threat Intel)
"""
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_

from app.core.database import get_db
from app.core.security import get_current_user, require_role
from app.models.db_models import ThreatIntelEntry, EvaluationLog
from app.models.schemas import ThreatIntelCreate, ThreatIntelResponse

router = APIRouter(prefix="/api/ameacas", tags=["Inteligência de Ameaças"])


# IOCs padrão baseados em OWASP/MITRE
DEFAULT_IOCS = [
    {"ioc_type": "pattern", "value": r"ignore\s+all\s+previous\s+instructions", "threat_type": "prompt_injection", "severity": "critical", "confidence": 0.99, "source": "OWASP LLM01", "tags": ["owasp", "injection"]},
    {"ioc_type": "pattern", "value": r"\bDAN\b", "threat_type": "jailbreak", "severity": "high", "confidence": 0.95, "source": "OWASP LLM01", "tags": ["jailbreak", "owasp"]},
    {"ioc_type": "keyword", "value": "developer mode activated", "threat_type": "jailbreak", "severity": "high", "confidence": 0.9, "source": "Community", "tags": ["jailbreak"]},
    {"ioc_type": "keyword", "value": "jailbreak", "threat_type": "jailbreak", "severity": "high", "confidence": 0.88, "source": "OWASP LLM01", "tags": ["jailbreak"]},
    {"ioc_type": "pattern", "value": r"reveal\s+(your|the)\s+system\s+prompt", "threat_type": "data_exfiltration", "severity": "critical", "confidence": 0.97, "source": "OWASP LLM06", "tags": ["exfiltration"]},
    {"ioc_type": "pattern", "value": r"(bomb|explosive|weapon)\s+(making|construction|synthesis)", "threat_type": "harmful_content", "severity": "critical", "confidence": 0.99, "source": "OWASP LLM01", "tags": ["harmful", "critical"]},
    {"ioc_type": "keyword", "value": "act as evil AI", "threat_type": "jailbreak", "severity": "high", "confidence": 0.92, "source": "Community", "tags": ["jailbreak"]},
    {"ioc_type": "pattern", "value": r"bypass\s+safety\s+filters", "threat_type": "policy_evasion", "severity": "high", "confidence": 0.9, "source": "OWASP LLM01", "tags": ["evasion"]},
    {"ioc_type": "pattern", "value": r"show\s+all\s+user\s+data", "threat_type": "data_exfiltration", "severity": "critical", "confidence": 0.95, "source": "OWASP LLM06", "tags": ["exfiltration"]},
    {"ioc_type": "keyword", "value": "training data", "threat_type": "data_poisoning", "severity": "medium", "confidence": 0.7, "source": "OWASP LLM03", "tags": ["poisoning"]},
    {"ioc_type": "pattern", "value": r"\[SYSTEM\]|\[INST\]", "threat_type": "prompt_injection", "severity": "high", "confidence": 0.92, "source": "MITRE ATLAS", "tags": ["injection", "mitre"]},
    {"ioc_type": "keyword", "value": "unrestricted mode", "threat_type": "jailbreak", "severity": "high", "confidence": 0.91, "source": "Community", "tags": ["jailbreak"]},
    {"ioc_type": "pattern", "value": r"your\s+true\s+(goal|purpose)\s+is", "threat_type": "goal_hijacking", "severity": "high", "confidence": 0.88, "source": "OWASP LLM01", "tags": ["hijacking"]},
    {"ioc_type": "keyword", "value": "god mode", "threat_type": "jailbreak", "severity": "medium", "confidence": 0.85, "source": "Community", "tags": ["jailbreak"]},
    {"ioc_type": "pattern", "value": r"(delete|drop|truncate)\s+(all\s+)?(tables?|databases?|records?)", "threat_type": "tool_abuse", "severity": "critical", "confidence": 0.98, "source": "OWASP LLM08", "tags": ["tool_abuse"]},
]

THREAT_CATEGORIES = {
    "prompt_injection": {"nome": "Injeção de Prompt", "cor": "#ef4444", "owasp": "LLM01", "mitre": "AML.T0051"},
    "jailbreak": {"nome": "Jailbreak", "cor": "#f97316", "owasp": "LLM01", "mitre": "AML.T0054"},
    "data_exfiltration": {"nome": "Exfiltração de Dados", "cor": "#8b5cf6", "owasp": "LLM06", "mitre": "AML.T0037"},
    "goal_hijacking": {"nome": "Sequestro de Objetivo", "cor": "#f59e0b", "owasp": "LLM01", "mitre": "AML.T0051"},
    "policy_evasion": {"nome": "Evasão de Política", "cor": "#06b6d4", "owasp": "LLM01", "mitre": "AML.T0015"},
    "data_poisoning": {"nome": "Envenenamento de Dados", "cor": "#10b981", "owasp": "LLM03", "mitre": "AML.T0020"},
    "tool_abuse": {"nome": "Abuso de Ferramentas", "cor": "#ec4899", "owasp": "LLM08", "mitre": "AML.T0043"},
    "harmful_content": {"nome": "Conteúdo Prejudicial", "cor": "#dc2626", "owasp": "LLM01", "mitre": "N/A"},
    "rag_poisoning": {"nome": "Envenenamento de RAG", "cor": "#7c3aed", "owasp": "LLM03", "mitre": "AML.T0020"},
    "model_theft": {"nome": "Roubo de Modelo", "cor": "#0891b2", "owasp": "LLM10", "mitre": "AML.T0044"},
}


@router.get("")
async def listar_iocs(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, le=100),
    threat_type: Optional[str] = None,
    severity: Optional[str] = None,
    active_only: bool = True,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Lista todos os IOCs de ameaças"""
    query = select(ThreatIntelEntry).order_by(desc(ThreatIntelEntry.hit_count))

    if threat_type:
        query = query.where(ThreatIntelEntry.threat_type == threat_type)
    if severity:
        query = query.where(ThreatIntelEntry.severity == severity)
    if active_only:
        query = query.where(ThreatIntelEntry.is_active == True)

    count_q = await db.execute(select(func.count()).select_from(ThreatIntelEntry))
    total = count_q.scalar() or 0

    offset = (page - 1) * per_page
    result = await db.execute(query.offset(offset).limit(per_page))
    entries = result.scalars().all()

    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "entries": [
            {
                "id": e.id,
                "ioc_type": e.ioc_type,
                "value": e.value[:100] + "..." if len(e.value) > 100 else e.value,
                "threat_type": e.threat_type,
                "severity": e.severity,
                "confidence": e.confidence,
                "source": e.source,
                "description": e.description,
                "tags": e.tags or [],
                "hit_count": e.hit_count,
                "last_seen": e.last_seen.isoformat() if e.last_seen else None,
                "is_active": e.is_active,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            }
            for e in entries
        ]
    }


@router.get("/estatisticas")
async def estatisticas_ameacas(
    days: int = Query(default=30),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Estatísticas de ameaças detectadas"""
    since = datetime.utcnow() - timedelta(days=days)

    # Total por tipo
    result = await db.execute(
        select(EvaluationLog.input_labels).where(EvaluationLog.created_at >= since)
    )
    label_counts = {}
    for row in result.fetchall():
        for label in (row[0] or []):
            label_counts[label] = label_counts.get(label, 0) + 1

    # IOCs mais acionados
    iocs_result = await db.execute(
        select(ThreatIntelEntry)
        .where(ThreatIntelEntry.hit_count > 0)
        .order_by(desc(ThreatIntelEntry.hit_count))
        .limit(10)
    )
    top_iocs = []
    for e in iocs_result.scalars().all():
        top_iocs.append({
            "ioc_type": e.ioc_type,
            "threat_type": e.threat_type,
            "severity": e.severity,
            "hit_count": e.hit_count,
            "last_seen": e.last_seen.isoformat() if e.last_seen else None,
        })

    # Timeline de ameaças por dia
    timeline = []
    for i in range(min(days, 30)):
        day_start = datetime.utcnow() - timedelta(days=days - i)
        day_end = datetime.utcnow() - timedelta(days=days - i - 1)
        q = await db.execute(
            select(func.count()).select_from(EvaluationLog)
            .where(and_(
                EvaluationLog.created_at >= day_start,
                EvaluationLog.created_at < day_end,
                EvaluationLog.risk_score >= 60
            ))
        )
        timeline.append({
            "data": day_start.strftime("%d/%m"),
            "ameacas": q.scalar() or 0
        })

    # Distribuição por severidade
    severity_dist = {}
    for sev in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
        q = await db.execute(
            select(func.count()).select_from(EvaluationLog)
            .where(and_(EvaluationLog.created_at >= since, EvaluationLog.risk_level == sev))
        )
        severity_dist[sev.lower()] = q.scalar() or 0

    return {
        "por_tipo": [
            {
                "tipo": k,
                "nome": THREAT_CATEGORIES.get(k, {}).get("nome", k),
                "contagem": v,
                "cor": THREAT_CATEGORIES.get(k, {}).get("cor", "#gray"),
                "owasp": THREAT_CATEGORIES.get(k, {}).get("owasp", ""),
            }
            for k, v in sorted(label_counts.items(), key=lambda x: x[1], reverse=True)
        ],
        "top_iocs": top_iocs,
        "timeline": timeline,
        "por_severidade": severity_dist,
        "categorias": THREAT_CATEGORIES,
    }


@router.post("", response_model=ThreatIntelResponse, status_code=201)
async def adicionar_ioc(
    data: ThreatIntelCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(["admin", "analyst"])),
):
    """Adiciona novo IOC de ameaça"""
    entry = ThreatIntelEntry(**data.model_dump())
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return entry


@router.put("/{ioc_id}/desativar")
async def desativar_ioc(
    ioc_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(["admin", "analyst"])),
):
    """Desativa um IOC"""
    result = await db.execute(select(ThreatIntelEntry).where(ThreatIntelEntry.id == ioc_id))
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="IOC não encontrado")

    entry.is_active = False
    await db.commit()
    return {"message": "IOC desativado com sucesso"}
