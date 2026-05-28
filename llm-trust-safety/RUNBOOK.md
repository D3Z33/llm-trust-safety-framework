# RUNBOOK

Comandos operacionais do prototipo academico LLM Trust & Safety Framework.

## Requisitos

- Python 3.12+
- Node.js 20+
- npm

## Backend

```powershell
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

API:

- Health: `http://localhost:8000/health`
- Readiness: `http://localhost:8000/api/readiness`
- Swagger: `http://localhost:8000/docs`

## Frontend

```powershell
cd frontend
npm install
npm run dev -- --host 127.0.0.1 --port 3000
```

Aplicacao:

- `http://localhost:3000`
- Login: `admin` / `admin123`
- Guia OWASP: `http://localhost:3000/owasp`

## Build

```powershell
cd frontend
npm run build
```

## Preview do Build

```powershell
cd frontend
npm run preview
```

## Testes e Lint

Nao ha scripts `test` ou `lint` cadastrados em `frontend/package.json`.

Validacoes manuais recomendadas:

```powershell
cd backend
python -m py_compile app/core/config.py app/routes/reports.py app/routes/compliance.py
python -c "from app.main import app; print(app.title); print(len(app.routes))"
```

## Smoke Test Manual

1. Abrir `http://localhost:3000/login`.
2. Login com `admin` / `admin123`.
3. Abrir `/dashboard`.
4. Abrir `/avaliar` e testar os arquivos de `examples/`.
5. Abrir `/owasp` diretamente pelo navegador.
6. Confirmar que a pagina mostra `OWASP LLM Top 10 Mapping`.
7. Confirmar que existem cards das categorias OWASP e status dos modulos.

## Observacoes

- O backend usa SQLite local e seed sintetico demonstrativo.
- O provider LLM padrao e `mock`; nao requer token externo.
- Arquivos `.env`, bancos locais, caches e `node_modules` nao devem ir para o repositorio principal.
