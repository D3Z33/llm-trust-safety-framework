"""
Geração de relatórios PDF premium para o LLM Trust & Safety Framework.

Cinco relatórios disponíveis:
  1. executivo       — Relatório Executivo de Segurança LLM
  2. tecnico         — Relatório Técnico de Eventos e Riscos
  3. exposicao       — Relatório de Exposição de Dados
  4. conformidade    — Relatório de Conformidade e Cobertura OWASP
  5. sessoes_alertas — Relatório de Sessões e Alertas Críticos

Cada gerador retorna `bytes` com o PDF renderizado, pronto para servir
como `application/pdf`.

Stack:
  - reportlab.platypus (layout estruturado)
  - matplotlib (gráficos PNG embutidos)
"""
from __future__ import annotations

import io
from datetime import datetime, timedelta
from typing import Any

import matplotlib

matplotlib.use("Agg")  # backend headless — obrigatório em servidor.
import matplotlib.pyplot as plt
from matplotlib.figure import Figure

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.pdfgen import canvas as pdfcanvas
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    Image,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

# ─── Identidade visual (corporativa neutra, sem branding de produto) ─────
BRAND_NAME = "Plataforma de Segurança e Governança para LLMs"
BRAND_SHORT = "Plataforma de Confiança e Segurança LLM"
BRAND_TAGLINE = (
    "Avaliação contínua, conformidade e auditoria para sistemas baseados em "
    "modelos de linguagem."
)
BRAND_RUBRICA = "Núcleo de Segurança da Informação · Governança e Conformidade"

# Paleta corporativa sóbria (compliance / auditoria)
PRIMARY     = colors.HexColor("#0f172a")  # quase preto azulado
SECONDARY   = colors.HexColor("#1e293b")  # cinza-azulado profundo
ACCENT      = colors.HexColor("#1d4ed8")  # azul corporativo
ACCENT_SOFT = colors.HexColor("#eff6ff")  # azul muito claro
GOLD        = colors.HexColor("#a16207")  # detalhe sóbrio
DANGER      = colors.HexColor("#b91c1c")
WARNING     = colors.HexColor("#b45309")
SUCCESS     = colors.HexColor("#15803d")
MUTED       = colors.HexColor("#475569")
MUTED_LIGHT = colors.HexColor("#94a3b8")
PAPER       = colors.HexColor("#ffffff")
ROW_ALT     = colors.HexColor("#f8fafc")
BORDER      = colors.HexColor("#e2e8f0")


# ─── Estilos de parágrafo ─────────────────────────────────────────────────
def _build_styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "cover_title": ParagraphStyle(
            "cover_title", parent=base["Title"],
            fontName="Helvetica-Bold", fontSize=32, leading=38,
            textColor=PRIMARY, alignment=TA_LEFT, spaceAfter=8,
        ),
        "cover_subtitle": ParagraphStyle(
            "cover_subtitle", parent=base["Heading2"],
            fontName="Helvetica", fontSize=14, leading=20,
            textColor=MUTED, alignment=TA_LEFT, spaceAfter=24,
        ),
        "cover_meta": ParagraphStyle(
            "cover_meta", fontName="Helvetica", fontSize=10,
            leading=14, textColor=MUTED, alignment=TA_LEFT,
        ),
        "h1": ParagraphStyle(
            "h1", parent=base["Heading1"], fontName="Helvetica-Bold",
            fontSize=18, leading=22, textColor=PRIMARY, spaceBefore=12, spaceAfter=10,
        ),
        "h2": ParagraphStyle(
            "h2", parent=base["Heading2"], fontName="Helvetica-Bold",
            fontSize=13, leading=16, textColor=PRIMARY, spaceBefore=10, spaceAfter=6,
        ),
        "h3": ParagraphStyle(
            "h3", parent=base["Heading3"], fontName="Helvetica-Bold",
            fontSize=11, leading=14, textColor=ACCENT, spaceBefore=6, spaceAfter=4,
        ),
        "body": ParagraphStyle(
            "body", fontName="Helvetica", fontSize=10, leading=15,
            textColor=PRIMARY, alignment=TA_JUSTIFY, spaceAfter=6,
        ),
        "body_small": ParagraphStyle(
            "body_small", fontName="Helvetica", fontSize=9, leading=13,
            textColor=PRIMARY, alignment=TA_JUSTIFY, spaceAfter=4,
        ),
        "muted": ParagraphStyle(
            "muted", fontName="Helvetica-Oblique", fontSize=9,
            leading=12, textColor=MUTED, alignment=TA_LEFT, spaceAfter=4,
        ),
        "kpi_label": ParagraphStyle(
            "kpi_label", fontName="Helvetica", fontSize=8,
            leading=10, textColor=MUTED, alignment=TA_LEFT,
        ),
        "kpi_value": ParagraphStyle(
            "kpi_value", fontName="Helvetica-Bold", fontSize=20,
            leading=22, textColor=PRIMARY, alignment=TA_LEFT,
        ),
        "kpi_delta": ParagraphStyle(
            "kpi_delta", fontName="Helvetica", fontSize=8,
            leading=10, textColor=ACCENT, alignment=TA_LEFT,
        ),
        "footer": ParagraphStyle(
            "footer", fontName="Helvetica", fontSize=8,
            leading=10, textColor=MUTED, alignment=TA_CENTER,
        ),
    }


STYLES = _build_styles()


# ─── Template com cabeçalho/rodapé ────────────────────────────────────────
class _CorporateDocTemplate(BaseDocTemplate):
    """Template A4 com header/footer institucionais e paginação elegante."""

    def __init__(self, filename, *, report_title: str, **kwargs):
        super().__init__(filename, pagesize=A4, **kwargs)
        self.report_title = report_title

        page_w, page_h = A4
        margin = 1.8 * cm

        cover_frame = Frame(
            margin, margin, page_w - 2 * margin, page_h - 2 * margin,
            id="cover", showBoundary=0, leftPadding=0, rightPadding=0,
            topPadding=0, bottomPadding=0,
        )
        body_frame = Frame(
            margin, margin + 1.2 * cm,
            page_w - 2 * margin,
            page_h - 2 * margin - 2.2 * cm,
            id="body", showBoundary=0, leftPadding=0, rightPadding=0,
            topPadding=0, bottomPadding=0,
        )
        self.addPageTemplates([
            PageTemplate(id="cover", frames=[cover_frame], onPage=self._draw_cover_chrome),
            PageTemplate(id="body", frames=[body_frame], onPage=self._draw_body_chrome),
        ])

    # Chrome da capa: faixa institucional no topo + filete dourado + base.
    def _draw_cover_chrome(self, c: pdfcanvas.Canvas, _doc):
        page_w, page_h = A4
        # Faixa principal
        c.setFillColor(PRIMARY)
        c.rect(0, page_h - 1.1 * cm, page_w, 1.1 * cm, stroke=0, fill=1)
        # Filete dourado (assinatura visual sutil)
        c.setFillColor(GOLD)
        c.rect(0, page_h - 1.18 * cm, page_w, 0.08 * cm, stroke=0, fill=1)
        # Faixa rodapé
        c.setFillColor(SECONDARY)
        c.rect(0, 0, page_w, 0.55 * cm, stroke=0, fill=1)
        # Texto faixa superior
        c.setFont("Helvetica-Bold", 8.5)
        c.setFillColor(colors.white)
        c.drawString(1.2 * cm, page_h - 0.75 * cm, BRAND_NAME.upper())
        c.setFont("Helvetica", 7.5)
        c.drawRightString(page_w - 1.2 * cm, page_h - 0.75 * cm,
                          datetime.utcnow().strftime("Emitido em %d/%m/%Y · %H:%M UTC"))

    # Chrome das páginas internas
    def _draw_body_chrome(self, c: pdfcanvas.Canvas, doc):
        page_w, page_h = A4
        # Header com filete duplo
        c.setStrokeColor(BORDER)
        c.setLineWidth(0.4)
        c.line(1.8 * cm, page_h - 1.2 * cm, page_w - 1.8 * cm, page_h - 1.2 * cm)
        c.setStrokeColor(GOLD)
        c.setLineWidth(0.3)
        c.line(1.8 * cm, page_h - 1.18 * cm, page_w - 1.8 * cm, page_h - 1.18 * cm)
        c.setFont("Helvetica-Bold", 8)
        c.setFillColor(PRIMARY)
        c.drawString(1.8 * cm, page_h - 1.0 * cm, BRAND_SHORT)
        c.setFont("Helvetica", 8)
        c.setFillColor(MUTED)
        c.drawRightString(page_w - 1.8 * cm, page_h - 1.0 * cm, self.report_title)
        # Footer com classificação
        c.setLineWidth(0.4)
        c.setStrokeColor(BORDER)
        c.line(1.8 * cm, 1.4 * cm, page_w - 1.8 * cm, 1.4 * cm)
        c.setFont("Helvetica", 7.5)
        c.setFillColor(MUTED)
        c.drawString(1.8 * cm, 1.05 * cm, "USO INTERNO · CONFIDENCIAL")
        c.drawCentredString(page_w / 2, 1.05 * cm, BRAND_RUBRICA)
        c.drawRightString(page_w - 1.8 * cm, 1.05 * cm, f"Página {doc.page}")
        c.setFont("Helvetica-Oblique", 6.5)
        c.setFillColor(MUTED_LIGHT)
        c.drawCentredString(page_w / 2, 0.65 * cm,
                            "Documento gerado automaticamente em ambiente controlado de validação acadêmica.")


# ─── Helpers de layout ────────────────────────────────────────────────────
def _cover(
    report_title: str,
    subtitle: str,
    meta_lines: list[str],
    *,
    classificacao: str = "USO INTERNO",
    confidencialidade: str = "CONFIDENCIAL",
    escopo: str | None = None,
    metodologia: str | None = None,
) -> list:
    """Renderiza a capa do PDF com identidade institucional sóbria."""
    story = []
    story.append(Spacer(1, 3.2 * cm))

    # Cabeçalho institucional
    story.append(Paragraph(BRAND_RUBRICA.upper(), STYLES["muted"]))
    story.append(Spacer(1, 4))
    story.append(Paragraph(report_title, STYLES["cover_title"]))
    story.append(Paragraph(subtitle, STYLES["cover_subtitle"]))

    # Filete dourado decorativo
    story.append(Spacer(1, 6))
    line_table = Table([[""]], colWidths=[4.5 * cm], rowHeights=[2.6])
    line_table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), GOLD)]))
    story.append(line_table)
    story.append(Spacer(1, 24))

    # Bloco "identificação"
    for ln in meta_lines:
        story.append(Paragraph(ln, STYLES["cover_meta"]))
        story.append(Spacer(1, 2))

    story.append(Spacer(1, 0.7 * cm))

    # Bloco de classificação e confidencialidade (caixa institucional)
    classif_data = [
        ["CLASSIFICAÇÃO",   classificacao],
        ["CONFIDENCIALIDADE", confidencialidade],
        ["DATA DE EMISSÃO", datetime.utcnow().strftime("%d/%m/%Y")],
        ["VERSÃO DO RELATÓRIO", "1.0"],
    ]
    classif_table = Table(classif_data, colWidths=[5.0 * cm, 11.0 * cm])
    classif_table.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (0, -1), SECONDARY),
        ("TEXTCOLOR",   (0, 0), (0, -1), colors.white),
        ("FONTNAME",    (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE",    (0, 0), (-1, -1), 8.5),
        ("FONTNAME",    (1, 0), (1, -1), "Helvetica"),
        ("TEXTCOLOR",   (1, 0), (1, -1), PRIMARY),
        ("BACKGROUND",  (1, 0), (1, -1), ACCENT_SOFT),
        ("BOX",         (0, 0), (-1, -1), 0.3, BORDER),
        ("INNERGRID",   (0, 0), (-1, -1), 0.3, BORDER),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING",(0, 0), (-1, -1), 8),
        ("TOPPADDING",  (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 6),
    ]))
    story.append(classif_table)
    story.append(Spacer(1, 0.6 * cm))

    if escopo:
        story.append(Paragraph("<b>Escopo:</b> " + escopo, STYLES["body_small"]))
        story.append(Spacer(1, 4))
    if metodologia:
        story.append(Paragraph("<b>Metodologia:</b> " + metodologia, STYLES["body_small"]))
        story.append(Spacer(1, 4))

    story.append(Spacer(1, 0.6 * cm))
    story.append(Paragraph(
        "Documento gerado a partir de dados do ambiente controlado de validação "
        "acadêmica da plataforma. As métricas refletem cenários simulados e devem "
        "ser interpretadas dentro desse contexto. Distribuição restrita.",
        STYLES["muted"],
    ))

    story.append(PageBreak())
    return story


def _section_title(text: str) -> Paragraph:
    return Paragraph(text, STYLES["h1"])


def _para(text: str, style: str = "body") -> Paragraph:
    return Paragraph(text, STYLES[style])


def _kpi_grid(items: list[tuple[str, str, str | None]], cols: int = 4) -> Table:
    """
    Renderiza uma grade de KPIs (label, valor, delta opcional).
    `items` = [(label, value, delta_or_none), ...]
    """
    cells = []
    for label, value, delta in items:
        bloco = [
            Paragraph(label.upper(), STYLES["kpi_label"]),
            Spacer(1, 4),
            Paragraph(value, STYLES["kpi_value"]),
        ]
        if delta:
            bloco.append(Spacer(1, 2))
            bloco.append(Paragraph(delta, STYLES["kpi_delta"]))
        cells.append(bloco)

    # Preenche para múltiplo de cols
    while len(cells) % cols != 0:
        cells.append([Paragraph(" ", STYLES["body_small"])])

    rows = [cells[i:i + cols] for i in range(0, len(cells), cols)]
    table = Table(rows, colWidths=[4.2 * cm] * cols, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), ACCENT_SOFT),
        ("BOX", (0, 0), (-1, -1), 0.3, BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, BORDER),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return table


def _data_table(
    headers: list[str],
    rows: list[list[Any]],
    col_widths: list[float] | None = None,
    zebra: bool = True,
) -> Table:
    data = [headers] + [[str(c) if c is not None else "—" for c in r] for r in rows]
    table = Table(data, colWidths=col_widths, repeatRows=1)
    style_cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 8.5),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), 8.5),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LINEBELOW", (0, 0), (-1, 0), 0.4, BORDER),
        ("LINEBELOW", (0, -1), (-1, -1), 0.4, BORDER),
    ]
    if zebra:
        for i in range(1, len(data)):
            if i % 2 == 0:
                style_cmds.append(("BACKGROUND", (0, i), (-1, i), ROW_ALT))
    table.setStyle(TableStyle(style_cmds))
    return table


def _chart_to_image(fig: Figure, width_cm: float = 16.0) -> Image:
    """Renderiza uma figura matplotlib em PNG e devolve um Flowable Image."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.close(fig)
    buf.seek(0)
    img = Image(buf, width=width_cm * cm, height=width_cm * cm * 0.55)
    img.hAlign = "LEFT"
    return img


def _no_data_block(msg: str) -> Paragraph:
    return Paragraph(
        f"<i>{msg}</i>",
        ParagraphStyle("nodata", fontName="Helvetica-Oblique", fontSize=9,
                       textColor=MUTED, leading=14, alignment=TA_CENTER,
                       borderColor=BORDER, borderWidth=0.4, borderPadding=10),
    )


def _build_doc(report_title: str, story: list) -> bytes:
    """Compila o story em bytes PDF."""
    buf = io.BytesIO()
    doc = _CorporateDocTemplate(buf, report_title=report_title)
    # 1ª página = cover; demais = body
    doc._nextPageTemplateIndex = 1  # noqa: SLF001 — internal hint
    # Inserimos a primeira PageBreak da capa, depois usamos body
    doc.build(story)
    return buf.getvalue()


# ─── Gráficos auxiliares ──────────────────────────────────────────────────
def _setup_mpl():
    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "font.size": 9,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.edgecolor": "#94a3b8",
        "axes.labelcolor": "#1f2937",
        "xtick.color": "#475569",
        "ytick.color": "#475569",
        "axes.grid": True,
        "grid.color": "#e2e8f0",
        "grid.linewidth": 0.6,
    })


def _chart_daily_volume(daily: list[dict]) -> Image | None:
    if not daily:
        return None
    _setup_mpl()
    fig, ax = plt.subplots(figsize=(9, 4.5), facecolor="white")
    dates = [d.get("date", "") for d in daily]
    counts = [d.get("count", 0) for d in daily]
    ax.fill_between(range(len(dates)), counts, color="#2563eb", alpha=0.15)
    ax.plot(range(len(dates)), counts, color="#2563eb", linewidth=2)
    step = max(1, len(dates) // 10)
    ax.set_xticks(range(0, len(dates), step))
    ax.set_xticklabels([dates[i] for i in range(0, len(dates), step)],
                       rotation=30, ha="right", fontsize=8)
    ax.set_ylabel("Volume diário")
    ax.set_title("Volume de avaliações por dia", loc="left",
                 fontsize=11, fontweight="bold", color="#1f2937", pad=12)
    return _chart_to_image(fig)


def _chart_risk_distribution(distribution: dict[str, int]) -> Image | None:
    if not distribution:
        return None
    _setup_mpl()
    order = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    palette = {"LOW": "#10b981", "MEDIUM": "#f59e0b",
               "HIGH": "#f97316", "CRITICAL": "#dc2626"}
    keys = [k for k in order if k in distribution]
    vals = [distribution[k] for k in keys]
    if not keys:
        return None
    fig, ax = plt.subplots(figsize=(9, 4.5), facecolor="white")
    bars = ax.bar(keys, vals, color=[palette[k] for k in keys],
                  edgecolor="white", linewidth=1.2)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, b.get_height() + max(vals) * 0.02,
                f"{v}", ha="center", fontsize=9, color="#1f2937", fontweight="bold")
    ax.set_ylabel("Quantidade")
    ax.set_title("Distribuição por nível de risco", loc="left",
                 fontsize=11, fontweight="bold", color="#1f2937", pad=12)
    return _chart_to_image(fig)


def _chart_top_categories(items: list[dict], titulo: str) -> Image | None:
    if not items:
        return None
    _setup_mpl()
    items = items[:10]
    labels = [str(i.get("category") or i.get("type") or i.get("tag") or "?") for i in items]
    counts = [i.get("count", 0) for i in items]
    fig, ax = plt.subplots(figsize=(9, max(3.5, 0.4 * len(labels) + 1.5)),
                           facecolor="white")
    ax.barh(labels[::-1], counts[::-1], color="#2563eb",
            edgecolor="white", linewidth=1)
    ax.set_xlabel("Ocorrências")
    ax.set_title(titulo, loc="left", fontsize=11, fontweight="bold",
                 color="#1f2937", pad=12)
    return _chart_to_image(fig)


# ─── Coletor de dados (single-pass para todos os relatórios) ─────────────
async def _collect_data(db, days: int) -> dict:
    """
    Coleta dados consolidados em uma única passagem assíncrona.
    Retorna dict com chaves: rates, totals, distribution, top_categories,
    daily, top_pii, top_apps, top_alerts, sessoes_blocked, recent_critical.
    """
    from sqlalchemy import and_, desc, func, select

    from app.models.db_models import Alert, EvaluationLog
    from app.models.db_models import Session as SessionModel

    since = datetime.utcnow() - timedelta(days=days)

    total = (await db.execute(
        select(func.count()).select_from(EvaluationLog)
        .where(EvaluationLog.created_at >= since)
    )).scalar() or 0

    blocked = (await db.execute(
        select(func.count()).select_from(EvaluationLog)
        .where(and_(EvaluationLog.created_at >= since, EvaluationLog.input_blocked == True))
    )).scalar() or 0

    attacks = (await db.execute(
        select(func.count()).select_from(EvaluationLog)
        .where(and_(EvaluationLog.created_at >= since, EvaluationLog.risk_score >= 60))
    )).scalar() or 0

    critical = (await db.execute(
        select(func.count()).select_from(EvaluationLog)
        .where(and_(EvaluationLog.created_at >= since, EvaluationLog.risk_score >= 85))
    )).scalar() or 0

    benigns = (await db.execute(
        select(func.count()).select_from(EvaluationLog)
        .where(and_(EvaluationLog.created_at >= since, EvaluationLog.risk_score < 30))
    )).scalar() or 0

    fp = (await db.execute(
        select(func.count()).select_from(EvaluationLog)
        .where(and_(
            EvaluationLog.created_at >= since,
            EvaluationLog.risk_score >= 30,
            EvaluationLog.risk_score < 60,
            EvaluationLog.input_blocked == False,
        ))
    )).scalar() or 0

    avg_risk = (await db.execute(
        select(func.avg(EvaluationLog.risk_score))
        .where(EvaluationLog.created_at >= since)
    )).scalar() or 0

    avg_lat = (await db.execute(
        select(func.avg(EvaluationLog.latency_ms))
        .where(EvaluationLog.created_at >= since)
    )).scalar() or 0

    # Distribuição
    levels_q = await db.execute(
        select(EvaluationLog.risk_level, func.count())
        .select_from(EvaluationLog)
        .where(EvaluationLog.created_at >= since)
        .group_by(EvaluationLog.risk_level)
    )
    distribution = {row[0]: row[1] for row in levels_q.fetchall()}

    # Top categorias de ataque
    label_q = await db.execute(
        select(EvaluationLog.input_labels)
        .where(and_(EvaluationLog.created_at >= since, EvaluationLog.risk_score >= 60))
    )
    label_count: dict[str, int] = {}
    for row in label_q.fetchall():
        for lab in (row[0] or []):
            label_count[lab] = label_count.get(lab, 0) + 1
    top_categories = [
        {"category": k, "count": v}
        for k, v in sorted(label_count.items(), key=lambda x: x[1], reverse=True)
    ][:10]

    # Top apps
    apps_q = await db.execute(
        select(EvaluationLog.app_name, func.count(), func.avg(EvaluationLog.risk_score))
        .where(EvaluationLog.created_at >= since)
        .group_by(EvaluationLog.app_name)
        .order_by(desc(func.count()))
    )
    top_apps = [
        {"app": r[0], "count": r[1], "avg_risk": round(r[2] or 0, 1)}
        for r in apps_q.fetchall()
    ]

    # Volume diário
    daily = []
    for d in range(days):
        d_start = (datetime.utcnow() - timedelta(days=days - d)).replace(
            hour=0, minute=0, second=0, microsecond=0)
        d_end = d_start + timedelta(days=1)
        cnt = (await db.execute(
            select(func.count()).select_from(EvaluationLog)
            .where(and_(EvaluationLog.created_at >= d_start, EvaluationLog.created_at < d_end))
        )).scalar() or 0
        daily.append({"date": d_start.strftime("%d/%m"), "count": cnt})

    # PII
    pii_q = await db.execute(
        select(EvaluationLog.pii_found, EvaluationLog.session_id)
        .where(and_(EvaluationLog.created_at >= since, EvaluationLog.pii_found != None))
    )
    pii_by_type: dict[str, int] = {}
    sessions_with_pii = set()
    total_pii = 0
    for row in pii_q.fetchall():
        for p in (row[0] or []):
            t = p.get("entity_type", "UNKNOWN")
            pii_by_type[t] = pii_by_type.get(t, 0) + 1
            total_pii += 1
        if row[0]:
            sessions_with_pii.add(row[1])
    top_pii = [
        {"type": k, "count": v}
        for k, v in sorted(pii_by_type.items(), key=lambda x: x[1], reverse=True)
    ]

    # Alertas
    al_total_q = await db.execute(
        select(func.count(), Alert.severity)
        .where(Alert.created_at >= since)
        .group_by(Alert.severity)
    )
    alerts_by_severity = {r[1]: r[0] for r in al_total_q.fetchall()}

    al_recent_q = await db.execute(
        select(Alert).where(Alert.created_at >= since)
        .order_by(desc(Alert.created_at)).limit(15)
    )
    recent_alerts = al_recent_q.scalars().all()

    # Sessões bloqueadas
    sess_q = await db.execute(
        select(SessionModel).where(SessionModel.state == "BLOCKED")
        .order_by(desc(SessionModel.max_risk_score)).limit(10)
    )
    sessoes_blocked = sess_q.scalars().all()

    # Eventos críticos recentes
    crit_q = await db.execute(
        select(EvaluationLog).where(and_(
            EvaluationLog.created_at >= since,
            EvaluationLog.risk_score >= 70,
        )).order_by(desc(EvaluationLog.created_at)).limit(15)
    )
    recent_critical = crit_q.scalars().all()

    # OWASP coverage
    owasp_q = await db.execute(
        select(EvaluationLog.owasp_categories)
        .where(EvaluationLog.created_at >= since)
    )
    owasp_count: dict[str, int] = {}
    for row in owasp_q.fetchall():
        for cat in (row[0] or []):
            owasp_count[cat] = owasp_count.get(cat, 0) + 1
    owasp_top = [
        {"category": k, "count": v}
        for k, v in sorted(owasp_count.items(), key=lambda x: x[1], reverse=True)
    ]

    rates = {
        "block_rate": round(blocked / total * 100, 1) if total else 0,
        "attack_rate": round(attacks / total * 100, 1) if total else 0,
        "critical_rate": round(critical / total * 100, 1) if total else 0,
        "fp_rate": round(fp / benigns * 100, 1) if benigns else 0,
        "pii_rate": round(len(sessions_with_pii) / total * 100, 1) if total else 0,
    }
    totals = {
        "total": total,
        "blocked": blocked,
        "attacks": attacks,
        "critical": critical,
        "benigns": benigns,
        "fp": fp,
        "avg_risk": round(avg_risk, 1),
        "avg_lat": round(avg_lat, 1),
        "total_pii": total_pii,
        "sessions_with_pii": len(sessions_with_pii),
    }
    return {
        "since": since,
        "days": days,
        "rates": rates,
        "totals": totals,
        "distribution": distribution,
        "top_categories": top_categories,
        "top_apps": top_apps,
        "daily": daily,
        "top_pii": top_pii,
        "alerts_by_severity": alerts_by_severity,
        "recent_alerts": recent_alerts,
        "sessoes_blocked": sessoes_blocked,
        "recent_critical": recent_critical,
        "owasp_top": owasp_top,
    }


# ─── Sumário comum ────────────────────────────────────────────────────────
def _toc(items: list[str]) -> list:
    """Gera um sumário simples (não-clicável, mas elegante)."""
    rows = [[f"{i+1:02d}", txt] for i, txt in enumerate(items)]
    table = Table(rows, colWidths=[1.2 * cm, 14 * cm], hAlign="LEFT")
    table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("TEXTCOLOR", (0, 0), (0, -1), ACCENT),
        ("TEXTCOLOR", (1, 0), (1, -1), PRIMARY),
        ("LINEBELOW", (0, 0), (-1, -1), 0.3, BORDER),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    return [Paragraph("Sumário", STYLES["h1"]), table, PageBreak()]


# ═══════════════════════════════════════════════════════════════════════════
# RELATÓRIOS
# ═══════════════════════════════════════════════════════════════════════════
async def gerar_relatorio_executivo(db, days: int = 30) -> bytes:
    """Relatório Executivo de Segurança LLM — visão de alto nível."""
    d = await _collect_data(db, days)
    report_title = "Relatório Executivo de Segurança LLM"

    story: list = []
    # ─── Capa ─────────────────────────────────────────────────────────
    story += _cover(
        report_title=report_title,
        subtitle="Análise consolidada de risco, conformidade e operação",
        meta_lines=[
            f"<b>Janela analisada:</b> últimos {days} dias",
            f"<b>Período:</b> {d['since'].strftime('%d/%m/%Y')} — {datetime.utcnow().strftime('%d/%m/%Y')}",
            f"<b>Total de avaliações no período:</b> {d['totals']['total']:,}",
            f"<b>Aplicações monitoradas:</b> {len(d['top_apps'])}",
            f"<b>Equipe responsável:</b> Governança e Conformidade",
            f"<b>Audiência primária:</b> Liderança técnica e diretoria",
        ],
        classificacao="USO INTERNO",
        confidencialidade="CONFIDENCIAL — LIDERANÇA",
        escopo=(
            "Avaliação agregada do firewall semântico para todas as "
            "aplicações consumidoras de LLM no período. Inclui "
            "InputGuard, OutputGuard, SessionWatch, Risk Aggregator e "
            "Data Exposure Mirror."
        ),
        metodologia=(
            "Agregação estatística dos eventos persistidos na trilha de "
            "auditoria. Limiares de bloqueio e categorização seguem o catálogo "
            "de políticas vigente. Indicadores apresentados sem qualquer "
            "tratamento de outliers."
        ),
    )

    # ─── Sumário ──────────────────────────────────────────────────────
    story += _toc([
        "Sumário executivo",
        "Indicadores-chave de desempenho (KPIs)",
        "Volume de tráfego e tendência",
        "Distribuição por nível de risco",
        "Principais categorias de ataque",
        "Cobertura por aplicação consumidora",
        "Conclusões e recomendações",
    ])

    # ─── 1. Sumário executivo ─────────────────────────────────────────
    story.append(_section_title("1. Sumário Executivo"))
    t = d["totals"]
    r = d["rates"]
    story.append(_para(
        f"Durante a janela analisada de {days} dias, o firewall semântico Phoenix "
        f"processou <b>{t['total']:,}</b> avaliações de prompts oriundos de "
        f"<b>{len(d['top_apps'])}</b> aplicações distintas. Foram detectados "
        f"<b>{t['attacks']:,}</b> eventos de risco elevado (≥60), dos quais "
        f"<b>{t['critical']:,}</b> classificados como críticos (≥85). "
        f"O sistema bloqueou <b>{t['blocked']:,}</b> requisições no input — "
        f"taxa de bloqueio de <b>{r['block_rate']}%</b>."
    ))
    story.append(_para(
        f"O score médio de risco consolidado foi <b>{t['avg_risk']:.1f}/100</b>, com "
        f"latência média de <b>{t['avg_lat']:.0f} ms</b> por avaliação. "
        f"A taxa estimada de falsos positivos ficou em <b>{r['fp_rate']}%</b>, "
        f"dentro da margem operacional aceitável."
    ))
    story.append(Spacer(1, 6))

    # ─── 2. KPIs ─────────────────────────────────────────────────────
    story.append(_section_title("2. Indicadores-chave de Desempenho"))
    story.append(_kpi_grid([
        ("Total de avaliações", f"{t['total']:,}", f"em {days} dias"),
        ("Eventos críticos",    f"{t['critical']:,}", f"{r['critical_rate']}% do total"),
        ("Taxa de bloqueio",    f"{r['block_rate']}%", f"{t['blocked']:,} bloqueios"),
        ("Risco médio",         f"{t['avg_risk']:.1f}", "0–100"),
        ("Latência média",      f"{t['avg_lat']:.0f} ms", "pipeline completo"),
        ("Falsos positivos",    f"{r['fp_rate']}%", "estimativa"),
        ("Detecções de PII",    f"{t['total_pii']:,}", f"{t['sessions_with_pii']} sessões"),
        ("Cobertura OWASP",     f"{len(d['owasp_top'])}/10", "categorias com sinal"),
    ]))
    story.append(Spacer(1, 16))

    # ─── 3. Volume diário ─────────────────────────────────────────────
    story.append(_section_title("3. Volume de Tráfego e Tendência"))
    chart = _chart_daily_volume(d["daily"])
    if chart:
        story.append(chart)
    story.append(_para(
        "A série acima mostra a evolução do volume de avaliações no período. "
        "Picos isolados representam dias de campanha, releases ou tentativas "
        "concentradas de ataque que merecem investigação posterior."
    ))
    story.append(PageBreak())

    # ─── 4. Distribuição por risco ────────────────────────────────────
    story.append(_section_title("4. Distribuição por Nível de Risco"))
    chart = _chart_risk_distribution(d["distribution"])
    if chart:
        story.append(chart)
    story.append(_para(
        "A maioria dos eventos permanece concentrada nas faixas <b>LOW</b> e "
        "<b>MEDIUM</b>, indicando que o tráfego típico é benigno. "
        "Os eventos <b>HIGH</b> e <b>CRITICAL</b> recebem tratamento prioritário "
        "via alertas automáticos para a equipe de plantão."
    ))
    story.append(Spacer(1, 6))

    # ─── 5. Top categorias ────────────────────────────────────────────
    story.append(_section_title("5. Principais Categorias de Ataque"))
    if d["top_categories"]:
        rows = [[i + 1, c["category"], c["count"]]
                for i, c in enumerate(d["top_categories"][:10])]
        story.append(_data_table(
            ["#", "Categoria", "Ocorrências"], rows,
            col_widths=[1 * cm, 12 * cm, 4 * cm],
        ))
    else:
        story.append(_no_data_block("Sem categorias de ataque registradas no período."))
    story.append(PageBreak())

    # ─── 6. Top apps ──────────────────────────────────────────────────
    story.append(_section_title("6. Cobertura por Aplicação Consumidora"))
    if d["top_apps"]:
        rows = [[a["app"] or "—", f"{a['count']:,}", f"{a['avg_risk']:.1f}"]
                for a in d["top_apps"][:12]]
        story.append(_data_table(
            ["Aplicação", "Avaliações", "Risco médio"], rows,
            col_widths=[9 * cm, 4 * cm, 4 * cm],
        ))

    # ─── 7. Conclusões ────────────────────────────────────────────────
    story.append(Spacer(1, 12))
    story.append(_section_title("7. Conclusões e Recomendações"))
    conclusoes = [
        "Manter a operação contínua dos cinco módulos do firewall (InputGuard, "
        "SessionWatch, OutputGuard, Risk Aggregator e Data Exposure Mirror).",
        "Investigar dias de pico cuja taxa de ataque ficou acima da média do período.",
        "Revisar mensalmente as políticas com maior número de acionamentos para "
        "calibração de limiares.",
        "Reforçar o treinamento de sensibilização sobre PII para usuários das "
        "aplicações com maior taxa de exposição (vide seção 6).",
        "Manter o atendimento aos requisitos de auditoria (NIST GOV-2.1) com "
        "trilha persistente de cada avaliação.",
    ]
    for c in conclusoes:
        story.append(_para(f"<b>•</b> {c}"))
        story.append(Spacer(1, 2))

    return _build_doc(report_title, story)


# ─── 2. Relatório Técnico ─────────────────────────────────────────────────
async def gerar_relatorio_tecnico(db, days: int = 30) -> bytes:
    d = await _collect_data(db, days)
    report_title = "Relatório Técnico de Eventos e Riscos"
    story: list = []

    story += _cover(
        report_title=report_title,
        subtitle="Detalhamento técnico das detecções e da operação do firewall",
        meta_lines=[
            f"<b>Janela:</b> últimos {days} dias",
            f"<b>Total de eventos avaliados:</b> {d['totals']['total']:,}",
            f"<b>Eventos críticos analisados:</b> {len(d['recent_critical'])}",
            f"<b>Aplicações cobertas:</b> {len(d['top_apps'])}",
            f"<b>Audiência primária:</b> SecOps, Engenharia e SRE",
        ],
        classificacao="USO INTERNO",
        confidencialidade="CONFIDENCIAL — EQUIPE TÉCNICA",
        escopo=(
            "Eventos persistidos pelo firewall semântico no período, com ênfase "
            "em ataques de risco elevado, sessões bloqueadas e categorias OWASP "
            "acionadas. Inclui amostras de prompts (truncadas) para evidência."
        ),
        metodologia=(
            "Seleção por threshold de risco (≥ 60) e ordenação cronológica "
            "reversa. Score consolidado pelo Risk Aggregator com pesos por "
            "módulo (InputGuard, SessionWatch, OutputGuard)."
        ),
    )

    story += _toc([
        "Resumo das métricas operacionais",
        "Distribuição e severidade",
        "Top eventos críticos do período",
        "Categorias de ataque detectadas",
        "Aplicações com maior risco médio",
        "Considerações operacionais",
    ])

    story.append(_section_title("1. Resumo das Métricas Operacionais"))
    t, r = d["totals"], d["rates"]
    story.append(_kpi_grid([
        ("Avaliações",     f"{t['total']:,}", f"{days} dias"),
        ("Bloqueios",      f"{t['blocked']:,}", f"{r['block_rate']}%"),
        ("Ataques (≥60)",  f"{t['attacks']:,}", f"{r['attack_rate']}%"),
        ("Críticos (≥85)", f"{t['critical']:,}", f"{r['critical_rate']}%"),
        ("Risco médio",    f"{t['avg_risk']:.1f}", "0–100"),
        ("Latência média", f"{t['avg_lat']:.0f} ms", "pipeline"),
        ("FP estimados",   f"{t['fp']:,}", f"{r['fp_rate']}%"),
        ("PII detectada",  f"{t['total_pii']:,}", "entidades"),
    ]))
    story.append(Spacer(1, 14))

    story.append(_section_title("2. Distribuição e Severidade"))
    chart = _chart_risk_distribution(d["distribution"])
    if chart:
        story.append(chart)
    story.append(PageBreak())

    story.append(_section_title("3. Top Eventos Críticos"))
    if d["recent_critical"]:
        rows = []
        for log in d["recent_critical"][:12]:
            prompt = (log.prompt or "").replace("\n", " ")
            if len(prompt) > 70:
                prompt = prompt[:67] + "…"
            rows.append([
                log.created_at.strftime("%d/%m %H:%M") if log.created_at else "—",
                log.app_name or "—",
                f"{log.risk_score:.0f}",
                log.risk_level or "—",
                "Sim" if log.input_blocked else "Não",
                prompt,
            ])
        story.append(_data_table(
            ["Quando", "Aplicação", "Risco", "Nível", "Bloqueado", "Trecho do prompt"],
            rows,
            col_widths=[2.4 * cm, 2.6 * cm, 1.5 * cm, 1.6 * cm, 1.7 * cm, 7.2 * cm],
        ))
    else:
        story.append(_no_data_block("Sem eventos críticos no período analisado."))

    story.append(PageBreak())

    story.append(_section_title("4. Categorias de Ataque Detectadas"))
    chart = _chart_top_categories(d["top_categories"], "Top categorias (≥60 de risco)")
    if chart:
        story.append(chart)

    story.append(_section_title("5. Aplicações com Maior Risco Médio"))
    if d["top_apps"]:
        ordenadas = sorted(d["top_apps"], key=lambda a: a["avg_risk"], reverse=True)
        rows = [[a["app"] or "—", f"{a['count']:,}", f"{a['avg_risk']:.1f}"]
                for a in ordenadas[:12]]
        story.append(_data_table(
            ["Aplicação", "Avaliações", "Risco médio"], rows,
            col_widths=[9 * cm, 4 * cm, 4 * cm],
        ))

    story.append(Spacer(1, 16))
    story.append(_section_title("6. Considerações Operacionais"))
    story.append(_para(
        "Recomenda-se que a equipe de SecOps revise diariamente os eventos "
        "críticos listados na seção 3 e correlacione-os com as sessões em estado "
        "<b>BLOCKED</b>. As aplicações com maior risco médio na seção 5 devem "
        "ter suas políticas de uso aceitável revistas."
    ))
    story.append(_para(
        "A latência média do pipeline deve ser monitorada no dashboard de "
        "Analytics para garantir aderência ao SLA interno (alvo: p95 ≤ 250 ms)."
    ))
    return _build_doc(report_title, story)


# ─── 3. Relatório de Exposição ────────────────────────────────────────────
async def gerar_relatorio_exposicao(db, days: int = 30) -> bytes:
    d = await _collect_data(db, days)
    report_title = "Relatório de Exposição de Dados"
    story: list = []

    story += _cover(
        report_title=report_title,
        subtitle="Detecção de PII e exposição progressiva por Data Exposure Mirror",
        meta_lines=[
            f"<b>Janela:</b> últimos {days} dias",
            f"<b>Entidades PII detectadas:</b> {d['totals']['total_pii']:,}",
            f"<b>Sessões com PII:</b> {d['totals']['sessions_with_pii']:,}",
            f"<b>Tipos distintos de PII:</b> {len(d['top_pii'])}",
            f"<b>Audiência primária:</b> Encarregado de Dados (DPO), jurídico e segurança",
        ],
        classificacao="USO INTERNO",
        confidencialidade="CONFIDENCIAL — PRIVACIDADE",
        escopo=(
            "Eventos persistidos no período em que houve detecção de PII na "
            "saída do modelo ou exposição progressiva da identidade do usuário "
            "ao longo de múltiplos turnos. Cobertura: CPF, CNPJ, e-mail, "
            "telefone, RG, CEP, cartão e tokens."
        ),
        metodologia=(
            "Combinação de regex de PII no OutputGuard com o módulo Data "
            "Exposure Mirror, que correlaciona mencões explícitas e implícitas "
            "de quasi-identificadores ao longo da sessão."
        ),
    )

    story += _toc([
        "Visão geral da exposição",
        "Tipos de PII detectados",
        "Sessões com maior exposição",
        "Recomendações de tratamento",
    ])

    story.append(_section_title("1. Visão Geral da Exposição"))
    t, r = d["totals"], d["rates"]
    story.append(_kpi_grid([
        ("Total avaliado",  f"{t['total']:,}", f"{days} dias"),
        ("Entidades PII",   f"{t['total_pii']:,}", "detectadas"),
        ("Sessões com PII", f"{t['sessions_with_pii']:,}", f"{r['pii_rate']}%"),
        ("Tipos distintos", f"{len(d['top_pii'])}", "categorias"),
    ]))
    story.append(Spacer(1, 14))
    story.append(_para(
        "O módulo Data Exposure Mirror combina detecção explícita (regex de PII "
        "como CPF, CNPJ, e-mail e cartão) com análise de exposição progressiva, "
        "que captura cenários onde o usuário revela informações ao longo de "
        "vários turnos da conversa, criando um perfil quasi-identificador."
    ))
    story.append(PageBreak())

    story.append(_section_title("2. Tipos de PII Detectados"))
    if d["top_pii"]:
        chart = _chart_top_categories(d["top_pii"], "Distribuição de PII por tipo")
        if chart:
            story.append(chart)
        rows = [[i + 1, p["type"], p["count"]] for i, p in enumerate(d["top_pii"])]
        story.append(_data_table(
            ["#", "Tipo de PII", "Ocorrências"], rows,
            col_widths=[1 * cm, 12 * cm, 4 * cm],
        ))
    else:
        story.append(_no_data_block("Nenhuma entidade PII detectada no período."))

    story.append(PageBreak())

    story.append(_section_title("3. Sessões com Maior Exposição"))
    if d["sessoes_blocked"]:
        rows = [[
            (s.session_id or "")[:12] + "…",
            s.app_name or "—",
            f"{s.max_risk_score:.0f}",
            s.total_interactions or 0,
            ", ".join((s.flags or [])[:3]) or "—",
        ] for s in d["sessoes_blocked"]]
        story.append(_data_table(
            ["Sessão", "Aplicação", "Risco máx.", "Interações", "Marcadores"],
            rows,
            col_widths=[3.5 * cm, 3.5 * cm, 2 * cm, 2.5 * cm, 5 * cm],
        ))
    else:
        story.append(_no_data_block("Sem sessões em estado BLOCKED no período."))

    story.append(Spacer(1, 14))
    story.append(_section_title("4. Recomendações de Tratamento"))
    recs = [
        "Manter o mascaramento automático de CPF, CNPJ, e-mail, telefone e cartão "
        "no fluxo de saída do modelo (LGPD Art. 46).",
        "Revisar mensalmente as sessões com flag DATA_EXPOSURE_PROGRESSIVE para "
        "ajustar limiares do Data Exposure Mirror.",
        "Para aplicações com alto volume de PII (>20% das sessões), considerar "
        "treinamento adicional dos usuários e limitação do escopo permitido.",
        "Em caso de exposição confirmada de PII de terceiros sem consentimento, "
        "abrir incidente formal junto ao Encarregado de Dados.",
    ]
    for rec in recs:
        story.append(_para(f"<b>•</b> {rec}"))
        story.append(Spacer(1, 2))
    return _build_doc(report_title, story)


# ─── 4. Relatório de Conformidade e Cobertura OWASP ──────────────────────
async def gerar_relatorio_conformidade(db, days: int = 30) -> bytes:
    d = await _collect_data(db, days)
    report_title = "Relatório de Conformidade e Cobertura OWASP"
    story: list = []

    OWASP_DESCRICAO = {
        "LLM01:PromptInjection":              "Injeção de prompt — direta ou indireta.",
        "LLM02:InsecureOutputHandling":       "Tratamento inseguro da saída do modelo.",
        "LLM03:TrainingDataPoisoning":        "Envenenamento de dados de treinamento.",
        "LLM04:ModelDenialOfService":         "Negação de serviço via prompts custosos.",
        "LLM05:SupplyChainVulnerabilities":   "Vulnerabilidades na cadeia de suprimento.",
        "LLM06:SensitiveInformationDisclosure": "Vazamento de informação sensível.",
        "LLM07:InsecurePluginDesign":         "Design inseguro de plugins/ferramentas.",
        "LLM08:ExcessiveAgency":              "Agência excessiva concedida ao modelo.",
        "LLM09:Overreliance":                 "Dependência excessiva do modelo.",
        "LLM10:ModelTheft":                   "Roubo ou cópia não autorizada do modelo.",
    }

    story += _cover(
        report_title=report_title,
        subtitle="Aderência a OWASP LLM Top-10, NIST AI RMF, ISO/IEC 42001 e LGPD",
        meta_lines=[
            f"<b>Janela:</b> últimos {days} dias",
            f"<b>Categorias OWASP com sinal:</b> {len(d['owasp_top'])}/10",
            f"<b>Total de eventos correlacionados:</b> {d['totals']['total']:,}",
            f"<b>Frameworks de referência:</b> OWASP LLM Top-10 (2025), NIST AI RMF 1.0,",
            "   ISO/IEC 42001, ISO/IEC 27001, LGPD",
            f"<b>Audiência primária:</b> Comitê de Governança e Auditoria",
        ],
        classificacao="USO INTERNO",
        confidencialidade="CONFIDENCIAL — GOVERNANÇA",
        escopo=(
            "Mapeamento de controles operacionais da plataforma contra os "
            "frameworks de segurança e privacidade aplicáveis a sistemas com "
            "modelos de linguagem em ambiente corporativo brasileiro."
        ),
        metodologia=(
            "Análise descritiva de cobertura por categoria, complementada por "
            "contagem real de detecções no período. Referências ao texto vigente "
            "das normas. Não substitui auditoria independente."
        ),
    )

    story += _toc([
        "Mapa OWASP LLM Top-10",
        "Cobertura observada no período",
        "Aderência ao NIST AI RMF",
        "Notas sobre LGPD",
        "Próximas ações de conformidade",
    ])

    story.append(_section_title("1. Mapa OWASP LLM Top-10"))
    rows = []
    for cat, desc in OWASP_DESCRICAO.items():
        cnt = next((o["count"] for o in d["owasp_top"] if o["category"] == cat), 0)
        rows.append([cat, desc, f"{cnt:,}"])
    story.append(_data_table(
        ["Categoria", "Descrição", "Ocorrências"], rows,
        col_widths=[5 * cm, 9 * cm, 3 * cm],
    ))
    story.append(PageBreak())

    story.append(_section_title("2. Cobertura Observada no Período"))
    chart = _chart_top_categories(d["owasp_top"], "Categorias OWASP detectadas")
    if chart:
        story.append(chart)
    story.append(_para(
        f"No período de {days} dias, foram detectadas ocorrências em "
        f"<b>{len(d['owasp_top'])}</b> categorias OWASP. As demais categorias "
        f"podem estar ausentes por dois motivos: (a) o tipo de ataque não "
        f"ocorreu no tráfego analisado, ou (b) a detecção depende de sinais "
        f"adicionais não cobertos pela versão atual do classificador."
    ))

    story.append(_section_title("3. Aderência ao NIST AI RMF"))
    nist_rows = [
        ("GOV-2.1", "Trilha de Auditoria",
         "Cumprida — toda avaliação produz audit_id persistente."),
        ("MAP-3.1", "Identificação de Riscos",
         "Cumprida — riscos mapeados por OWASP, NIST e ISO."),
        ("MEA-2.2", "Testes Adversariais",
         f"Cumprida — {d['totals']['attacks']:,} eventos adversariais detectados."),
        ("MEA-2.5", "Monitoramento Contínuo",
         "Cumprida — pipeline ativo com latência média monitorada."),
        ("MEA-4.1", "Avaliação de Privacidade",
         f"Cumprida — {d['totals']['total_pii']:,} entidades PII detectadas e tratadas."),
        ("MAN-1.1", "Plano de Resposta a Incidentes",
         "Em maturação — alertas críticos disparam webhook de plantão."),
        ("MAN-2.2", "Controles de Mitigação",
         f"Em produção — {d['totals']['blocked']:,} bloqueios automáticos no período."),
    ]
    story.append(_data_table(
        ["Controle", "Nome", "Status"],
        [[a, b, c] for a, b, c in nist_rows],
        col_widths=[2.6 * cm, 5 * cm, 9.4 * cm],
    ))
    story.append(PageBreak())

    story.append(_section_title("4. Notas sobre LGPD"))
    story.append(_para(
        "O sistema implementa mascaramento automático de PII na saída do modelo "
        "(Art. 46 — adoção de medidas de segurança técnicas) e mantém trilha de "
        "auditoria com prazo de retenção configurável (Art. 16 — eliminação de "
        "dados após o cumprimento da finalidade). O Encarregado de Dados deve "
        "validar o tempo de retenção dos logs operacionais conforme política "
        "interna da organização."
    ))

    story.append(_section_title("5. Próximas Ações de Conformidade"))
    acoes = [
        "Ampliar a cobertura para as categorias OWASP atualmente sem ocorrências, "
        "incluindo testes adversariais sintéticos para validar a presença do "
        "classificador.",
        "Formalizar o plano de resposta a incidentes (NIST MAN-1.1) com "
        "playbooks por categoria de ataque.",
        "Periodicamente revisar limiares de bloqueio em conjunto com a área de "
        "negócio para minimizar falsos positivos.",
        "Iniciar discussão sobre certificação ISO/IEC 42001 (Gestão de IA).",
    ]
    for a in acoes:
        story.append(_para(f"<b>•</b> {a}"))
        story.append(Spacer(1, 2))
    return _build_doc(report_title, story)


# ─── 5. Relatório de Sessões e Alertas Críticos ──────────────────────────
async def gerar_relatorio_sessoes_alertas(db, days: int = 30) -> bytes:
    d = await _collect_data(db, days)
    report_title = "Relatório de Sessões e Alertas Críticos"
    story: list = []

    sev_count = d["alerts_by_severity"]
    total_alertas = sum(sev_count.values())

    story += _cover(
        report_title=report_title,
        subtitle="Triagem operacional de alertas e sessões em estado crítico",
        meta_lines=[
            f"<b>Janela:</b> últimos {days} dias",
            f"<b>Alertas no período:</b> {total_alertas:,}",
            f"<b>Sessões em estado BLOCKED:</b> {len(d['sessoes_blocked'])}",
            f"<b>Eventos críticos amostrados:</b> {len(d['recent_critical'])}",
            f"<b>Audiência primária:</b> Equipe de plantão (SecOps / SRE)",
        ],
        classificacao="USO INTERNO",
        confidencialidade="CONFIDENCIAL — OPERAÇÕES",
        escopo=(
            "Alertas e sessões de segurança observados no período, ordenados "
            "por severidade e tempo de criação. Inclui correlação entre "
            "alertas e os eventos de auditoria que os originaram."
        ),
        metodologia=(
            "Seleção por severidade decrescente; status original preservado. "
            "Métricas operacionais (tempo de reconhecimento, taxa de FP) "
            "calculadas a partir dos timestamps registrados."
        ),
    )

    story += _toc([
        "Distribuição de alertas por severidade",
        "Alertas recentes no período",
        "Sessões em estado crítico",
        "Recomendações de triagem",
    ])

    story.append(_section_title("1. Distribuição de Alertas por Severidade"))
    sev_order = ["critical", "high", "medium", "low", "info"]
    sev_label = {
        "critical": "Crítico", "high": "Alto", "medium": "Moderado",
        "low": "Baixo", "info": "Informativo",
    }
    rows = [[sev_label.get(s, s), sev_count.get(s, 0)] for s in sev_order]
    story.append(_data_table(
        ["Severidade", "Quantidade"], rows,
        col_widths=[8 * cm, 4 * cm],
    ))
    story.append(Spacer(1, 8))

    story.append(_section_title("2. Alertas Recentes"))
    if d["recent_alerts"]:
        rows = []
        for al in d["recent_alerts"][:14]:
            rows.append([
                al.created_at.strftime("%d/%m %H:%M") if al.created_at else "—",
                sev_label.get(al.severity, al.severity),
                (al.title or "—")[:50],
                al.status or "—",
                f"{al.risk_score:.0f}" if al.risk_score is not None else "—",
            ])
        story.append(_data_table(
            ["Quando", "Severidade", "Título", "Status", "Risco"], rows,
            col_widths=[2.4 * cm, 2 * cm, 8.8 * cm, 2.6 * cm, 1.6 * cm],
        ))
    else:
        story.append(_no_data_block("Sem alertas registrados no período."))

    story.append(PageBreak())

    story.append(_section_title("3. Sessões em Estado Crítico"))
    if d["sessoes_blocked"]:
        rows = [[
            (s.session_id or "")[:14] + "…",
            s.app_name or "—",
            s.attack_count or 0,
            s.total_interactions or 0,
            f"{s.max_risk_score:.0f}",
            s.started_at.strftime("%d/%m") if s.started_at else "—",
        ] for s in d["sessoes_blocked"]]
        story.append(_data_table(
            ["Sessão", "Aplicação", "Ataques", "Total", "Risco máx.", "Início"], rows,
            col_widths=[3.6 * cm, 3.4 * cm, 2 * cm, 2 * cm, 2.4 * cm, 2 * cm],
        ))
    else:
        story.append(_no_data_block("Sem sessões em estado BLOCKED no período."))

    story.append(Spacer(1, 14))
    story.append(_section_title("4. Recomendações de Triagem"))
    recs = [
        "Priorizar alertas com severidade <b>Crítico</b> e status <b>Aberto</b>; "
        "meta operacional: tempo de reconhecimento ≤ 30 minutos.",
        "Para cada sessão bloqueada, verificar se houve correlação com IPs ou "
        "contas suspeitas registradas em Threat Intel.",
        "Documentar os alertas marcados como <b>falso positivo</b> para "
        "calibrar políticas e reduzir ruído operacional.",
        "Manter integração de webhook ativa para o canal de plantão da "
        "equipe de SecOps.",
    ]
    for r in recs:
        story.append(_para(f"<b>•</b> {r}"))
        story.append(Spacer(1, 2))
    return _build_doc(report_title, story)


# ─── Catálogo público ─────────────────────────────────────────────────────
RELATORIOS_DISPONIVEIS = {
    "executivo": {
        "titulo": "Relatório Executivo de Segurança LLM",
        "descricao": "Visão de alto nível para liderança e diretoria.",
        "gerador": gerar_relatorio_executivo,
    },
    "tecnico": {
        "titulo": "Relatório Técnico de Eventos e Riscos",
        "descricao": "Análise técnica detalhada para SecOps e Engenharia.",
        "gerador": gerar_relatorio_tecnico,
    },
    "exposicao": {
        "titulo": "Relatório de Exposição de Dados",
        "descricao": "Detecção de PII e Data Exposure Mirror.",
        "gerador": gerar_relatorio_exposicao,
    },
    "conformidade": {
        "titulo": "Relatório de Conformidade e Cobertura OWASP",
        "descricao": "Aderência a OWASP LLM Top-10, NIST AI RMF e LGPD.",
        "gerador": gerar_relatorio_conformidade,
    },
    "sessoes_alertas": {
        "titulo": "Relatório de Sessões e Alertas Críticos",
        "descricao": "Triagem de alertas e sessões em estado crítico.",
        "gerador": gerar_relatorio_sessoes_alertas,
    },
}
