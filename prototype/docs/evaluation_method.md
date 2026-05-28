# Método de Avaliação

> Define o protocolo controlado utilizado para validar empiricamente o
> protótipo Phoenix LLM Trust & Safety Framework sobre o dataset
> demonstrativo descrito em [`demo_dataset_description.md`](./demo_dataset_description.md).

---

## 1. Escopo

A avaliação responde a três perguntas:

1. **Cobertura.** Os módulos InputGuard, OutputGuard, SessionWatch e
   Data Exposure Mirror conseguem identificar o tipo de evento para o
   qual foram desenhados?
2. **Precisão estrutural.** As métricas calculadas pelo sistema
   coincidem com as métricas calculadas independentemente sobre o
   mesmo dataset?
3. **Coerência operacional.** O dashboard reflete fielmente os dados
   armazenados, sem invenção visual?

Este protocolo **não** afirma generalização para tráfego real de
produção. As limitações estão explicitadas em
[`05-LIMITACOES-E-PROXIMOS-PASSOS.md`](./05-LIMITACOES-E-PROXIMOS-PASSOS.md).

---

## 2. Ambiente

| Componente | Versão / valor |
|-----------|----------------|
| Python | 3.12 |
| FastAPI | 0.111 |
| SQLAlchemy | 2.x async + aiosqlite |
| Banco | SQLite local (`llm_trust_enterprise.db`) |
| LLM | `LLM_PROVIDER=mock` (sem chamadas externas) |
| Sistema | Local de desenvolvimento (não VM) |
| Frontend | Vite dev server (porta 3000) |

**Importante:** o ambiente é local-determinístico. Latências reportadas
são aquelas geradas pelo seeder, **não** medições de tempo real do
pipeline. Medições reais do pipeline exigem benchmark separado.

---

## 3. Dataset utilizado

- **Geração:** `_seed_demo_data(db, days=30)` — ver
  [`demo_dataset_description.md`](./demo_dataset_description.md).
- **Volume:** 350–500 logs principais + ~30 logs de Data Exposure
  Mirror em sessões multi-turn dedicadas.
- **Marca:** `source_type="synthetic_demo"` em 100% dos registros.
- **Distribuição temporal:** 30 dias, com 3 dias de pico, fim de
  semana reduzido, ~70% horário comercial.

---

## 4. Tipos de teste aplicados

### 4.1 Teste funcional por módulo

| Módulo | Entrada de teste | Saída esperada | Como verificar |
|--------|-----------------|----------------|----------------|
| InputGuard | Prompt com padrão de injection | `input_blocked=true`, `risk_level=CRITICAL` | `POST /api/evaluate` |
| OutputGuard | Resposta contendo CPF fictício | `pii_found` não vazio, `output.sanitized` mascarado | inspecionar response |
| SessionWatch | 3+ ataques na mesma `session_id` | Estado escala `NORMAL→SUSPICIOUS→BLOCKED` | `GET /api/sessions` |
| RiskAggregator | Sinais de input + output + session | `risk_score` consolidado 0-100 | resposta de evaluate |
| DataExposureMirror | Histórico com revelação progressiva | Tags categorizadas (cidade, rotina, trabalho…) | `GET /api/reports/exposure` |

### 4.2 Teste de regressão sobre dataset

Sobre todos os logs do seeder, verificar:

| Invariante | Critério |
|-----------|---------|
| Marcação | 100% dos logs têm `source_type="synthetic_demo"` |
| Distribuição | Volume diário não constante (variabilidade > 20%) |
| Risco | `LOW`, `MEDIUM`, `HIGH`, `CRITICAL` todos representados |
| OWASP | LLM01, LLM06, LLM08 todos com pelo menos 1 ocorrência |
| PII | Pelo menos 5 tipos distintos (CPF, EMAIL, CARTÃO, …) |
| Sessões | Pelo menos 1 sessão em cada estado da FSM |

### 4.3 Teste de integração end-to-end

| Caminho | Verificação |
|---------|-------------|
| Login → Dashboard | `POST /api/auth/login/json` retorna token; `GET /api/dashboard` reflete totais consistentes com `/api/reports/metrics` |
| Avaliação ao vivo | `POST /api/evaluate` cria registro com `source_type="live"` (distinguível dos sintéticos) |
| Reset demo | `POST /api/seed/demo-data` com `wipe_existing=true` regenera apenas registros sintéticos preservando avaliações reais |

### 4.4 Teste de RBAC

| Endpoint | Admin | Analyst | Viewer | Sem auth |
|----------|-------|---------|--------|---------|
| `POST /api/evaluate` | ✅ | ✅ | ✅ | ✅ (auth opcional) |
| `GET /api/dashboard` | ✅ | ✅ | ✅ | ❌ 401 |
| `POST /api/seed/demo-data` | ✅ | ❌ 403 | ❌ 403 | ❌ 401 |

---

## 5. Métricas calculadas

Definição formal das fórmulas (ver
[`metrics_summary.md`](./metrics_summary.md) para resultados):

```
Attack Catch Rate (%)   = #{logs : risk_score ≥ 60} / #total_logs × 100
False Positive Rate (%) = #{benignos : risk_score ∈ [30,60) ∧ ¬blocked} / #benignos × 100
Leak Precision (%)      = #{logs : pii_found ≠ ∅ ∧ (blocked ∨ output_score>30)} / #{logs : pii_found ≠ ∅} × 100
PII Mask Rate (%)       = #{logs : pii_found ≠ ∅} / #total_logs × 100
Block Rate (%)          = #{logs : input_blocked} / #total_logs × 100
```

Onde:
- "benignos" ≡ `risk_score < 30`
- "ataques" ≡ `risk_score ≥ 60`
- "zona ambígua" ≡ `30 ≤ risk_score < 60`

**Latência:**
```
avg_latency_ms = avg(latency_ms)   sobre janela de tempo selecionada
```
Latency Overhead **não é calculado** porque exigiria medição de baseline
sem-pipeline em ambiente isolado, fora do escopo do protótipo.

---

## 6. Coleta dos resultados

```bash
# Métricas formuladas
curl -s -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/reports/metrics?days=30 > metrics_30d.json

# Agregação de exposição
curl -s -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/reports/exposure?days=30 > exposure_30d.json

# Logs completos
curl -s -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/logs?per_page=100" > logs_p1.json
```

Os JSONs são fonte para os números reportados em
[`results_and_discussion.md`](./results_and_discussion.md).

---

## 7. Limitações Metodológicas Honestas

| Limitação | Implicação |
|-----------|------------|
| Dataset gerado pelo mesmo time que projeta o detector | Risco de overfitting implícito — prompts maliciosos foram escolhidos pelos mesmos padrões que o regex detecta |
| Sem ground-truth externo | Recall verdadeiro contra ataques nunca-vistos não pode ser estimado |
| Volume pequeno | Variância alta nas métricas; intervalos de confiança não calculados |
| Mock LLM | Sem ruído de saída real; OutputGuard testado contra strings determinísticas |
| Sem teste adversarial ativo | Não foi tentado evadir o regex com obfuscação Unicode, leetspeak, etc. |
| Ausência de baseline | Sem comparação com NeMo Guardrails ou Guardrails AI |

Estas limitações são esperadas para um TCC focado em **arquitetura e
demonstração**, e estão alinhadas com o escopo declarado.

---

## 8. Replicação

Para replicar a avaliação:

```bash
# 1. Reset do banco
rm -f backend/llm_trust_enterprise.db

# 2. Iniciar backend (gera dataset automaticamente)
cd backend && uvicorn app.main:app --port 8000

# 3. Login admin
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login/json \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"admin123"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# 4. Coletar métricas
curl -s -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/reports/metrics?days=30 | python3 -m json.tool
```

A variação entre execuções é esperada e descrita na
[seção 6 do dataset description](./demo_dataset_description.md#6-reproducibilidade).
