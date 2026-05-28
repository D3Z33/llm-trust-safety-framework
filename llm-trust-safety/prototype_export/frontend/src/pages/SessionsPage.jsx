import { useEffect, useState, useCallback } from 'react'
import { dashboardAPI, sessionsAPI } from '../utils/api'
import { LoadingSpinner, toast } from '../components/ui'
import {
  Users, AlertTriangle, Shield, Activity, Clock,
  RefreshCw, Filter, ChevronRight, Zap, ShieldOff, ShieldCheck, Eye,
  Bell, MessageSquare, FileText
} from 'lucide-react'
import { formatRelative, formatDate, getRiskColor, getLabelName } from '../utils/helpers'

const STATE_CONFIG = {
  NORMAL:    { label: 'Normal',    bg: 'bg-green-500/10',  border: 'border-green-500/30',  text: 'text-green-400',  dot: 'bg-green-400' },
  SUSPICIOUS:{ label: 'Suspeita', bg: 'bg-yellow-500/10', border: 'border-yellow-500/30', text: 'text-yellow-400', dot: 'bg-yellow-400' },
  BLOCKED:   { label: 'Bloqueada', bg: 'bg-red-500/10',   border: 'border-red-500/30',    text: 'text-red-400',   dot: 'bg-red-400' },
  TERMINATED:{ label: 'Encerrada', bg: 'bg-gray-500/10',  border: 'border-gray-500/30',   text: 'text-gray-400',  dot: 'bg-gray-500' },
}

function RiskBar({ value }) {
  const color = value >= 80 ? '#ef4444' : value >= 60 ? '#f97316' : value >= 40 ? '#f59e0b' : '#22c55e'
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 bg-gray-800 rounded-full h-1.5">
        <div className="h-1.5 rounded-full transition-all" style={{ width: `${Math.min(value, 100)}%`, backgroundColor: color }} />
      </div>
      <span className="text-xs font-bold w-8 text-right" style={{ color }}>{Math.round(value)}</span>
    </div>
  )
}

export default function SessionsPage() {
  const [sessions, setSessions] = useState([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('ALL')
  const [refreshing, setRefreshing] = useState(false)
  const [expanded, setExpanded] = useState(null)
  const [timelines, setTimelines] = useState({})
  const [loadingTimeline, setLoadingTimeline] = useState(null)

  const handleExpand = async (sessionId) => {
    if (expanded === sessionId) {
      setExpanded(null)
      return
    }
    setExpanded(sessionId)
    if (timelines[sessionId]) return // já cacheado
    setLoadingTimeline(sessionId)
    try {
      const r = await sessionsAPI.getTimeline(sessionId)
      setTimelines(prev => ({ ...prev, [sessionId]: r.data }))
    } catch (e) {
      toast('Erro ao carregar timeline da sessão', 'error')
    } finally {
      setLoadingTimeline(null)
    }
  }

  const fetchSessions = useCallback(async () => {
    setRefreshing(true)
    try {
      const r = await dashboardAPI.getSessions()
      setSessions(Array.isArray(r.data) ? r.data : [])
    } catch (e) {
      toast('Erro ao carregar sessões', 'error')
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }, [])

  useEffect(() => { fetchSessions() }, [fetchSessions])

  const counts = sessions.reduce((acc, s) => {
    acc[s.state] = (acc[s.state] || 0) + 1
    return acc
  }, { NORMAL: 0, SUSPICIOUS: 0, BLOCKED: 0 })

  const filtered = filter === 'ALL' ? sessions : sessions.filter(s => s.state === filter)
  const threatLevel = counts.BLOCKED > 0 ? 'ALTO' : counts.SUSPICIOUS > 0 ? 'MÉDIO' : 'BAIXO'
  const threatColor = counts.BLOCKED > 0 ? 'text-red-400' : counts.SUSPICIOUS > 0 ? 'text-yellow-400' : 'text-green-400'

  return (
    <div className="p-6 space-y-5 bg-gray-950 min-h-screen">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Activity className="w-6 h-6 text-purple-400" />
            Monitoramento de Sessões
          </h1>
          <p className="text-gray-400 text-sm mt-1">
            SessionWatch FSM — detecção de ataques encadeados em tempo real
          </p>
        </div>
        <div className="flex items-center gap-2">
          <div className={`flex items-center gap-2 text-xs font-bold px-3 py-1.5 rounded-lg border ${
            threatLevel === 'ALTO' ? 'bg-red-500/10 border-red-500/30 text-red-400'
            : threatLevel === 'MÉDIO' ? 'bg-yellow-500/10 border-yellow-500/30 text-yellow-400'
            : 'bg-green-500/10 border-green-500/30 text-green-400'
          }`}>
            <Shield className="w-3.5 h-3.5" />
            Ameaça: {threatLevel}
          </div>
          <button
            onClick={fetchSessions}
            disabled={refreshing}
            className="p-2 rounded-lg bg-gray-800 hover:bg-gray-700 text-gray-400 hover:text-white transition-colors"
          >
            <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: 'Total', value: sessions.length, icon: Users, color: 'text-blue-400', border: 'border-blue-500/20' },
          { label: 'Normais', value: counts.NORMAL, icon: ShieldCheck, color: 'text-green-400', border: 'border-green-500/20' },
          { label: 'Suspeitas', value: counts.SUSPICIOUS, icon: Eye, color: 'text-yellow-400', border: 'border-yellow-500/20' },
          { label: 'Bloqueadas', value: counts.BLOCKED, icon: ShieldOff, color: 'text-red-400', border: 'border-red-500/20' },
        ].map(({ label, value, icon: Icon, color, border }) => (
          <div key={label} className={`bg-gray-900 border ${border} rounded-xl p-4 flex items-center gap-3`}>
            <div className={`w-10 h-10 rounded-xl bg-gray-800 flex items-center justify-center flex-shrink-0`}>
              <Icon className={`w-5 h-5 ${color}`} />
            </div>
            <div>
              <p className={`text-2xl font-bold ${color}`}>{value}</p>
              <p className="text-xs text-gray-500">{label}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Filter tabs */}
      <div className="flex items-center gap-2">
        <Filter className="w-4 h-4 text-gray-500" />
        <div className="flex bg-gray-900 border border-gray-800 rounded-lg p-1 gap-1">
          {['ALL', 'NORMAL', 'SUSPICIOUS', 'BLOCKED'].map(f => {
            const cfg = STATE_CONFIG[f] || { label: 'Todos', text: 'text-gray-300' }
            return (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={`px-3 py-1.5 rounded text-xs font-medium transition-all ${
                  filter === f
                    ? `bg-gray-800 ${cfg.text}`
                    : 'text-gray-500 hover:text-gray-300'
                }`}
              >
                {f === 'ALL' ? `Todas (${sessions.length})` : `${cfg.label} (${counts[f] || 0})`}
              </button>
            )
          })}
        </div>
      </div>

      {/* Session List */}
      <div className="space-y-2">
        {loading ? (
          <LoadingSpinner text="Carregando sessões..." />
        ) : filtered.length === 0 ? (
          <div className="bg-gray-900 border border-gray-800 rounded-xl py-16 text-center">
            <Users className="w-12 h-12 mx-auto mb-3 text-gray-700" />
            <p className="text-gray-500 font-medium">Nenhuma sessão encontrada</p>
            <p className="text-gray-600 text-sm mt-1">Realize avaliações para gerar sessões monitoradas</p>
          </div>
        ) : (
          filtered.map(s => {
            const cfg = STATE_CONFIG[s.state] || STATE_CONFIG.NORMAL
            const isOpen = expanded === s.session_id
            return (
              <div
                key={s.session_id}
                className={`bg-gray-900 border rounded-xl overflow-hidden transition-all ${cfg.border}`}
              >
                {/* Row header */}
                <button
                  className="w-full flex items-center gap-4 p-4 text-left hover:bg-gray-800/30 transition-colors"
                  onClick={() => handleExpand(s.session_id)}
                >
                  {/* Status dot */}
                  <div className="flex-shrink-0 relative">
                    <span className={`inline-flex h-3 w-3 rounded-full ${cfg.dot}`}>
                      {s.state === 'SUSPICIOUS' && (
                        <span className={`animate-ping absolute inline-flex h-full w-full rounded-full ${cfg.dot} opacity-50`} />
                      )}
                    </span>
                  </div>

                  {/* Session ID */}
                  <div className="flex-1 min-w-0">
                    <p className="font-mono text-xs text-gray-300 truncate">{s.session_id}</p>
                    <p className="text-[10px] text-gray-600 mt-0.5">
                      {s.last_activity ? formatRelative(s.last_activity) : 'Sem atividade'}
                    </p>
                  </div>

                  {/* State badge */}
                  <span className={`flex-shrink-0 text-xs font-bold px-2.5 py-1 rounded-full border ${cfg.bg} ${cfg.border} ${cfg.text}`}>
                    {cfg.label}
                  </span>

                  {/* Attacks */}
                  <div className="flex-shrink-0 text-center w-16">
                    <p className={`text-sm font-bold ${s.attack_count > 0 ? 'text-red-400' : 'text-gray-600'}`}>
                      {s.attack_count}
                    </p>
                    <p className="text-[10px] text-gray-600">ataques</p>
                  </div>

                  {/* Interactions */}
                  <div className="flex-shrink-0 text-center w-20 hidden sm:block">
                    <p className="text-sm font-bold text-gray-300">{s.total_interactions}</p>
                    <p className="text-[10px] text-gray-600">interações</p>
                  </div>

                  {/* Max risk bar */}
                  <div className="flex-shrink-0 w-32 hidden md:block">
                    <RiskBar value={s.max_risk_score || 0} />
                    <p className="text-[10px] text-gray-600 mt-1">max risk</p>
                  </div>

                  <ChevronRight className={`w-4 h-4 text-gray-600 flex-shrink-0 transition-transform ${isOpen ? 'rotate-90' : ''}`} />
                </button>

                {/* Expanded — timeline real da sessão (Fase 2) */}
                {isOpen && (
                  <SessionTimelineView
                    session={s}
                    timeline={timelines[s.session_id]}
                    loading={loadingTimeline === s.session_id}
                  />
                )}
              </div>
            )
          })
        )}
      </div>

      {/* FSM Diagram */}
      <div className="bg-gray-900 border border-blue-500/15 rounded-xl p-5">
        <h3 className="text-sm font-bold text-white mb-4 flex items-center gap-2">
          <Zap className="w-4 h-4 text-blue-400" />
          SessionWatch — Máquina de Estados Finitos (FSM)
        </h3>
        <div className="flex items-start justify-center gap-3 flex-wrap">
          {[
            { state: 'NORMAL',     color: '#22c55e', desc: 'Comportamento padrão',       trigger: 'Qualquer prompt limpo' },
            { state: 'SUSPICIOUS', color: '#f59e0b', desc: '1 ataque detectado',          trigger: 'InputGuard score ≥ 60' },
            { state: 'BLOCKED',    color: '#ef4444', desc: '2+ ataques consecutivos',     trigger: 'InputGuard score ≥ 80' },
          ].map((s, i, arr) => (
            <div key={s.state} className="flex items-center gap-3">
              <div className="text-center">
                <div
                  className="w-28 h-14 rounded-xl border-2 flex flex-col items-center justify-center gap-0.5"
                  style={{ borderColor: s.color, backgroundColor: `${s.color}12` }}
                >
                  <span className="text-xs font-bold" style={{ color: s.color }}>{s.state}</span>
                  <span className="text-[9px] text-gray-500">{s.desc}</span>
                </div>
                <p className="text-[9px] text-gray-600 mt-1.5 max-w-[112px]">{s.trigger}</p>
              </div>
              {i < arr.length - 1 && (
                <ChevronRight className="w-5 h-5 text-gray-700 flex-shrink-0 mt-1" />
              )}
            </div>
          ))}
        </div>
        <p className="text-[10px] text-gray-600 text-center mt-4">
          Recuperação automática após 3 interações limpas. Sessões BLOCKED requerem revisão manual ou expiram após timeout.
        </p>
      </div>
    </div>
  )
}


// ─── Timeline detalhada da sessão (Fase 2) ────────────────────────────────
function SessionTimelineView({ session, timeline, loading }) {
  if (loading || !timeline) {
    return (
      <div className="px-4 py-6 border-t border-gray-800/60 text-center">
        <div className="inline-flex items-center gap-2 text-xs text-gray-500">
          <div className="w-3 h-3 border-2 border-blue-500/30 border-t-blue-500 rounded-full animate-spin" />
          Carregando linha do tempo da sessão…
        </div>
      </div>
    )
  }

  if (timeline.error) {
    return (
      <div className="px-4 py-6 border-t border-gray-800/60 text-center text-xs text-red-400">
        Não foi possível carregar a timeline desta sessão.
      </div>
    )
  }

  const logs = timeline.logs || []
  const alerts = timeline.alerts || []
  const piiAcum = timeline.pii_acumulada || {}
  const resumo = timeline.resumo || {}

  return (
    <div className="px-4 pb-5 border-t border-gray-800/60 pt-4 space-y-4">

      {/* Resumo executivo */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-2">
        {[
          { label: 'Interações', value: resumo.total_logs ?? 0, color: '#3b82f6' },
          { label: 'Bloqueadas', value: resumo.total_bloqueados ?? 0, color: '#ef4444' },
          { label: 'Alertas',    value: resumo.total_alertas ?? 0, color: '#f59e0b' },
          { label: 'Tipos PII',  value: resumo.tipos_pii ?? 0, color: '#a855f7' },
          { label: 'PII total',  value: resumo.ocorrencias_pii ?? 0, color: '#a855f7' },
        ].map(({ label, value, color }) => (
          <div key={label} className="bg-gray-800/50 rounded-lg p-2.5">
            <p className="text-[9px] uppercase tracking-widest text-gray-500">{label}</p>
            <p className="text-base font-bold tabular-nums" style={{ color }}>{value}</p>
          </div>
        ))}
      </div>

      {/* Flags + app + janela */}
      <div className="flex flex-wrap items-center gap-3 text-[11px] text-gray-400">
        {session.app_name && (
          <span className="flex items-center gap-1">
            <FileText className="w-3 h-3" /> Aplicação:
            <span className="text-gray-200 font-semibold">{session.app_name}</span>
          </span>
        )}
        {(session.flags || []).length > 0 && (
          <div className="flex items-center gap-1.5 flex-wrap">
            <Shield className="w-3 h-3 text-purple-400" />
            {session.flags.map(f => (
              <span key={f} className="text-[10px] bg-purple-500/15 text-purple-300 border border-purple-500/25 px-2 py-0.5 rounded-full font-mono">
                {f}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Linha do tempo de mensagens */}
      <div>
        <p className="text-[10px] uppercase tracking-widest text-gray-500 font-bold mb-2 flex items-center gap-1.5">
          <MessageSquare className="w-3 h-3" /> Mensagens da sessão · {logs.length}
        </p>
        {logs.length === 0 ? (
          <p className="text-[11px] text-gray-600 italic">Sem mensagens registradas para esta sessão.</p>
        ) : (
          <div className="space-y-2 max-h-96 overflow-y-auto pr-2">
            {logs.map((log, idx) => {
              const cor = getRiskColor(log.risk_level)
              return (
                <div
                  key={log.audit_id}
                  className={`bg-gray-950 border rounded-lg p-3 space-y-1.5 ${
                    log.input_blocked ? 'border-red-500/30' : 'border-gray-800'
                  }`}
                >
                  <div className="flex items-center justify-between gap-2 text-[10px] text-gray-500">
                    <div className="flex items-center gap-2">
                      <span className="w-5 h-5 rounded-full bg-blue-500/15 border border-blue-500/30 flex items-center justify-center text-blue-300 font-bold">
                        {idx + 1}
                      </span>
                      <span className="font-mono">{formatDate(log.created_at)}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="font-bold tabular-nums" style={{ color: cor }}>
                        risco {Math.round(log.risk_score ?? 0)}/100
                      </span>
                      {log.input_blocked
                        ? <span className="text-red-400 font-bold flex items-center gap-1"><ShieldOff className="w-3 h-3" />BLOQ</span>
                        : <span className="text-green-400 flex items-center gap-1"><ShieldCheck className="w-3 h-3" />OK</span>
                      }
                    </div>
                  </div>
                  <p className="text-xs text-gray-200 leading-relaxed line-clamp-2">{log.prompt}</p>
                  {(log.input_labels?.length > 0 || log.owasp_categories?.length > 0) && (
                    <div className="flex flex-wrap gap-1 pt-1">
                      {log.input_labels?.slice(0, 3).map(l => (
                        <span key={l} className="text-[9px] bg-red-500/15 text-red-300 border border-red-500/20 px-1.5 py-0.5 rounded-full">
                          {getLabelName(l)}
                        </span>
                      ))}
                      {log.owasp_categories?.slice(0, 2).map(c => (
                        <span key={c} className="text-[9px] bg-purple-500/15 text-purple-300 border border-purple-500/20 px-1.5 py-0.5 rounded-full font-mono">
                          {c.split(':')[0]}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        )}
      </div>

      {/* PII acumulada */}
      {Object.keys(piiAcum).length > 0 && (
        <div>
          <p className="text-[10px] uppercase tracking-widest text-gray-500 font-bold mb-2">
            PII acumulada na sessão
          </p>
          <div className="flex flex-wrap gap-1.5">
            {Object.entries(piiAcum).map(([tipo, qtd]) => (
              <span key={tipo} className="text-[10px] bg-yellow-500/15 text-yellow-300 border border-yellow-500/25 px-2 py-1 rounded-full">
                <span className="font-mono uppercase">{tipo}</span> · {qtd}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Alertas relacionados */}
      {alerts.length > 0 && (
        <div>
          <p className="text-[10px] uppercase tracking-widest text-gray-500 font-bold mb-2 flex items-center gap-1.5">
            <Bell className="w-3 h-3 text-red-400" /> Alertas correlacionados · {alerts.length}
          </p>
          <ul className="space-y-1.5">
            {alerts.map(a => (
              <li key={a.alert_id} className="bg-red-500/5 border border-red-500/20 rounded-lg px-3 py-2 text-[11px] flex items-center justify-between gap-2">
                <span className="text-red-200 truncate flex-1">{a.title}</span>
                <span className="text-[9px] uppercase font-mono tracking-wider text-red-300 shrink-0">{a.severity}</span>
                <span className="text-[9px] text-gray-500 shrink-0">{formatRelative(a.created_at)}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
