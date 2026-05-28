# 01 — Status Atual do Projeto Phoenix

> **Documento:** Estado real do projeto em Abril/2026  
> **Fase:** Pré-deploy em VM — MVP validado localmente

---

## Resumo Executivo

O **Phoenix LLM Trust & Safety Framework** é um firewall semântico para modelos de linguagem (LLMs), desenvolvido como Trabalho de Conclusão de Curso (TCC). O sistema intercepta prompts antes que cheguem a um LLM, avalia riscos de segurança e privacidade, e fornece um painel de monitoramento para operadores.

O projeto está funcional como MVP completo: backend API, frontend dashboard e infraestrutura de staging (Docker + nginx) estão prontos e validados localmente. O próximo passo é o deploy em VM na nuvem.

---

## Objetivo do Projeto

Demonstrar que é possível construir uma camada de segurança reutilizável e auditável entre um sistema de produção e um LLM, cobrindo:

- **Detecção de ataques** (Prompt Injection, Jailbreak, Goal Hijacking e 6 outras categorias)
- **Proteção de dados pessoais** (mascaramento de PII em conformidade com LGPD)
- **Monitoramento de sessões** com escalada automática de risco (FSM)
- **Auditoria completa** de todas as interações
- **Conformidade** com frameworks: OWASP LLM Top-10, NIST AI RMF, LGPD, ISO 27001, ISO 42001

---

## Visão Geral do Estado Atual

```
Estado:     MVP Funcional — Pré-VM
Backend:    ✅ Operacional (local + Docker)
Frontend:   ✅ Operacional (local + Docker)
Staging:    ✅ Configurado (docker-compose.staging.yml + nginx)
Auth/RBAC:  ✅ JWT + 3 roles implementados e funcionando
API Docs:   ✅ Swagger UI com exemplos
Multiuser:  ✅ 5 usuários de demo com roles distintos
VM Deploy:  🔲 Pendente (infraestrutura pronta, falta execução)
```

---

## Funcionalidades Prontas e Validadas

### Core — Pipeline de Avaliação (`POST /api/evaluate`)

| Passo | Módulo | Status | Tecnologia |
|-------|--------|--------|-----------|
| 1 | InputGuard | ✅ Funcional | Regex + padrões OWASP |
| 2 | SessionWatch | ✅ Funcional | FSM em memória |
| 3 | LLM Service | ✅ Mock padrão / OpenAI opcional | httpx + mock |
| 4 | OutputGuard | ✅ Funcional | Regex + 8 tipos PII |
| 5 | Risk Aggregator | ✅ Funcional | Fórmula ponderada |
| 6 | Data Exposure Mirror | ✅ Funcional | Análise de histórico |
| 7 | Persistência (SQLite) | ✅ Funcional | SQLAlchemy async |

### Dashboard — 12 Páginas Implementadas

| Página | Rota | Status | Observação |
|--------|------|--------|------------|
| Dashboard Principal | `/dashboard` | ✅ | KPIs, gráficos, timeline |
| Avaliar Prompt | `/avaliar` | ✅ | Fluxo interativo completo |
| Analytics Avançado | `/analytics` | ✅ | Heatmap, tendências, latência |
| Logs de Auditoria | `/logs` | ✅ | Paginação, filtros, exportação |
| Sessões | `/sessoes` | ✅ | FSM por sessão |
| Alertas | `/alertas` | ✅ | Triagem (open/ack/resolved) |
| Conformidade | `/conformidade` | ✅ | NIST, LGPD, ISO |
| Threat Intelligence | `/ameacas` | ✅ | IOCs, 15+ indicadores |
| Políticas | `/politicas` | ✅ | 6 políticas padrão + custom |
| OWASP Top-10 | `/owasp` | ✅ | Cobertura por categoria |
| Usuários | `/usuarios` | ✅ | Admin only; API Keys |
| Configurações | `/configuracoes` | ✅ | Perfil, senha |

### Infraestrutura e API

| Feature | Status | Observação |
|---------|--------|------------|
| JWT Auth (login/refresh) | ✅ | 8h access + 7d refresh |
| RBAC (admin/analyst/viewer) | ✅ | Sidebar + route guards |
| Role badge no sidebar | ✅ | ADMIN/ANALYST/VIEWER com cor |
| Swagger UI com exemplos | ✅ | 3 exemplos no `/api/evaluate` |
| `/api/info` | ✅ | Sem autenticação |
| `/api/readiness` | ✅ | Para healthcheck de orquestração |
| Erro 422 padronizado | ✅ | `{"error": "validation_error", ...}` |
| Dados de seed (150 logs) | ✅ | Gerados no startup |
| docker-compose.staging.yml | ✅ | Backend + Frontend + nginx |
| nginx reverse proxy | ✅ | `/api/` → backend, `/` → frontend |
| WebSocket `/ws/events` | ✅ | Infra presente no backend |
| Exportação CSV/JSON de logs | ✅ | Via `/api/logs/export` |

---

## O que Ainda Falta (em Alto Nível)

| Item | Criticidade | Observação |
|------|-------------|------------|
| Deploy em VM pública | Alta | Infraestrutura pronta; falta executar |
| Validação multiusuário externo | Alta | Depende do deploy em VM |
| Testes automatizados (pytest) | Média | Nenhum teste unitário escrito |
| SessionWatch persistência entre restarts | Baixa | FSM em memória; perda de estado ao reiniciar |
| Rate limiting real (middleware) | Baixa | Config existe mas middleware não implementado |
| Integração Anthropic | Baixa | Código preparado mas não implementado |
| Modo produção com PostgreSQL | Baixa | Opcional para demo; SQLite suficiente |

---

## Dados de Seed (Demo Pronto)

Ao subir o backend pela primeira vez, os seguintes dados são criados automaticamente:

- **5 usuários** com roles: admin, analyst (×3), viewer
- **150 logs** de avaliação (45% ataques, 55% prompts benignos) — 6 dias de histórico
- **30 sessões** com estados NORMAL/SUSPICIOUS/BLOCKED
- **15 alertas** com severidades e status variados
- **15+ IOCs** de Threat Intelligence
- **6 políticas** de segurança padrão

---

## Métricas Validadas (ambiente local, modo mock)

| Métrica | Valor medido | Meta |
|---------|-------------|------|
| Latência extra (sem LLM) | < 30ms | ≤ 200ms |
| Latência total (mock LLM) | 80–200ms | ≤ 300ms |
| Taxa de detecção (ataques óbvios) | ~90% | ≥ 80% |
| Falsos positivos (prompts benignos) | ~2% | ≤ 5% |
| Cobertura OWASP | 7/10 categorias | 7/10 |

> ⚠️ Métricas com LLM real (OpenAI) não foram validadas por custo. Modo mock simula latência e respostas.
