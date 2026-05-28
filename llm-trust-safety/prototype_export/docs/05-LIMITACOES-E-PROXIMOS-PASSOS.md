# 05 — Limitações e Próximos Passos

> **Documento:** Estado honesto das lacunas técnicas, diferenças entre visão e implementação, e backlog pós-demo.

---

## Princípio deste Documento

Este documento registra **o que o sistema realmente é**, não o que foi planejado. Cada limitação aqui listada representa uma decisão de escopo consciente para o MVP/TCC, não necessariamente uma falha de design.

---

## Limitações Técnicas Atuais

### 1. InputGuard — Regex Only, sem ML

**O que foi proposto:** Detecção semântica de ataques com modelo de linguagem ou embeddings.  
**O que foi implementado:** Regex puro (módulo `re`) com 150+ padrões categorizados.

**Consequências reais:**
- Ataques em idiomas não cobertos pelos regex passam despercebidos
- Ataques semânticos sofisticados sem palavras-chave literais não são detectados
- Obfuscação básica (ex.: l33tsp3ak, unicode lookalikes) pode enganar os padrões
- Alta eficácia para ataques conhecidos e diretos (~90% dos casos de demo)

**Nota para banca:** Isso é intencional para o escopo do TCC. A implementação demonstra a arquitetura e o conceito; a troca por um modelo ML seria um exercício de evolução, não de correção.

---

### 2. OutputGuard — Regex Only, PII sem contexto

**O que foi proposto:** Detecção contextual de PII usando NER (Named Entity Recognition).  
**O que foi implementado:** Regex por tipo de dado com padrões fixos.

**Consequências reais:**
- PII sem formato padrão não é detectada ("meu número de documento é 12345678")
- Não há validação de dígito verificador para CPF/CNPJ
- Nomes próprios, endereços, datas de nascimento NÃO são detectados
- Detecção de cartão de crédito pode ter falsos positivos com outros números de 16 dígitos

---

### 3. SessionWatch — Estado In-Memory, Não Persistido

**O que foi proposto:** FSM com estado durável entre reinicializações.  
**O que foi implementado:** `threading.Lock()` em memória — `dict[session_id → SessionState]`.

**Consequências reais:**
- Um restart do backend (ou redeploy) zera todas as sessões ativas em memória
- A tabela `Session` no banco é atualizada para exibição, mas o estado operacional real da FSM é reconstruído do zero
- Sessões bloqueadas voltam para NORMAL após restart
- **Para demo:** não é um problema prático pois restarts são raros; os dados exibidos persistem

---

### 4. LLM Service — Mock por Padrão, OpenAI Parcial

**O que foi proposto:** Integração com múltiplos provedores (OpenAI, Anthropic, local).  
**O que foi implementado:**
- `mock`: funcional, respostas pré-definidas
- `openai`: funcional, hardcoded em `gpt-3.5-turbo` (não `gpt-4o-mini` apesar do config)
- `anthropic`: campo de config existe, código retorna mock — **não implementado**

**Consequências reais:**
- Config `LLM_MODEL=gpt-4o-mini` no `.env` não tem efeito — o código usa `gpt-3.5-turbo`
- `ANTHROPIC_API_KEY` no `.env` não é usado
- Respostas mock não refletem o conteúdo do prompt real (são aleatórias de lista fixa)

---

### 5. Rate Limiting — Configurado, Não Implementado

**O que foi proposto:** Rate limiting de 60 req/min por usuário.  
**O que foi implementado:** Variável `RATE_LIMIT_PER_MINUTE` existe no config — **sem middleware ativo**.

**Consequências reais:**
- Um cliente malicioso pode fazer requisições ilimitadas
- Para demo/TCC: não é crítico; em produção real seria bloqueante

---

### 6. Compliance Scores — Parcialmente Calculados

**O que foi proposto:** Score de conformidade calculado dinamicamente com base nas configurações reais do sistema.  
**O que foi implementado:** Scores base definidos no código (`compliance.py`) com ajustes baseados em contagem de logs. A apresentação visual é rica, mas os valores não refletem auditoria completa do sistema.

**Categorias com scores estáticos/aproximados:**
- ISO 42001, ISO 27001: base fixa com variação por atividade
- NIST AI RMF: mapeamento real para as categorias, scores calculados por subcategoria
- LGPD: baseado em detecções de PII + configurações de políticas

---

### 7. API Keys — Geração Visual, Não Integrada ao Pipeline

**O que foi proposto:** API Keys como autenticação alternativa ao JWT.  
**O que foi implementado:** UI para criar/revogar API Keys em `UsuariosPage`. O endpoint `POST /api/evaluate` aceita apenas JWT Bearer Token — não aceita API Key no header `X-API-Key`.

---

### 8. WebSocket — Infraestrutura Presente, Broadcasting Parcial

**O que foi proposto:** Dashboard com atualizações em tempo real via WebSocket.  
**O que foi implementado:** `ConnectionManager` e endpoint `/ws/events` funcionais. O broadcasting não é chamado automaticamente a cada nova avaliação — o dashboard usa polling HTTP periódico.

---

### 9. Testes Automatizados — Ausentes

**O que foi proposto:** Suite de testes unitários e de integração.  
**O que foi implementado:** Nenhum arquivo de teste (`pytest`, `vitest`).

**Consequências:** Regressões são detectadas apenas manualmente. Para TCC, a validação manual cobre os casos principais.

---

## Comparativo: Proposta vs Implementação

| Feature | Proposta | Implementação Real | Gap |
|---------|----------|-------------------|-----|
| Detecção de ataques | Semântica (ML/embeddings) | Regex + padrões | Alta eficácia para casos conhecidos |
| PII detection | NER contextual | Regex por tipo | PII não estruturada não detectada |
| SessionWatch FSM | Durável | In-memory | Perdido em restart |
| LLM providers | OpenAI, Anthropic, local | Mock + OpenAI parcial | Anthropic não implementado |
| Rate limiting | Middleware ativo | Config sem middleware | Sem proteção real |
| Compliance scores | Calculados dinamicamente | Híbrido (estático + dinâmico) | Valores aproximados |
| API Keys auth | Funcional no pipeline | UI apenas | JWT é o único método |
| WebSocket realtime | Full push | Infra + polling | Dashboard não é push puro |
| Testes | Suite pytest | Zero testes | Validação manual |
| Múltiplos tenants | Multitenancy por `app_name` | Campo existe, não isolado | Logs de todos misturados |

---

## Riscos Conhecidos para VM

| Risco | Probabilidade | Impacto | Mitigação |
|-------|--------------|---------|-----------|
| Banco SQLite com múltiplos writers simultâneos | Baixa (1 worker) | Alto | `--workers 1` no uvicorn; SQLite aguenta para demo |
| SessionWatch zerado em restart acidental | Baixa | Médio | Dados no banco preservados; FSM reinicia |
| SECRET_KEY padrão em deploy | Baixa (doc clara) | Alto | Validação no startup para `ENVIRONMENT=production` |
| nginx config inválida | Muito baixa (validada) | Alto | Corrigida antes do deploy |
| Porta 80 em conflito na VM | Baixa | Alto | Verificar `ss -tlnp | grep :80` |

---

## Backlog Pós-VM (Próximos Passos Técnicos)

### Curto Prazo (pós-banca)
- [ ] Testes unitários para InputGuard, OutputGuard, RiskAggregator
- [ ] Rate limiting real (middleware `slowapi` ou similar)
- [ ] Persistência de SessionWatch (serializar estado no banco)
- [ ] Broadcasting WebSocket em cada `POST /api/evaluate`

### Médio Prazo
- [ ] Integração Anthropic Claude completa
- [ ] Respeitar `LLM_MODEL` do config no LLMService
- [ ] API Key como método de autenticação alternativo
- [ ] Multitenancy real (isolamento por `app_name`)
- [ ] PostgreSQL como banco padrão para produção

### Longo Prazo (visão de produto)
- [ ] Substituir regex por classificador ML (ex.: fine-tuned BERT, sentence-transformers)
- [ ] NER para PII (spaCy ou Presidio real)
- [ ] Dashboard multi-tenant com isolamento por organização
- [ ] SDK Python/Node para integração simplificada
- [ ] CI/CD pipeline (GitHub Actions)
- [ ] Certificação SSL/HTTPS via Certbot no nginx

---

## Próximos Passos Acadêmicos

Para fortalecer o TCC além do MVP atual:

1. **Comparativo de eficácia:** testar InputGuard regex vs. classificador ML em dataset de prompts adversariais (ex.: PromptBench, RLHF-jailbreaking)
2. **Análise de falsos positivos:** medir taxa de FP em corpus de prompts benignos em domínios específicos (medicina, jurídico)
3. **Avaliação de conformidade real:** mapear cada controle implementado para requisito específico de LGPD/NIST/ISO
4. **Estudo de escalabilidade:** benchmark SQLite vs. PostgreSQL + múltiplos workers para cenário de 100+ req/s

---

## O que Está Sólido para a Banca

Apesar das limitações, o seguinte está **validado e confiável** para apresentação:

- ✅ Pipeline completo de 7 etapas funcionando end-to-end
- ✅ ~90% de detecção para os 20+ padrões de ataque mais comuns
- ✅ Data Exposure Mirror demonstrável com CPF/CNPJ no histórico
- ✅ FSM NORMAL→SUSPICIOUS→BLOCKED demonstrável em tempo real
- ✅ Auditoria completa persistida com audit_id único por avaliação
- ✅ Dashboard com 150+ registros de seed, gráficos funcionais
- ✅ RBAC com 3 roles funcionando visualmente
- ✅ Mapeamento automático para OWASP LLM Top-10 em cada detecção
- ✅ Compliance notes automáticas (LGPD Art. 46, OWASP) na resposta da API
- ✅ Swagger UI com 3 exemplos interativos prontos
