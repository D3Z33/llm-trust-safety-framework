import { useEffect, useState } from 'react'
import { dashboardAPI } from '../utils/api'
import { LoadingSpinner, toast } from '../components/ui'
import {
  Shield, AlertTriangle, CheckCircle, Info, Target, BarChart2, BookOpen,
  Activity, Clock, Globe, ShieldAlert
} from 'lucide-react'

// ── Configuração visual por severidade ────────────────────────────────────
const SEV_CFG = {
  'Crítico':         { color: '#ef4444', bg: 'bg-red-500/10',    border: 'border-red-500/30',    label: 'CRÍTICO' },
  'Alto':            { color: '#f97316', bg: 'bg-orange-500/10', border: 'border-orange-500/30', label: 'ALTO' },
  'Médio':           { color: '#f59e0b', bg: 'bg-yellow-500/10', border: 'border-yellow-500/30', label: 'MÉDIO' },
  'Baixo':           { color: '#22c55e', bg: 'bg-green-500/10',  border: 'border-green-500/30',  label: 'BAIXO' },
  'Critico':          { color: '#ef4444', bg: 'bg-red-500/10',    border: 'border-red-500/30',    label: 'CRITICO' },
  'Medio':            { color: '#f59e0b', bg: 'bg-yellow-500/10', border: 'border-yellow-500/30', label: 'MEDIO' },
  'Sem ocorrencias':  { color: '#64748b', bg: 'bg-gray-500/10',   border: 'border-gray-500/30',   label: 'SEM OCORRENCIAS' },
  'Sem ocorrências': { color: '#64748b', bg: 'bg-gray-500/10',   border: 'border-gray-500/30',   label: 'SEM OCORRÊNCIAS' },
}

const ID_ICONS = {
  LLM01: '💉', LLM02: '🔓', LLM03: '🕵️', LLM04: '⏸',
  LLM05: '⛓️', LLM06: '📋', LLM07: '🧩', LLM08: '🤖',
  LLM09: '🤝', LLM10: '🗝️',
}

// ── Sparkline simples (SVG inline) ────────────────────────────────────────
const MODULE_COVERAGE = [
  { name: 'InputGuard', status: 'Implemented', coverage: 'LLM01, LLM07', detail: 'Detects prompt injection, jailbreaks, credential requests, and system-prompt disclosure attempts.' },
  { name: 'OutputGuard', status: 'Implemented', coverage: 'LLM02, LLM05, LLM07', detail: 'Masks PII and sanitizes model output before it reaches the user interface.' },
  { name: 'SessionWatch', status: 'Partial', coverage: 'LLM01, LLM06, LLM10', detail: 'Tracks multi-turn risk escalation and suspicious session patterns.' },
  { name: 'Risk Score', status: 'Implemented', coverage: 'All categories', detail: 'Aggregates input, output, and session signals into a 0-100 operational score.' },
  { name: 'Dashboard', status: 'Implemented', coverage: 'All categories', detail: 'Shows coverage, incidents, blocked events, alerts, and compliance evidence.' },
  { name: 'Data Exposure Mirror', status: 'Implemented', coverage: 'LLM02', detail: 'Highlights progressive exposure of sensitive personal or corporate data.' },
]

const FALLBACK_CATEGORIES = [
  ['LLM01:PromptInjection', 'Prompt Injection', 'InputGuard + SessionWatch', 'Critico', ['InputGuard', 'SessionWatch', 'Risk Score']],
  ['LLM02:SensitiveInformationDisclosure', 'Sensitive Information Disclosure', 'OutputGuard + Data Exposure Mirror', 'Critico', ['OutputGuard', 'Data Exposure Mirror']],
  ['LLM03:SupplyChain', 'Supply Chain', 'Dependency review + documentation', 'Alto', ['Dashboard', 'Policies']],
  ['LLM04:DataAndModelPoisoning', 'Data and Model Poisoning', 'Threat Intel + dataset governance', 'Alto', ['Threat Intelligence', 'Dashboard']],
  ['LLM05:ImproperOutputHandling', 'Improper Output Handling', 'OutputGuard + response sanitization', 'Alto', ['OutputGuard', 'Risk Score']],
  ['LLM06:ExcessiveAgency', 'Excessive Agency', 'SessionWatch + policy review', 'Alto', ['SessionWatch', 'Policies']],
  ['LLM07:SystemPromptLeakage', 'System Prompt Leakage', 'InputGuard + OutputGuard', 'Alto', ['InputGuard', 'OutputGuard']],
  ['LLM08:VectorAndEmbeddingWeaknesses', 'Vector and Embedding Weaknesses', 'RAG controls documented for next iteration', 'Medio', ['Documentation', 'Dashboard']],
  ['LLM09:Misinformation', 'Misinformation', 'Dashboard evidence + human review guidance', 'Medio', ['Dashboard', 'Risk Score']],
  ['LLM10:UnboundedConsumption', 'Unbounded Consumption', 'SessionWatch + rate-limit configuration', 'Alto', ['SessionWatch', 'Risk Score']],
]

const FALLBACK_DESCRIPTIONS = {
  LLM01: 'Malicious or indirect inputs attempt to override instructions or redirect the model behavior.',
  LLM02: 'Sensitive personal, corporate, credential, or system-prompt data may be exposed.',
  LLM03: 'Third-party models, plugins, datasets, or libraries introduce supply-chain risk.',
  LLM04: 'Training, fine-tuning, embedding, or knowledge-base data may be manipulated.',
  LLM05: 'Model output is used without enough validation, sanitization, or downstream control.',
  LLM06: 'The LLM application receives more permissions or autonomy than required.',
  LLM07: 'Hidden system instructions or guardrail configuration can be disclosed.',
  LLM08: 'RAG, vectors, and embeddings can leak or retrieve unsafe context.',
  LLM09: 'Unsupported or inaccurate model output is trusted without adequate review.',
  LLM10: 'Attackers abuse token, inference, rate, context, or cost boundaries.',
}

function buildFallbackDetails(days) {
  return {
    janela_dias: days,
    total_categorias: FALLBACK_CATEGORIES.length,
    categorias_com_ocorrencia: 0,
    total_eventos: 0,
    detalhes: FALLBACK_CATEGORIES.map(([categoria, nome, controle, severidade, modulos]) => {
      const id = categoria.split(':')[0]
      return {
        categoria,
        id,
        nome_pt: nome,
        descricao_pt: FALLBACK_DESCRIPTIONS[id],
        controle,
        severidade_padrao: severidade,
        severidade_observada: 'Sem ocorrencias',
        total_eventos: 0,
        total_bloqueados: 0,
        taxa_bloqueio: 0,
        score_medio: 0,
        top_app: 'demo',
        top_app_count: 0,
        tendencia: [],
        exemplos: [],
        ultimo_evento: null,
        modulos_relacionados: modulos,
        status_cobertura: ['LLM08', 'LLM09'].includes(id) ? 'Documented' : 'Implemented',
      }
    }),
  }
}

function Sparkline({ data, color }) {
  if (!data || data.length === 0) return null
  const max = Math.max(...data.map(d => d.total), 1)
  const w = 96, h = 28
  const stepX = w / Math.max(data.length - 1, 1)
  const path = data.map((d, i) => {
    const x = i * stepX
    const y = h - (d.total / max) * (h - 4) - 2
    return `${i === 0 ? 'M' : 'L'} ${x.toFixed(1)} ${y.toFixed(1)}`
  }).join(' ')
  return (
    <svg width={w} height={h} className="overflow-visible">
      <path d={path} stroke={color} strokeWidth="1.6" fill="none" strokeLinecap="round" strokeLinejoin="round" />
      {data.map((d, i) => (
        <circle key={i} cx={i * stepX} cy={h - (d.total / max) * (h - 4) - 2}
                r={d.total > 0 ? 1.6 : 0} fill={color} />
      ))}
    </svg>
  )
}

export default function OWASPPage() {
  const [details, setDetails] = useState(null)
  const [loading, setLoading] = useState(true)
  const [apiWarning, setApiWarning] = useState('')
  const [days, setDays] = useState(30)
  const [tab, setTab] = useState('categorias')
  const [selected, setSelected] = useState(null)

  useEffect(() => {
    setLoading(true)
    setApiWarning('')
    dashboardAPI.getOWASPDetails(days)
      .then(r => setDetails(r.data))
      .catch(() => {
        setDetails(buildFallbackDetails(days))
        setApiWarning('API unavailable: showing demonstrative OWASP mapping with static coverage status.')
        toast('Erro ao carregar detalhes OWASP; exibindo mapeamento demonstrativo.', 'error')
      })
      .finally(() => setLoading(false))
  }, [days])

  if (loading) return <LoadingSpinner text="Carregando analise OWASP LLM Top 10..." />

  const safeDetails = details || buildFallbackDetails(days)
  const categorias = safeDetails.detalhes || []
  const total = safeDetails.total_eventos || 0
  const cobertas = safeDetails.categorias_com_ocorrencia || 0
  const cobertaPct = Math.round((cobertas / Math.max(categorias.length, 1)) * 100)
  const totalBloqueado = categorias.reduce((s, c) => s + c.total_bloqueados, 0)
  const maxEventos = Math.max(...categorias.map(c => c.total_eventos), 1)
  const ranking = [...categorias].sort((a, b) => b.total_eventos - a.total_eventos)

  return (
    <div className="p-6 space-y-6 bg-gray-950 min-h-screen">
      {/* Header */}
      <div className="flex items-start justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Target className="w-6 h-6 text-orange-400" />
            OWASP LLM Top 10 Mapping
          </h1>
          <p className="text-gray-400 text-sm mt-1">
            Coverage view for the 2025 OWASP LLM categories, connected to runtime guards, risk scoring, sessions, and data exposure controls.
          </p>
        </div>
        <div className="flex items-center gap-2">
          {[7, 30, 90].map(d => (
            <button key={d} onClick={() => setDays(d)}
              className={`text-xs font-semibold px-3 py-1.5 rounded-lg border transition-colors ${
                days === d
                  ? 'bg-blue-500/15 border-blue-500/40 text-blue-300'
                  : 'bg-gray-900 border-gray-800 text-gray-400 hover:text-white'
              }`}>
              {d}d
            </button>
          ))}
        </div>
      </div>

      {apiWarning && (
        <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-xl px-4 py-3 text-xs text-yellow-200">
          {apiWarning}
        </div>
      )}

      {/* Hero */}
      <div className="bg-gradient-to-r from-blue-900/20 via-purple-900/10 to-orange-900/10 border border-blue-500/20 rounded-2xl p-5">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <p className="text-[10px] uppercase tracking-widest text-gray-500 font-bold mb-1">Cobertura observada</p>
            <p className="text-3xl font-black text-white">
              {cobertas}<span className="text-lg text-gray-500">/{categorias.length}</span>
            </p>
            <div className="h-1.5 bg-gray-800 rounded-full overflow-hidden mt-2">
              <div className="h-full rounded-full bg-gradient-to-r from-blue-500 to-purple-500"
                   style={{ width: `${cobertaPct}%` }} />
            </div>
            <p className="text-[10px] text-gray-500 mt-1.5">{cobertaPct}% das categorias com ao menos 1 ocorrência</p>
          </div>
          <div>
            <p className="text-[10px] uppercase tracking-widest text-gray-500 font-bold mb-1">Eventos correlacionados</p>
            <p className="text-3xl font-black text-blue-400">{total.toLocaleString()}</p>
            <p className="text-[10px] text-gray-500 mt-1">Logs com ao menos uma categoria atribuída</p>
          </div>
          <div>
            <p className="text-[10px] uppercase tracking-widest text-gray-500 font-bold mb-1">Eventos bloqueados</p>
            <p className="text-3xl font-black text-red-400">{totalBloqueado.toLocaleString()}</p>
            <p className="text-[10px] text-gray-500 mt-1">
              {total > 0 ? Math.round(totalBloqueado / total * 100) : 0}% da incidência
            </p>
          </div>
          <div>
            <p className="text-[10px] uppercase tracking-widest text-gray-500 font-bold mb-1">Frameworks correlacionados</p>
            <div className="flex flex-wrap gap-1.5 mt-2">
              {['NIST AI RMF', 'ISO/IEC 42001', 'ISO/IEC 27001', 'LGPD'].map(f => (
                <span key={f} className="text-[10px] bg-gray-900/60 text-blue-300 border border-blue-500/25 px-2 py-0.5 rounded-full font-medium">
                  {f}
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
        {MODULE_COVERAGE.map((module) => (
          <div key={module.name} className="bg-gray-900 border border-gray-800 rounded-xl p-4">
            <div className="flex items-start justify-between gap-3">
              <div>
                <h3 className="text-sm font-bold text-white">{module.name}</h3>
                <p className="text-[11px] text-gray-400 mt-1 leading-relaxed">{module.detail}</p>
              </div>
              <span className={`text-[9px] font-bold px-2 py-0.5 rounded-full border ${
                module.status === 'Implemented'
                  ? 'bg-green-500/10 border-green-500/30 text-green-300'
                  : 'bg-yellow-500/10 border-yellow-500/30 text-yellow-300'
              }`}>
                {module.status}
              </span>
            </div>
            <p className="text-[10px] uppercase tracking-widest text-gray-500 font-bold mt-3">Coverage</p>
            <p className="text-xs text-blue-300 mt-1">{module.coverage}</p>
          </div>
        ))}
      </div>

      {/* Tabs */}
      <div className="flex gap-1 bg-gray-900 border border-gray-800 rounded-lg p-1 w-fit">
        {[
          { key: 'categorias',  label: 'Categorias',  icon: Shield },
          { key: 'ranking',     label: 'Ranking',     icon: BarChart2 },
          { key: 'compliance',  label: 'Conformidade', icon: BookOpen },
        ].map(({ key, label, icon: Icon }) => (
          <button key={key} onClick={() => setTab(key)}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-medium transition-all ${
              tab === key ? 'bg-gray-800 text-white' : 'text-gray-500 hover:text-gray-300'
            }`}>
            <Icon className="w-3.5 h-3.5" />
            {label}
          </button>
        ))}
      </div>

      {/* Tab: Categorias */}
      {tab === 'categorias' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
          {categorias.map(cat => {
            const sev = SEV_CFG[cat.severidade_observada] || SEV_CFG['Sem ocorrências']
            const sevPad = SEV_CFG[cat.severidade_padrao] || SEV_CFG['Médio']
            const isOpen = selected === cat.categoria
            return (
              <div key={cat.categoria}
                className={`bg-gray-900 border rounded-xl overflow-hidden transition-all ${sev.border}`}>
                <button onClick={() => setSelected(isOpen ? null : cat.categoria)}
                  className="w-full text-left p-4 hover:bg-gray-800/30 transition-colors">
                  <div className="flex items-start gap-3">
                    {/* Ícone + ID */}
                    <div className={`w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0 text-xl ${sev.bg} border ${sev.border}`}>
                      {ID_ICONS[cat.id] || '🛡️'}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-baseline justify-between gap-2 flex-wrap">
                        <div>
                          <span className="font-mono text-[10px] text-gray-500">{cat.id}</span>
                          <h3 className="text-sm font-bold text-white leading-tight">{cat.nome_pt}</h3>
                        </div>
                        <div className="flex items-center gap-1.5 flex-wrap">
                          <span className={`text-[9px] font-bold px-2 py-0.5 rounded-full border ${sev.bg} ${sev.border}`}
                            style={{ color: sev.color }}>
                            {sev.label}
                          </span>
                        </div>
                      </div>
                      <p className="text-[11px] text-gray-400 leading-relaxed mt-1.5 line-clamp-2">
                        {cat.descricao_pt}
                      </p>
                      {/* Linha de métricas */}
                      <div className="flex items-center gap-3 mt-3 flex-wrap">
                        <span className="text-[10px] text-gray-500 flex items-center gap-1">
                          <Activity className="w-3 h-3" />
                          <span className="font-bold text-gray-200">{cat.total_eventos}</span> eventos
                        </span>
                        <span className="text-[10px] text-gray-500 flex items-center gap-1">
                          <ShieldAlert className="w-3 h-3" />
                          <span className="font-bold text-red-400">{cat.total_bloqueados}</span> bloq.
                        </span>
                        <span className="text-[10px] text-gray-500 flex items-center gap-1">
                          score
                          <span className="font-bold tabular-nums" style={{ color: sev.color }}>
                            {cat.score_medio.toFixed(1)}
                          </span>
                        </span>
                        <div className="ml-auto">
                          <Sparkline data={cat.tendencia} color={sev.color} />
                        </div>
                      </div>
                    </div>
                  </div>
                </button>

                {/* Drill-down */}
                {isOpen && (
                  <div className="px-4 pb-4 border-t border-gray-800/60 pt-3 space-y-3 text-xs">
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                      <div className="bg-gray-800/50 rounded-lg p-2.5">
                        <p className="text-[9px] uppercase tracking-widest text-gray-500">Severidade padrão</p>
                        <p className="text-xs font-bold" style={{ color: sevPad.color }}>{cat.severidade_padrao}</p>
                      </div>
                      <div className="bg-gray-800/50 rounded-lg p-2.5">
                        <p className="text-[9px] uppercase tracking-widest text-gray-500">Severidade observada</p>
                        <p className="text-xs font-bold" style={{ color: sev.color }}>{cat.severidade_observada}</p>
                      </div>
                      <div className="bg-gray-800/50 rounded-lg p-2.5">
                        <p className="text-[9px] uppercase tracking-widest text-gray-500">Taxa de bloqueio</p>
                        <p className="text-xs font-bold text-orange-300">{cat.taxa_bloqueio.toFixed(1)}%</p>
                      </div>
                      <div className="bg-gray-800/50 rounded-lg p-2.5">
                        <p className="text-[9px] uppercase tracking-widest text-gray-500">Top app</p>
                        <p className="text-xs font-bold text-blue-300 truncate">
                          {cat.top_app}
                          {cat.top_app_count ? <span className="text-gray-500 font-normal"> ({cat.top_app_count})</span> : null}
                        </p>
                      </div>
                    </div>

                    <div>
                      <p className="text-[10px] uppercase tracking-widest text-gray-500 font-bold mb-1">Controle implementado</p>
                      <p className="text-[11px] text-gray-300 bg-gray-800/40 px-3 py-1.5 rounded-lg border border-gray-700/40">
                        <Shield className="w-3 h-3 inline mr-1.5 text-blue-400" />
                        {cat.controle}
                      </p>
                    </div>

                    <div>
                      <p className="text-[10px] uppercase tracking-widest text-gray-500 font-bold mb-1">Related modules</p>
                      <div className="flex flex-wrap gap-1.5">
                        {(cat.modulos_relacionados || []).map((module) => (
                          <span key={module} className="text-[10px] bg-blue-500/10 text-blue-300 border border-blue-500/25 px-2 py-0.5 rounded-full font-medium">
                            {module}
                          </span>
                        ))}
                        {cat.status_cobertura && (
                          <span className="text-[10px] bg-gray-800 text-gray-300 border border-gray-700 px-2 py-0.5 rounded-full font-medium">
                            {cat.status_cobertura}
                          </span>
                        )}
                      </div>
                    </div>

                    {cat.exemplos?.length > 0 && (
                      <div>
                        <p className="text-[10px] uppercase tracking-widest text-gray-500 font-bold mb-1.5">
                          Eventos recentes ({cat.exemplos.length})
                        </p>
                        <div className="space-y-1.5">
                          {cat.exemplos.map(ex => (
                            <div key={ex.audit_id} className={`bg-gray-950 border rounded-lg p-2 ${
                              ex.blocked ? 'border-red-500/25' : 'border-gray-800'
                            }`}>
                              <div className="flex items-center justify-between gap-2 text-[9px] text-gray-500 mb-1">
                                <span className="font-mono">{ex.app_name || '—'}</span>
                                <span className="flex items-center gap-2">
                                  <span className="font-bold tabular-nums" style={{ color: sev.color }}>
                                    {ex.risk_score.toFixed(0)}
                                  </span>
                                  {ex.blocked && (
                                    <span className="text-red-400 font-bold">BLOQ</span>
                                  )}
                                </span>
                              </div>
                              <p className="text-[11px] text-gray-300 leading-relaxed line-clamp-2">{ex.prompt}</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {cat.ultimo_evento && (
                      <p className="text-[10px] text-gray-500 flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        Última ocorrência: <span className="font-mono text-gray-300">{new Date(cat.ultimo_evento).toLocaleString('pt-BR')}</span>
                      </p>
                    )}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}

      {/* Tab: Ranking */}
      {tab === 'ranking' && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 space-y-3">
          <h3 className="text-sm font-bold text-white mb-3">
            Incidência por categoria — janela de {days} dias
          </h3>
          {ranking.map(cat => {
            const sev = SEV_CFG[cat.severidade_observada] || SEV_CFG['Sem ocorrências']
            const pct = Math.round((cat.total_eventos / maxEventos) * 100)
            return (
              <div key={cat.categoria} className="grid grid-cols-12 items-center gap-2 text-xs">
                <span className="col-span-2 font-mono text-[10px] text-gray-500">{cat.id}</span>
                <span className="col-span-3 text-gray-300 truncate">{cat.nome_pt}</span>
                <div className="col-span-5 bg-gray-800 rounded-full h-2 overflow-hidden">
                  <div className="h-full rounded-full" style={{ width: `${pct}%`, backgroundColor: sev.color }} />
                </div>
                <span className="col-span-1 font-bold tabular-nums text-right" style={{ color: cat.total_eventos ? sev.color : '#4b5563' }}>
                  {cat.total_eventos}
                </span>
                <span className="col-span-1 text-[10px] text-gray-500 text-right">
                  {cat.total_bloqueados ? `${cat.total_bloqueados} bloq.` : '—'}
                </span>
              </div>
            )
          })}
        </div>
      )}

      {/* Tab: Conformidade */}
      {tab === 'compliance' && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
          <h3 className="text-sm font-bold text-white mb-4 flex items-center gap-2">
            <Info className="w-4 h-4 text-blue-400" />
            Mapeamento de conformidade da plataforma
          </h3>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="text-left text-gray-500 border-b border-gray-800">
                  <th className="pb-2 font-medium w-32">Framework</th>
                  <th className="pb-2 font-medium w-32">Função / Controle</th>
                  <th className="pb-2 font-medium">Implementação</th>
                  <th className="pb-2 font-medium w-20 text-center">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-800/50">
                {[
                  { fw: 'NIST AI RMF',    fn: 'GOVERN',                desc: 'Trilha de auditoria completa por audit_id; políticas versionadas', ok: true },
                  { fw: 'NIST AI RMF',    fn: 'MAP',                   desc: 'InputGuard e SessionWatch mapeiam riscos por interação',           ok: true },
                  { fw: 'NIST AI RMF',    fn: 'MEASURE',               desc: 'Risk Score 0–100 consolidado por prompt e por sessão',             ok: true },
                  { fw: 'NIST AI RMF',    fn: 'MANAGE',                desc: 'Bloqueio automático, sanitização, alertas e webhook de plantão',   ok: true },
                  { fw: 'ISO/IEC 42001',  fn: 'AIMS',                  desc: 'Sistema de gestão de IA com controles documentados em /politicas', ok: true },
                  { fw: 'ISO/IEC 27001',  fn: 'A.8 — DLP',             desc: 'OutputGuard mascara PII antes da entrega',                          ok: true },
                  { fw: 'ISO/IEC 27001',  fn: 'A.12 — Auditoria',      desc: 'Trilha persistente com session_id + audit_id',                      ok: true },
                  { fw: 'LGPD',           fn: 'Art. 6º — Minimização', desc: 'Data Exposure Mirror sinaliza coleta excessiva durante a sessão',   ok: true },
                  { fw: 'LGPD',           fn: 'Art. 46 — Segurança',    desc: 'Mascaramento de CPF, CNPJ, e-mail, telefone e cartão na saída',     ok: true },
                  { fw: 'OWASP LLM',      fn: 'Top-10 (2025)',         desc: `${cobertas}/${categorias.length} categorias com ocorrência observada na janela`, ok: true },
                ].map((row, i) => (
                  <tr key={i} className="hover:bg-gray-800/20">
                    <td className="py-2.5 font-mono text-blue-400 font-bold">{row.fw}</td>
                    <td className="py-2.5 font-medium text-gray-200">{row.fn}</td>
                    <td className="py-2.5 text-gray-400">{row.desc}</td>
                    <td className="py-2.5 text-center">
                      {row.ok
                        ? <CheckCircle className="w-4 h-4 text-green-400 mx-auto" />
                        : <AlertTriangle className="w-4 h-4 text-yellow-400 mx-auto" />
                      }
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
