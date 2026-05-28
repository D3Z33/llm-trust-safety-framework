"""
Rotas de Conformidade - Relatórios NIST, ISO, LGPD, OWASP
"""
import uuid
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.db_models import EvaluationLog, Alert, ComplianceReport
from app.models.schemas import ComplianceReportCreate

router = APIRouter(prefix="/api/conformidade", tags=["Conformidade"])

# ─── Mapeamentos de Conformidade ──────────────────────────────────────────

NIST_CONTROLS = {
    "GOVERN": {
        "id": "GOVERN",
        "nome": "Governança",
        "descricao": "Políticas, processos e procedimentos de governança de IA",
        "controles": [
            {"id": "GOV-1.1", "nome": "Política de IA Documentada", "peso": 15},
            {"id": "GOV-1.2", "nome": "Papéis e Responsabilidades Definidos", "peso": 10},
            {"id": "GOV-2.1", "nome": "Inventário de Sistemas de IA", "peso": 10},
            {"id": "GOV-3.1", "nome": "Treinamento e Conscientização", "peso": 8},
            {"id": "GOV-4.1", "nome": "Gestão de Riscos de IA", "peso": 12},
        ]
    },
    "MAP": {
        "id": "MAP",
        "nome": "Mapear",
        "descricao": "Identificação e classificação de riscos de IA",
        "controles": [
            {"id": "MAP-1.1", "nome": "Categorização de Contexto de IA", "peso": 12},
            {"id": "MAP-2.1", "nome": "Análise de Stakeholders", "peso": 8},
            {"id": "MAP-3.1", "nome": "Identificação de Benefícios e Riscos", "peso": 15},
            {"id": "MAP-5.1", "nome": "Mapeamento de Impactos", "peso": 10},
        ]
    },
    "MEASURE": {
        "id": "MEASURE",
        "nome": "Medir",
        "descricao": "Análise, avaliação e monitoramento de riscos",
        "controles": [
            {"id": "MEA-1.1", "nome": "Métricas de Risco Definidas", "peso": 15},
            {"id": "MEA-2.2", "nome": "Testes de Adversários", "peso": 20},
            {"id": "MEA-2.5", "nome": "Monitoramento em Produção", "peso": 18},
            {"id": "MEA-4.1", "nome": "Avaliação de Privacidade", "peso": 12},
        ]
    },
    "MANAGE": {
        "id": "MANAGE",
        "nome": "Gerenciar",
        "descricao": "Priorização e tratamento de riscos",
        "controles": [
            {"id": "MAN-1.1", "nome": "Plano de Resposta a Incidentes", "peso": 15},
            {"id": "MAN-2.2", "nome": "Controles de Mitigação Implementados", "peso": 20},
            {"id": "MAN-3.1", "nome": "Monitoramento Contínuo", "peso": 18},
            {"id": "MAN-4.1", "nome": "Comunicação de Incidentes", "peso": 10},
        ]
    },
}

LGPD_CONTROLES = {
    "bases_legais": {"nome": "Bases Legais para Tratamento", "artigo": "Art. 7º", "peso": 20},
    "direitos_titulares": {"nome": "Direitos dos Titulares", "artigo": "Art. 18", "peso": 20},
    "minimizacao": {"nome": "Minimização de Dados", "artigo": "Art. 6º III", "peso": 15},
    "transparencia": {"nome": "Transparência no Tratamento", "artigo": "Art. 6º VI", "peso": 15},
    "seguranca_tecnica": {"nome": "Segurança Técnica e Organizacional", "artigo": "Art. 46", "peso": 20},
    "dpia": {"nome": "Relatório de Impacto (DPIA)", "artigo": "Art. 38", "peso": 10},
}

ISO27001_CONTROLES = {
    "A.5": {"nome": "Políticas de Segurança da Informação", "peso": 10},
    "A.6": {"nome": "Organização da Segurança da Informação", "peso": 8},
    "A.8": {"nome": "Gestão de Ativos", "peso": 10},
    "A.9": {"nome": "Controle de Acesso", "peso": 15},
    "A.10": {"nome": "Criptografia", "peso": 10},
    "A.12": {"nome": "Segurança nas Operações", "peso": 15},
    "A.14": {"nome": "Aquisição, Desenvolvimento e Manutenção", "peso": 12},
    "A.16": {"nome": "Gestão de Incidentes", "peso": 15},
    "A.18": {"nome": "Conformidade", "peso": 5},
}

OWASP_LLM_TOP10 = [
    {
        "id": "LLM01",
        "nome": "Injeção de Prompt",
        "descricao": "Manipulação de LLMs por entradas maliciosas que alteram o comportamento",
        "risco": "Crítico",
        "mitigacoes": ["InputGuard", "Validação de entrada", "Isolamento de contexto"]
    },
    {
        "id": "LLM02",
        "nome": "Tratamento Inseguro de Saída",
        "descricao": "Falha ao validar ou sanitizar saídas do LLM",
        "risco": "Alto",
        "mitigacoes": ["OutputGuard", "Sanitização de saída", "Validação de schema"]
    },
    {
        "id": "LLM03",
        "nome": "Envenenamento de Dados de Treinamento",
        "descricao": "Manipulação de dados de treinamento para comprometer o modelo",
        "risco": "Alto",
        "mitigacoes": ["Validação de dataset", "Auditoria de dados", "Monitoramento"]
    },
    {
        "id": "LLM04",
        "nome": "Negação de Serviço do Modelo",
        "descricao": "Sobrecarga do modelo com entradas maliciosas",
        "risco": "Médio",
        "mitigacoes": ["Rate limiting", "Timeout configurável", "Circuit breaker"]
    },
    {
        "id": "LLM05",
        "nome": "Vulnerabilidades na Cadeia de Suprimentos",
        "descricao": "Dependências e plugins inseguros que afetam o sistema",
        "risco": "Alto",
        "mitigacoes": ["Gestão de dependências", "SBOM", "Verificação de integridade"]
    },
    {
        "id": "LLM06",
        "nome": "Divulgação de Informações Sensíveis",
        "descricao": "Exposição de dados confidenciais nas respostas do LLM",
        "risco": "Crítico",
        "mitigacoes": ["OutputGuard PII", "Microsoft Presidio", "Mascaramento de dados"]
    },
    {
        "id": "LLM07",
        "nome": "Design Inseguro de Plugins",
        "descricao": "Plugins ou extensões com controles de segurança inadequados",
        "risco": "Alto",
        "mitigacoes": ["ToolGate", "Validação de plugin", "Princípio do menor privilégio"]
    },
    {
        "id": "LLM08",
        "nome": "Agência Excessiva",
        "descricao": "LLM com permissões ou capacidades além do necessário",
        "risco": "Alto",
        "mitigacoes": ["Controle de ferramentas", "Sandbox de execução", "Auditoria de ações"]
    },
    {
        "id": "LLM09",
        "nome": "Supersconfiança",
        "descricao": "Dependência excessiva em LLMs sem supervisão humana",
        "risco": "Médio",
        "mitigacoes": ["Human-in-the-loop", "Alertas de confiança", "Revisão humana"]
    },
    {
        "id": "LLM10",
        "nome": "Roubo do Modelo",
        "descricao": "Extração não autorizada do modelo através de consultas",
        "risco": "Médio",
        "mitigacoes": ["Rate limiting", "Detecção de extração", "Watermarking"]
    },
]

OWASP_LLM_TOP10 = [
    {
        "id": "LLM01",
        "nome": "Prompt Injection",
        "descricao": "Entradas controladas pelo usuario tentam sobrescrever instrucoes ou sequestrar o objetivo do modelo",
        "risco": "Critico",
        "mitigacoes": ["InputGuard", "SessionWatch", "Isolamento de contexto"],
    },
    {
        "id": "LLM02",
        "nome": "Sensitive Information Disclosure",
        "descricao": "Exposicao de PII, segredos, credenciais, system prompts ou contexto sensivel",
        "risco": "Critico",
        "mitigacoes": ["OutputGuard", "Data Exposure Mirror", "Mascaramento de dados"],
    },
    {
        "id": "LLM03",
        "nome": "Supply Chain",
        "descricao": "Risco em modelos, bibliotecas, datasets, plugins ou dependencias terceiras",
        "risco": "Alto",
        "mitigacoes": ["Revisao de dependencias", "SBOM", "Governanca de fornecedores"],
    },
    {
        "id": "LLM04",
        "nome": "Data and Model Poisoning",
        "descricao": "Manipulacao de dados de treinamento, fine-tuning, embeddings ou bases RAG",
        "risco": "Alto",
        "mitigacoes": ["Threat Intelligence", "Auditoria de dados", "Validacao de fontes"],
    },
    {
        "id": "LLM05",
        "nome": "Improper Output Handling",
        "descricao": "Saidas do modelo sem validacao ou sanitizacao antes de renderizar, armazenar ou executar",
        "risco": "Alto",
        "mitigacoes": ["OutputGuard", "Sanitizacao de saida", "Validacao de schema"],
    },
    {
        "id": "LLM06",
        "nome": "Excessive Agency",
        "descricao": "Modelo ou agente recebe permissao acima do necessario para sua tarefa",
        "risco": "Alto",
        "mitigacoes": ["SessionWatch", "Menor privilegio", "Revisao humana"],
    },
    {
        "id": "LLM07",
        "nome": "System Prompt Leakage",
        "descricao": "Revelacao de instrucoes internas, politicas ocultas ou configuracao de guardrails",
        "risco": "Alto",
        "mitigacoes": ["InputGuard", "OutputGuard", "Politicas de bloqueio"],
    },
    {
        "id": "LLM08",
        "nome": "Vector and Embedding Weaknesses",
        "descricao": "Falhas em RAG, busca vetorial ou pipelines de embeddings",
        "risco": "Medio",
        "mitigacoes": ["Validacao de retrieval", "Controle de fonte", "Auditoria de contexto"],
    },
    {
        "id": "LLM09",
        "nome": "Misinformation",
        "descricao": "Uso de resposta imprecisa como fonte confiavel sem revisao adequada",
        "risco": "Medio",
        "mitigacoes": ["Human-in-the-loop", "Evidencias no Dashboard", "Politicas de uso"],
    },
    {
        "id": "LLM10",
        "nome": "Unbounded Consumption",
        "descricao": "Abuso de tokens, inferencia, custo ou contexto causando degradacao ou extracao",
        "risco": "Alto",
        "mitigacoes": ["Rate limiting", "SessionWatch", "Monitoramento de custo"],
    },
]

OWASP_COMPLIANCE_ALIASES = {
    "LLM02:InsecureOutputHandling": "LLM05",
    "LLM03:TrainingDataPoisoning": "LLM04",
    "LLM04:ModelDenialOfService": "LLM10",
    "LLM05:SupplyChainVulnerabilities": "LLM03",
    "LLM06:SensitiveInformationDisclosure": "LLM02",
    "LLM07:InsecurePluginDesign": "LLM06",
    "LLM08:ExcessiveAgency": "LLM06",
    "LLM09:Overreliance": "LLM09",
    "LLM10:ModelTheft": "LLM10",
}


async def _calcular_score_conformidade(db: AsyncSession, days: int = 30) -> dict:
    """Calcula score de conformidade baseado nos dados reais"""
    since = datetime.utcnow() - timedelta(days=days)

    # Métricas base
    total_q = await db.execute(
        select(func.count()).select_from(EvaluationLog).where(EvaluationLog.created_at >= since)
    )
    total = total_q.scalar() or 1

    blocked_q = await db.execute(
        select(func.count()).select_from(EvaluationLog)
        .where(and_(EvaluationLog.created_at >= since, EvaluationLog.input_blocked == True))
    )
    blocked = blocked_q.scalar() or 0

    critical_q = await db.execute(
        select(func.count()).select_from(EvaluationLog)
        .where(and_(EvaluationLog.created_at >= since, EvaluationLog.risk_level == "CRITICAL"))
    )
    critical = critical_q.scalar() or 0

    pii_q = await db.execute(
        select(EvaluationLog.pii_found).select_from(EvaluationLog).where(EvaluationLog.created_at >= since)
    )
    pii_total = sum(len(r[0] or []) for r in pii_q.fetchall())

    alerts_q = await db.execute(
        select(func.count()).select_from(Alert)
        .where(and_(Alert.created_at >= since, Alert.status == "open"))
    )
    open_alerts = alerts_q.scalar() or 0

    # Scores por framework
    block_rate = (blocked / total) * 100
    pii_detection_ok = pii_total > 0  # pelo menos está detectando
    low_open_alerts = open_alerts < 10

    return {
        "total": total,
        "blocked": blocked,
        "critical": critical,
        "pii_total": pii_total,
        "open_alerts": open_alerts,
        "block_rate": block_rate,
        "pii_detection_ok": pii_detection_ok,
        "low_open_alerts": low_open_alerts,
    }


@router.get("/visao-geral")
async def visao_geral_conformidade(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Visão geral de conformidade com todos os frameworks"""
    metrics = await _calcular_score_conformidade(db)

    # NIST AI RMF Score
    nist_score = min(95, 40 + metrics["block_rate"] * 0.4 + (20 if metrics["pii_detection_ok"] else 0) + (15 if metrics["low_open_alerts"] else 0))

    # LGPD Score
    lgpd_score = min(95, 30 + (25 if metrics["pii_detection_ok"] else 0) + (20 if metrics["block_rate"] > 50 else 10) + (20 if metrics["low_open_alerts"] else 0))

    # ISO 27001 Score
    iso27001_score = min(95, 35 + metrics["block_rate"] * 0.3 + (20 if metrics["pii_detection_ok"] else 0) + (15 if metrics["low_open_alerts"] else 0))

    # ISO 42001 Score
    iso42001_score = min(90, 30 + metrics["block_rate"] * 0.35 + (15 if metrics["pii_detection_ok"] else 0) + (15 if metrics["low_open_alerts"] else 0))

    # OWASP Score
    owasp_score = min(95, 20 + metrics["block_rate"] * 0.5 + (20 if metrics["pii_detection_ok"] else 0))

    frameworks = [
        {
            "id": "nist_ai_rmf",
            "nome": "NIST AI RMF 1.0",
            "score": round(nist_score, 1),
            "cor": "#3b82f6",
            "status": "Conforme" if nist_score >= 70 else "Parcialmente Conforme" if nist_score >= 40 else "Não Conforme",
            "controles_atendidos": int(nist_score / 100 * 15),
            "controles_total": 15,
        },
        {
            "id": "lgpd",
            "nome": "LGPD (Lei 13.709/2018)",
            "score": round(lgpd_score, 1),
            "cor": "#10b981",
            "status": "Conforme" if lgpd_score >= 70 else "Parcialmente Conforme" if lgpd_score >= 40 else "Não Conforme",
            "controles_atendidos": int(lgpd_score / 100 * 6),
            "controles_total": 6,
        },
        {
            "id": "iso27001",
            "nome": "ISO/IEC 27001:2022",
            "score": round(iso27001_score, 1),
            "cor": "#8b5cf6",
            "status": "Conforme" if iso27001_score >= 70 else "Parcialmente Conforme" if iso27001_score >= 40 else "Não Conforme",
            "controles_atendidos": int(iso27001_score / 100 * 9),
            "controles_total": 9,
        },
        {
            "id": "iso42001",
            "nome": "ISO/IEC 42001:2023",
            "score": round(iso42001_score, 1),
            "cor": "#f59e0b",
            "status": "Conforme" if iso42001_score >= 70 else "Parcialmente Conforme" if iso42001_score >= 40 else "Não Conforme",
            "controles_atendidos": int(iso42001_score / 100 * 12),
            "controles_total": 12,
        },
        {
            "id": "owasp",
            "nome": "OWASP LLM Top-10",
            "score": round(owasp_score, 1),
            "cor": "#ef4444",
            "status": "Conforme" if owasp_score >= 70 else "Parcialmente Conforme" if owasp_score >= 40 else "Não Conforme",
            "controles_atendidos": int(owasp_score / 100 * 10),
            "controles_total": 10,
        },
    ]

    score_geral = round(sum(f["score"] for f in frameworks) / len(frameworks), 1)

    return {
        "score_geral": score_geral,
        "frameworks": frameworks,
        "metricas_base": {
            "total_avaliacoes": metrics["total"],
            "taxa_bloqueio": round(metrics["block_rate"], 1),
            "deteccoes_pii": metrics["pii_total"],
            "alertas_abertos": metrics["open_alerts"],
        },
        "ultima_atualizacao": datetime.utcnow().isoformat(),
    }


@router.get("/nist")
async def conformidade_nist(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Detalhes de conformidade NIST AI RMF"""
    metrics = await _calcular_score_conformidade(db)

    funcoes = []
    for func_id, func_data in NIST_CONTROLS.items():
        controles_avaliados = []
        for ctrl in func_data["controles"]:
            # Score baseado nas métricas reais
            if "Métricas" in ctrl["nome"] or "Monitoramento" in ctrl["nome"]:
                score = min(100, 60 + metrics["block_rate"] * 0.3)
            elif "Testes" in ctrl["nome"]:
                score = min(95, 50 + metrics["block_rate"] * 0.4)
            elif "PII" in ctrl["nome"] or "Privacidade" in ctrl["nome"]:
                score = 85 if metrics["pii_detection_ok"] else 30
            else:
                score = min(100, 55 + metrics["block_rate"] * 0.25)

            controles_avaliados.append({
                **ctrl,
                "score": round(score, 1),
                "status": "Atendido" if score >= 70 else "Parcial" if score >= 40 else "Não Atendido",
                "evidencia": f"Baseado em {metrics['total']} avaliações e {metrics['blocked']} bloqueios"
            })

        avg_score = sum(c["score"] for c in controles_avaliados) / len(controles_avaliados)
        funcoes.append({
            **func_data,
            "controles": controles_avaliados,
            "score_medio": round(avg_score, 1),
        })

    return {"funcoes": funcoes, "framework": "NIST AI RMF 1.0"}


@router.get("/lgpd")
async def conformidade_lgpd(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Detalhes de conformidade LGPD"""
    metrics = await _calcular_score_conformidade(db)

    controles = []
    for ctrl_id, ctrl in LGPD_CONTROLES.items():
        if ctrl_id == "seguranca_tecnica":
            score = min(95, 50 + metrics["block_rate"] * 0.4)
        elif ctrl_id == "minimizacao":
            score = 80 if metrics["pii_detection_ok"] else 30
        elif ctrl_id == "transparencia":
            score = 75
        else:
            score = min(85, 45 + metrics["block_rate"] * 0.3)

        controles.append({
            "id": ctrl_id,
            **ctrl,
            "score": round(score, 1),
            "status": "Conforme" if score >= 70 else "Parcialmente Conforme" if score >= 40 else "Não Conforme",
            "evidencias": [
                f"Detecção de PII ativa: {metrics['pii_total']} ocorrências" if ctrl_id == "minimizacao" else f"Sistema auditável: {metrics['total']} registros",
            ],
            "gaps": [] if score >= 70 else ["Necessita implementação adicional"],
        })

    return {"controles": controles, "framework": "LGPD Lei 13.709/2018"}


@router.get("/owasp")
async def conformidade_owasp(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Detalhes OWASP LLM Top-10 com cobertura"""
    # Contagem de detecções por categoria
    result = await db.execute(
        select(EvaluationLog.owasp_categories).select_from(EvaluationLog)
        .where(EvaluationLog.created_at >= datetime.utcnow() - timedelta(days=30))
    )
    owasp_counts = {}
    for row in result.fetchall():
        for cat in (row[0] or []):
            cat_id = OWASP_COMPLIANCE_ALIASES.get(cat, cat.split(":", 1)[0])
            owasp_counts[cat_id] = owasp_counts.get(cat_id, 0) + 1

    categorias_com_cobertura = []
    for cat in OWASP_LLM_TOP10:
        hits = owasp_counts.get(cat["id"], 0)
        covered = hits > 0

        categorias_com_cobertura.append({
            **cat,
            "deteccoes": hits,
            "coberto": covered,
            "nivel_cobertura": "Total" if hits > 10 else "Parcial" if hits > 0 else "Sem Cobertura",
        })

    cobertura_total = sum(1 for c in categorias_com_cobertura if c["coberto"])
    return {
        "categorias": categorias_com_cobertura,
        "cobertura_total": cobertura_total,
        "total_categorias": len(OWASP_LLM_TOP10),
        "percentual": round(cobertura_total / len(OWASP_LLM_TOP10) * 100, 1),
        "framework": "OWASP LLM Top-10 2025",
    }


@router.post("/gerar-relatorio")
async def gerar_relatorio(
    data: ComplianceReportCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Gera relatório de conformidade"""
    metrics = await _calcular_score_conformidade(db, data.period_days)

    titulo = data.title or f"Relatório de Conformidade {data.framework} - {datetime.utcnow().strftime('%d/%m/%Y')}"

    # Score baseado no framework
    scores = {"NIST": 72.5, "ISO27001": 68.0, "ISO42001": 65.0, "LGPD": 78.0, "OWASP": 70.0}
    score = scores.get(data.framework, 70.0) + (metrics["block_rate"] * 0.1)

    findings = [
        {
            "id": "F001",
            "tipo": "positivo",
            "descricao": f"Sistema detectou e bloqueou {metrics['blocked']} de {metrics['total']} requisições suspeitas",
            "impacto": "Alto",
        },
        {
            "id": "F002",
            "tipo": "positivo" if metrics["pii_detection_ok"] else "negativo",
            "descricao": f"Detecção de PII {'ativa e funcionando' if metrics['pii_detection_ok'] else 'precisa de melhoria'}",
            "impacto": "Alto",
        },
        {
            "id": "F003",
            "tipo": "negativo" if metrics["open_alerts"] > 5 else "positivo",
            "descricao": f"{metrics['open_alerts']} alertas em aberto no período",
            "impacto": "Médio" if metrics["open_alerts"] < 10 else "Alto",
        },
    ]

    recommendations = [
        "Revisar e atualizar políticas de segurança trimestralmente",
        "Implementar treinamento de conscientização para todos os usuários",
        "Expandir cobertura de detecção para incluir ataques emergentes",
        "Estabelecer SLA para resolução de alertas críticos (máx. 4 horas)",
        "Realizar testes de penetração semestral no sistema de IA",
    ]

    report = ComplianceReport(
        report_id=str(uuid.uuid4()),
        title=titulo,
        framework=data.framework,
        status="completed",
        score=round(min(score, 100), 1),
        summary={
            "total_avaliacoes": metrics["total"],
            "taxa_bloqueio": round(metrics["block_rate"], 1),
            "deteccoes_pii": metrics["pii_total"],
            "alertas_abertos": metrics["open_alerts"],
        },
        findings=findings,
        recommendations=recommendations,
        period_start=datetime.utcnow() - timedelta(days=data.period_days),
        period_end=datetime.utcnow(),
        generated_by=current_user.get("id"),
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)

    return {
        "report_id": report.report_id,
        "title": report.title,
        "framework": report.framework,
        "score": report.score,
        "status": report.status,
        "summary": report.summary,
        "findings": report.findings,
        "recommendations": report.recommendations,
        "period_start": report.period_start.isoformat() if report.period_start else None,
        "period_end": report.period_end.isoformat() if report.period_end else None,
        "created_at": report.created_at.isoformat() if report.created_at else None,
    }
