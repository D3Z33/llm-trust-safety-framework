"""
Rotas de Analytics Avançado
"""
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.db_models import EvaluationLog, Session as SessionModel, Alert

router = APIRouter(prefix="/api/analytics", tags=["Analytics Avançado"])


@router.get("/visao-geral")
async def visao_geral_analytics(
    days: int = Query(default=30),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Visão geral de analytics do período"""
    since = datetime.utcnow() - timedelta(days=days)
    prev_since = since - timedelta(days=days)

    async def count_with_filter(filter_clause=None):
        q = select(func.count()).select_from(EvaluationLog).where(EvaluationLog.created_at >= since)
        if filter_clause is not None:
            q = q.where(filter_clause)
        r = await db.execute(q)
        return r.scalar() or 0

    async def prev_count(filter_clause=None):
        q = select(func.count()).select_from(EvaluationLog).where(
            and_(EvaluationLog.created_at >= prev_since, EvaluationLog.created_at < since)
        )
        if filter_clause is not None:
            q = q.where(filter_clause)
        r = await db.execute(q)
        return r.scalar() or 0

    total = await count_with_filter()
    prev_total = await prev_count()
    blocked = await count_with_filter(EvaluationLog.input_blocked == True)
    prev_blocked = await prev_count(EvaluationLog.input_blocked == True)
    critical = await count_with_filter(EvaluationLog.risk_level == "CRITICAL")
    high = await count_with_filter(EvaluationLog.risk_level == "HIGH")

    # Média de risco
    avg_q = await db.execute(
        select(func.avg(EvaluationLog.risk_score))
        .where(EvaluationLog.created_at >= since)
    )
    avg_risk = avg_q.scalar() or 0

    prev_avg_q = await db.execute(
        select(func.avg(EvaluationLog.risk_score))
        .where(and_(EvaluationLog.created_at >= prev_since, EvaluationLog.created_at < since))
    )
    prev_avg_risk = prev_avg_q.scalar() or 0

    # Latência média
    lat_q = await db.execute(
        select(func.avg(EvaluationLog.latency_ms)).where(EvaluationLog.created_at >= since)
    )
    avg_latency = lat_q.scalar() or 0

    def delta_pct(current, previous):
        if previous == 0:
            return 100.0 if current > 0 else 0.0
        return round((current - previous) / previous * 100, 1)

    return {
        "periodo_dias": days,
        "metricas": {
            "total_avaliacoes": {"valor": total, "delta_pct": delta_pct(total, prev_total)},
            "total_bloqueados": {"valor": blocked, "delta_pct": delta_pct(blocked, prev_blocked)},
            "taxa_bloqueio": {"valor": round(blocked / total * 100, 1) if total else 0},
            "eventos_criticos": {"valor": critical},
            "eventos_alto_risco": {"valor": high},
            "risco_medio": {"valor": round(avg_risk, 1), "delta_pct": delta_pct(avg_risk, prev_avg_risk)},
            "latencia_media_ms": {"valor": round(avg_latency, 1)},
        }
    }


@router.get("/heatmap")
async def heatmap_ataques(
    days: int = Query(default=7),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Heatmap de ataques por hora do dia e dia da semana"""
    since = datetime.utcnow() - timedelta(days=days)

    result = await db.execute(
        select(EvaluationLog.created_at, EvaluationLog.risk_score)
        .where(and_(EvaluationLog.created_at >= since, EvaluationLog.risk_score >= 60))
    )

    # 7 dias x 24 horas
    heatmap = [[0] * 24 for _ in range(7)]
    for row in result.fetchall():
        if row[0]:
            dow = row[0].weekday()  # 0=segunda, 6=domingo
            hour = row[0].hour
            heatmap[dow][hour] += 1

    dias = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]

    return {
        "heatmap": [
            {
                "dia": dias[i],
                "dia_idx": i,
                "dados": [{"hora": h, "count": heatmap[i][h]} for h in range(24)]
            }
            for i in range(7)
        ]
    }


@router.get("/tendencias")
async def tendencias(
    days: int = Query(default=30),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Tendências de ataques e risco por dia"""
    since = datetime.utcnow() - timedelta(days=days)

    data_points = []
    for i in range(days):
        day_start = datetime.utcnow() - timedelta(days=days - i)
        day_end = datetime.utcnow() - timedelta(days=days - i - 1)

        total_q = await db.execute(
            select(func.count()).select_from(EvaluationLog)
            .where(and_(EvaluationLog.created_at >= day_start, EvaluationLog.created_at < day_end))
        )
        total = total_q.scalar() or 0

        attack_q = await db.execute(
            select(func.count()).select_from(EvaluationLog)
            .where(and_(
                EvaluationLog.created_at >= day_start,
                EvaluationLog.created_at < day_end,
                EvaluationLog.risk_score >= 60
            ))
        )
        attacks = attack_q.scalar() or 0

        avg_q = await db.execute(
            select(func.avg(EvaluationLog.risk_score))
            .where(and_(EvaluationLog.created_at >= day_start, EvaluationLog.created_at < day_end))
        )
        avg_risk = avg_q.scalar() or 0

        data_points.append({
            "data": day_start.strftime("%d/%m"),
            "total": total,
            "ataques": attacks,
            "risco_medio": round(avg_risk, 1),
            "taxa_ataque": round(attacks / total * 100, 1) if total > 0 else 0,
        })

    return {"tendencias": data_points, "periodo_dias": days}


@router.get("/top-sessoes-risco")
async def top_sessoes_risco(
    limit: int = Query(default=10),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Top sessões com maior risco"""
    result = await db.execute(
        select(SessionModel)
        .where(SessionModel.state != "NORMAL")
        .order_by(desc(SessionModel.max_risk_score))
        .limit(limit)
    )
    sessions = result.scalars().all()
    return [
        {
            "session_id": s.session_id,
            "state": s.state,
            "attack_count": s.attack_count,
            "total_interactions": s.total_interactions,
            "max_risk_score": s.max_risk_score,
            "avg_risk_score": s.avg_risk_score,
            "flags": s.flags or [],
            "started_at": s.started_at.isoformat() if s.started_at else None,
            "last_activity": s.last_activity.isoformat() if s.last_activity else None,
        }
        for s in sessions
    ]


@router.get("/latencia")
async def analise_latencia(
    days: int = Query(default=7),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Análise detalhada de latência do sistema"""
    since = datetime.utcnow() - timedelta(days=days)

    # Percentis de latência
    result = await db.execute(
        select(EvaluationLog.latency_ms)
        .where(EvaluationLog.created_at >= since)
        .order_by(EvaluationLog.latency_ms)
    )
    latencies = [row[0] for row in result.fetchall() if row[0]]

    if not latencies:
        return {"latencias": [], "percentis": {}}

    def percentile(data, p):
        idx = int(len(data) * p / 100)
        return data[min(idx, len(data) - 1)]

    return {
        "percentis": {
            "p50": round(percentile(latencies, 50), 2),
            "p75": round(percentile(latencies, 75), 2),
            "p90": round(percentile(latencies, 90), 2),
            "p95": round(percentile(latencies, 95), 2),
            "p99": round(percentile(latencies, 99), 2),
            "max": round(max(latencies), 2),
            "min": round(min(latencies), 2),
            "media": round(sum(latencies) / len(latencies), 2),
        },
        "total_amostras": len(latencies),
        "dentro_sla_200ms": sum(1 for l in latencies if l <= 200),
        "percentual_sla": round(sum(1 for l in latencies if l <= 200) / len(latencies) * 100, 1),
    }


@router.get("/exposicao-dados")
async def analise_exposicao_dados(
    days: int = Query(default=30),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Análise de exposição de dados e PII"""
    since = datetime.utcnow() - timedelta(days=days)

    result = await db.execute(
        select(EvaluationLog.pii_found, EvaluationLog.created_at)
        .where(and_(EvaluationLog.created_at >= since))
    )

    pii_by_type = {}
    pii_timeline = {}  # data -> count
    total_pii = 0

    for row in result.fetchall():
        pii_list = row[0] or []
        date_key = row[1].strftime("%d/%m") if row[1] else "?"

        for pii in pii_list:
            ptype = pii.get("entity_type", "UNKNOWN")
            pii_by_type[ptype] = pii_by_type.get(ptype, 0) + 1
            pii_timeline[date_key] = pii_timeline.get(date_key, 0) + 1
            total_pii += 1

    TIPO_DESCRICOES = {
        "CPF": "Cadastro de Pessoa Física",
        "CNPJ": "Cadastro Nacional de Pessoas Jurídicas",
        "EMAIL": "Endereço de e-mail",
        "PHONE": "Número de telefone",
        "CREDIT_CARD": "Cartão de crédito",
        "RG": "Registro Geral",
        "CEP": "Código de Endereço Postal",
        "PASSPORT": "Número de passaporte",
        "IP_ADDRESS": "Endereço IP",
        "DATE_OF_BIRTH": "Data de nascimento",
    }

    return {
        "total_pii_detectado": total_pii,
        "por_tipo": [
            {
                "tipo": k,
                "descricao": TIPO_DESCRICOES.get(k, k),
                "contagem": v,
                "percentual": round(v / total_pii * 100, 1) if total_pii else 0,
            }
            for k, v in sorted(pii_by_type.items(), key=lambda x: x[1], reverse=True)
        ],
        "timeline": [
            {"data": k, "contagem": v}
            for k, v in sorted(pii_timeline.items())
        ],
        "periodo_dias": days,
    }
