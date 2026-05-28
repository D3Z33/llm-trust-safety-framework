# PROJECT_STRUCTURE

Estrutura principal do prototipo.

```text
llm-trust-safety/
├── backend/
│   ├── app/
│   │   ├── core/
│   │   ├── models/
│   │   ├── routes/
│   │   ├── services/
│   │   └── main.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── pages/
│   │   ├── utils/
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── package.json
│   ├── vite.config.js
│   └── Dockerfile
├── docs/
│   ├── architecture.md
│   ├── owasp_mapping.md
│   └── risk_score.md
├── examples/
├── screenshots/
├── README.md
├── RUNBOOK.md
├── PROTOTYPE_STATUS.md
├── QA_PROTOTYPE.md
└── PROJECT_STRUCTURE.md
```

## Rotas frontend

As rotas ficam em `frontend/src/App.jsx`.

- `/login`
- `/dashboard`
- `/avaliar`
- `/analytics`
- `/logs`
- `/sessoes`
- `/alertas`
- `/conformidade`
- `/ameacas`
- `/owasp`
- `/politicas`
- `/usuarios`
- `/configuracoes`

O menu fica em `frontend/src/components/Sidebar.jsx`.

## Rotas backend relevantes

- `POST /api/auth/login/json`
- `POST /api/evaluate`
- `GET /api/dashboard`
- `GET /api/logs`
- `GET /api/sessions`
- `GET /api/owasp`
- `GET /api/owasp/details`
- `GET /api/conformidade/owasp`
- `GET /health`
- `GET /api/readiness`

## Arquivos que nao entram na exportacao

- `frontend/node_modules/`
- `frontend/dist/`
- `backend/__pycache__/` e `backend/app/**/__pycache__/`
- `backend/*.db`
- `.env`, `.env.staging`, tokens e credenciais
- caches de build/teste
