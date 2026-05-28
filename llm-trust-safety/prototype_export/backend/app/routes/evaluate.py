"""
Route: /api/evaluate - Endpoint principal do LLM Trust & Safety Framework
"""
import uuid
import time
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.config import settings
from app.models.schemas import EvaluateRequest, EvaluateResponse
from app.models.db_models import EvaluationLog, Session as SessionModel
from app.services.input_guard import input_guard
from app.services.output_guard import output_guard
from app.services.session_watch import session_watch
from app.services.risk_aggregator import risk_aggregator, data_exposure_mirror
from app.services.llm_service import llm_service

router = APIRouter(prefix="/api/evaluate", tags=["Evaluate"])


@router.post("", response_model=EvaluateResponse)
async def evaluate(
    request: EvaluateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[dict] = Depends(get_current_user),
):
    """
    Endpoint principal do firewall semântico.
    Analisa o prompt, aplica todos os guards e retorna o resultado.
    """
    start_time = time.time()

    # Gerar IDs
    audit_id = str(uuid.uuid4())
    session_id = request.session_id or str(uuid.uuid4())

    # ─── 1. InputGuard ───────────────────────────────────────────
    input_result = input_guard.evaluate(request.prompt)

    # ─── 2. SessionWatch ─────────────────────────────────────────
    session_result = session_watch.evaluate(session_id, request.prompt, input_result)

    # ─── 3. LLM (se configurado e não bloqueado) ─────────────────
    llm_response = None
    output_result = None

    if request.use_llm or settings.LLM_PROVIDER == "mock":
        # Se sessão bloqueada, não enviar ao LLM
        blocked_by_session = session_result.get("state") == "BLOCKED"
        should_block = input_result["blocked"] or blocked_by_session

        llm_response = await llm_service.generate_response(
            prompt=input_result["sanitized_prompt"],
            history=request.history,
            is_blocked=should_block,
            provider=settings.LLM_PROVIDER
        )

        # ─── 4. OutputGuard ───────────────────────────────────────────
        if llm_response:
            output_result_raw = output_guard.evaluate(llm_response)
            output_result = output_result_raw
            llm_response = output_result_raw["sanitized"]

    # ─── 5. Risk Aggregator ───────────────────────────────────────
    risk = risk_aggregator.calculate(
        input_result=input_result,
        output_result=output_result,
        session_result=session_result,
    )

    # ─── 6. Data Exposure Mirror ──────────────────────────────────
    exposure = data_exposure_mirror.analyze(request.history, request.prompt)

    # ─── 7. Coletar categorias OWASP ─────────────────────────────
    owasp_categories = input_result.get("owasp_categories", [])
    if output_result and output_result.get("labels"):
        owasp_categories.append("LLM02:InsecureOutputHandling")

    # ─── 8. Calcular latência ─────────────────────────────────────
    latency_ms = (time.time() - start_time) * 1000

    # ─── 9. Persistir no banco ────────────────────────────────────
    all_labels = list(set(
        input_result.get("labels", []) +
        (output_result.get("labels", []) if output_result else []) +
        session_result.get("flags", [])
    ))

    log = EvaluationLog(
        audit_id=audit_id,
        session_id=session_id,
        user_id=current_user.get("id") if current_user else None,
        prompt=request.prompt[:1000],
        sanitized_prompt=input_result["sanitized_prompt"][:1000],
        input_blocked=input_result["blocked"],
        input_labels=input_result.get("labels", []),
        input_score=input_result.get("score", 0),
        policy_hits=input_result.get("policy_hits", []),
        output_text=(llm_response[:2000] if llm_response else None),
        output_sanitized=(output_result.get("sanitized", "")[:2000] if output_result else None),
        pii_found=(output_result.get("pii_found", []) if output_result else []),
        output_score=(output_result.get("score", 0) if output_result else 0),
        session_flags=session_result.get("flags", []),
        session_score=session_result.get("score", 0),
        risk_score=risk["risk_score"],
        risk_level=risk["risk_level"],
        latency_ms=latency_ms,
        owasp_categories=owasp_categories,
    )
    db.add(log)

    # Atualizar/criar sessão no banco
    existing_session = await db.execute(
        select(SessionModel).where(SessionModel.session_id == session_id)
    )
    existing_session = existing_session.scalar_one_or_none()

    if existing_session:
        existing_session.attack_count = session_result.get("attack_count", 0)
        existing_session.total_interactions = session_result.get("total_interactions", 0)
        existing_session.max_risk_score = session_result.get("max_risk_score", 0)
        existing_session.state = session_result.get("state", "NORMAL")
        existing_session.flags = session_result.get("flags", [])
        existing_session.last_activity = datetime.utcnow()
    else:
        new_session = SessionModel(
            session_id=session_id,
            attack_count=session_result.get("attack_count", 0),
            total_interactions=session_result.get("total_interactions", 0),
            max_risk_score=session_result.get("max_risk_score", 0),
            state=session_result.get("state", "NORMAL"),
            flags=session_result.get("flags", []),
        )
        db.add(new_session)

    await db.commit()

    # ─── 10. Compliance notes ─────────────────────────────────────
    compliance_notes = []
    owasp_map = {
        "LLM01": "Prompt Injection detectado — revisar política de sistema.",
        "LLM02": "Saída insegura do LLM — potencial exfiltração de dados.",
        "LLM06": "Exposição de informação sensível no prompt ou contexto.",
        "LLM07": "Execução de ação não intencional pelo agente LLM.",
        "LLM09": "Dependência excessiva em saída LLM sem validação humana.",
    }
    for cat in owasp_categories:
        prefix = cat.split(":")[0] if ":" in cat else cat[:5]
        note = owasp_map.get(prefix)
        if note:
            compliance_notes.append(note)
    if exposure and exposure.get("privacy_risk_score", 0) > 40:
        compliance_notes.append("LGPD Art. 46 — Dados pessoais expostos; acionar procedimento de minimização.")

    # ─── 11. Montar resposta ──────────────────────────────────────
    from app.models.schemas import InputGuardResult, OutputGuardResult, SessionWatchResult

    return EvaluateResponse(
        audit_id=audit_id,
        session_id=session_id,
        timestamp=datetime.utcnow().isoformat() + "Z",
        risk=int(risk["risk_score"]),
        risk_level=risk["risk_level"],
        labels=all_labels,
        sanitized_prompt=input_result["sanitized_prompt"],
        pii_found=(output_result.get("pii_found", []) if output_result else []),
        policy_hits=input_result.get("policy_hits", []),
        session_flags=session_result.get("flags", []),
        latency_ms=round(latency_ms, 2),
        owasp_categories=owasp_categories,
        compliance_notes=list(set(compliance_notes)),
        llm_response=llm_response,
        input_guard=InputGuardResult(**{
            "blocked": input_result["blocked"],
            "labels": input_result.get("labels", []),
            "score": input_result.get("score", 0),
            "policy_hits": input_result.get("policy_hits", []),
            "sanitized_prompt": input_result["sanitized_prompt"],
            "owasp_categories": input_result.get("owasp_categories", []),
            "justification": input_result.get("justification", ""),
            "policy_hints": input_result.get("policy_hints", []),
        }),
        justification=input_result.get("justification", ""),
        policy_hints=input_result.get("policy_hints", []),
        output_guard=(OutputGuardResult(**{
            "sanitized": output_result.get("sanitized", ""),
            "pii_found": output_result.get("pii_found", []),
            "score": output_result.get("score", 0),
            "labels": output_result.get("labels", []),
        }) if output_result else None),
        session_watch=SessionWatchResult(**{
            "flags": session_result.get("flags", []),
            "score": session_result.get("score", 0),
            "state": session_result.get("state", "NORMAL"),
            "attack_count": session_result.get("attack_count", 0),
            "total_interactions": session_result.get("total_interactions", 0),
        }),
        data_exposure=exposure,
    )
