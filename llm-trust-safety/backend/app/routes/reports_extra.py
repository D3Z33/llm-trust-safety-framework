"""
Routes adicionais — métricas formuladas, agregação de exposição
e endpoint manual de seed demonstrativo.

Os endpoints aqui assumem dataset SINTÉTICO/DEMONSTRATIVO. As fórmulas
e agregações são adequadas para protótipo acadêmico e geração de
evidências para o trabalho final, NÃO para SLA de produção.
"""
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc, delete

from app.core.database import get_db, AsyncSessionLocal
from app.core.security import require_role
from app.models.db_models import EvaluationLog, Session as SessionModel, Alert

router = APIRouter(prefix="/api", tags=["Reports & Demo Data"])


# ─── Métricas formuladas ──────────────────────────────────────────────────
@router.get("/reports/metrics", summary="Métricas calculadas com fórmulas explícitas")
async def reports_metrics(
    days: int = Query(default=30, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
):
    """
    Retorna métricas calculadas a partir do dataset demonstrativo.

    **Fórmulas aplicadas:**
    - Attack Catch Rate = (logs com risk >= 60) / (total de logs) × 100
    - False Positive Rate = (benignos com risk >= 30) / (total benignos) × 100
    - Leak Precision = (logs com PII e bloqueio/mascaramento) / (logs com PII detectada) × 100
    - Latency Overhead = latência média do pipeline (sem baseline real)
    - PII Mask Rate = (logs com pii_found não vazio) / (total de logs) × 100
    """
    since = datetime.utcnow() - timedelta(days=days)

    # Total
    total_q = await db.execute(
        select(func.count()).select_from(EvaluationLog)
        .where(EvaluationLog.created_at >= since)
    )
    total = total_q.scalar() or 0

    if total == 0:
        return {
            "window_days": days,
            "data_source": "synthetic_demo",
            "disclaimer": "Métricas calculadas sobre dataset demonstrativo. Não representam tráfego real de produção.",
            "metrics": {},
        }

    # Atacantes (risk >= 60)
    atk_q = await db.execute(
        select(func.count()).select_from(EvaluationLog)
        .where(and_(EvaluationLog.created_at >= since, EvaluationLog.risk_score >= 60))
    )
    atk = atk_q.scalar() or 0

    # Bloqueados
    blk_q = await db.execute(
        select(func.count()).select_from(EvaluationLog)
        .where(and_(EvaluationLog.created_at >= since, EvaluationLog.input_blocked == True))
    )
    blocked = blk_q.scalar() or 0

    # Benignos (risk < 30) e benignos marcados (risk 30-59 sem bloqueio = falso positivo)
    benigno_q = await db.execute(
        select(func.count()).select_from(EvaluationLog)
        .where(and_(EvaluationLog.created_at >= since, EvaluationLog.risk_score < 30))
    )
    benignos = benigno_q.scalar() or 0

    fp_q = await db.execute(
        select(func.count()).select_from(EvaluationLog)
        .where(and_(
            EvaluationLog.created_at >= since,
            EvaluationLog.risk_score >= 30,
            EvaluationLog.risk_score < 60,
            EvaluationLog.input_blocked == False,
        ))
    )
    falsos_positivos = fp_q.scalar() or 0

    # Logs com PII
    pii_logs_q = await db.execute(
        select(EvaluationLog.pii_found, EvaluationLog.input_blocked, EvaluationLog.output_score)
        .select_from(EvaluationLog)
        .where(EvaluationLog.created_at >= since)
    )
    rows = pii_logs_q.fetchall()
    logs_with_pii = sum(1 for r in rows if r[0])
    pii_count_total = sum(len(r[0] or []) for r in rows)
    pii_handled = sum(1 for r in rows if r[0] and (r[1] or (r[2] or 0) > 30))

    # Latência
    lat_q = await db.execute(
        select(
            func.avg(EvaluationLog.latency_ms),
            func.min(EvaluationLog.latency_ms),
            func.max(EvaluationLog.latency_ms),
        ).select_from(EvaluationLog)
        .where(EvaluationLog.created_at >= since)
    )
    lat = lat_q.fetchone()

    # Volume diário
    daily = []
    for d in range(days):
        d_start = (datetime.utcnow() - timedelta(days=days - d)).replace(hour=0, minute=0, second=0, microsecond=0)
        d_end = d_start + timedelta(days=1)
        d_q = await db.execute(
            select(func.count(), func.avg(EvaluationLog.risk_score))
            .select_from(EvaluationLog)
            .where(and_(EvaluationLog.created_at >= d_start, EvaluationLog.created_at < d_end))
        )
        cnt, avg_r = d_q.fetchone()
        daily.append({
            "date": d_start.strftime("%Y-%m-%d"),
            "count": cnt or 0,
            "avg_risk": round(avg_r or 0, 1),
        })

    # Distribuição por risco
    levels_q = await db.execute(
        select(EvaluationLog.risk_level, func.count())
        .select_from(EvaluationLog)
        .where(EvaluationLog.created_at >= since)
        .group_by(EvaluationLog.risk_level)
    )
    by_level = {row[0]: row[1] for row in levels_q.fetchall()}

    # Top categorias de ataque
    labels_q = await db.execute(
        select(EvaluationLog.input_labels)
        .select_from(EvaluationLog)
        .where(and_(EvaluationLog.created_at >= since, EvaluationLog.risk_score >= 60))
    )
    label_counts = {}
    for row in labels_q.fetchall():
        for lab in (row[0] or []):
            label_counts[lab] = label_counts.get(lab, 0) + 1
    top_categories = sorted(
        [{"category": k, "count": v} for k, v in label_counts.items()],
        key=lambda x: x["count"], reverse=True
    )[:10]

    # Cálculo final
    catch_rate = round(atk / total * 100, 2) if total else 0
    fpr = round(falsos_positivos / benignos * 100, 2) if benignos else 0
    leak_precision = round(pii_handled / logs_with_pii * 100, 2) if logs_with_pii else 0
    pii_mask_rate = round(logs_with_pii / total * 100, 2) if total else 0

    return {
        "window_days": days,
        "data_source": "synthetic_demo",
        "disclaimer": (
            "Métricas calculadas sobre dataset DEMONSTRATIVO/SINTÉTICO gerado pelo "
            "seeder. Não representam tráfego real de produção. Ver "
            "docs/demo_dataset_description.md."
        ),
        "totals": {
            "total_evaluations": total,
            "total_attacks_detected": atk,
            "total_blocked": blocked,
            "total_benign": benignos,
            "logs_with_pii": logs_with_pii,
            "pii_entities_found": pii_count_total,
            "false_positives_estimated": falsos_positivos,
        },
        "rates": {
            "attack_catch_rate_pct": catch_rate,
            "false_positive_rate_pct": fpr,
            "leak_precision_pct": leak_precision,
            "pii_mask_rate_pct": pii_mask_rate,
            "block_rate_pct": round(blocked / total * 100, 2),
        },
        "latency": {
            "avg_ms": round(lat[0] or 0, 2),
            "min_ms": round(lat[1] or 0, 2),
            "max_ms": round(lat[2] or 0, 2),
            "note": (
                "Sem baseline sem-pipeline implementado. Para Latency Overhead "
                "real, comparar com chamada direta ao LLM em ambiente isolado."
            ),
        },
        "distribution_by_risk_level": by_level,
        "top_attack_categories": top_categories,
        "daily_volume": daily,
        "formulas": {
            "attack_catch_rate": "logs_with_risk_>=_60 / total_logs * 100",
            "false_positive_rate": "benigns_marked_30_to_59_without_block / total_benigns * 100",
            "leak_precision": "logs_with_pii_handled / logs_with_pii_detected * 100",
            "pii_mask_rate": "logs_with_pii_found / total_logs * 100",
        },
    }


# ─── Agregação de Data Exposure Mirror ────────────────────────────────────
@router.get("/reports/exposure", summary="Agregado de exposição de dados")
async def reports_exposure(
    days: int = Query(default=30, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
):
    """
    Retorna agregação dos dados detectados pelo Data Exposure Mirror
    nas sessões demonstrativas.
    """
    since = datetime.utcnow() - timedelta(days=days)

    # Logs com pii_found não vazio
    q = await db.execute(
        select(
            EvaluationLog.session_id,
            EvaluationLog.pii_found,
            EvaluationLog.input_score,
            EvaluationLog.created_at,
            EvaluationLog.app_name,
        )
        .select_from(EvaluationLog)
        .where(and_(EvaluationLog.created_at >= since, EvaluationLog.pii_found != None))
        .order_by(desc(EvaluationLog.created_at))
    )
    rows = q.fetchall()

    by_pii_type = {}
    by_session = {}
    by_exposure_tag = {}
    total_pii_entities = 0

    for sid, pii_list, risk, created, app in rows:
        for pii in (pii_list or []):
            t = pii.get("entity_type", "UNKNOWN")
            by_pii_type[t] = by_pii_type.get(t, 0) + 1
            total_pii_entities += 1
            for tag in pii.get("exposure_tags", []) or []:
                by_exposure_tag[tag] = by_exposure_tag.get(tag, 0) + 1

        if sid not in by_session:
            by_session[sid] = {
                "session_id": sid,
                "pii_count": 0,
                "max_risk": 0,
                "app_name": app,
                "first_event": created.isoformat() if created else None,
            }
        by_session[sid]["pii_count"] += len(pii_list or [])
        by_session[sid]["max_risk"] = max(by_session[sid]["max_risk"], risk or 0)

    top_sessions = sorted(
        by_session.values(),
        key=lambda x: (x["pii_count"], x["max_risk"]),
        reverse=True,
    )[:10]

    top_tags = sorted(
        [{"tag": k, "count": v} for k, v in by_exposure_tag.items()],
        key=lambda x: x["count"], reverse=True,
    )[:15]

    # Sessões com flag DATA_EXPOSURE_PROGRESSIVE
    progressive_q = await db.execute(
        select(SessionModel)
        .where(SessionModel.flags.contains(["DATA_EXPOSURE_PROGRESSIVE"]) if False else True)
    )
    # SQLite JSON contains workaround: filter in Python
    all_sess = progressive_q.scalars().all()
    progressive_sessions = [
        {
            "session_id": s.session_id,
            "app_name": s.app_name,
            "max_risk_score": s.max_risk_score,
            "avg_risk_score": s.avg_risk_score,
            "total_interactions": s.total_interactions,
            "flags": s.flags or [],
            "started_at": s.started_at.isoformat() if s.started_at else None,
        }
        for s in all_sess
        if s.flags and "DATA_EXPOSURE_PROGRESSIVE" in (s.flags or [])
    ]

    return {
        "window_days": days,
        "data_source": "synthetic_demo",
        "disclaimer": (
            "Agregação calculada sobre sessões DEMONSTRATIVAS criadas pelo "
            "seeder do Data Exposure Mirror. Os identificadores PII (CPF, "
            "email, cartão etc.) presentes nos exemplos são fictícios."
        ),
        "summary": {
            "total_pii_entities": total_pii_entities,
            "unique_sessions_with_pii": len(by_session),
            "progressive_exposure_sessions": len(progressive_sessions),
            "distinct_pii_types": len(by_pii_type),
            "distinct_exposure_categories": len(by_exposure_tag),
        },
        "by_pii_type": [{"type": k, "count": v} for k, v in sorted(by_pii_type.items(), key=lambda x: x[1], reverse=True)],
        "top_exposure_categories": top_tags,
        "top_exposed_sessions": top_sessions,
        "progressive_sessions": progressive_sessions,
    }


# ─── Reset/seed manual de dados demo ──────────────────────────────────────
class SeedDemoRequest(BaseModel):
    days: int = Field(default=30, ge=1, le=90, description="Janela em dias para o histórico sintético")
    wipe_existing: bool = Field(default=False, description="Se true, apaga TODOS os logs/sessões/alertas anteriores antes de gerar")
    confirm: bool = Field(default=False, description="Confirmação obrigatória quando wipe_existing=true")


@router.post(
    "/seed/demo-data",
    summary="Gera/regenera dataset demonstrativo (admin only)",
    dependencies=[Depends(require_role(["admin"]))],
)
async def seed_demo_data(payload: SeedDemoRequest):
    """
    Endpoint administrativo para popular o sistema com **dados sintéticos**
    distribuídos ao longo de `days` dias.

    - `wipe_existing=true` requer `confirm=true` para evitar destruição acidental.
    - Sem wipe, apenas adiciona registros (potencialmente duplicando volumes).
    - Todos os registros recebem `source_type="synthetic_demo"`.
    """
    if payload.wipe_existing and not payload.confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="wipe_existing=true requer confirm=true para prosseguir.",
        )

    # Importa lazy para evitar import circular com main.py
    from app.main import _seed_demo_data

    async with AsyncSessionLocal() as db:
        if payload.wipe_existing:
            # Apaga apenas registros marcados como demo (preserva eventuais logs reais)
            await db.execute(delete(EvaluationLog).where(EvaluationLog.source_type == "synthetic_demo"))
            await db.execute(delete(SessionModel).where(SessionModel.source_type == "synthetic_demo"))
            # Apaga TODOS os alertas (não há flag de origem)
            await db.execute(delete(Alert))
            await db.commit()

        await _seed_demo_data(db, days=payload.days)
        await db.commit()

    # Retornar contagens pós-seed
    async with AsyncSessionLocal() as db2:
        c = (await db2.execute(
            select(func.count()).select_from(EvaluationLog)
            .where(EvaluationLog.source_type == "synthetic_demo")
        )).scalar() or 0
        s = (await db2.execute(
            select(func.count()).select_from(SessionModel)
            .where(SessionModel.source_type == "synthetic_demo")
        )).scalar() or 0
        a = (await db2.execute(select(func.count()).select_from(Alert))).scalar() or 0

    return {
        "status": "ok",
        "data_source": "synthetic_demo",
        "window_days": payload.days,
        "wiped_existing": payload.wipe_existing,
        "totals_after_seed": {
            "evaluation_logs_demo": c,
            "sessions_demo": s,
            "alerts_total": a,
        },
        "disclaimer": (
            "Dataset gerado para fins demonstrativos e validação acadêmica. "
            "NÃO usar em ambiente de produção real."
        ),
    }
