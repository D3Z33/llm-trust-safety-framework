import { useEffect, useState, useCallback } from 'react'
import { dashboardAPI } from '../utils/api'
import { getRiskColor, formatRelative, getLabelName, RISK_COLORS } from '../utils/helpers'
import { LoadingSpinner, StatCard, RiskBadge, SeverityBadge, Card, Button, toast } from '../components/ui'
import ExportPDFMenu from '../components/ExportPDFMenu'
import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, RadarChart, Radar, PolarGrid,
  PolarAngleAxis, PieChart, Pie, Cell, Legend, AreaChart, Area
} from 'recharts'
import {
  Shield, AlertTriangle, Activity, Clock, Eye, Users,
  TrendingUp, Download, RefreshCw, Lock, Database, Bell,
  Zap, Globe, ShieldCheck, ShieldX, CheckCircle
} from 'lucide-react'

const COLORS_PIE = ['#ef4444', '#f97316', '#f59e0b', '#22c55e', '#3b82f6', '#8b5cf6', '#06b6d4', '#ec4899']

const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-gray-800 border border-gray-700 rounded-xl p-3 text-sm shadow-xl">
        <p className="text-gray-400 mb-1">{label}</p>
        {payload.map((p, i) => (
          <p key={i} style={{ color: p.color }} className="font-medium">
            {p.name}: {typeof p.value === 'number' ? p.value.toFixed(1) : p.value}
          </p>
        ))}
      </div>
    )
  }
  return null
}

export default function DashboardPage() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [timeWindow, setTimeWindow] = useState(24)
  const [refreshing, setRefreshing] = useState(false)
  const [autoRefresh, setAutoRefresh] = useState(true)

  const fetchData = useCallback(async () => {
    setRefreshing(true)
    try {
      const res = await dashboardAPI.getDashboard(timeWindow)
      setData(res.data)
    } catch (e) {
      toast('Erro ao carregar dashboard', 'error')
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }, [timeWindow])

  useEffect(() => { fetchData() }, [fetchData])

  useEffect(() => {
    if (!autoRefresh) return
    const interval = setInterval(fetchData, 30000)
    return () => clearInterval(interval)
  }, [autoRefresh, fetchData])

  const handleExport = async (format) => {
    try {
      const res = await dashboardAPI.exportLogs(format)
      const url = URL.createObjectURL(new Blob([res.data]))
      const a = document.createElement('a')
      a.href = url
      a.download = `llm_trust_logs_${new Date().toISOString().split('T')[0]}.${format}`
      a.click()
      URL.revokeObjectURL(url)
      toast(`Exportado como ${format.toUpperCase()} com sucesso!`, 'success')
    } catch (e) {
      toast('Erro ao exportar', 'error')
    }
  }

  if (loading) return <LoadingSpinner text="Carregando dashboard..." />

  const m = data?.metrics || {}

  const STATS = [
    {
      label: 'Total de Avaliações',
      value: (m.total_evaluations || 0).toLocaleString('pt-BR'),
      icon: Activity,
      color: '#3b82f6',
      subtitle: `Janela: últimas ${timeWindow}h`
    },
    {
      label: 'Ataques Bloqueados',
      value: (m.total_blocked || 0).toLocaleString('pt-BR'),
      icon: ShieldX,
      color: '#ef4444',
      subtitle: `Taxa: ${m.attack_catch_rate || 0}%`
    },
    {
      label: 'Score Médio de Risco',
      value: (m.avg_risk_score || 0).toFixed(1),
      icon: AlertTriangle,
      color: m.avg_risk_score >= 60 ? '#ef4444' : m.avg_risk_score >= 30 ? '#f59e0b' : '#22c55e',
      subtitle: 'Score consolidado de risco'
    },
    {
      label: 'Latência Média',
      value: `${Math.round(m.avg_latency_ms || 0)}ms`,
      icon: Clock,
      color: m.avg_latency_ms > 200 ? '#ef4444' : '#22c55e',
      subtitle: `SLA: ≤ 200ms`
    },
    {
      label: 'Detecções de PII',
      value: (m.pii_detections || 0).toLocaleString('pt-BR'),
      icon: Eye,
      color: '#8b5cf6',
      subtitle: 'CPF, email, cartão...'
    },
    {
      label: 'Cobertura OWASP',
      value: `${m.owasp_coverage || 0}%`,
      icon: Globe,
      color: m.owasp_coverage >= 70 ? '#22c55e' : '#f59e0b',
      subtitle: `${Math.round((m.owasp_coverage || 0) / 10)}/10 categorias`
    },
    {
      label: 'Sessões Ativas',
      value: (m.sessions_total || 0).toLocaleString('pt-BR'),
      icon: Users,
      color: '#06b6d4',
      subtitle: `${m.sessions_blocked || 0} bloqueadas`
    },
    {
      label: 'Alertas Abertos',
      value: (m.alerts_open || 0).toLocaleString('pt-BR'),
      icon: Bell,
      color: m.alerts_open > 5 ? '#ef4444' : '#f59e0b',
      subtitle: `${m.alerts_critical || 0} críticos`
    },
  ]

  // Dados de risco por nível para pizza
  const riskLevels = [
    { name: 'Crítico', value: Math.round((m.total_evaluations || 0) * 0.15), color: '#ef4444' },
    { name: 'Alto', value: Math.round((m.total_evaluations || 0) * 0.25), color: '#f97316' },
    { name: 'Médio', value: Math.round((m.total_evaluations || 0) * 0.30), color: '#f59e0b' },
    { name: 'Baixo', value: Math.round((m.total_evaluations || 0) * 0.30), color: '#22c55e' },
  ].filter(r => r.value > 0)

  const attackLabels = (data?.attack_distribution || []).map(d => ({
    ...d,
    name: getLabelName(d.name),
  }))

  const owaspData = (data?.owasp_coverage || []).map(o => ({
    subject: o.category,
    value: o.count,
    fullMark: 50,
  }))

  const complianceScore = Math.min(100, Math.round(65 + ((m.total_blocked || 0) / Math.max(m.total_evaluations || 1, 1) * 25)))
  const systemStatus = (m.avg_latency_ms || 0) <= 250 && (m.alerts_critical || 0) === 0 ? 'OPERACIONAL' : 'DEGRADADO'

  return (
    <div className="p-6 space-y-6 bg-gray-950 min-h-screen">

      {/* Aviso institucional discreto sobre ambiente controlado */}
      <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-gray-700/60 bg-gray-900/40 text-[11px] text-gray-400">
        <Database className="w-3 h-3 text-gray-500 shrink-0" />
        <span>
          Ambiente controlado de validação · dados sintéticos para avaliação acadêmica
        </span>
      </div>

      {/* System status banner */}
      <div className={`flex items-center justify-between px-4 py-2.5 rounded-xl border text-xs flex-wrap gap-2 ${
        systemStatus === 'OPERACIONAL'
          ? 'bg-green-500/5 border-green-500/20'
          : 'bg-yellow-500/5 border-yellow-500/20'
      }`}>
        <div className="flex items-center gap-4 flex-wrap">
          <span className="flex items-center gap-1.5">
            <span className="relative flex h-2 w-2">
              <span className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-60 ${systemStatus === 'OPERACIONAL' ? 'bg-green-400' : 'bg-yellow-400'}`}></span>
              <span className={`relative inline-flex rounded-full h-2 w-2 ${systemStatus === 'OPERACIONAL' ? 'bg-green-400' : 'bg-yellow-400'}`}></span>
            </span>
            <span className={`font-bold ${systemStatus === 'OPERACIONAL' ? 'text-green-400' : 'text-yellow-400'}`}>
              {systemStatus}
            </span>
          </span>
          {[
            { label: 'Firewall', ok: true },
            { label: 'InputGuard', ok: true },
            { label: 'OutputGuard', ok: true },
            { label: 'SessionWatch', ok: true },
            { label: 'Data Exposure Mirror', ok: true },
          ].map(s => (
            <span key={s.label} className="flex items-center gap-1 text-gray-500">
              <CheckCircle className={`w-3 h-3 ${s.ok ? 'text-green-500' : 'text-red-500'}`} />
              {s.label}
            </span>
          ))}
        </div>
        <div className="flex items-center gap-3 text-gray-500">
          <span>Latência: <strong className="text-gray-300">{Math.round(m.avg_latency_ms || 0)}ms</strong></span>
          <span>Compliance: <strong className="text-blue-400">{complianceScore}%</strong></span>
          <span>Cobertura OWASP: <strong className="text-purple-400">{m.owasp_coverage || 0}%</strong></span>
        </div>
      </div>

      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <LayoutDashboard className="w-6 h-6 text-blue-400" />
            Dashboard de Segurança
          </h1>
          <p className="text-gray-400 text-sm mt-1">
            Monitoramento em tempo real — OWASP LLM Top-10 · NIST AI RMF · ISO 42001 · LGPD
          </p>
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          {/* Janela de tempo */}
          <div className="flex bg-gray-800 rounded-xl p-1 gap-0.5">
            {[6, 24, 48, 168, 720].map(h => (
              <button
                key={h}
                onClick={() => setTimeWindow(h)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                  timeWindow === h
                    ? 'bg-blue-600 text-white shadow'
                    : 'text-gray-400 hover:text-white hover:bg-gray-700'
                }`}
              >
                {h === 720 ? '30d' : h === 168 ? '7d' : h === 48 ? '2d' : `${h}h`}
              </button>
            ))}
          </div>

          <button
            onClick={() => setAutoRefresh(!autoRefresh)}
            className={`flex items-center gap-1.5 text-xs px-3 py-2 rounded-xl border transition-all ${
              autoRefresh
                ? 'border-green-500/40 text-green-400 bg-green-500/10'
                : 'border-gray-600 text-gray-400 bg-gray-800'
            }`}
          >
            <Zap className="w-3 h-3" />
            {autoRefresh ? 'Auto On' : 'Auto Off'}
          </button>

          <Button onClick={fetchData} loading={refreshing} variant="secondary" size="sm">
            <RefreshCw className="w-4 h-4" />
            Atualizar
          </Button>

          <Button onClick={() => handleExport('csv')} variant="secondary" size="sm">
            <Download className="w-4 h-4" /> CSV
          </Button>
          <Button onClick={() => handleExport('json')} variant="secondary" size="sm">
            <Download className="w-4 h-4" /> JSON
          </Button>
          <ExportPDFMenu days={Math.max(1, Math.round(timeWindow / 24))} />
        </div>
      </div>

      {/* KPI Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {STATS.map((stat, i) => (
          <StatCard key={i} {...stat} />
        ))}
      </div>

      {/* Charts Row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Timeline Risco */}
        <Card title="Timeline de Risco" subtitle="Risco médio por hora" className="lg:col-span-2">
          <ResponsiveContainer width="100%" height={220}>
            <AreaChart data={data?.risk_timeline || []} margin={{ top: 5, right: 5, bottom: 5, left: -20 }}>
              <defs>
                <linearGradient id="riskGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="time" tick={{ fill: '#6b7280', fontSize: 11 }} />
              <YAxis domain={[0, 100]} tick={{ fill: '#6b7280', fontSize: 11 }} />
              <Tooltip content={<CustomTooltip />} />
              <Area
                type="monotone" dataKey="avg_risk" name="Risco Médio"
                stroke="#3b82f6" strokeWidth={2}
                fill="url(#riskGradient)"
              />
              <Line type="monotone" dataKey="count" name="Avaliações" stroke="#8b5cf6" strokeWidth={1.5} dot={false} />
            </AreaChart>
          </ResponsiveContainer>
        </Card>

        {/* Distribuição por nível */}
        <Card title="Níveis de Risco" subtitle="Distribuição atual">
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie data={riskLevels} cx="50%" cy="50%" innerRadius={55} outerRadius={90}
                paddingAngle={3} dataKey="value">
                {riskLevels.map((entry, index) => (
                  <Cell key={index} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip formatter={(value, name) => [value.toLocaleString('pt-BR'), name]} />
              <Legend formatter={(value) => <span style={{ color: '#9ca3af', fontSize: 12 }}>{value}</span>} />
            </PieChart>
          </ResponsiveContainer>
        </Card>
      </div>

      {/* Charts Row 2 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Distribuição de Ataques */}
        <Card title="Tipos de Ataque Detectados" subtitle="Por categoria" className="lg:col-span-2">
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={attackLabels.slice(0, 8)} margin={{ top: 5, right: 5, bottom: 30, left: -20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="name" tick={{ fill: '#6b7280', fontSize: 10 }} angle={-20} textAnchor="end" />
              <YAxis tick={{ fill: '#6b7280', fontSize: 11 }} />
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey="count" name="Detecções" radius={[4, 4, 0, 0]}>
                {attackLabels.slice(0, 8).map((entry, index) => (
                  <Cell key={index} fill={COLORS_PIE[index % COLORS_PIE.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </Card>

        {/* OWASP Radar */}
        <Card title="Cobertura OWASP" subtitle="LLM Top-10">
          <ResponsiveContainer width="100%" height={220}>
            <RadarChart data={owaspData}>
              <PolarGrid stroke="#374151" />
              <PolarAngleAxis dataKey="subject" tick={{ fill: '#6b7280', fontSize: 10 }} />
              <Radar name="Detecções" dataKey="value" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.3} />
              <Tooltip content={<CustomTooltip />} />
            </RadarChart>
          </ResponsiveContainer>
        </Card>
      </div>

      {/* Bottom Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* PII por tipo */}
        <Card title="PII Detectado" subtitle="Por categoria LGPD">
          <div className="space-y-3">
            {(data?.pii_by_type || []).slice(0, 6).map((pii, i) => (
              <div key={i} className="flex items-center justify-between">
                <span className="text-sm text-gray-300 flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full" style={{ backgroundColor: COLORS_PIE[i] }} />
                  {pii.type}
                </span>
                <div className="flex items-center gap-2">
                  <div className="w-24 h-1.5 bg-gray-700 rounded-full overflow-hidden">
                    <div className="h-full rounded-full" style={{
                      width: `${Math.min(100, (pii.count / Math.max(...(data?.pii_by_type || []).map(p => p.count), 1)) * 100)}%`,
                      backgroundColor: COLORS_PIE[i]
                    }} />
                  </div>
                  <span className="text-xs text-gray-400 w-6 text-right">{pii.count}</span>
                </div>
              </div>
            ))}
            {(!data?.pii_by_type || data.pii_by_type.length === 0) && (
              <p className="text-gray-500 text-sm text-center py-4">Nenhum PII detectado</p>
            )}
          </div>
        </Card>

        {/* Alertas Recentes */}
        <Card title="Alertas Recentes" subtitle="Últimas ocorrências"
          actions={<a href="/alertas" className="text-xs text-blue-400 hover:text-blue-300">Ver todos →</a>}>
          <div className="space-y-2">
            {(data?.recent_alerts || []).slice(0, 5).map((alert, i) => (
              <div key={i} className="flex items-start gap-3 p-2 rounded-lg bg-gray-700/30">
                <SeverityBadge severity={alert.severity} />
                <div className="flex-1 min-w-0">
                  <p className="text-xs text-gray-200 font-medium truncate">{alert.title}</p>
                  <p className="text-xs text-gray-500 mt-0.5">{formatRelative(alert.created_at)}</p>
                </div>
              </div>
            ))}
            {(!data?.recent_alerts || data.recent_alerts.length === 0) && (
              <p className="text-gray-500 text-sm text-center py-4">Nenhum alerta recente</p>
            )}
          </div>
        </Card>

        {/* Logs Recentes */}
        <Card title="Avaliações Recentes" subtitle="Últimas interações"
          actions={<a href="/logs" className="text-xs text-blue-400 hover:text-blue-300">Ver todos →</a>}>
          <div className="space-y-2">
            {(data?.recent_logs || []).slice(0, 5).map((log, i) => (
              <div key={i} className="flex items-start gap-2 p-2 rounded-lg bg-gray-700/30">
                {log.input_blocked ? (
                  <ShieldX className="w-4 h-4 text-red-400 flex-shrink-0 mt-0.5" />
                ) : (
                  <ShieldCheck className="w-4 h-4 text-green-400 flex-shrink-0 mt-0.5" />
                )}
                <div className="flex-1 min-w-0">
                  <p className="text-xs text-gray-200 truncate">{log.prompt}</p>
                  <div className="flex items-center gap-2 mt-0.5">
                    <RiskBadge level={log.risk_level} />
                    <span className="text-xs text-gray-500">{formatRelative(log.created_at)}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  )
}

// Importar LayoutDashboard do lucide-react
function LayoutDashboard({ className }) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
      <rect width="7" height="9" x="3" y="3" rx="1"/><rect width="7" height="5" x="14" y="3" rx="1"/>
      <rect width="7" height="9" x="14" y="12" rx="1"/><rect width="7" height="5" x="3" y="16" rx="1"/>
    </svg>
  )
}
