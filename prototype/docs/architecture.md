# Architecture

O prototipo e uma aplicacao full-stack demonstrativa para avaliacao de riscos em interacoes com LLMs.

## Fluxo principal

```text
Usuario
  -> Frontend React/Vite
  -> FastAPI /api/evaluate
  -> InputGuard
  -> SessionWatch
  -> LLMService mock
  -> OutputGuard
  -> Risk Aggregator
  -> SQLite audit log
  -> Dashboard / Logs / OWASP / Alertas
```

## Frontend

- React Router registra paginas e rotas em `frontend/src/App.jsx`.
- Sidebar registra navegacao em `frontend/src/components/Sidebar.jsx`.
- Chamadas HTTP ficam em `frontend/src/utils/api.js`.
- A pagina `/owasp` fica em `frontend/src/pages/OWASPPage.jsx`.

## Backend

- FastAPI inicia em `backend/app/main.py`.
- Rotas ficam em `backend/app/routes/`.
- Servicos de seguranca ficam em `backend/app/services/`.
- Modelos SQLAlchemy ficam em `backend/app/models/db_models.py`.
- Configuracao fica em `backend/app/core/config.py`.

## Modulos

- InputGuard: detecta prompt injection, jailbreak, exfiltracao e pedidos de segredo.
- OutputGuard: mascara PII e reduz risco de vazamento na resposta.
- SessionWatch: acompanha comportamento multi-turn e escalada de risco.
- Risk Score: consolida sinais em escala 0-100.
- Data Exposure Mirror: evidencia exposicao progressiva de dados sensiveis.
- Dashboard: agrega KPIs, cobertura OWASP e eventos.

## Banco

O prototipo usa SQLite local. O dataset de demonstracao e sintetico e criado no boot do backend.
