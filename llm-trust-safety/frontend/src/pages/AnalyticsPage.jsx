import { useState, useEffect } from 'react'
import { analyticsAPI } from '../utils/api'
import { LoadingSpinner, Card, StatCard, Button } from '../components/ui'
import {
  AreaChart, Area, BarChart, Bar, LineChart, Line, XAxis, YAxis,
  CartesianGrid, Tooltip, ResponsiveContainer, Cell, ScatterChart, Scatter
} from 'recharts'
import { BarChart3, TrendingUp, Clock, Eye, RefreshCw } from 'lucide-react'

const CHART_TOOLTIP = {
  contentStyle: {
    background: '#1f2937', border: '1px solid #374151',
    borderRadius: '12px', fontSize: '12px'
  }
}

export default function AnalyticsPage() {
  const [overview, setOverview] = useState(null)
  const [tendencias, setTendencias] = useState(null)
  const [heatmap, setHeatmap] = useState(null)
  const [latencia, setLatencia] = useState(null)
  const [exposicao, setExposicao] = useState(null)
  const [topSessoes, setTopSessoes] = useState([])
  const [loading, setLoading] = useState(true)
  const [days, setDays] = useState(30)

  useEffect(() => {
    const fetch = async () => {
      setLoading(true)
      try {
        const [ov, td, hm, lat, exp, ts] = await Promise.all([
          analyticsAPI.visaoGeral(days),
          analyticsAPI.tendencias(days),
          analyticsAPI.heatmap(7),
          analyticsAPI.latencia(),
          analyticsAPI.exposicaoDados(days),
          analyticsAPI.topSessoes(),
        ])
        setOverview(ov.data)
        setTendencias(td.data.tendencias)
        setHeatmap(hm.data.heatmap)
        setLatencia(lat.data)
        setExposicao(exp.data)
        setTopSessoes(ts.data)
      } catch (e) {
        console.error(e)
      } finally {
        setLoading(false)
      }
    }
    fetch()
  }, [days])

  if (loading) return <LoadingSpinner text="Carregando analytics..." />

  const m = overview?.metricas || {}

  const latStats = latencia?.percentis || {}

  // Heatmap max para normalização
  const heatmapMax = heatmap ? Math.max(...heatmap.flatMap(d => d.dados.map(h => h.count))) || 1 : 1

  const piiData = (exposicao?.por_tipo || []).slice(0, 8)

  return (
    <div className="p-6 space-y-6 bg-gray-950 min-h-screen">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <BarChart3 className="w-6 h-6 text-green-400" />
            Analytics Avançado
          </h1>
          <p className="text-gray-400 text-sm mt-1">Análises detalhadas de segurança e performance</p>
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

      {/* KPI com variação */}
      <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
        {[
          { label: 'Total Avaliações', value: m.total_avaliacoes?.valor || 0, delta: m.total_avaliacoes?.delta_pct, icon: BarChart3, color: '#3b82f6' },
          { label: 'Total Bloqueados', value: m.total_bloqueados?.valor || 0, delta: m.total_bloqueados?.delta_pct, icon: TrendingUp, color: '#ef4444' },
          { label: 'Risco Médio', value: `${m.risco_medio?.valor || 0}`, delta: m.risco_medio?.delta_pct, icon: Eye, color: '#f59e0b' },
          { label: 'Eventos Críticos', value: m.eventos_criticos?.valor || 0, icon: TrendingUp, color: '#8b5cf6' },
          { label: 'Latência Média', value: `${m.latencia_media_ms?.valor || 0}ms`, icon: Clock, color: '#06b6d4' },
          { label: 'Taxa de Bloqueio', value: `${m.taxa_bloqueio?.valor || 0}%`, icon: Eye, color: '#10b981' },
        ].map((s, i) => (
          <StatCard key={i} {...s}
            trend={s.delta}
            trendPositive={s.delta > 0}
          />
        ))}
      </div>

      {/* Tendências */}
      <Card title="Tendências de Ataques" subtitle={`Últimos ${days} dias`}>
        <ResponsiveContainer width="100%" height={220}>
          <AreaChart data={tendencias || []}>
            <defs>
              <linearGradient id="attackGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="totalGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis dataKey="data" tick={{ fill: '#6b7280', fontSize: 11 }} />
            <YAxis tick={{ fill: '#6b7280', fontSize: 11 }} />
            <Tooltip {...CHART_TOOLTIP} />
            <Area type="monotone" dataKey="total" name="Total" stroke="#3b82f6" fill="url(#totalGrad)" strokeWidth={2} />
            <Area type="monotone" dataKey="ataques" name="Ataques" stroke="#ef4444" fill="url(#attackGrad)" strokeWidth={2} />
          </AreaChart>
        </ResponsiveContainer>
      </Card>

      {/* Heatmap de Ataques */}
      <Card title="Heatmap de Ataques" subtitle="Por hora do dia e dia da semana (últimos 7 dias)">
        {heatmap ? (
          <div className="overflow-x-auto">
            <div className="min-w-[600px]">
              {/* Labels das horas */}
              <div className="flex mb-1">
                <div className="w-20 flex-shrink-0" />
                {Array.from({ length: 24 }, (_, h) => (
                  <div key={h} className="flex-1 text-center text-xs text-gray-600">
                    {h % 4 === 0 ? `${h}h` : ''}
                  </div>
                ))}
              </div>
              {heatmap.map((row) => (
                <div key={row.dia} className="flex items-center mb-1">
                  <div className="w-20 text-xs text-gray-400 flex-shrink-0">{row.dia}</div>
                  {row.dados.map((cell) => {
                    const intensity = cell.count / heatmapMax
                    return (
                      <div
                        key={cell.hora}
                        className="flex-1 h-6 rounded-sm mx-0.5 transition-all hover:scale-110 cursor-default"
                        style={{
                          backgroundColor: cell.count === 0
                            ? '#1f2937'
                            : `rgba(239, 68, 68, ${0.1 + intensity * 0.9})`,
                        }}
                        title={`${row.dia} ${cell.hora}h: ${cell.count} ataques`}
                      />
                    )
                  })}
                </div>
              ))}
              {/* Legenda */}
              <div className="flex items-center gap-2 mt-2 text-xs text-gray-500">
                <span>Menos</span>
                {[0.1, 0.3, 0.5, 0.7, 0.9].map(v => (
                  <div key={v} className="w-4 h-4 rounded-sm"
                    style={{ backgroundColor: `rgba(239, 68, 68, ${v})` }} />
                ))}
                <span>Mais</span>
              </div>
            </div>
          </div>
        ) : (
          <p className="text-gray-500 text-sm">Sem dados suficientes</p>
        )}
      </Card>

      {/* Latência + Exposição */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Latência */}
        <Card title="Análise de Latência" subtitle="Percentis de performance">
          {latencia ? (
            <div className="space-y-4">
              <div className="grid grid-cols-3 gap-3">
                {[
                  { label: 'Mediana (P50)', value: `${latStats.p50?.toFixed(0) || 0}ms`, color: '#22c55e' },
                  { label: 'P90', value: `${latStats.p90?.toFixed(0) || 0}ms`, color: latStats.p90 > 200 ? '#f59e0b' : '#22c55e' },
                  { label: 'P99', value: `${latStats.p99?.toFixed(0) || 0}ms`, color: latStats.p99 > 200 ? '#ef4444' : '#f59e0b' },
                ].map((s, i) => (
                  <div key={i} className="bg-gray-700/30 rounded-xl p-3 text-center">
                    <div className="text-lg font-bold" style={{ color: s.color }}>{s.value}</div>
                    <div className="text-xs text-gray-500 mt-1">{s.label}</div>
                  </div>
                ))}
              </div>
              <div className="p-3 rounded-xl" style={{
                backgroundColor: latencia.percentual_sla >= 95 ? '#16a34a22' : '#ef444422',
                borderColor: latencia.percentual_sla >= 95 ? '#16a34a44' : '#ef444444',
                border: '1px solid',
              }}>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-300">SLA ≤ 200ms</span>
                  <span className="font-bold text-lg" style={{
                    color: latencia.percentual_sla >= 95 ? '#22c55e' : '#ef4444'
                  }}>
                    {latencia.percentual_sla || 0}%
                  </span>
                </div>
                <div className="mt-2 h-2 bg-gray-700 rounded-full overflow-hidden">
                  <div className="h-full rounded-full transition-all duration-700"
                    style={{
                      width: `${latencia.percentual_sla || 0}%`,
                      backgroundColor: latencia.percentual_sla >= 95 ? '#22c55e' : '#ef4444'
                    }} />
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  {latencia.dentro_sla_200ms || 0}/{latencia.total_amostras || 0} requisições dentro do SLA
                </p>
              </div>
            </div>
          ) : (
            <p className="text-gray-500 text-sm">Sem dados de latência</p>
          )}
        </Card>

        {/* Exposição de Dados */}
        <Card title="Exposição de Dados PII" subtitle={`${exposicao?.total_pii_detectado || 0} ocorrências detectadas`}>
          <div className="space-y-3">
            {piiData.length === 0 ? (
              <div className="flex items-center gap-3 p-3 bg-green-900/10 border border-green-700/20 rounded-xl">
                <span className="text-2xl">✅</span>
                <div>
                  <p className="text-green-400 font-medium">Nenhuma exposição de PII detectada</p>
                  <p className="text-xs text-gray-400 mt-0.5">O sistema está protegendo os dados adequadamente</p>
                </div>
              </div>
            ) : (
              piiData.map((pii, i) => (
                <div key={i} className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-xs bg-purple-900/40 text-purple-300 border border-purple-800/50 px-2 py-0.5 rounded">
                      {pii.tipo}
                    </span>
                    <span className="text-xs text-gray-400">{pii.descricao}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-20 h-1.5 bg-gray-700 rounded-full overflow-hidden">
                      <div className="h-full bg-purple-500 rounded-full"
                        style={{ width: `${pii.percentual}%` }} />
                    </div>
                    <span className="text-xs text-gray-300 w-8 text-right">{pii.contagem}</span>
                  </div>
                </div>
              ))
            )}
          </div>
        </Card>
      </div>

      {/* Top Sessões de Risco */}
      <Card title="Sessões com Maior Risco" subtitle="Top 10 sessões mais perigosas">
        <div className="space-y-2">
          {topSessoes.slice(0, 8).map((sess, i) => (
            <div key={sess.session_id} className="flex items-center gap-4 p-3 bg-gray-800/30 rounded-xl">
              <span className="text-gray-600 font-bold w-5 text-center">{i + 1}</span>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${
                    sess.state === 'BLOCKED' ? 'bg-red-900/40 text-red-400' :
                    sess.state === 'SUSPICIOUS' ? 'bg-yellow-900/40 text-yellow-400' :
                    'bg-gray-700 text-gray-400'
                  }`}>{sess.state}</span>
                  <span className="text-xs text-gray-500 font-mono truncate">{sess.session_id.slice(0, 12)}...</span>
                </div>
                <div className="flex gap-4 mt-1 text-xs text-gray-500">
                  <span>{sess.attack_count} ataques</span>
                  <span>{sess.total_interactions} interações</span>
                </div>
              </div>
              <div className="text-right flex-shrink-0">
                <div className="text-sm font-bold text-red-400">{sess.max_risk_score?.toFixed(0)}</div>
                <div className="text-xs text-gray-500">max risk</div>
              </div>
            </div>
          ))}
          {topSessoes.length === 0 && (
            <p className="text-gray-500 text-sm text-center py-6">Nenhuma sessão de alto risco encontrada</p>
          )}
        </div>
      </Card>
    </div>
  )
}
