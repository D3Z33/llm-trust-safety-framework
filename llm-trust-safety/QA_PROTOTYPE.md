# QA_PROTOTYPE

Data da execucao: 2026-05-28

## Testes executados

| Teste | Comando/acao | Resultado |
|---|---|---|
| Diagnostico de estrutura | `Get-ChildItem -Force`, `rg --files`, leituras de `App.jsx`, `Sidebar.jsx`, `OWASPPage.jsx`, `main.py` | Stack e rotas identificadas |
| Import backend antes da correcao | `python -c "from app.main import app; print(app.title); print(len(app.routes))"` | Falhou com `DEBUG=release` invalido para boolean |
| Py compile apos correcao | `python -m py_compile backend\app\core\config.py backend\app\routes\reports.py backend\app\routes\compliance.py` | Passou |
| Import backend apos correcao | `python -c "from app.main import app; print(app.title); print(len(app.routes))"` | Passou, app com 62 rotas |
| Build frontend no sandbox | `npm run build` | Falhou por `EPERM` do sandbox ao resolver `C:\Users\Renan` |
| Build frontend fora do sandbox | `npm run build` | Passou |
| Instalacao backend no sandbox | `pip install -r requirements.txt` | Falhou por bloqueio de rede/permissao |
| Instalacao backend fora do sandbox | `pip install -r requirements.txt` | Passou; ajustou `uvicorn==0.30.1` e `pydantic-settings==2.3.0` |
| Smoke backend temporario | `uvicorn app.main:app --host 127.0.0.1 --port 8001` + `GET /health` e `GET /api/owasp/details?days=30` | Passou com HTTP 200 |
| Smoke frontend temporario | `npm run dev -- --host 127.0.0.1 --port 3001` + `GET /` e `GET /owasp` | Passou com HTTP 200 fora do sandbox |
| Servidores finais para teste local | Backend `8001` e frontend `3001` em segundo plano | `GET /health`, `GET /api/owasp/details?days=30` e `GET /owasp` passaram com HTTP 200 |

## Erros encontrados

- Backend quebrava no import quando o ambiente tinha `DEBUG=release`.
- `/owasp` dependia de `/api/owasp/details` e podia ficar em loading infinito quando a API estivesse indisponivel.
- Mapeamento OWASP misturava nomenclaturas antigas com a lista 2025 esperada.
- Build do Vite precisou ser executado fora do sandbox por restricao de permissao local.
- Backend falhava ao subir no Windows por `UnicodeEncodeError` em prints com emoji quando o console estava em `cp1252`.
- Porta `8000` estava ocupada por processo Python antigo; smoke test final foi executado em `8001`.

## Correcoes feitas

- `backend/app/core/config.py`: parser tolerante para `DEBUG=release`, `prod`, `staging`, `false`, etc.
- `backend/app/routes/reports.py`: mapeamento OWASP 2025, aliases de categorias antigas e retorno de status por modulo.
- `backend/app/routes/compliance.py`: mapeamento OWASP 2025 e normalizacao de aliases para cobertura.
- `frontend/src/pages/OWASPPage.jsx`: fallback demonstrativo, titulo `OWASP LLM Top 10 Mapping`, status por modulo e relacao com controles.
- `backend/app/main.py`: stdout/stderr reconfigurados para UTF-8 no boot em Windows.

## Validacao final

- Backend importa corretamente.
- Frontend builda corretamente fora do sandbox.
- Backend sobe e responde `/health` e `/api/owasp/details?days=30` em porta alternativa `8001`.
- Frontend Vite responde `/` e `/owasp` em porta alternativa `3001`.
- Servidores locais ativos para teste: frontend `http://127.0.0.1:3001/owasp`, backend `http://127.0.0.1:8001`.
- Guia `/owasp` tem rota registrada em `frontend/src/App.jsx`.
- Menu aponta para `/owasp` em `frontend/src/components/Sidebar.jsx`.
- A tela `/owasp` agora mostra conteudo util mesmo se a API falhar.

## Pendencias

- Adicionar screenshots finais em `screenshots/`.
- Adicionar testes automatizados futuros.
