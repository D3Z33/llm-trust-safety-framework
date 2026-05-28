# Resultados e Discussões

> **Aviso metodológico.** Os resultados apresentados foram obtidos a partir
> de um **dataset sintético/demonstrativo**, gerado pelo próprio seeder do
> sistema com 30 dias de histórico simulado. Conforme detalhado em
> [`demo_dataset_description.md`](./demo_dataset_description.md) e
> [`evaluation_method.md`](./evaluation_method.md), as métricas servem
> para evidenciar **comportamento estrutural** do protótipo, não validade
> generalizada para tráfego real de produção. Esta seção pode ser
> incorporada ao trabalho final com adaptações editoriais.

---

## 1. Visão geral dos testes controlados

A avaliação do protótipo Phoenix LLM Trust & Safety Framework foi
conduzida sobre uma base de dados gerada artificialmente, contendo
entre 350 e 500 registros de avaliação distribuídos ao longo de 30
dias, somada a oito sessões multi-turn dedicadas ao módulo Data
Exposure Mirror. Cada registro recebeu o marcador
`source_type="synthetic_demo"` no banco, garantindo que os dados de
demonstração possam ser distinguidos a qualquer momento de eventuais
avaliações reais oriundas do endpoint `POST /api/evaluate`.

A composição da amostra foi desenhada para refletir um cenário
operacional plausível: aproximadamente 40% de prompts ofensivos
(prompt injection, jailbreak, exfiltração, abuso de ferramentas,
desvio de objetivo, evasão de política, decepção multi-passo e
sequestro de contexto), 60% de prompts benignos (perguntas sobre
LGPD, OWASP, NIST, autenticação e tarefas corporativas neutras), com
~5% de falsos positivos injetados deliberadamente para permitir a
discussão de erros do classificador, e ~20% de prompts benignos com
PII fictícia (CPF, e-mail, telefone, cartão, RG, CEP, chave de API)
para exercitar o OutputGuard.

A janela diária de eventos foi modulada para parecer um padrão
realista: dias úteis com volume baseline de 8 a 15 eventos, três dias
de pico com 25 a 40 eventos e fins de semana reduzidos. Cerca de 70%
dos eventos foram alocados em horário comercial (8h–19h).

---

## 2. Comportamento do InputGuard

O InputGuard, implementado por meio de regras determinísticas
(expressões regulares) ancoradas no OWASP LLM Top-10, comportou-se
de maneira consistente nos cenários sintéticos. Nas execuções típicas
do seeder, o módulo identificou e bloqueou aproximadamente 85% dos
prompts ofensivos com `risk_score ≥ 60`, com a categoria
`prompt_injection` representando cerca de 40% das detecções, seguida
por `jailbreak`, `data_exfiltration`, `goal_hijacking` e
`tool_abuse`. As demais categorias do OWASP, como
`InsecureOutputHandling` (LLM02) e `Overreliance` (LLM09), não
apareceram com volume significativo, o que está coerente com o
desenho do dataset — não foram inseridos prompts especificamente
projetados para essas categorias.

Esse resultado é defensável como **prova de conceito** de detecção
baseada em regras claras, com saída interpretável (cada bloqueio
carrega `policy_hits`, `owasp_categories` e `compliance_notes`),
mas é importante reconhecer um **viés metodológico explícito**: os
prompts ofensivos do dataset foram redigidos pela mesma equipe que
projetou as regras de detecção. Há, portanto, sobreposição estrutural
entre o conjunto de teste e o conjunto de regras. Em termos práticos,
isso significa que a métrica de Attack Catch Rate observada (em torno
de 40% de todo o tráfego e 85% sobre o conjunto declaradamente
malicioso) deve ser lida como **limite superior** da capacidade do
protótipo. Generalizar essa taxa para ataques nunca-vistos exigiria
um conjunto adversarial independente, fora do escopo do TCC.

---

## 3. Comportamento do OutputGuard

O OutputGuard atuou sobre as respostas do mock LLM e sobre os campos
de prompt dos cenários de exposição, identificando e mascarando
entidades de PII. Nos testes controlados, o módulo detectou
consistentemente as oito categorias suportadas (CPF, CNPJ, EMAIL,
PHONE, CREDIT_CARD, RG, CEP e API_KEY), produzindo `pii_found`
estruturado e marcando o campo `output_score` proporcionalmente à
gravidade da exposição.

Sobre os logs com PII detectada, a métrica de Leak Precision
permaneceu próxima de 100%, o que reflete fielmente o comportamento
do dataset: por desenho do seeder, todo PII detectado é também
marcado como tratado (bloqueado ou com `output_score` elevado). Esse
número, portanto, não deve ser interpretado como Recall de detecção
em texto livre. A métrica responde à pergunta "quando o sistema
detectou PII, ele aplicou a ação prevista?", não à pergunta
"o sistema detectou todo o PII presente?".

A taxa de mascaramento bruta (PII Mask Rate) ficou na faixa de
12–18% do tráfego, alinhada com o desenho do dataset (20% de
benignos com PII + sessões dedicadas de Data Exposure Mirror).

A principal limitação do OutputGuard atual é a dependência de regex
para detecção. Variações de obfuscação (espaços, caracteres
intercalados, leetspeak) não foram testadas adversarialmente neste
protótipo. Documentar essa limitação no
[backlog pós-VM](./05-LIMITACOES-E-PROXIMOS-PASSOS.md) é uma escolha
deliberada de transparência.

---

## 4. Comportamento do SessionWatch

O SessionWatch foi avaliado pelo número de sessões que progrediram
nos estados `NORMAL → SUSPICIOUS → BLOCKED` ao longo de múltiplas
mensagens. No dataset sintético, foi observado entre 8% e 15% das
sessões em estado `BLOCKED`, ativadas após a terceira detecção de
ataque na mesma `session_id`, e uma fração maior em `SUSPICIOUS`
(uma ou duas detecções).

A escalada da máquina de estados finita foi visível em sessões
multi-turn que combinam tentativas variadas (ex.: prompt injection
seguido de tentativa de exfiltração). O comportamento é
**determinístico e reprodutível**, com flags como
`MULTI_ATTACK_PATTERN`, `HIGH_FREQUENCY` e
`DATA_EXPOSURE_PROGRESSIVE` registradas adequadamente.

A limitação principal — discutida abertamente — é que o SessionWatch
mantém estado **em memória**, o que significa que reinícios do
backend zeram a FSM. Em produção, esse estado migraria para Redis ou
equivalente, conforme indicado em
[`05-LIMITACOES-E-PROXIMOS-PASSOS.md`](./05-LIMITACOES-E-PROXIMOS-PASSOS.md).
Para o escopo do TCC, a abordagem in-memory é suficiente para
demonstrar a lógica de progressão de risco entre interações.

---

## 5. Comportamento do Risk Aggregator

O Risk Aggregator (Phoenix Risk Score) consolidou os sinais dos três
guards em um valor único entre 0 e 100, com pesos de 45% para
InputGuard, 30% para OutputGuard e 25% para SessionWatch. A
distribuição final obtida nas execuções do seeder cobriu as quatro
faixas (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`) com presença em todas,
permitindo discussão visual no dashboard de cada nível.

Pontos positivos: o score é **explicável** — para qualquer log
individual é possível reconstruir os componentes que contribuíram
(`input_score`, `output_score`, `session_score`) e, no UI, a
visualização do detalhe da avaliação mostra essa decomposição.

Pontos a discutir: a fórmula é uma média ponderada simples, sem
calibração contra ground-truth. Em particular, a soma de sinais
fracos pode levar um prompt benigno à zona MEDIUM, gerando o que
classificamos no dataset como falso positivo. A taxa de falso positivo
observada (4–7%) reflete tanto o ruído natural da fórmula quanto a
injeção deliberada de FPs no seeder. Para uma métrica calibrada,
seria necessário um conjunto rotulado externo, atualmente fora do
escopo.

---

## 6. Comportamento do Data Exposure Mirror

O módulo Data Exposure Mirror recebeu atenção dedicada na geração de
dados, com oito sessões multi-turn organizadas em categorias
distintas: engenharia social progressiva, exposição corporativa,
vazamento de PII familiar, rotina e localização, preferências e
perfil, credenciais simuladas e dois controles de baixo risco. Cada
sessão simula a revelação **gradual** de informação ao longo de
três a quatro mensagens, com a flag `DATA_EXPOSURE_PROGRESSIVE`
sendo ativada a partir da terceira mensagem.

O endpoint `GET /api/reports/exposure` consolida essas sessões em
agregados por tipo de PII, por categoria de exposição (location,
routine, family_size, credential_pattern, financial_status, etc.) e
por sessão mais exposta. Esse formato permite, em uma demonstração,
mostrar tanto a **identificação explícita** (CPF revelado em texto)
quanto a **inferência implícita** (combinação de bairro + horário +
estabelecimento permitindo reconstruir rotina).

Esse módulo é didaticamente o mais forte do protótipo, pois
materializa um problema de privacidade que raramente é discutido em
ferramentas de safety: o uso de LLMs como **espelho de exposição**,
em que a soma de pequenas revelações pode constituir risco de
engenharia social. Para o trabalho final, a recomendação é destacar
esse módulo como **diferencial conceitual** em relação a soluções
focadas apenas em detecção de PII bruta.

---

## 7. Interpretação de gráficos do dashboard

O dashboard apresenta as evidências em quatro cortes principais:

1. **Cards superiores** — totais brutos, taxa de captura, score médio
   e latência. Servem como visão imediata do estado do sistema.
2. **Timeline diária** — gráfico de linhas com volume e risco médio
   por dia. Os três dias de pico do seeder ficam visualmente
   destacados, demonstrando a capacidade do sistema de perceber
   variações de tráfego.
3. **Distribuição de ataques** — gráfico de barras ordenando as
   categorias OWASP por frequência. Reflete fielmente o desenho do
   dataset (LLM01 dominante, LLM06 e LLM08 secundários).
4. **Cobertura OWASP** — radar de 10 dimensões mostrando em quais
   categorias o sistema teve detecções no período. As três
   categorias com volume e as sete sem volume ficam claras.

A janela de tempo é configurável (6h, 24h, 2d, 7d e 30d). Selecionar
30d permite visualizar o histórico completo do dataset
demonstrativo.

---

## 8. Resultados positivos

| Aspecto | Evidência |
|---------|-----------|
| Pipeline funcional ponta-a-ponta | `POST /api/evaluate` executa os cinco módulos em < 200ms (sintético) e retorna estrutura completa |
| Cobertura OWASP parcial real | LLM01, LLM06 e LLM08 têm detecções ativas com mapeamento automático |
| Conformidade com LGPD | Mascaramento automático de PII e geração de `compliance_notes` referenciando Art. 46 |
| Auditoria completa | Cada avaliação produz `audit_id` único persistido no banco |
| Distinção honesta synthetic/live | Coluna `source_type` permite operar com dados reais e demonstrativos coexistindo |
| RBAC funcional | Endpoints administrativos (ex.: seed) protegidos por `require_role(["admin"])` |
| UI consistente | Banner de aviso de dados sintéticos visível no dashboard, sem ocultar a origem |

---

## 9. Limitações honestas

| Limitação | Impacto na leitura dos resultados |
|-----------|-----------------------------------|
| Dataset gerado pela mesma equipe que projeta o detector | Métricas devem ser lidas como limite superior |
| Sem ground-truth externo | Recall verdadeiro impossível de calcular |
| Sem teste adversarial ativo | Resistência a obfuscação não foi mensurada |
| Latências sintetizadas | Latência média reportada é ilustrativa, não medida |
| Volume pequeno (~500 logs) | Variância alta entre execuções |
| Mock LLM | Sem ruído de saída real do modelo |
| Sem comparação com baseline | Não há contraste com NeMo Guardrails, Guardrails AI ou outras soluções |
| FSM in-memory | Estado de sessão zera em restart |
| Sem testes automatizados | Validação foi manual, sem suíte pytest/vitest |

Cada uma dessas limitações está documentada no
[backlog acadêmico](./05-LIMITACOES-E-PROXIMOS-PASSOS.md) com indicação
de como pode ser endereçada em uma evolução do trabalho.

---

## 10. Considerações Finais

O protótipo Phoenix LLM Trust & Safety Framework, na fase pré-VM,
demonstra a viabilidade arquitetural de uma camada de segurança
desacoplada para sistemas que utilizam LLMs. As cinco peças
funcionais (InputGuard, OutputGuard, SessionWatch, Risk Aggregator e
Data Exposure Mirror) operam em conjunto, persistem auditoria
completa em banco relacional, expõem API consumível por qualquer
sistema externo e renderizam evidências em um dashboard moderno e
interpretável.

Os resultados não devem ser interpretados como evidência de
**eficácia em produção** — o ambiente de teste é controlado, o
dataset é sintético, o LLM é mock, e a equipe que constrói o detector
é a mesma que constrói os ataques. Esses pontos são reconhecidos
explicitamente como limitações metodológicas, e estão alinhados com
o escopo declarado de um TCC focado em **arquitetura demonstrável**.

A principal contribuição do trabalho, do ponto de vista acadêmico,
está menos nas métricas absolutas e mais em três aspectos
arquiteturais: a separação clara de responsabilidades entre os
guards, o módulo Data Exposure Mirror como abordagem complementar à
detecção tradicional de PII, e a integração explícita com frameworks
de conformidade (OWASP, NIST, LGPD) por meio de mapeamento
automático no fluxo de avaliação.

Os próximos passos, descritos no documento de limitações, focam em
três frentes: substituir as regras determinísticas por classificadores
ML calibrados, adicionar baseline comparativo com soluções
existentes, e migrar o estado de sessão para um backend persistente
distribuído. Essas evoluções são naturais para uma versão pós-TCC,
sem implicar refatoração arquitetural.
