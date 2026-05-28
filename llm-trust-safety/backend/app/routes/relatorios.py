"""
Rotas de geração de relatórios PDF premium.

  GET /api/relatorios/lista                     — catálogo de relatórios disponíveis
  GET /api/relatorios/pdf/{tipo}?days=30        — baixa o PDF gerado (auth bearer)
  GET /api/relatorios/pdf/{tipo}/preview        — alias para visualização inline
"""
from datetime import datetime
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.services.pdf_reports import RELATORIOS_DISPONIVEIS

router = APIRouter(prefix="/api/relatorios", tags=["Relatórios PDF"])


@router.get("/lista", summary="Lista os relatórios PDF disponíveis")
async def listar_relatorios(_user: dict = Depends(get_current_user)):
    return {
        "relatorios": [
            {"tipo": tipo, "titulo": meta["titulo"], "descricao": meta["descricao"]}
            for tipo, meta in RELATORIOS_DISPONIVEIS.items()
        ]
    }


@router.get(
    "/pdf/{tipo}",
    summary="Gera e devolve o PDF do relatório indicado",
    responses={200: {"content": {"application/pdf": {}}}},
)
async def gerar_pdf(
    tipo: str,
    days: int = Query(default=30, ge=1, le=180,
                      description="Janela em dias usada para agregar os dados."),
    inline: bool = Query(default=False,
                         description="Se true, força exibição no navegador."),
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    meta = RELATORIOS_DISPONIVEIS.get(tipo)
    if not meta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tipo de relatório desconhecido: '{tipo}'. "
                   f"Tipos válidos: {list(RELATORIOS_DISPONIVEIS.keys())}",
        )

    try:
        pdf_bytes = await meta["gerador"](db, days=days)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Falha ao gerar relatório: {exc}",
        ) from exc

    timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M")
    filename = f"phoenix_{tipo}_{days}d_{timestamp}.pdf"
    disposition = "inline" if inline else "attachment"
    encoded = quote(filename)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"{disposition}; filename=\"{filename}\"; "
                                   f"filename*=UTF-8''{encoded}",
            "Cache-Control": "no-store",
        },
    )
