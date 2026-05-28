# Sumário de Métricas

> Compilação das métricas implementadas, suas fórmulas, fonte no código
> e exemplos típicos observados no dataset demonstrativo. Para a
> definição formal do método, ver [`evaluation_method.md`](./evaluation_method.md).

---

## 1. Endpoint Único de Métricas

```
GET /api/reports/metrics?days=30
Authorization: Bearer <token>
```

Retorna todas as métricas listadas neste documento em um único payload
JSON, calculado dinamicamente sobre `evaluation_logs` no momento da
chamada.

---

## 2. Métricas e Fórmulas

### 2.1 Attack Catch Rate
```
Attack Catch Rate (%) = (#logs com risk_score ≥ 60) / (#total_logs) × 100
```
- **Onde no código:** `reports_extra.reports_metrics()` campo `rates.attack_catch_rate_pct`
- **Interpretação:** proporção do tráfego classificado como ameaça pelo
  Phoenix Risk Score consolidado.
- **Faixa típica observada:** 35–45% (dataset balanceado por desenho).

### 2.2 False Positive Rate
```
FPR (%) = (#benignos marcados em [30,60) sem block) / (#benignos) × 100
```
- "benigno" ≡ `risk_score < 30` no critério final.
- **Campo:** `rates.false_positive_rate_pct`
- **Interpretação:** prompts inofensivos elevados a "zona ambígua" sem
  serem bloqueados — proxy para falsos alarmes que **não** geraram
  bloqueio. FP "duros" (bloqueio injusto) requerem rotulação manual.
- **Faixa típica:** 4–7%.

### 2.3 Leak Precision
```
Leak Precision (%) = (#logs com PII tratada) / (#logs com PII detectada) × 100
                     onde "tratada" = blocked OR output_score > 30
```
- **Campo:** `rates.leak_precision_pct`
- **Interpretação:** dos casos em que o OutputGuard detectou PII, qual
  fração foi efetivamente bloqueada/sanitizada.
- **Faixa típica:** ~95–100% (no dataset sintético, todo PII detectado é
  marcado para mascaramento por design).

### 2.4 PII Mask Rate
```
PII Mask Rate (%) = (#logs com pii_found ≠ ∅) / (#total_logs) × 100
```
- **Campo:** `rates.pii_mask_rate_pct`
- **Interpretação:** fração do tráfego com PII detectada. Indicador de
  exposição **bruta** do dataset.
- **Faixa típica:** 12–18% (combinação de benignos com PII + sessões de
  Data Exposure Mirror).

### 2.5 Block Rate
```
Block Rate (%) = (#logs com input_blocked=true) / (#total_logs) × 100
```
- **Campo:** `rates.block_rate_pct`
- **Interpretação:** fração do tráfego que o InputGuard bloqueou
  efetivamente. Diferente de `Attack Catch Rate`, considera só ações
  duras (block), não detecções soft (`risk ≥ 60` sem block).
- **Faixa típica:** 30–38%.

### 2.6 Latência média
```
avg_latency_ms = avg(latency_ms) sobre janela
```
- **Campo:** `latency.avg_ms`, `latency.min_ms`, `latency.max_ms`
- **Faixa típica observada (sintética):** avg ≈ 100ms, min ≈ 15ms, max ≈ 195ms.
- **Caveat:** valores sintetizados pelo seeder. Latency Overhead real
  (vs baseline sem pipeline) **não é calculado** — exigiria benchmark
  isolado.

---

## 3. Métricas Auxiliares

### 3.1 Distribuição por nível de risco
```
distribution_by_risk_level = { LOW: n1, MEDIUM: n2, HIGH: n3, CRITICAL: n4 }
```
Histograma direto sobre `risk_level` do `EvaluationLog`.

### 3.2 Top categorias de ataque
Frequência de cada label em `input_labels` para logs com `risk_score ≥ 60`,
ordenado decrescente, top 10.

### 3.3 Volume diário
Lista de objetos `{date, count, avg_risk}` para cada dia da janela.
Permite identificar dias-pico no dashboard.

### 3.4 Totais brutos
| Campo | Significado |
|-------|------------|
| `total_evaluations` | logs no período |
| `total_attacks_detected` | logs com `risk_score ≥ 60` |
| `total_blocked` | logs com `input_blocked=true` |
| `total_benign` | logs com `risk_score < 30` |
| `logs_with_pii` | logs com `pii_found ≠ ∅` |
| `pii_entities_found` | total de entidades PII somadas |
| `false_positives_estimated` | logs em [30, 60) sem block |

---

## 4. Métricas Específicas de Exposição

Endpoint dedicado:
```
GET /api/reports/exposure?days=30
```

| Campo | Significado |
|-------|------------|
| `summary.total_pii_entities` | soma de PII em todos os logs |
| `summary.unique_sessions_with_pii` | sessões distintas com PII |
| `summary.progressive_exposure_sessions` | sessões com flag `DATA_EXPOSURE_PROGRESSIVE` |
| `summary.distinct_pii_types` | tipos únicos detectados |
| `by_pii_type` | contagem por tipo (CPF, EMAIL, …) |
| `top_exposure_categories` | tags de exposição mais frequentes (location, routine, …) |
| `top_exposed_sessions` | 10 sessões mais expostas |
| `progressive_sessions` | dump das sessões multi-turn de Data Exposure |

---

## 5. Métricas Não Implementadas (declaração honesta)

| Métrica solicitada | Status | Motivo |
|--------------------|--------|--------|
| **Leak Recall** | ❌ Não calculada | Exigiria ground-truth externo de quais PII existem nos prompts antes do detector. Sem rotulação manual, não há denominador confiável. |
| **Latency Overhead** | ❌ Não calculada | Exigiria baseline de chamada direta ao LLM (sem pipeline) em ambiente equivalente. |
| **Precision/Recall por categoria de ataque** | ❌ Não calculada | Mesma razão de Leak Recall — exigiria rotulagem ataque-a-ataque. |
| **Confidence intervals** | ❌ Não calculados | Volume pequeno (~500 logs) torna cálculos de IC pouco informativos para um protótipo. |

Essas lacunas estão alinhadas com o escopo do TCC (arquitetura +
demonstração). Sua incorporação está prevista no backlog
([`05-LIMITACOES-E-PROXIMOS-PASSOS.md`](./05-LIMITACOES-E-PROXIMOS-PASSOS.md)).

---

## 6. Tabela-resumo (valores típicos observados)

> Os valores abaixo são **referências aproximadas** observadas em
> múltiplas execuções do seeder. Cada execução produz variação
> (random sem seed fixa). Para reproduzir, ver seção 6 de
> [`demo_dataset_description.md`](./demo_dataset_description.md#6-reproducibilidade).

| Métrica | Faixa observada |
|---------|-----------------|
| Attack Catch Rate | 35–45% |
| Block Rate | 30–38% |
| False Positive Rate | 4–7% |
| Leak Precision | 95–100% |
| PII Mask Rate | 12–18% |
| Latência média (sintética) | 90–110 ms |
| Sessões em estado BLOCKED | 8–15% das sessões |
| Cobertura OWASP | 3/10 categorias com detecções (LLM01, LLM06, LLM08) |
| Top label de ataque | `prompt_injection` (~40% dos ataques) |

---

## 7. Como gerar a tabela com os valores da execução atual

```bash
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login/json \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"admin123"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

curl -s -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/reports/metrics?days=30" \
  | python3 -c "
import sys, json
d = json.load(sys.stdin)
r = d['rates']; t = d['totals']; l = d['latency']
print(f\"Total logs: {t['total_evaluations']}\")
print(f\"Attack Catch Rate: {r['attack_catch_rate_pct']}%\")
print(f\"Block Rate: {r['block_rate_pct']}%\")
print(f\"False Positive Rate: {r['false_positive_rate_pct']}%\")
print(f\"Leak Precision: {r['leak_precision_pct']}%\")
print(f\"PII Mask Rate: {r['pii_mask_rate_pct']}%\")
print(f\"Latência média: {l['avg_ms']}ms\")
"
```
