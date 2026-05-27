# Artifact Generator

Esta pasta contem a camada de geracao, organizacao e entrega dos artefatos academicos do projeto LLM Trust & Safety Framework.

Ela nao representa o codigo completo do sistema. O prototipo demonstrativo ficara na pasta `../prototype/`.

## Conteudo

```text
docs/       Relatorio final, fontes academicas e QA do PDF.
slides/     Apresentacao final, exportacao em PDF e QA dos slides.
video/      Roteiro do video e espaco para entrega final.
scripts/    Validacao de artefatos, manifesto e scripts de geracao.
archive/    Copias preservadas dos arquivos originais recebidos.
```

## Artefatos finais

- Relatorio final: `docs/report/final/llm_trust_safety_framework_relatorio_final.pdf`
- Apresentacao final: `slides/final/llm_trust_safety_framework_apresentacao_final.pptx`
- Apresentacao em PDF: `slides/final/llm_trust_safety_framework_apresentacao_final.pdf`
- Checklist de entrega: `DELIVERY_CHECKLIST.md`
- Manifesto de artefatos: `ARTIFACT_MANIFEST.md`

## Scripts principais

Rodando a partir da raiz do repositorio:

```bash
python artifact-generator/scripts/validate_artifacts.py
python artifact-generator/scripts/generate_manifest.py
```

Rodando a partir desta pasta:

```bash
python scripts/validate_artifacts.py
python scripts/generate_manifest.py
```

## Status

Status atual: artefatos finais de documentacao, apresentacao, QA e roteiro organizados para versionamento.

O material tem carater academico e demonstrativo. Nao deve ser tratado como produto final de mercado.

