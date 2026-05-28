# OWASP Mapping

Referencia usada: OWASP Top 10 for LLM Applications 2025, conforme lista publica em `https://genai.owasp.org/llm-top-10/`.

O prototipo normaliza categorias historicas usadas no codigo para a nomenclatura 2025 na tela `/owasp` e nos endpoints de cobertura.

| Categoria OWASP 2025 | Cobertura no prototipo | Modulos relacionados |
|---|---|---|
| LLM01: Prompt Injection | Implementada | InputGuard, SessionWatch, Risk Score, Dashboard |
| LLM02: Sensitive Information Disclosure | Implementada | OutputGuard, Data Exposure Mirror, Logs, Risk Score |
| LLM03: Supply Chain | Documentada | Dashboard, Policies, documentacao |
| LLM04: Data and Model Poisoning | Parcial | Threat Intelligence, InputGuard, Dashboard |
| LLM05: Improper Output Handling | Implementada | OutputGuard, Risk Score, Logs |
| LLM06: Excessive Agency | Parcial | SessionWatch, Policies, Risk Score |
| LLM07: System Prompt Leakage | Implementada | InputGuard, OutputGuard, Logs |
| LLM08: Vector and Embedding Weaknesses | Documentada | Dashboard, documentacao |
| LLM09: Misinformation | Documentada | Dashboard, Policies, revisao humana |
| LLM10: Unbounded Consumption | Parcial | SessionWatch, Risk Score, rate-limit configuration |

## Aliases de compatibilidade

Alguns dados sinteticos e regras antigas usam nomes anteriores. O backend converte esses aliases para a lista 2025:

| Alias legado | Categoria 2025 |
|---|---|
| LLM02:InsecureOutputHandling | LLM05:ImproperOutputHandling |
| LLM03:TrainingDataPoisoning | LLM04:DataAndModelPoisoning |
| LLM04:ModelDenialOfService | LLM10:UnboundedConsumption |
| LLM05:SupplyChainVulnerabilities | LLM03:SupplyChain |
| LLM06:SensitiveInformationDisclosure | LLM02:SensitiveInformationDisclosure |
| LLM07:InsecurePluginDesign | LLM06:ExcessiveAgency |
| LLM08:ExcessiveAgency | LLM06:ExcessiveAgency |
| LLM09:Overreliance | LLM09:Misinformation |
| LLM10:ModelTheft | LLM10:UnboundedConsumption |

## Decisao de nomenclatura

A UI principal passa a exibir a lista OWASP LLM Top 10 2025. O codigo preserva aliases antigos para nao perder evidencias ja gravadas no banco demonstrativo.
