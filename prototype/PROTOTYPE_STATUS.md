# PROTOTYPE_STATUS

## Stack

- Frontend: React 18, Vite, Tailwind CSS, React Router, Axios, Recharts, lucide-react.
- Backend: FastAPI, SQLAlchemy async, SQLite, JWT, Pydantic Settings.
- Infra opcional: Docker Compose e nginx.

## Funcionalidades implementadas

- Login JWT e RBAC basico.
- Dashboard com KPIs de risco, cobertura OWASP, alertas e eventos recentes.
- Avaliacao de prompt com InputGuard, OutputGuard, SessionWatch e Risk Score.
- Logs de auditoria com categorias OWASP e trilha de evidencias.
- Sessoes com estado operacional e historico.
- Alertas, politicas, threat intelligence e conformidade.
- Guia `/owasp` com mapeamento OWASP LLM Top 10, fallback estatico e relacao com modulos.
- Data Exposure Mirror demonstrativo.

## Funcionalidades parciais

- Cobertura de supply chain, RAG/vector risks, misinformation e consumo ilimitado e principalmente documental/demonstrativa.
- SessionWatch usa estado em memoria.
- Rate limiting esta configurado, mas nao foi validado como middleware completo.
- Provider LLM real e opcional; modo padrao e mock.

## Limitacoes

- Projeto academico/demonstrativo, nao pronto para producao.
- Deteccoes principais sao baseadas em regras e regex.
- Sem suite automatizada de testes cadastrada.
- Banco SQLite local e dataset sintetico.
- Algumas categorias historicas usam nomenclatura OWASP antiga; o endpoint `/api/owasp/details` normaliza aliases para a lista 2025.

## Correcoes recentes

- Corrigida falha de import do backend quando a variavel global `DEBUG` chega como `release`.
- Corrigido comportamento da guia `/owasp` para nao ficar presa em carregamento quando a API falha.
- Atualizado mapeamento visual para `OWASP LLM Top 10 Mapping` com lista 2025 e status por modulo.

## Proximos passos

- Adicionar testes automatizados de API e componentes frontend.
- Persistir SessionWatch em banco ou cache externo.
- Implementar middleware de rate limit.
- Expandir cobertura RAG/vector e supply chain.
- Gerar screenshots finais para `screenshots/`.
