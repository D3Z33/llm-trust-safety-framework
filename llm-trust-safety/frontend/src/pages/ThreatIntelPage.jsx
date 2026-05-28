import { useState, useEffect } from 'react'
import { threatIntelAPI } from '../utils/api'
import { formatRelative, formatDate } from '../utils/helpers'
import { LoadingSpinner, Card, StatCard, Button, SeverityBadge, toast, EmptyState } from '../components/ui'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  LineChart, Line, AreaChart, Area
} from 'recharts'
import { ShieldAlert, TrendingUp, Database, RefreshCw, Zap } from 'lucide-react'

const IOC_TYPE_LABELS = {
  pattern: 'Padrão Regex',
  keyword: 'Palavra-chave',
  ip: 'Endereço IP',
  hash: 'Hash',
}

const THREAT_ICONS = {
  prompt_injection: '💉',
  jailbreak: '🔓',
  data_exfiltration: '📤',
  goal_hijacking: '🎯',
  policy_evasion: '🎭',
  data_poisoning: '☠️',
  tool_abuse: '🔧',
  harmful_content: '⚠️',
  rag_poisoning: '🧪',
  model_theft: '🕵️',
}

export default function ThreatIntelPage() {
  const [iocs, setIocs] = useState([])
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [days, setDays] = useState(30)

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true)
      try {
        const [iocsRes, statsRes] = await Promise.all([
          threatIntelAPI.listar({ per_page: 20 }),
          threatIntelAPI.estatisticas(days),
        ])
        setIocs(iocsRes.data.entries)
        setStats(statsRes.data)
      } catch (e) {
        toast('Erro ao carregar Threat Intelligence', 'error')
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [days])

  if (loading) return <LoadingSpinner text="Carregando Threat Intelligence..." />

  const s = stats || {}

  const threatTypeData = (s.por_tipo || []).slice(0, 8).map(t => ({
    nome: t.nome || t.tipo,
    contagem: t.contagem,
    cor: t.cor,
  }))

  const timelineData = (s.timeline || []).slice(-14)

  const statCards = [
    { label: 'IOCs Ativos', value: iocs.length, icon: Database, color: '#3b82f6' },
    { label: 'Ameaças Detectadas', value: (s.por_tipo || []).reduce((a, b) => a + b.contagem, 0), icon: ShieldAlert, color: '#ef4444' },
    { label: 'Top IOC Hits', value: s.top_iocs?.[0]?.hit_count || 0, icon: Zap, color: '#f59e0b' },
    { label: 'Eventos Críticos', value: s.por_severidade?.critical || 0, icon: TrendingUp, color: '#8b5cf6' },
  ]

  return (
    <div className="p-6 space-y-6 bg-gray-950 min-h-screen">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <ShieldAlert className="w-6 h-6 text-orange-400" />
            Inteligência de Ameaças
          </h1>
          <p className="text-gray-400 text-sm mt-1">
            IOCs, padrões de ataque e análise de ameaças em tempo real
          </p>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex bg-gray-800 rounded-xl p-1">
            {[7, 30, 90].map(d => (
              <button key={d} onClick={() => setDays(d)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                  days === d ? 'bg-blue-600 text-white' : 'text-gray-400 hover:text-white'
                }`}>
                {d}d
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {statCards.map((s, i) => <StatCard key={i} {...s} />)}
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card title="Distribuição de Tipos de Ameaça">
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={threatTypeData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="nome" tick={{ fill: '#6b7280', fontSize: 10 }} />
              <YAxis tick={{ fill: '#6b7280', fontSize: 11 }} />
              <Tooltip contentStyle={{ background: '#1f2937', border: '1px solid #374151', borderRadius: '12px' }} />
              <Bar dataKey="contagem" name="Detecções" radius={[4, 4, 0, 0]}>
                {threatTypeData.map((entry, index) => (
                  <Bar key={index} dataKey="contagem" fill={entry.cor || '#ef4444'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </Card>

        <Card title="Timeline de Ameaças" subtitle={`Últimos ${days} dias`}>
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={timelineData}>
              <defs>
                <linearGradient id="threatGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="data" tick={{ fill: '#6b7280', fontSize: 10 }} />
              <YAxis tick={{ fill: '#6b7280', fontSize: 11 }} />
              <Tooltip contentStyle={{ background: '#1f2937', border: '1px solid #374151', borderRadius: '12px' }} />
              <Area type="monotone" dataKey="ameacas" name="Ameaças" stroke="#ef4444" fill="url(#threatGrad)" strokeWidth={2} />
            </AreaChart>
          </ResponsiveContainer>
        </Card>
      </div>

      {/* Top IOCs */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card title="Top IOCs Mais Acionados" subtitle="Por frequência de hit">
          <div className="space-y-3">
            {(s.top_iocs || []).map((ioc, i) => (
              <div key={i} className="flex items-center gap-3 p-3 bg-gray-700/30 rounded-xl">
                <span className="text-lg">{THREAT_ICONS[ioc.threat_type] || '⚡'}</span>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-gray-200 capitalize">
                      {ioc.threat_type?.replace(/_/g, ' ')}
                    </span>
                    <SeverityBadge severity={ioc.severity} />
                  </div>
                  <div className="flex items-center gap-3 mt-1 text-xs text-gray-500">
                    <span>{ioc.hit_count} hits</span>
                    {ioc.last_seen && <span>Última vez: {formatRelative(ioc.last_seen)}</span>}
                  </div>
                </div>
              </div>
            ))}
            {(!s.top_iocs || s.top_iocs.length === 0) && (
              <EmptyState icon={Database} title="Sem dados de IOC" description="Nenhum IOC acionado ainda" />
            )}
          </div>
        </Card>

        {/* Distribuição por severidade */}
        <Card title="Severidade dos Eventos" subtitle={`Últimos ${days} dias`}>
          <div className="space-y-4 mt-2">
            {[
              { key: 'critical', label: 'Crítico', color: '#ef4444' },
              { key: 'high', label: 'Alto', color: '#f97316' },
              { key: 'medium', label: 'Médio', color: '#f59e0b' },
              { key: 'low', label: 'Baixo', color: '#22c55e' },
            ].map(({ key, label, color }) => {
              const val = s.por_severidade?.[key] || 0
              const total = Object.values(s.por_severidade || {}).reduce((a, b) => a + b, 0) || 1
              const pct = (val / total) * 100
              return (
                <div key={key} className="space-y-1">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-300">{label}</span>
                    <span className="font-semibold" style={{ color }}>{val.toLocaleString('pt-BR')}</span>
                  </div>
                  <div className="h-2 bg-gray-700 rounded-full">
                    <div className="h-full rounded-full transition-all duration-700"
                      style={{ width: `${pct}%`, backgroundColor: color }} />
                  </div>
                </div>
              )
            })}
          </div>
        </Card>
      </div>

      {/* IOC List */}
      <Card title="Indicadores de Comprometimento (IOCs)" subtitle={`${iocs.length} IOCs ativos`}>
        <div className="space-y-2">
          {iocs.map((ioc) => (
            <div key={ioc.id} className="flex items-start gap-3 p-3 rounded-xl bg-gray-800/40 border border-gray-700/20 hover:border-gray-600/40 transition-all">
              <span className="text-lg mt-0.5">{THREAT_ICONS[ioc.threat_type] || '⚡'}</span>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="text-xs bg-gray-700 text-gray-300 px-2 py-0.5 rounded font-mono">
                    {IOC_TYPE_LABELS[ioc.ioc_type] || ioc.ioc_type}
                  </span>
                  <SeverityBadge severity={ioc.severity} />
                  <span className="text-xs text-gray-500">{ioc.source}</span>
                  {ioc.tags?.map((tag, i) => (
                    <span key={i} className="text-xs bg-blue-900/30 text-blue-300 px-2 py-0.5 rounded">{tag}</span>
                  ))}
                </div>
                <div className="text-sm text-gray-300 mt-1 font-mono bg-gray-900/50 rounded px-2 py-1 truncate">
                  {ioc.value}
                </div>
                {ioc.description && (
                  <p className="text-xs text-gray-500 mt-1">{ioc.description}</p>
                )}
              </div>
              <div className="text-right flex-shrink-0">
                <div className="text-sm font-bold text-white">{ioc.hit_count}</div>
                <div className="text-xs text-gray-500">hits</div>
                {ioc.last_seen && (
                  <div className="text-xs text-gray-600 mt-0.5">{formatRelative(ioc.last_seen)}</div>
                )}
              </div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  )
}
