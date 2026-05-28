# Risk Score

O Risk Score e a metrica operacional central do prototipo. Ele consolida sinais de entrada, saida e sessao em uma escala de 0 a 100.

## Componentes

| Componente | Peso | Origem |
|---|---:|---|
| InputGuard | 45% | Padroes de prompt injection, jailbreak, exfiltracao, segredo e abuso de ferramenta |
| OutputGuard | 30% | PII, dados sensiveis e saida insegura |
| SessionWatch | 25% | Escalada multi-turn, repeticao de ataques e estado da sessao |

## Faixas

| Score | Nivel | Interpretacao |
|---:|---|---|
| 0-29 | LOW | Interacao aparentemente segura |
| 30-59 | MEDIUM | Sinais moderados; revisar contexto |
| 60-79 | HIGH | Atividade suspeita |
| 80-100 | CRITICAL | Ataque ou vazamento provavel; bloquear ou alertar |

## Uso no sistema

- Dashboard mostra score medio e eventos criticos.
- Logs persistem `risk_score`, `risk_level`, categorias OWASP e labels.
- `/owasp` usa score medio por categoria para severidade observada.
- Alertas usam score para priorizacao operacional.
