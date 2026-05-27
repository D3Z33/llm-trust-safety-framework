# LLM Trust & Safety Framework

Projeto academico desenvolvido para a disciplina Cyber Defense Project da Faculdade Impacta, com foco em seguranca, privacidade e governanca para aplicacoes baseadas em Large Language Models.

O LLM Trust & Safety Framework propoe uma arquitetura de guardrails para avaliar riscos conversacionais antes, durante e depois da interacao com modelos de linguagem. A proposta tem carater academico e utiliza um prototipo demonstrativo para ilustrar conceitos de controle, auditoria e reducao de risco.

## Objetivo

Organizar uma camada complementar de confianca para aplicacoes com IA generativa, permitindo analisar entradas, respostas e contexto de sessao com criterios de seguranca, privacidade e governanca.

## Problema abordado

Modelos de linguagem podem ser expostos a prompt injection, vazamento de dados sensiveis, manipulacao de contexto, exfiltracao indireta de informacoes e ausencia de rastreabilidade operacional. O projeto aborda esses riscos por meio de modulos especializados e uma pontuacao de risco consolidada.

## Modulos principais

- InputGuard: avalia entradas do usuario antes do envio ao modelo.
- OutputGuard: identifica riscos na resposta gerada, incluindo dados sensiveis.
- SessionWatch: observa o comportamento ao longo da conversa.
- Risk Score: consolida sinais em uma escala operacional de 0 a 100.
- Dashboard: apoia auditoria, visibilidade e acompanhamento dos eventos.
- Data Exposure Mirror: demonstra inferencias e exposicoes indiretas percebidas na interacao.

## Alinhamento de governanca

O projeto considera referencias de seguranca, privacidade, IA responsavel e governanca:

- OWASP LLM Top 10
- NIST AI RMF
- ISO/IEC 42001
- ISO/IEC 27001
- ISO/IEC 23894
- ISO/IEC 27701
- CIS Controls
- LGPD

## Estrutura do repositorio

```text
docs/       Relatorio final, fontes academicas e QA do PDF.
slides/     Apresentacao final, exportacao em PDF e QA dos slides.
video/      Roteiro do video e espaco para entrega final.
prototype/  Area reservada para o codigo do prototipo demonstrativo.
scripts/    Validacao de artefatos, manifesto e scripts de geracao usados.
archive/    Copias preservadas dos arquivos originais recebidos.
```

## Artefatos finais

- Relatorio final: `docs/report/final/llm_trust_safety_framework_relatorio_final.pdf`
- Apresentacao final: `slides/final/llm_trust_safety_framework_apresentacao_final.pptx`
- Apresentacao em PDF: `slides/final/llm_trust_safety_framework_apresentacao_final.pdf`
- Checklist de entrega: `DELIVERY_CHECKLIST.md`
- Manifesto de artefatos: `ARTIFACT_MANIFEST.md`

## Status do projeto

Status atual: artefatos finais de documentacao e apresentacao organizados para versionamento.

O codigo completo do prototipo demonstrativo sera adicionado posteriormente em `prototype/`.

## Integrantes

- Andrey Senra Jacinto
- Paulo Patrick da Silva
- Renan Rocha dos Reis
- Renes Vale Moreira

Professor: Ricardo Amorim  
Instituicao: Faculdade Impacta  
Disciplina: Cyber Defense Project  
Periodo: 2025-2026

## Validacao local

```bash
python scripts/generate_manifest.py
python scripts/validate_artifacts.py
```

