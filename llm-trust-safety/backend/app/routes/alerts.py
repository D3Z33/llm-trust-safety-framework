"""
Rotas de Alertas - Gerenciamento de alertas de segurança
"""
import uuid
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.db_models import Alert
from app.models.schemas import AlertCreate, AlertUpdate, AlertResponse

router = APIRouter(prefix="/api/alertas", tags=["Alertas"])


@router.get("")
async def listar_alertas(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, le=100),
    severity: Optional[str] = None,
    status: Optional[str] = None,
    category: Optional[str] = None,
    hours: int = Query(default=168),  # 7 dias
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Lista alertas com filtros e paginação"""
    since = datetime.utcnow() - timedelta(hours=hours)
    query = select(Alert).where(Alert.created_at >= since).order_by(desc(Alert.created_at))

    if severity:
        query = query.where(Alert.severity == severity)
    if status:
        query = query.where(Alert.status == status)
    if category:
        query = query.where(Alert.category == category)

    # Total
    count_q = select(func.count()).select_from(
        select(Alert).where(Alert.created_at >= since).subquery()
    )
    total_result = await db.execute(count_q)
    total = total_result.scalar() or 0

    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page)
    result = await db.execute(query)
    alerts = result.scalars().all()

    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page,
        "alertas": [
            {
                "id": a.id,
                "alert_id": a.alert_id,
                "title": a.title,
                "description": a.description,
                "severity": a.severity,
                "category": a.category,
                "status": a.status,
                "risk_score": a.risk_score,
                "audit_id": a.audit_id,
                "session_id": a.session_id,
                "owasp_category": a.owasp_category,
                "metadata": a.alert_metadata or {},
                "created_at": a.created_at.isoformat() if a.created_at else None,
                "acknowledged_at": a.acknowledged_at.isoformat() if a.acknowledged_at else None,
                "resolved_at": a.resolved_at.isoformat() if a.resolved_at else None,
                "resolution_notes": a.resolution_notes,
            }
            for a in alerts
        ]
    }


@router.get("/resumo")
async def resumo_alertas(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Retorna resumo de alertas por severidade e status"""
    since = datetime.utcnow() - timedelta(hours=168)

    # Por severidade
    sevs = ["critical", "high", "medium", "low", "info"]
    by_severity = {}
    for sev in sevs:
        q = await db.execute(
            select(func.count()).select_from(Alert)
            .where(and_(Alert.severity == sev, Alert.created_at >= since))
        )
        by_severity[sev] = q.scalar() or 0

    # Por status
    stats_list = ["open", "acknowledged", "resolved", "false_positive"]
    by_status = {}
    for st in stats_list:
        q = await db.execute(
            select(func.count()).select_from(Alert)
            .where(and_(Alert.status == st, Alert.created_at >= since))
        )
        by_status[st] = q.scalar() or 0

    # Por categoria
    categories = ["attack", "pii", "session", "policy", "system"]
    by_category = {}
    for cat in categories:
        q = await db.execute(
            select(func.count()).select_from(Alert)
            .where(and_(Alert.category == cat, Alert.created_at >= since))
        )
        by_category[cat] = q.scalar() or 0

    # Timeline (últimas 48h)
    timeline = []
    for i in range(48):
        h_start = datetime.utcnow() - timedelta(hours=48 - i)
        h_end = datetime.utcnow() - timedelta(hours=48 - i - 1)
        q = await db.execute(
            select(func.count()).select_from(Alert)
            .where(and_(Alert.created_at >= h_start, Alert.created_at < h_end))
        )
        timeline.append({
            "hora": h_start.strftime("%d/%m %H:00"),
            "total": q.scalar() or 0
        })

    return {
        "por_severidade": by_severity,
        "por_status": by_status,
        "por_categoria": by_category,
        "timeline": timeline,
    }


@router.post("", response_model=AlertResponse, status_code=201)
async def criar_alerta(
    data: AlertCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Cria um novo alerta manualmente"""
    alert = Alert(
        alert_id=str(uuid.uuid4()),
        title=data.title,
        description=data.description,
        severity=data.severity,
        category=data.category,
        source="manual",
        audit_id=data.audit_id,
        session_id=data.session_id,
        owasp_category=data.owasp_category,
        alert_metadata=data.metadata,
        created_by=current_user.get("id"),
    )
    db.add(alert)
    await db.commit()
    await db.refresh(alert)
    return alert


@router.put("/{alert_id}/reconhecer")
async def reconhecer_alerta(
    alert_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Reconhece um alerta (acknowledged)"""
    result = await db.execute(select(Alert).where(Alert.alert_id == alert_id))
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alerta não encontrado")

    alert.status = "acknowledged"
    alert.acknowledged_by = current_user.get("id")
    alert.acknowledged_at = datetime.utcnow()
    await db.commit()
    return {"message": "Alerta reconhecido com sucesso", "status": "acknowledged"}


@router.put("/{alert_id}/resolver")
async def resolver_alerta(
    alert_id: str,
    data: AlertUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Resolve um alerta"""
    result = await db.execute(select(Alert).where(Alert.alert_id == alert_id))
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alerta não encontrado")

    alert.status = "resolved"
    alert.resolved_by = current_user.get("id")
    alert.resolved_at = datetime.utcnow()
    alert.resolution_notes = data.resolution_notes
    await db.commit()
    return {"message": "Alerta resolvido com sucesso", "status": "resolved"}


@router.put("/{alert_id}/falso-positivo")
async def marcar_falso_positivo(
    alert_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Marca alerta como falso positivo"""
    result = await db.execute(select(Alert).where(Alert.alert_id == alert_id))
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alerta não encontrado")

    alert.status = "false_positive"
    alert.resolved_by = current_user.get("id")
    alert.resolved_at = datetime.utcnow()
    await db.commit()
    return {"message": "Marcado como falso positivo", "status": "false_positive"}
