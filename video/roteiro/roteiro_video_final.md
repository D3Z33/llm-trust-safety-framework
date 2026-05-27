# Roteiro do Video Final

Projeto: LLM Trust & Safety Framework  
Disciplina: Cyber Defense Project  
Instituicao: Faculdade Impacta  
Professor: Ricardo Amorim  
Periodo: 2025-2026

## 1. Abertura

Apresentar o projeto, a equipe LLM Trust e o objetivo geral: propor uma arquitetura de guardrails para seguranca, privacidade e governanca em aplicacoes baseadas em modelos de linguagem.

## 2. Contexto e problema

Explicar que a IA generativa passou a ser usada em chatbots, copilotos, automacao e analise documental, criando uma nova superficie de ataque. Destacar riscos como prompt injection, vazamento de dados sensiveis e manipulacao de sessoes.

## 3. Solucao e arquitetura

Apresentar o fluxo conceitual:

```text
Usuario -> Aplicacao -> InputGuard -> LLM -> OutputGuard -> Resposta
```

Explicar que SessionWatch, Risk Score e Dashboard atuam em paralelo para observar contexto, consolidar sinais e apoiar auditoria.

## 4. Modulos principais

- InputGuard: analise preventiva da entrada.
- OutputGuard: avaliacao da resposta gerada.
- SessionWatch: acompanhamento do comportamento da conversa.
- Risk Score: classificacao do risco em escala de 0 a 100.
- Dashboard: visibilidade para auditoria e governanca.
- Data Exposure Mirror: conscientizacao sobre exposicao indireta de dados.

## 5. Demonstracao do sistema

Mostrar tres cenarios:

1. Prompt Injection
2. Dados sensiveis
3. Sessao suspeita

Durante a demonstracao, reforcar que o MVP e academico e demonstrativo.

## 6. Conclusao

Fechar destacando que seguranca em IA precisa ir alem do modelo. A proposta atua como camada complementar para reduzir riscos, registrar eventos e apoiar governanca.

## Divisao individual

Os textos individuais estao organizados nos arquivos:

- `andrey.txt`
- `paulo.txt`
- `renes.txt`
- `renan.txt`

