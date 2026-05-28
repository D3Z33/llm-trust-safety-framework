import { useEffect, useState, useCallback } from 'react'
import { dashboardAPI } from '../utils/api'
import { getRiskColor, formatDate, getLabelName } from '../utils/helpers'
import { RiskBadge, LoadingSpinner, toast } from '../components/ui'
import ExportPDFMenu from '../components/ExportPDFMenu'
import {
  Search, Download, Filter, ChevronLeft, ChevronRight, X,
  Shield, AlertTriangle, Clock, Database, RefreshCw, CheckCircle, ShieldOff
} from 'lucide-react'

export default function LogsPage() {
  const [logs, setLogs] = useState([])
  const [total, setTotal] = useState(0)
  const [pages, setPages] = useState(1)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [page, setPage] = useState(1)
  const [riskFilter, setRiskFilter] = useState('')
  const [blockedOnly, setBlockedOnly] = useState(false)
  const [selected, setSelected] = useState(null)

  const fetchLogs = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await dashboardAPI.getLogs({
        page,
        per_page: 20,
        risk_level: riskFilter || undefined,
        blocked_only: blockedOnly || undefined,
      })
      setLogs(res.data.logs || [])
      setTotal(res.data.total || 0)
      setPages(res.data.pages || 1)
    } catch (e) {
      setError('Erro ao carregar logs. Verifique se o backend está disponível.')
      toast('Erro ao carregar logs', 'error')
    } finally {
      setLoading(false)
    }
  }, [page, riskFilter, blockedOnly])

  useEffect(() => { fetchLogs() }, [fetchLogs])

  const handleExport = async (format) => {
    try {
      const res = await dashboardAPI.exportLogs(format)
      const url = URL.createObjectURL(new Blob([res.data]))
      const a = document.createElement('a')
      a.href = url
      a.download = `llm_trust_logs.${format}`
      a.click()
    } catch (e) { console.error(e) }
  }

  const blockedCount = logs.filter(l => l.input_blocked).length
  const criticalCount = logs.filter(l => l.risk_level === 'CRITICAL').length

  return (
    <div className="p-6 space-y-5 bg-gray-950 min-h-screen">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Database className="w-6 h-6 text-blue-400" />
            Logs de Auditoria
          </h1>
          <p className="text-gray-400 text-sm mt-1">Trilha completa e auditável — {total} registros totais</p>
        </div>
        <div className="flex gap-2">
          <button onClick={fetchLogs} className="p-2 rounded-lg bg-gray-800 hover:bg-gray-700 text-gray-400 hover:text-white transition-colors">
            <RefreshCw className="w-4 h-4" />
          </button>
          <button onClick={() => handleExport('csv')} className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-gray-800 hover:bg-gray-700 text-gray-300 text-xs transition-colors">
            <Download className="w-3.5 h-3.5" /> CSV
          </button>
          <button onClick={() => handleExport('json')} className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-gray-800 hover:bg-gray-700 text-gray-300 text-xs transition-colors">
            <Download className="w-3.5 h-3.5" /> JSON
          </button>
          <ExportPDFMenu days={30} tipos={["tecnico", "sessoes_alertas", "executivo"]} />
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        {[
          { label: 'Total (pág.)', value: logs.length, icon: Database, color: 'text-blue-400', border: 'border-blue-500/20' },
          { label: 'Bloqueados', value: blockedCount, icon: ShieldOff, color: 'text-red-400', border: 'border-red-500/20' },
          { label: 'Críticos', value: criticalCount, icon: AlertTriangle, color: 'text-orange-400', border: 'border-orange-500/20' },
          { label: 'Total Geral', value: total, icon: Shield, color: 'text-green-400', border: 'border-green-500/20' },
        ].map(({ label, value, icon: Icon, color, border }) => (
          <div key={label} className={`bg-gray-900 border ${border} rounded-xl p-3 flex items-center gap-3`}>
            <Icon className={`w-5 h-5 ${color} flex-shrink-0`} />
            <div>
              <p className={`text-xl font-bold ${color}`}>{value}</p>
              <p className="text-[10px] text-gray-500">{label}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3 flex-wrap">
        <Filter className="w-4 h-4 text-gray-500" />
        <div className="flex bg-gray-900 border border-gray-800 rounded-lg p-1 gap-1">
          {[
            { value: '', label: 'Todos' },
            { value: 'LOW', label: 'LOW' },
            { value: 'MEDIUM', label: 'MED' },
            { value: 'HIGH', label: 'HIGH' },
            { value: 'CRITICAL', label: 'CRIT' },
          ].map(({ value, label }) => (
            <button
              key={value}
              onClick={() => { setRiskFilter(value); setPage(1) }}
              className={`px-3 py-1.5 rounded text-xs font-medium transition-colors ${
                riskFilter === value
                  ? 'bg-blue-600 text-white'
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              {label}
            </button>
          ))}
        </div>
        <label className="flex items-center gap-2 cursor-pointer bg-gray-900 border border-gray-800 rounded-lg px-3 py-2">
          <input
            type="checkbox"
            checked={blockedOnly}
            onChange={e => { setBlockedOnly(e.target.checked); setPage(1) }}
            className="rounded border-gray-700 bg-gray-800 text-blue-600 w-3 h-3"
          />
          <span className="text-xs text-gray-400">Apenas Bloqueados</span>
        </label>
      </div>

      {/* Table */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
        {loading ? (
          <div className="p-8"><LoadingSpinner text="Carregando logs..." /></div>
        ) : error ? (
          <div className="text-center py-16">
            <AlertTriangle className="w-10 h-10 mx-auto mb-3 text-red-500 opacity-60" />
            <p className="text-red-400 font-medium text-sm">{error}</p>
            <button onClick={fetchLogs} className="mt-4 text-xs text-blue-400 hover:text-blue-300 underline">
              Tentar novamente
            </button>
          </div>
        ) : logs.length === 0 ? (
          <div className="text-center py-16">
            <Database className="w-12 h-12 mx-auto mb-3 text-gray-700" />
            <p className="text-gray-500 font-medium">Nenhum log encontrado</p>
            <p className="text-gray-600 text-sm mt-1">
              {riskFilter || blockedOnly ? 'Tente remover os filtros' : 'Realize avaliações para gerar registros'}
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-[10px] text-gray-500 border-b border-gray-800 bg-gray-900/80">
                  <th className="px-4 py-3 font-medium uppercase tracking-wider">Prompt</th>
                  <th className="px-4 py-3 font-medium uppercase tracking-wider w-16">Score</th>
                  <th className="px-4 py-3 font-medium uppercase tracking-wider w-20">Nível</th>
                  <th className="px-4 py-3 font-medium uppercase tracking-wider w-24">Status</th>
                  <th className="px-4 py-3 font-medium uppercase tracking-wider">Labels</th>
                  <th className="px-4 py-3 font-medium uppercase tracking-wider w-12">PII</th>
                  <th className="px-4 py-3 font-medium uppercase tracking-wider w-20 hidden md:table-cell">Latência</th>
                  <th className="px-4 py-3 font-medium uppercase tracking-wider w-36 hidden lg:table-cell">Data/Hora</th>
                  <th className="px-4 py-3 w-8"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-800/40">
                {logs.map(log => (
                  <tr key={log.id} className="hover:bg-gray-800/25 transition-colors group">
                    <td className="px-4 py-3 text-gray-300 max-w-xs">
                      <span className="truncate block text-xs leading-relaxed">
                        {log.prompt?.slice(0, 75)}{(log.prompt?.length || 0) > 75 ? '…' : ''}
                      </span>
                      <span className="text-[9px] text-gray-600 font-mono">{log.session_id?.slice(0, 12)}…</span>
                    </td>
                    <td className="px-4 py-3">
                      <span className="text-sm font-bold tabular-nums" style={{ color: getRiskColor(log.risk_level) }}>
                        {Math.round(log.risk_score ?? 0)}
                      </span>
                    </td>
                    <td className="px-4 py-3"><RiskBadge level={log.risk_level} /></td>
                    <td className="px-4 py-3">
                      {log.input_blocked
                        ? <span className="flex items-center gap-1 text-[10px] text-red-400 font-semibold"><ShieldOff className="w-3 h-3" />Bloqueado</span>
                        : <span className="flex items-center gap-1 text-[10px] text-green-400 font-semibold"><CheckCircle className="w-3 h-3" />Passou</span>
                      }
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex flex-wrap gap-1">
                        {(log.input_labels || []).slice(0, 2).map(l => (
                          <span key={l} className="text-[9px] bg-red-500/10 text-red-300 border border-red-500/20 px-1.5 py-0.5 rounded-full">
                            {getLabelName(l)}
                          </span>
                        ))}
                        {(log.input_labels || []).length > 2 && (
                          <span className="text-[9px] text-gray-500">+{log.input_labels.length - 2}</span>
                        )}
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      {(log.pii_found?.length || 0) > 0
                        ? <span className="text-xs text-yellow-400 font-bold">{log.pii_found.length}</span>
                        : <span className="text-[10px] text-gray-600">—</span>
                      }
                    </td>
                    <td className="px-4 py-3 text-xs text-gray-500 hidden md:table-cell">
                      {Math.round(log.latency_ms ?? 0)}ms
                    </td>
                    <td className="px-4 py-3 text-[10px] text-gray-600 hidden lg:table-cell">
                      {formatDate(log.created_at)}
                    </td>
                    <td className="px-4 py-3">
                      <button
                        onClick={() => setSelected(log)}
                        className="opacity-0 group-hover:opacity-100 text-gray-500 hover:text-blue-400 transition-all text-lg leading-none"
                      >
                        ···
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            {/* Pagination */}
            <div className="flex items-center justify-between px-4 py-3 border-t border-gray-800 bg-gray-900/50">
              <span className="text-xs text-gray-500">
                Página {page} de {pages} — <span className="text-gray-400">{total} registros</span>
              </span>
              <div className="flex items-center gap-1">
                <button
                  disabled={page <= 1}
                  onClick={() => setPage(p => p - 1)}
                  className="p-1.5 rounded-lg bg-gray-800 hover:bg-gray-700 text-gray-400 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                >
                  <ChevronLeft className="w-4 h-4" />
                </button>
                {Array.from({ length: Math.min(pages, 5) }, (_, i) => {
                  const p = i + 1
                  return (
                    <button
                      key={p}
                      onClick={() => setPage(p)}
                      className={`w-7 h-7 rounded-lg text-xs font-medium transition-colors ${
                        page === p ? 'bg-blue-600 text-white' : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
                      }`}
                    >
                      {p}
                    </button>
                  )
                })}
                {pages > 5 && <span className="text-gray-600 text-xs px-1">…{pages}</span>}
                <button
                  disabled={page >= pages}
                  onClick={() => setPage(p => p + 1)}
                  className="p-1.5 rounded-lg bg-gray-800 hover:bg-gray-700 text-gray-400 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                >
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Detail Modal — versão de auditoria (Fase 2) */}
      {selected && <LogDetailModal log={selected} onClose={() => setSelected(null)} />}
    </div>
  )
}

// ─── Modal de drill-down completo ───────────────────────────────────────────
function LogDetailModal({ log, onClose }) {
  const blocked = log.input_blocked
  const decisao = blocked ? 'BLOQUEADO' : log.risk_score >= 60 ? 'SINALIZADO' : 'PERMITIDO'
  const decisaoColor = blocked ? 'text-red-400' : log.risk_score >= 60 ? 'text-yellow-400' : 'text-green-400'
  const decisaoBg = blocked ? 'bg-red-500/10 border-red-500/30' : log.risk_score >= 60 ? 'bg-yellow-500/10 border-yellow-500/30' : 'bg-green-500/10 border-green-500/30'

  // Trilha de processamento — gera passos a partir dos campos disponíveis
  const trilha = [
    { passo: '1. Recepção',     label: 'Prompt recebido pela API',           valor: `${log.prompt?.length ?? 0} caracteres`, ok: true },
    { passo: '2. InputGuard',   label: 'Análise de padrões de ataque',       valor: `score ${Math.round(log.input_score ?? 0)}/100 · ${(log.input_labels || []).length} categoria(s)`, ok: !blocked },
    { passo: '3. SessionWatch', label: 'Avaliação do contexto da sessão',    valor: `score ${Math.round(log.session_score ?? 0)}/100`, ok: true },
    { passo: '4. LLM',          label: blocked ? 'Pulado (bloqueado no input)' : 'Resposta gerada e analisada', valor: log.output_text ? `${(log.output_text || '').length} caracteres` : '—', ok: !blocked },
    { passo: '5. OutputGuard',  label: 'Detecção de PII na saída',           valor: `${(log.pii_found || []).length} entidade(s) PII`, ok: true },
    { passo: '6. Risk Aggregator', label: 'Score consolidado',                valor: `${Math.round(log.risk_score ?? 0)}/100 (${log.risk_level})`, ok: true },
    { passo: '7. Persistência', label: 'Audit trail registrado',             valor: `${log.audit_id?.slice(0, 12)}…`, ok: true },
  ]

  return (
    <div
      className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-start justify-center p-4 overflow-y-auto"
      onClick={onClose}
    >
      <div
        className="bg-gray-950 border border-gray-700 rounded-2xl w-full max-w-4xl my-8 shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Cabeçalho */}
        <div className="sticky top-0 z-10 bg-gray-950/95 backdrop-blur-sm border-b border-gray-800 px-6 py-4 flex items-center justify-between rounded-t-2xl">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-blue-500/15 border border-blue-500/30 flex items-center justify-center">
              <Database className="w-4 h-4 text-blue-400" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-white">Trilha de Auditoria — Avaliação #{log.id}</h3>
              <p className="text-[10px] text-gray-500 font-mono">{log.audit_id}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-white transition-colors p-1.5 rounded-lg hover:bg-gray-800"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Corpo */}
        <div className="px-6 py-5 space-y-5">

          {/* Faixa de decisão */}
          <div className={`rounded-xl border ${decisaoBg} p-4 flex items-center justify-between flex-wrap gap-3`}>
            <div className="flex items-center gap-3">
              <div className={`w-12 h-12 rounded-xl border-2 flex items-center justify-center ${decisaoBg.replace('/10', '/20')}`}>
                {blocked
                  ? <ShieldOff className="w-5 h-5 text-red-400" />
                  : log.risk_score >= 60
                    ? <AlertTriangle className="w-5 h-5 text-yellow-400" />
                    : <CheckCircle className="w-5 h-5 text-green-400" />
                }
              </div>
              <div>
                <p className="text-[10px] uppercase tracking-widest text-gray-500 font-bold">Decisão final</p>
                <p className={`text-xl font-bold ${decisaoColor}`}>{decisao}</p>
                <p className="text-[10px] text-gray-500 mt-0.5">
                  Risco {Math.round(log.risk_score ?? 0)}/100 · nível {log.risk_level} · latência {Math.round(log.latency_ms ?? 0)} ms
                </p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-[10px] uppercase tracking-widest text-gray-500 font-bold">Aplicação</p>
              <p className="text-xs font-semibold text-gray-200">{log.app_name || '—'}</p>
              <p className="text-[10px] text-gray-500 mt-0.5">{formatDate(log.created_at)}</p>
            </div>
          </div>

          {/* Identificadores */}
          <div className="grid grid-cols-2 gap-3 text-xs">
            <div className="bg-gray-900 border border-gray-800 rounded-lg p-3">
              <p className="text-[10px] uppercase tracking-widest text-gray-500 mb-1">Audit ID</p>
              <p className="font-mono text-gray-200 break-all text-[11px]">{log.audit_id}</p>
            </div>
            <div className="bg-gray-900 border border-gray-800 rounded-lg p-3">
              <p className="text-[10px] uppercase tracking-widest text-gray-500 mb-1">Sessão</p>
              <p className="font-mono text-gray-200 break-all text-[11px]">{log.session_id}</p>
            </div>
          </div>

          {/* Prompt original × sanitizado */}
          <div className="space-y-2">
            <p className="text-[10px] uppercase tracking-widest text-gray-500 font-bold">Prompt original</p>
            <div className="bg-gray-900 border border-gray-800 rounded-lg p-3 text-xs text-gray-200 leading-relaxed whitespace-pre-wrap break-words max-h-40 overflow-y-auto">
              {log.prompt || '—'}
            </div>
            {log.sanitized_prompt && log.sanitized_prompt !== log.prompt && (
              <>
                <p className="text-[10px] uppercase tracking-widest text-gray-500 font-bold">Prompt sanitizado (após guardrails)</p>
                <div className="bg-gray-900 border border-blue-500/20 rounded-lg p-3 text-xs text-blue-200 leading-relaxed whitespace-pre-wrap break-words max-h-40 overflow-y-auto">
                  {log.sanitized_prompt}
                </div>
              </>
            )}
          </div>

          {/* Resposta do LLM (se houve) */}
          {log.output_text && (
            <div className="space-y-2">
              <p className="text-[10px] uppercase tracking-widest text-gray-500 font-bold">Resposta do LLM</p>
              <div className="bg-gray-900 border border-gray-800 rounded-lg p-3 text-xs text-gray-200 leading-relaxed whitespace-pre-wrap break-words max-h-40 overflow-y-auto">
                {log.output_text}
              </div>
              {log.output_sanitized && log.output_sanitized !== log.output_text && (
                <div className="bg-gray-900 border border-yellow-500/20 rounded-lg p-3 text-xs text-yellow-100 leading-relaxed whitespace-pre-wrap break-words max-h-40 overflow-y-auto">
                  <p className="text-[9px] uppercase tracking-widest text-yellow-400 font-bold mb-1.5">Resposta após mascaramento de PII</p>
                  {log.output_sanitized}
                </div>
              )}
            </div>
          )}

          {/* Scores por módulo */}
          <div>
            <p className="text-[10px] uppercase tracking-widest text-gray-500 font-bold mb-2">Score por módulo</p>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
              {[
                { label: 'InputGuard',  v: log.input_score,    color: '#3b82f6' },
                { label: 'OutputGuard', v: log.output_score,   color: '#f59e0b' },
                { label: 'SessionWatch',v: log.session_score,  color: '#8b5cf6' },
                { label: 'Risco final', v: log.risk_score,     color: getRiskColor(log.risk_level) },
              ].map(({ label, v, color }) => (
                <div key={label} className="bg-gray-900 border border-gray-800 rounded-lg p-2.5">
                  <p className="text-[9px] uppercase tracking-widest text-gray-500">{label}</p>
                  <p className="text-base font-bold tabular-nums" style={{ color }}>{Math.round(v ?? 0)}</p>
                  <div className="h-1 bg-gray-800 rounded-full overflow-hidden mt-1.5">
                    <div className="h-full rounded-full" style={{ width: `${Math.min(v ?? 0, 100)}%`, background: color }} />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Categorias OWASP + Labels */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div>
              <p className="text-[10px] uppercase tracking-widest text-gray-500 font-bold mb-2">Categorias OWASP</p>
              {log.owasp_categories?.length > 0 ? (
                <div className="flex flex-wrap gap-1.5">
                  {log.owasp_categories.map((c, i) => (
                    <span key={i} className="text-[10px] bg-purple-500/15 text-purple-300 border border-purple-500/25 px-2 py-1 rounded-full font-mono">
                      {c}
                    </span>
                  ))}
                </div>
              ) : <p className="text-[11px] text-gray-600 italic">Nenhuma categoria OWASP detectada.</p>}
            </div>
            <div>
              <p className="text-[10px] uppercase tracking-widest text-gray-500 font-bold mb-2">Labels do classificador</p>
              {log.input_labels?.length > 0 ? (
                <div className="flex flex-wrap gap-1.5">
                  {log.input_labels.map((l) => (
                    <span key={l} className="text-[10px] bg-red-500/15 text-red-300 border border-red-500/25 px-2 py-1 rounded-full">
                      {getLabelName(l)}
                    </span>
                  ))}
                </div>
              ) : <p className="text-[11px] text-gray-600 italic">Sem labels acionados.</p>}
            </div>
          </div>

          {/* PII detectada */}
          {log.pii_found?.length > 0 && (
            <div>
              <p className="text-[10px] uppercase tracking-widest text-gray-500 font-bold mb-2">
                PII detectada (Output) · {log.pii_found.length}
              </p>
              <div className="bg-yellow-500/5 border border-yellow-500/20 rounded-lg divide-y divide-yellow-500/10">
                {log.pii_found.map((p, i) => (
                  <div key={i} className="px-3 py-2 flex items-center gap-3 text-[11px]">
                    <span className="text-yellow-300 font-mono uppercase tracking-wider w-24 shrink-0">{p.entity_type}</span>
                    <span className="text-gray-300 font-mono break-all flex-1">{p.value}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Policy hits */}
          {log.policy_hits?.length > 0 && (
            <div>
              <p className="text-[10px] uppercase tracking-widest text-gray-500 font-bold mb-2">
                Políticas acionadas · {log.policy_hits.length}
              </p>
              <ul className="space-y-1.5">
                {log.policy_hits.map((h, i) => (
                  <li key={i} className="text-[11px] text-orange-200 bg-orange-500/10 border border-orange-500/20 px-3 py-2 rounded-lg leading-relaxed">
                    {h}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Trilha de processamento */}
          <div>
            <p className="text-[10px] uppercase tracking-widest text-gray-500 font-bold mb-2">Trilha de processamento</p>
            <div className="space-y-1.5">
              {trilha.map((t, i) => (
                <div key={i} className={`flex items-center gap-3 text-[11px] px-3 py-2 rounded-lg border ${
                  t.ok ? 'bg-gray-900 border-gray-800' : 'bg-red-500/5 border-red-500/20'
                }`}>
                  <div className={`w-5 h-5 rounded-full border flex items-center justify-center text-[9px] font-bold ${
                    t.ok ? 'bg-blue-500/15 border-blue-500/40 text-blue-300' : 'bg-red-500/15 border-red-500/40 text-red-300'
                  }`}>
                    {i + 1}
                  </div>
                  <span className="font-semibold text-gray-200 w-36 shrink-0">{t.label}</span>
                  <span className="text-gray-400 flex-1 text-right font-mono">{t.valor}</span>
                </div>
              ))}
            </div>
          </div>

        </div>
      </div>
    </div>
  )
}
