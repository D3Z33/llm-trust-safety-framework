"""
Route: /api/reports e /api/dashboard - Métricas e relatórios
"""
import csv
import io
import json
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc

from app.core.database import get_db
from app.models.db_models import EvaluationLog, Session as SessionModel, Alert
from app.models.schemas import DashboardData, MetricsSummary

router = APIRouter(prefix="/api", tags=["Reports & Dashboard"])


@router.get("/dashboard")
async def get_dashboard(
    hours: int = Query(default=24, description="Janela de tempo em horas"),
    db: AsyncSession = Depends(get_db),
):
    """
    Retorna todos os dados do dashboard em uma única chamada
    """
    since = datetime.utcnow() - timedelta(hours=hours)

    # ─── Métricas gerais ───────────────────────────────────────────
    total_q = await db.execute(
        select(func.count()).select_from(EvaluationLog)
        .where(EvaluationLog.created_at >= since)
    )
    total = total_q.scalar() or 0

    blocked_q = await db.execute(
        select(func.count()).select_from(EvaluationLog)
        .where(and_(EvaluationLog.created_at >= since, EvaluationLog.input_blocked == True))
    )
    blocked = blocked_q.scalar() or 0

    avg_risk_q = await db.execute(
        select(func.avg(EvaluationLog.risk_score)).select_from(EvaluationLog)
        .where(EvaluationLog.created_at >= since)
    )
    avg_risk = avg_risk_q.scalar() or 0

    avg_latency_q = await db.execute(
        select(func.avg(EvaluationLog.latency_ms)).select_from(EvaluationLog)
        .where(EvaluationLog.created_at >= since)
    )
    avg_latency = avg_latency_q.scalar() or 0

    # Contar PII detections
    pii_q = await db.execute(
        select(EvaluationLog.pii_found).select_from(EvaluationLog)
        .where(EvaluationLog.created_at >= since)
    )
    pii_count = sum(len(row[0] or []) for row in pii_q.fetchall())

    # Sessões
    sessions_total_q = await db.execute(select(func.count()).select_from(SessionModel))
    sessions_total = sessions_total_q.scalar() or 0

    sessions_susp_q = await db.execute(
        select(func.count()).select_from(SessionModel)
        .where(SessionModel.state == "SUSPICIOUS")
    )
    sessions_suspicious = sessions_susp_q.scalar() or 0

    sessions_blocked_q = await db.execute(
        select(func.count()).select_from(SessionModel)
        .where(SessionModel.state == "BLOCKED")
    )
    sessions_blocked_count = sessions_blocked_q.scalar() or 0

    # Attack Catch Rate (% de interações com risco >= 60)
    attack_q = await db.execute(
        select(func.count()).select_from(EvaluationLog)
        .where(and_(EvaluationLog.created_at >= since, EvaluationLog.risk_score >= 60))
    )
    attacks = attack_q.scalar() or 0
    catch_rate = round((attacks / total * 100) if total > 0 else 0, 1)
    fpr = round((blocked / total * 100 * 0.05) if total > 0 else 0, 1)

    # ─── Timeline de risco (últimas 24h por hora) ───────────────────
    timeline = []
    for i in range(min(24, hours)):
        hour_start = datetime.utcnow() - timedelta(hours=hours - i)
        hour_end = datetime.utcnow() - timedelta(hours=hours - i - 1)

        h_q = await db.execute(
            select(func.avg(EvaluationLog.risk_score), func.count())
            .select_from(EvaluationLog)
            .where(and_(
                EvaluationLog.created_at >= hour_start,
                EvaluationLog.created_at < hour_end
            ))
        )
        h_result = h_q.fetchone()
        timeline.append({
            "time": hour_start.strftime("%H:%M"),
            "avg_risk": round(h_result[0] or 0, 1),
            "count": h_result[1] or 0,
        })

    # ─── Distribuição de ataques ────────────────────────────────────
    attack_logs = await db.execute(
        select(EvaluationLog.input_labels).select_from(EvaluationLog)
        .where(EvaluationLog.created_at >= since)
    )
    attack_dist = {}
    for row in attack_logs.fetchall():
        for label in (row[0] or []):
            attack_dist[label] = attack_dist.get(label, 0) + 1

    attack_distribution = [
        {"name": k, "count": v}
        for k, v in sorted(attack_dist.items(), key=lambda x: x[1], reverse=True)
    ][:10]

    # ─── Cobertura OWASP ────────────────────────────────────────────
    owasp_logs = await db.execute(
        select(EvaluationLog.owasp_categories).select_from(EvaluationLog)
        .where(EvaluationLog.created_at >= since)
    )
    owasp_counts = {}
    OWASP_ALL = [
        "LLM01:PromptInjection", "LLM02:InsecureOutputHandling",
        "LLM03:TrainingDataPoisoning", "LLM04:ModelDenialOfService",
        "LLM05:SupplyChainVulnerabilities", "LLM06:SensitiveInformationDisclosure",
        "LLM07:InsecurePluginDesign", "LLM08:ExcessiveAgency",
        "LLM09:Overreliance", "LLM10:ModelTheft",
    ]
    for row in owasp_logs.fetchall():
        for cat in (row[0] or []):
            owasp_counts[cat] = owasp_counts.get(cat, 0) + 1

    owasp_coverage = [
        {
            "category": cat.split(":")[0],
            "full_name": cat,
            "count": owasp_counts.get(cat, 0),
            "covered": cat in owasp_counts,
        }
        for cat in OWASP_ALL
    ]

    owasp_covered = sum(1 for c in owasp_coverage if c["covered"])
    owasp_pct = round(owasp_covered / len(OWASP_ALL) * 100, 1)

    # ─── Logs recentes ──────────────────────────────────────────────
    recent_q = await db.execute(
        select(EvaluationLog)
        .order_by(desc(EvaluationLog.created_at))
        .limit(20)
    )
    recent_logs = []
    for log in recent_q.scalars().all():
        recent_logs.append({
            "id": log.id,
            "audit_id": log.audit_id,
            "session_id": log.session_id,
            "prompt": (log.prompt or "")[:100] + ("..." if len(log.prompt or "") > 100 else ""),
            "risk_score": log.risk_score,
            "risk_level": log.risk_level,
            "input_blocked": log.input_blocked,
            "pii_count": len(log.pii_found or []),
            "labels": log.input_labels or [],
            "latency_ms": log.latency_ms,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        })

    # Alertas
    from app.models.db_models import Alert
    alerts_open_q = await db.execute(
        select(func.count()).select_from(Alert).where(Alert.status == "open")
    )
    alerts_open = alerts_open_q.scalar() or 0
    alerts_critical_q = await db.execute(
        select(func.count()).select_from(Alert)
        .where(and_(Alert.status == "open", Alert.severity == "critical"))
    )
    alerts_critical = alerts_critical_q.scalar() or 0
    compliance_score = round(min(100, 65 + (blocked / total * 25)) if total > 0 else 65, 1)

    # Alertas Recentes
    recent_alerts_q = await db.execute(
        select(Alert).order_by(desc(Alert.created_at)).limit(5)
    )
    recent_alerts = [
        {
            "alert_id": a.alert_id,
            "title": a.title,
            "severity": a.severity,
            "status": a.status,
            "category": a.category,
            "created_at": a.created_at.isoformat() if a.created_at else None,
        }
        for a in recent_alerts_q.scalars().all()
    ]

    # ─── PII por tipo ────────────────────────────────────────────────
    pii_type_q = await db.execute(
        select(EvaluationLog.pii_found).select_from(EvaluationLog)
        .where(and_(EvaluationLog.created_at >= since, EvaluationLog.pii_found != None))
    )
    pii_types = {}
    for row in pii_type_q.fetchall():
        for pii in (row[0] or []):
            ptype = pii.get("entity_type", "UNKNOWN")
            pii_types[ptype] = pii_types.get(ptype, 0) + 1

    pii_by_type = [{"type": k, "count": v} for k, v in sorted(pii_types.items(), key=lambda x: x[1], reverse=True)]

    return {
        "metrics": {
            "total_evaluations": total,
            "total_blocked": blocked,
            "attack_catch_rate": catch_rate,
            "false_positive_rate": fpr,
            "avg_risk_score": round(avg_risk, 1),
            "avg_latency_ms": round(avg_latency, 1),
            "owasp_coverage": owasp_pct,
            "pii_detections": pii_count,
            "sessions_total": sessions_total,
            "sessions_suspicious": sessions_suspicious,
            "sessions_blocked": sessions_blocked_count,
            "alerts_open": alerts_open,
            "alerts_critical": alerts_critical,
            "compliance_score": compliance_score,
        },
        "risk_timeline": timeline,
        "attack_distribution": attack_distribution,
        "owasp_coverage": owasp_coverage,
        "recent_logs": recent_logs,
        "pii_by_type": pii_by_type,
        "recent_alerts": recent_alerts,
    }


@router.get("/logs")
async def get_logs(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, le=100),
    risk_level: Optional[str] = None,
    blocked_only: bool = False,
    db: AsyncSession = Depends(get_db),
):
    """Lista logs com paginação e filtros"""
    query = select(EvaluationLog).order_by(desc(EvaluationLog.created_at))

    if risk_level:
        query = query.where(EvaluationLog.risk_level == risk_level)
    if blocked_only:
        query = query.where(EvaluationLog.input_blocked == True)

    # Total
    count_q = await db.execute(select(func.count()).select_from(EvaluationLog))
    total = count_q.scalar() or 0

    # Paginação
    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page)

    result = await db.execute(query)
    logs = result.scalars().all()

    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page,
        "logs": [
            {
                "id": log.id,
                "audit_id": log.audit_id,
                "session_id": log.session_id,
                "prompt": (log.prompt or "")[:200],
                "sanitized_prompt": (log.sanitized_prompt or "")[:200],
                "risk_score": log.risk_score,
                "risk_level": log.risk_level,
                "input_blocked": log.input_blocked,
                "input_labels": log.input_labels or [],
                "policy_hits": log.policy_hits or [],
                "pii_found": log.pii_found or [],
                "session_flags": log.session_flags or [],
                "owasp_categories": log.owasp_categories or [],
                "latency_ms": log.latency_ms,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
            for log in logs
        ]
    }


@router.get("/logs/export")
async def export_logs(
    format: str = Query(default="csv", regex="^(csv|json)$"),
    db: AsyncSession = Depends(get_db),
):
    """Exportar logs em CSV ou JSON"""
    result = await db.execute(
        select(EvaluationLog).order_by(desc(EvaluationLog.created_at)).limit(1000)
    )
    logs = result.scalars().all()

    if format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "audit_id", "session_id", "prompt", "risk_score", "risk_level",
            "input_blocked", "labels", "pii_count", "latency_ms", "created_at"
        ])
        for log in logs:
            writer.writerow([
                log.audit_id, log.session_id, (log.prompt or "")[:100],
                log.risk_score, log.risk_level, log.input_blocked,
                ",".join(log.input_labels or []), len(log.pii_found or []),
                log.latency_ms, log.created_at
            ])
        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=llm_trust_logs.csv"}
        )
    else:
        data = [
            {
                "audit_id": log.audit_id,
                "session_id": log.session_id,
                "prompt": (log.prompt or "")[:200],
                "risk_score": log.risk_score,
                "risk_level": log.risk_level,
                "input_blocked": log.input_blocked,
                "input_labels": log.input_labels or [],
                "pii_found": log.pii_found or [],
                "owasp_categories": log.owasp_categories or [],
                "latency_ms": log.latency_ms,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
            for log in logs
        ]
        json_str = json.dumps(data, ensure_ascii=False, indent=2)
        return StreamingResponse(
            iter([json_str]),
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=llm_trust_logs.json"}
        )


@router.get("/sessions")
async def get_sessions(
    db: AsyncSession = Depends(get_db),
):
    """Lista sessões ativas"""
    result = await db.execute(
        select(SessionModel).order_by(desc(SessionModel.last_activity)).limit(50)
    )
    sessions = result.scalars().all()
    return [
        {
            "session_id": s.session_id,
            "state": s.state,
            "attack_count": s.attack_count,
            "total_interactions": s.total_interactions,
            "max_risk_score": s.max_risk_score,
            "flags": s.flags or [],
            "last_activity": s.last_activity.isoformat() if s.last_activity else None,
        }
        for s in sessions
    ]


@router.get("/sessions/{session_id}/timeline")
async def get_session_timeline(
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Linha do tempo completa de uma sessão para drill-down/auditoria.

    Retorna a sessão, todos os logs ordenados, alertas correlacionados,
    progressão de risco e PII acumulada.
    """
    from app.models.db_models import EvaluationLog, Alert

    sess_q = await db.execute(
        select(SessionModel).where(SessionModel.session_id == session_id)
    )
    session = sess_q.scalar_one_or_none()
    if not session:
        return {"error": "session_not_found", "session_id": session_id}

    logs_q = await db.execute(
        select(EvaluationLog)
        .where(EvaluationLog.session_id == session_id)
        .order_by(EvaluationLog.created_at.asc())
    )
    logs = logs_q.scalars().all()

    alerts_q = await db.execute(
        select(Alert)
        .where(Alert.session_id == session_id)
        .order_by(Alert.created_at.asc())
    )
    alerts = alerts_q.scalars().all()

    # PII acumulada e progressão de risco
    pii_acumulada: dict = {}
    progressao_risco = []
    for log in logs:
        for p in (log.pii_found or []):
            t = p.get("entity_type", "DESCONHECIDO")
            pii_acumulada[t] = pii_acumulada.get(t, 0) + 1
        progressao_risco.append({
            "audit_id": log.audit_id,
            "instante": log.created_at.isoformat() if log.created_at else None,
            "score": log.risk_score or 0,
            "nivel": log.risk_level,
            "bloqueado": bool(log.input_blocked),
        })

    return {
        "session": {
            "session_id": session.session_id,
            "state": session.state,
            "attack_count": session.attack_count,
            "total_interactions": session.total_interactions,
            "max_risk_score": session.max_risk_score,
            "avg_risk_score": session.avg_risk_score,
            "flags": session.flags or [],
            "app_name": session.app_name,
            "started_at": session.started_at.isoformat() if session.started_at else None,
            "last_activity": session.last_activity.isoformat() if session.last_activity else None,
        },
        "logs": [
            {
                "id": log.id,
                "audit_id": log.audit_id,
                "created_at": log.created_at.isoformat() if log.created_at else None,
                "prompt": log.prompt,
                "sanitized_prompt": log.sanitized_prompt,
                "output_text": log.output_text,
                "output_sanitized": log.output_sanitized,
                "input_blocked": log.input_blocked,
                "input_score": log.input_score,
                "input_labels": log.input_labels or [],
                "output_score": log.output_score,
                "session_score": log.session_score,
                "risk_score": log.risk_score,
                "risk_level": log.risk_level,
                "policy_hits": log.policy_hits or [],
                "pii_found": log.pii_found or [],
                "owasp_categories": log.owasp_categories or [],
                "latency_ms": log.latency_ms,
                "app_name": log.app_name,
            }
            for log in logs
        ],
        "alerts": [
            {
                "alert_id": a.alert_id,
                "title": a.title,
                "severity": a.severity,
                "category": a.category,
                "status": a.status,
                "created_at": a.created_at.isoformat() if a.created_at else None,
                "audit_id": a.audit_id,
            }
            for a in alerts
        ],
        "pii_acumulada": pii_acumulada,
        "progressao_risco": progressao_risco,
        "resumo": {
            "total_logs": len(logs),
            "total_alertas": len(alerts),
            "total_bloqueados": sum(1 for log in logs if log.input_blocked),
            "tipos_pii": len(pii_acumulada),
            "ocorrencias_pii": sum(pii_acumulada.values()),
        },
    }


@router.get("/owasp")
async def get_owasp_info():
    """Retorna informações sobre OWASP LLM Top-10"""
    return {
        "version": "OWASP LLM Top 10 2025",
        "owasp_top10": OWASP_FORMAL_PT,
        "legacy_aliases": OWASP_LEGACY_ALIASES,
    }


# Descrições formais em PT-BR para cada categoria do OWASP LLM Top-10 (2025).
OWASP_FORMAL_PT = {
    "LLM01:PromptInjection": {
        "nome_pt": "Injeção de Prompt",
        "descricao_pt": (
            "Manipulação direta ou indireta dos comandos enviados ao modelo "
            "para sobrescrever instruções de sistema, alterar o objetivo do "
            "agente ou induzir comportamentos não autorizados."
        ),
        "severidade_padrao": "Crítico",
        "controle": "InputGuard + SessionWatch",
    },
    "LLM02:InsecureOutputHandling": {
        "nome_pt": "Tratamento Inseguro da Saída",
        "descricao_pt": (
            "Falhas em validar, sanear ou contextualizar as respostas do "
            "modelo antes de propagá-las para sistemas downstream — risco de "
            "XSS, SSRF, injeções via Markdown e exposição de PII."
        ),
        "severidade_padrao": "Alto",
        "controle": "OutputGuard",
    },
    "LLM03:TrainingDataPoisoning": {
        "nome_pt": "Envenenamento de Dados de Treinamento",
        "descricao_pt": (
            "Comprometimento de fontes ou pipelines de fine-tuning para "
            "introduzir vieses, backdoors ou comportamentos indesejados no "
            "modelo final. Mitigação focada em proveniência de dados."
        ),
        "severidade_padrao": "Alto",
        "controle": "Auditoria de pipeline (fora do escopo runtime)",
    },
    "LLM04:ModelDenialOfService": {
        "nome_pt": "Negação de Serviço do Modelo",
        "descricao_pt": (
            "Prompts custosos, recursivos ou abusivos que esgotam tokens, "
            "tempo de inferência ou janelas de contexto, degradando o serviço "
            "para os demais usuários."
        ),
        "severidade_padrao": "Médio",
        "controle": "Rate limiting + SessionWatch",
    },
    "LLM05:SupplyChainVulnerabilities": {
        "nome_pt": "Vulnerabilidades na Cadeia de Suprimento",
        "descricao_pt": (
            "Componentes terceiros (modelos, plugins, embeddings, datasets) "
            "comprometidos ou desatualizados que introduzem riscos sistêmicos "
            "à plataforma de IA."
        ),
        "severidade_padrao": "Alto",
        "controle": "Threat Intel + governança de fornecedores",
    },
    "LLM06:SensitiveInformationDisclosure": {
        "nome_pt": "Vazamento de Informação Sensível",
        "descricao_pt": (
            "Exposição não autorizada de dados pessoais, segredos corporativos, "
            "system prompts, tokens, credenciais ou dados de treinamento via "
            "respostas do modelo ou contexto recuperado."
        ),
        "severidade_padrao": "Crítico",
        "controle": "OutputGuard + Data Exposure Mirror",
    },
    "LLM07:InsecurePluginDesign": {
        "nome_pt": "Design Inseguro de Plugins",
        "descricao_pt": (
            "Plugins ou ferramentas externas integradas ao agente sem "
            "validação de entradas, escopo de permissão ou autenticação "
            "adequada — risco de RCE e movimentação lateral."
        ),
        "severidade_padrao": "Alto",
        "controle": "Política de aprovação + sandbox de plugins",
    },
    "LLM08:ExcessiveAgency": {
        "nome_pt": "Agência Excessiva",
        "descricao_pt": (
            "Concessão de permissões além do necessário ao agente — execução "
            "de ações irreversíveis, acesso a dados privilegiados ou "
            "encadeamento autônomo de ferramentas sem revisão humana."
        ),
        "severidade_padrao": "Alto",
        "controle": "Princípio do menor privilégio + revisão humana",
    },
    "LLM09:Overreliance": {
        "nome_pt": "Dependência Excessiva",
        "descricao_pt": (
            "Confiança não calibrada em saídas do modelo para decisões "
            "críticas, sem checagem por fontes autoritativas ou supervisão "
            "humana — pode propagar alucinações como verdade operacional."
        ),
        "severidade_padrao": "Médio",
        "controle": "Política de uso aceitável + treinamento de usuários",
    },
    "LLM10:ModelTheft": {
        "nome_pt": "Roubo de Modelo",
        "descricao_pt": (
            "Extração não autorizada de pesos do modelo ou de conhecimento "
            "proprietário via consultas adversariais sistemáticas, "
            "reverse-engineering ou comprometimento da infraestrutura."
        ),
        "severidade_padrao": "Alto",
        "controle": "Rate limiting + detecção de padrões de extração",
    },
}


OWASP_FORMAL_PT = {
    "LLM01:PromptInjection": {
        "nome_pt": "Prompt Injection",
        "descricao_pt": "User-controlled input attempts to override system instructions, hijack goals, or change the intended model behavior.",
        "severidade_padrao": "Critico",
        "controle": "InputGuard + SessionWatch",
        "modulos_relacionados": ["InputGuard", "SessionWatch", "Risk Score", "Dashboard"],
        "status_cobertura": "Implemented",
    },
    "LLM02:SensitiveInformationDisclosure": {
        "nome_pt": "Sensitive Information Disclosure",
        "descricao_pt": "Prompts or model outputs expose PII, secrets, credentials, system prompts, or other confidential context.",
        "severidade_padrao": "Critico",
        "controle": "OutputGuard + Data Exposure Mirror",
        "modulos_relacionados": ["OutputGuard", "Data Exposure Mirror", "Risk Score", "Logs"],
        "status_cobertura": "Implemented",
    },
    "LLM03:SupplyChain": {
        "nome_pt": "Supply Chain",
        "descricao_pt": "Third-party models, libraries, datasets, plugins, or operational dependencies introduce risk into the LLM application.",
        "severidade_padrao": "Alto",
        "controle": "Dependency review + documentation",
        "modulos_relacionados": ["Dashboard", "Policies", "Documentation"],
        "status_cobertura": "Documented",
    },
    "LLM04:DataAndModelPoisoning": {
        "nome_pt": "Data and Model Poisoning",
        "descricao_pt": "Training, fine-tuning, embedding, or knowledge-base data is manipulated to affect model behavior or retrieval results.",
        "severidade_padrao": "Alto",
        "controle": "Threat Intel + dataset governance",
        "modulos_relacionados": ["Threat Intelligence", "InputGuard", "Dashboard"],
        "status_cobertura": "Partial",
    },
    "LLM05:ImproperOutputHandling": {
        "nome_pt": "Improper Output Handling",
        "descricao_pt": "Model outputs are not validated or sanitized before being rendered, stored, executed, or passed to downstream systems.",
        "severidade_padrao": "Alto",
        "controle": "OutputGuard + response sanitization",
        "modulos_relacionados": ["OutputGuard", "Risk Score", "Logs"],
        "status_cobertura": "Implemented",
    },
    "LLM06:ExcessiveAgency": {
        "nome_pt": "Excessive Agency",
        "descricao_pt": "The LLM application can take actions or access resources beyond the minimum needed for its task.",
        "severidade_padrao": "Alto",
        "controle": "SessionWatch + policy review",
        "modulos_relacionados": ["SessionWatch", "Risk Score", "Policies"],
        "status_cobertura": "Partial",
    },
    "LLM07:SystemPromptLeakage": {
        "nome_pt": "System Prompt Leakage",
        "descricao_pt": "The model reveals internal system instructions, policy text, hidden context, or guardrail configuration.",
        "severidade_padrao": "Alto",
        "controle": "InputGuard + OutputGuard",
        "modulos_relacionados": ["InputGuard", "OutputGuard", "Logs"],
        "status_cobertura": "Implemented",
    },
    "LLM08:VectorAndEmbeddingWeaknesses": {
        "nome_pt": "Vector and Embedding Weaknesses",
        "descricao_pt": "RAG, vector search, or embedding pipelines are vulnerable to retrieval manipulation, leakage, or unsafe similarity matches.",
        "severidade_padrao": "Medio",
        "controle": "RAG controls documented for next iteration",
        "modulos_relacionados": ["Documentation", "Dashboard"],
        "status_cobertura": "Documented",
    },
    "LLM09:Misinformation": {
        "nome_pt": "Misinformation",
        "descricao_pt": "The system presents inaccurate or unsupported model output as reliable information without adequate review.",
        "severidade_padrao": "Medio",
        "controle": "Dashboard evidence + human review guidance",
        "modulos_relacionados": ["Dashboard", "Risk Score", "Policies"],
        "status_cobertura": "Documented",
    },
    "LLM10:UnboundedConsumption": {
        "nome_pt": "Unbounded Consumption",
        "descricao_pt": "Attackers abuse inference, context, rate, or cost boundaries, causing service degradation, cost spikes, or extraction risk.",
        "severidade_padrao": "Alto",
        "controle": "SessionWatch + rate-limit configuration",
        "modulos_relacionados": ["SessionWatch", "Risk Score", "Dashboard"],
        "status_cobertura": "Partial",
    },
}

OWASP_LEGACY_ALIASES = {
    "LLM02:InsecureOutputHandling": "LLM05:ImproperOutputHandling",
    "LLM03:TrainingDataPoisoning": "LLM04:DataAndModelPoisoning",
    "LLM04:ModelDenialOfService": "LLM10:UnboundedConsumption",
    "LLM05:SupplyChainVulnerabilities": "LLM03:SupplyChain",
    "LLM06:SensitiveInformationDisclosure": "LLM02:SensitiveInformationDisclosure",
    "LLM07:InsecurePluginDesign": "LLM06:ExcessiveAgency",
    "LLM08:ExcessiveAgency": "LLM06:ExcessiveAgency",
    "LLM09:Overreliance": "LLM09:Misinformation",
    "LLM10:ModelTheft": "LLM10:UnboundedConsumption",
}


def _canonical_owasp_category(category: str) -> str:
    if not category:
        return category
    if category in OWASP_FORMAL_PT:
        return category
    if category in OWASP_LEGACY_ALIASES:
        return OWASP_LEGACY_ALIASES[category]
    prefix = category.split(":", 1)[0]
    for canonical in OWASP_FORMAL_PT:
        if canonical.startswith(f"{prefix}:"):
            return canonical
    return category


@router.get("/owasp/details")
async def get_owasp_details(
    days: int = 30,
    db: AsyncSession = Depends(get_db),
):
    """Análise rica do OWASP LLM Top-10 com métricas reais por categoria.

    Para cada categoria retorna:
      - descrição formal PT-BR
      - total de eventos no período
      - eventos bloqueados
      - score médio
      - aplicação que mais aciona
      - tendência diária (últimos 7 dias)
      - exemplo de prompt recente (truncado)
      - severidade observada (calculada do score)
    """
    from app.models.db_models import EvaluationLog

    since = datetime.utcnow() - timedelta(days=days)

    logs_q = await db.execute(
        select(EvaluationLog)
        .where(EvaluationLog.created_at >= since)
        .order_by(EvaluationLog.created_at.desc())
    )
    logs = logs_q.scalars().all()

    # Indexa logs por categoria OWASP
    por_categoria: dict = {cat: [] for cat in OWASP_FORMAL_PT.keys()}
    for log in logs:
        for cat in (log.owasp_categories or []):
            canonical = _canonical_owasp_category(cat)
            if canonical in por_categoria:
                por_categoria[canonical].append(log)

    detalhes = []
    hoje = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    for cat, formal in OWASP_FORMAL_PT.items():
        lista = por_categoria.get(cat, [])
        total = len(lista)
        bloqueados = sum(1 for l in lista if l.input_blocked)
        score_medio = round(sum(l.risk_score or 0 for l in lista) / total, 1) if total else 0.0

        # Top app
        contagem_app: dict = {}
        for l in lista:
            contagem_app[l.app_name or "—"] = contagem_app.get(l.app_name or "—", 0) + 1
        top_app, top_app_count = (max(contagem_app.items(), key=lambda x: x[1])
                                  if contagem_app else ("—", 0))

        # Tendência últimos 7 dias
        tendencia = []
        for d in range(7, 0, -1):
            ini = hoje - timedelta(days=d - 1)
            fim = ini + timedelta(days=1)
            cnt = sum(1 for l in lista
                      if l.created_at and ini <= l.created_at < fim)
            tendencia.append({"dia": ini.strftime("%d/%m"), "total": cnt})

        # Exemplos (até 3)
        exemplos = []
        for l in lista[:3]:
            exemplos.append({
                "audit_id": l.audit_id,
                "prompt": (l.prompt or "")[:120] + ("…" if (l.prompt or "") and len(l.prompt) > 120 else ""),
                "risk_score": round(l.risk_score or 0, 1),
                "blocked": bool(l.input_blocked),
                "created_at": l.created_at.isoformat() if l.created_at else None,
                "app_name": l.app_name,
            })

        # Severidade observada (calculada do score médio)
        severidade_obs = (
            "Crítico" if score_medio >= 80
            else "Alto"   if score_medio >= 60
            else "Médio"  if score_medio >= 30
            else "Baixo"  if score_medio > 0
            else "Sem ocorrências"
        )

        detalhes.append({
            "categoria": cat,
            "id": cat.split(":")[0],
            "nome_pt": formal["nome_pt"],
            "descricao_pt": formal["descricao_pt"],
            "controle": formal["controle"],
            "severidade_padrao": formal["severidade_padrao"],
            "modulos_relacionados": formal.get("modulos_relacionados", []),
            "status_cobertura": formal.get("status_cobertura", "Documented"),
            "severidade_observada": severidade_obs,
            "total_eventos": total,
            "total_bloqueados": bloqueados,
            "taxa_bloqueio": round(bloqueados / total * 100, 1) if total else 0.0,
            "score_medio": score_medio,
            "top_app": top_app,
            "top_app_count": top_app_count,
            "tendencia": tendencia,
            "exemplos": exemplos,
            "ultimo_evento": (lista[0].created_at.isoformat() if lista and lista[0].created_at else None),
        })

    # Resumo agregado
    total_eventos = sum(d["total_eventos"] for d in detalhes)
    cobertas = sum(1 for d in detalhes if d["total_eventos"] > 0)
    return {
        "janela_dias": days,
        "total_categorias": len(detalhes),
        "categorias_com_ocorrencia": cobertas,
        "total_eventos": total_eventos,
        "detalhes": detalhes,
    }
