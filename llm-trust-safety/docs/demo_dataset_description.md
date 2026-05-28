# Descrição do Dataset Demonstrativo

> **Aviso de honestidade científica**
> Todo o conteúdo descrito neste documento é **sintético**. Os registros
> existem exclusivamente para validação acadêmica do protótipo, geração
> de evidências visuais para o dashboard e discussão das métricas no
> trabalho final. Eles **não representam** tráfego real de produção,
> usuários reais nem incidentes reais. CPFs, e-mails, cartões e demais
> identificadores presentes nos exemplos são **fictícios**.

---

## 1. Identificação no Banco

Cada registro sintético é marcado com:

| Tabela | Coluna | Valor |
|--------|--------|-------|
| `evaluation_logs` | `source_type` | `synthetic_demo` |
| `sessions` | `source_type` | `synthetic_demo` |

A coluna `source_type` é adicionada idempotentemente no startup (`init_db()`)
e tem default `"live"` para qualquer registro futuro criado via
`POST /api/evaluate`. Isso garante que **dados gerados pelo seeder podem
ser distinguidos de avaliações reais** a qualquer momento, inclusive
em queries SQL diretas.

---

## 2. Geração

A função `_seed_demo_data(db, days=30)` em `backend/app/main.py` é
responsável pela geração. Pode ser invocada de três formas:

| Quando | Como |
|--------|------|
| Primeiro startup do backend | Automático, se a tabela `evaluation_logs` estiver vazia |
| Reset manual durante demo | `POST /api/seed/demo-data` (admin only) com `wipe_existing=true, confirm=true` |
| Reload em desenvolvimento | Apagar o arquivo SQLite e iniciar o backend novamente |

---

## 3. Composição do Dataset

### 3.1 Janela temporal
- **Padrão:** 30 dias (configurável via parâmetro `days`).
- **Distribuição diária variável:**
  - **Dias úteis baseline:** 8–15 eventos/dia
  - **3 dias de pico aleatórios:** 25–40 eventos/dia
  - **Sábados/domingos:** 5–10 eventos/dia
- **Distribuição horária:** ~70% dos eventos em horário comercial (8h–19h),
  ~30% espalhados nas demais horas.

### 3.2 Volume total esperado
| Componente | Volume aproximado |
|-----------|------------------|
| Logs de avaliação principais | 350–500 |
| Logs de Data Exposure Mirror (sessões dedicadas) | ~30 |
| Sessões agregadas | 50–80 |
| Alertas | 15 (datas distribuídas no período) |

### 3.3 Mix de cenários

| Categoria | Proporção alvo | Exemplos |
|-----------|----------------|---------|
| Ataques (`risk_score` ≥ 60) | ~40% | Prompt Injection, Jailbreak, Goal Hijacking, Data Exfiltration, Tool Abuse, Multi-Step Deception, Context Hijacking, Policy Evasion |
| Benignos (`risk_score` < 30) | ~60% (descontados FP/PII) | Perguntas sobre LGPD, OWASP, NIST, autenticação, criptografia |
| Falsos positivos | ~5% dos benignos | Prompts marcados como `policy_evasion` em zona MEDIUM (35–55) sem bloqueio |
| Vazamento PII (mascarado) | ~20% dos benignos | CPF, EMAIL, PHONE, CNPJ, CREDIT_CARD, RG, CEP, API_KEY |

### 3.4 Sessões dedicadas ao Data Exposure Mirror

Oito sessões multi-turn (3–4 mensagens cada) que simulam revelação
**progressiva** de informação ao longo da conversa:

| Sessão | Foco | Tags expostas |
|--------|------|---------------|
| `engenharia_social_progressiva` | Identidade técnica → contato → CPF | name, profession, location, email, cpf |
| `exposicao_corporativa` | Trabalho → infra → privilégio → credencial | company, role, infrastructure, credential_pattern |
| `vazamento_pii_familiar` | Terceiro → cartão → CPF de terceiro | family, age, card_pattern, cpf |
| `rotina_e_localizacao` | Rotina → bairro → endereço → família | routine, neighborhood, specific_address, family_size |
| `preferencias_e_perfil` | Política/dieta → saúde → finanças | political, diet, mental_health, salary |
| `credenciais_simuladas` | Token → senha → cartão | token_pattern, password, credit_card |
| `baixo_risco_normal` | Conversa neutra (controle) | — |
| `baixo_risco_normal_2` | Conversa neutra (controle) | — |

Sessões de exposição recebem flag `DATA_EXPOSURE_PROGRESSIVE` a partir
da terceira mensagem para que o agregador `/api/reports/exposure` as
identifique.

---

## 4. Fontes dos Prompts

### 4.1 Prompts de ataque (24 templates)
Inspirados em padrões públicos:
- **OWASP LLM Top-10 (2023/2024)** — categorias LLM01, LLM06, LLM08
- **MITRE ATLAS** — técnicas de evasão e exfiltração
- **DAN-prompt corpus** público — variações de jailbreak

Todos os prompts são exemplos didáticos, **não funcionais contra LLMs
modernos atualizados**. Servem para gerar tráfego sintético reconhecível
pelo InputGuard baseado em regex.

### 4.2 Prompts benignos (25 templates)
Tópicos de segurança da informação, conformidade e tarefas
corporativas neutras (resumos, e-mails, retrospectivas).

### 4.3 PII fictícia
- **CPFs gerados manualmente** com dígitos verificadores **inválidos**
  (ex: `123.456.789-00`, `987.654.321-00`)
- **E-mails de domínios fictícios** ou exemplos como `gmail.com`
  (sem associação a pessoa real)
- **Cartão `4111 1111 1111 1111`** — número público de teste Visa
- **Token JWT fake** com assinatura inválida

---

## 5. Limitações Documentadas

| Limitação | Impacto |
|-----------|---------|
| Volume relativamente pequeno (~500 logs em 30 dias) | Distribuições podem ter cauda curta; gráficos extremos com poucos pontos |
| `attack_count` da sessão é incrementado mesmo entre sessões re-aproveitadas aleatoriamente | Sessões podem ter `attacks` proporcionalmente alto sem refletir progressão real |
| Latências `latency_ms` são `random.uniform(15, 195)` — **não medidas** | Não comparáveis a medições reais; usar como ilustração |
| Falsos positivos são marcados artificialmente (5%) | A taxa real do classificador regex pode diferir |
| Falsos negativos não são injetados explicitamente no seeder | Cálculo de Recall verdadeiro requer dataset rotulado externo |
| Compliance score é calculado por fórmula heurística simples | Não substitui auditoria formal NIST/ISO |

---

## 6. Reproducibilidade

A geração usa `random` da biblioteca padrão do Python sem seed fixo.
Isso significa que **cada execução do seeder produz um dataset levemente
diferente** (volumes, distribuição horária, IDs).

**Para reproduzir um dataset idêntico**, fixar a seed antes de
`_seed_demo_data()`:

```python
import random
random.seed(42)
```

Não foi imposta seed fixa por padrão para que cada demonstração tenha
variabilidade visual realista.

---

## 7. Arquivos Relevantes

| Arquivo | Conteúdo |
|---------|---------|
| `backend/app/main.py` | função `_seed_demo_data()` — geração |
| `backend/app/routes/reports_extra.py` | endpoint `POST /api/seed/demo-data` |
| `backend/app/models/db_models.py` | coluna `source_type` |
| `backend/app/core/database.py` | migração idempotente da coluna |
| `frontend/src/pages/DashboardPage.jsx` | banner de aviso na UI |
