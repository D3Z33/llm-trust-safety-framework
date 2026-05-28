import { useState, useEffect } from 'react'
import { conformidadeAPI } from '../utils/api'
import { LoadingSpinner, Card, Button, ScoreBar, StatCard, Modal, Select, toast } from '../components/ui'
import ExportPDFMenu from '../components/ExportPDFMenu'
import { scoreToGrade } from '../utils/helpers'
import {
  RadarChart, Radar, PolarGrid, PolarAngleAxis, ResponsiveContainer, Tooltip,
  BarChart, Bar, XAxis, YAxis, CartesianGrid
} from 'recharts'
import { Globe, CheckCircle, XCircle, AlertTriangle, FileText, RefreshCw, Download } from 'lucide-react'

export default function ConformidadePage() {
  const [visaoGeral, setVisaoGeral] = useState(null)
  const [nist, setNist] = useState(null)
  const [lgpd, setLgpd] = useState(null)
  const [owasp, setOwasp] = useState(null)
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('visao-geral')
  const [reportModal, setReportModal] = useState(false)
  const [reportFramework, setReportFramework] = useState('NIST')
  const [reportPeriod, setReportPeriod] = useState(30)
  const [generatingReport, setGeneratingReport] = useState(false)
  const [generatedReport, setGeneratedReport] = useState(null)

  useEffect(() => {
    const fetchAll = async () => {
      setLoading(true)
      try {
        const [vg, n, l, o] = await Promise.all([
          conformidadeAPI.visaoGeral(),
          conformidadeAPI.nist(),
          conformidadeAPI.lgpd(),
          conformidadeAPI.owasp(),
        ])
        setVisaoGeral(vg.data)
        setNist(n.data)
        setLgpd(l.data)
        setOwasp(o.data)
      } catch (e) {
        toast('Erro ao carregar dados de conformidade', 'error')
      } finally {
        setLoading(false)
      }
    }
    fetchAll()
  }, [])

  const handleGerarRelatorio = async () => {
    setGeneratingReport(true)
    try {
      const res = await conformidadeAPI.gerarRelatorio({
        framework: reportFramework,
        period_days: reportPeriod,
      })
      setGeneratedReport(res.data)
      toast('Relatório gerado com sucesso!', 'success')
    } catch (e) {
      toast('Erro ao gerar relatório', 'error')
    } finally {
      setGeneratingReport(false)
    }
  }

  if (loading) return <LoadingSpinner text="Carregando dados de conformidade..." />

  const vg = visaoGeral || {}
  const scoreGeral = vg.score_geral || 0
  const { grade, color: gradeColor } = scoreToGrade(scoreGeral)

  const radarData = (vg.frameworks || []).map(f => ({
    framework: f.nome.split(' ')[0],
    score: f.score,
  }))

  const TABS = [
    { id: 'visao-geral', label: 'Visão Geral' },
    { id: 'nist', label: 'NIST AI RMF' },
    { id: 'lgpd', label: 'LGPD' },
    { id: 'owasp', label: 'OWASP Top-10' },
  ]

  return (
    <div className="p-6 space-y-6 bg-gray-950 min-h-screen">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Globe className="w-6 h-6 text-violet-400" />
            Conformidade &amp; Compliance
          </h1>
          <p className="text-gray-400 text-sm mt-1">
            NIST AI RMF 1.0 · ISO/IEC 42001 · ISO/IEC 27001 · LGPD · OWASP LLM Top-10
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button onClick={() => setReportModal(true)} variant="primary" size="sm">
            <FileText className="w-4 h-4" />
            Gerar Relatório
          </Button>
          <ExportPDFMenu days={30} tipos={["conformidade", "executivo", "sessoes_alertas"]} />
        </div>
      </div>

      {/* Score Geral */}
      <div className="bg-gradient-to-r from-violet-900/30 to-blue-900/30 border border-violet-700/30 rounded-2xl p-6">
        <div className="flex items-center gap-8">
          <div className="text-center">
            <div className="text-6xl font-bold" style={{ color: gradeColor }}>{grade}</div>
            <div className="text-gray-400 text-sm mt-1">Nota Geral</div>
          </div>
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-2">
              <span className="text-3xl font-bold text-white">{scoreGeral.toFixed(1)}</span>
              <span className="text-gray-400">/100</span>
            </div>
            <div className="h-3 bg-gray-700/50 rounded-full overflow-hidden mb-4">
              <div
                className="h-full rounded-full transition-all duration-1000"
                style={{ width: `${scoreGeral}%`, backgroundColor: gradeColor }}
              />
            </div>
            <p className="text-gray-400 text-sm">
              Score composto de {vg.frameworks?.length || 0} frameworks de segurança e privacidade
            </p>
          </div>
          <ResponsiveContainer width={200} height={160}>
            <RadarChart data={radarData} margin={{ top: 10, right: 10, bottom: 10, left: 10 }}>
              <PolarGrid stroke="#374151" />
              <PolarAngleAxis dataKey="framework" tick={{ fill: '#9ca3af', fontSize: 9 }} />
              <Radar dataKey="score" stroke="#8b5cf6" fill="#8b5cf6" fillOpacity={0.3} />
            </RadarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Framework Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-3 xl:grid-cols-5 gap-4">
        {(vg.frameworks || []).map((fw) => {
          const { grade: g, color: c } = scoreToGrade(fw.score)
          return (
            <div key={fw.id} className="bg-gray-800/60 border border-gray-700/50 rounded-2xl p-4 hover:border-gray-600 transition-all">
              <div className="flex items-center justify-between mb-3">
                <span className="text-2xl font-bold" style={{ color: c }}>{g}</span>
                <span className="text-lg font-bold text-white">{fw.score.toFixed(0)}%</span>
              </div>
              <h4 className="text-sm font-semibold text-white mb-1">{fw.nome.split(' ')[0]}</h4>
              <p className="text-xs text-gray-400 mb-3">{fw.nome}</p>
              <div className="h-1.5 bg-gray-700 rounded-full overflow-hidden mb-2">
                <div className="h-full rounded-full" style={{ width: `${fw.score}%`, backgroundColor: fw.cor }} />
              </div>
              <div className="flex items-center justify-between text-xs">
                <span style={{
                  color: fw.status === 'Conforme' ? '#22c55e' : fw.status === 'Parcialmente Conforme' ? '#f59e0b' : '#ef4444'
                }}>
                  {fw.status === 'Conforme' ? '✓' : fw.status === 'Parcialmente Conforme' ? '◐' : '✗'} {fw.status}
                </span>
                <span className="text-gray-500">{fw.controles_atendidos}/{fw.controles_total}</span>
              </div>
            </div>
          )
        })}
      </div>

      {/* Tabs */}
      <div className="flex gap-1 bg-gray-800/50 rounded-xl p-1 w-fit">
        {TABS.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
              activeTab === tab.id ? 'bg-blue-600 text-white' : 'text-gray-400 hover:text-white'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      {activeTab === 'visao-geral' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* NIST + LGPD bars */}
          <Card title="Scores por Framework">
            <div className="space-y-4">
              {(vg.frameworks || []).map(fw => (
                <ScoreBar key={fw.id} label={fw.nome.split('(')[0].trim()} score={fw.score} color={fw.cor} />
              ))}
            </div>
          </Card>
          {/* Métricas base */}
          <Card title="Métricas Base">
            <div className="grid grid-cols-2 gap-4">
              {Object.entries(vg.metricas_base || {}).map(([k, v]) => (
                <div key={k} className="bg-gray-700/30 rounded-xl p-3">
                  <div className="text-lg font-bold text-white">{typeof v === 'number' ? v.toLocaleString('pt-BR') : v}</div>
                  <div className="text-xs text-gray-400 mt-1 capitalize">{k.replace(/_/g, ' ')}</div>
                </div>
              ))}
            </div>
          </Card>
        </div>
      )}

      {activeTab === 'nist' && nist && (
        <div className="space-y-4">
          {nist.funcoes?.map((func) => (
            <Card key={func.id} title={`${func.id}: ${func.nome}`} subtitle={func.descricao}
              badge={
                <span className="text-sm font-bold" style={{
                  color: func.score_medio >= 70 ? '#22c55e' : func.score_medio >= 40 ? '#f59e0b' : '#ef4444'
                }}>
                  {func.score_medio.toFixed(0)}%
                </span>
              }
            >
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {func.controles?.map((ctrl) => (
                  <div key={ctrl.id} className="flex items-start gap-3 p-3 bg-gray-700/30 rounded-xl">
                    {ctrl.score >= 70 ? (
                      <CheckCircle className="w-4 h-4 text-green-400 mt-0.5 flex-shrink-0" />
                    ) : ctrl.score >= 40 ? (
                      <AlertTriangle className="w-4 h-4 text-yellow-400 mt-0.5 flex-shrink-0" />
                    ) : (
                      <XCircle className="w-4 h-4 text-red-400 mt-0.5 flex-shrink-0" />
                    )}
                    <div className="flex-1">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-mono text-gray-500">{ctrl.id}</span>
                        <span className="text-xs font-semibold" style={{
                          color: ctrl.score >= 70 ? '#22c55e' : ctrl.score >= 40 ? '#f59e0b' : '#ef4444'
                        }}>{ctrl.score.toFixed(0)}%</span>
                      </div>
                      <p className="text-sm text-gray-200 mt-0.5">{ctrl.nome}</p>
                      <p className="text-xs text-gray-500 mt-0.5">{ctrl.evidencia}</p>
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          ))}
        </div>
      )}

      {activeTab === 'lgpd' && lgpd && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {lgpd.controles?.map((ctrl) => (
            <div key={ctrl.id} className={`p-4 rounded-2xl border ${
              ctrl.score >= 70 ? 'bg-green-900/10 border-green-700/30' :
              ctrl.score >= 40 ? 'bg-yellow-900/10 border-yellow-700/30' :
              'bg-red-900/10 border-red-700/30'
            }`}>
              <div className="flex items-start justify-between gap-3">
                <div>
                  <span className="text-xs font-mono text-gray-500 bg-gray-700 px-2 py-0.5 rounded">{ctrl.artigo}</span>
                  <h4 className="font-semibold text-white mt-2">{ctrl.nome}</h4>
                </div>
                <div className="text-right">
                  <div className="text-xl font-bold" style={{
                    color: ctrl.score >= 70 ? '#22c55e' : ctrl.score >= 40 ? '#f59e0b' : '#ef4444'
                  }}>{ctrl.score.toFixed(0)}%</div>
                  <div className="text-xs text-gray-500">{ctrl.status}</div>
                </div>
              </div>
              {ctrl.evidencias?.length > 0 && (
                <div className="mt-3 space-y-1">
                  {ctrl.evidencias.map((e, i) => (
                    <div key={i} className="flex items-center gap-2 text-xs text-gray-400">
                      <CheckCircle className="w-3 h-3 text-green-400" />
                      {e}
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {activeTab === 'owasp' && owasp && (
        <div className="space-y-4">
          <div className="flex items-center gap-4 p-4 bg-blue-900/20 border border-blue-700/30 rounded-xl">
            <div className="text-3xl font-bold text-blue-400">{owasp.percentual}%</div>
            <div>
              <div className="text-white font-semibold">Cobertura Total</div>
              <div className="text-gray-400 text-sm">{owasp.cobertura_total}/{owasp.total_categorias} categorias cobertas</div>
            </div>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {owasp.categorias?.map((cat) => (
              <div key={cat.id} className={`p-4 rounded-xl border ${
                cat.coberto ? 'bg-green-900/10 border-green-700/30' : 'bg-gray-800/40 border-gray-700/30'
              }`}>
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    {cat.coberto ? (
                      <CheckCircle className="w-4 h-4 text-green-400" />
                    ) : (
                      <XCircle className="w-4 h-4 text-gray-500" />
                    )}
                    <span className="font-mono text-xs text-gray-400">{cat.id}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                      cat.nivel_cobertura === 'Total' ? 'bg-green-900/40 text-green-400' :
                      cat.nivel_cobertura === 'Parcial' ? 'bg-yellow-900/40 text-yellow-400' :
                      'bg-gray-700/50 text-gray-500'
                    }`}>{cat.nivel_cobertura}</span>
                    {cat.deteccoes > 0 && (
                      <span className="text-xs text-gray-400">{cat.deteccoes} detecções</span>
                    )}
                  </div>
                </div>
                <h4 className="font-semibold text-white text-sm">{cat.nome}</h4>
                <p className="text-xs text-gray-400 mt-1">{cat.descricao}</p>
                <div className="flex flex-wrap gap-1 mt-2">
                  {cat.mitigacoes?.map((m, i) => (
                    <span key={i} className="text-xs bg-gray-700/50 text-gray-300 px-2 py-0.5 rounded">{m}</span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Modal Relatório */}
      <Modal isOpen={reportModal} onClose={() => { setReportModal(false); setGeneratedReport(null) }}
        title="Gerar Relatório de Conformidade" size="lg">
        {!generatedReport ? (
          <div className="space-y-4">
            <Select label="Framework" value={reportFramework} onChange={e => setReportFramework(e.target.value)}>
              <option value="NIST">NIST AI RMF 1.0</option>
              <option value="ISO27001">ISO/IEC 27001:2022</option>
              <option value="ISO42001">ISO/IEC 42001:2023</option>
              <option value="LGPD">LGPD Lei 13.709/2018</option>
              <option value="OWASP">OWASP LLM Top-10</option>
            </Select>
            <Select label="Período de Análise" value={reportPeriod} onChange={e => setReportPeriod(Number(e.target.value))}>
              <option value={7}>Últimos 7 dias</option>
              <option value={30}>Últimos 30 dias</option>
              <option value={60}>Últimos 60 dias</option>
              <option value={90}>Últimos 90 dias</option>
            </Select>
            <div className="flex justify-end gap-3">
              <Button variant="secondary" onClick={() => setReportModal(false)}>Cancelar</Button>
              <Button variant="primary" onClick={handleGerarRelatorio} loading={generatingReport}>
                <FileText className="w-4 h-4" />
                Gerar Relatório
              </Button>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="flex items-center justify-between p-4 bg-green-900/20 border border-green-700/30 rounded-xl">
              <div>
                <h3 className="font-semibold text-white">{generatedReport.title}</h3>
                <p className="text-sm text-gray-400 mt-1">Framework: {generatedReport.framework}</p>
              </div>
              <div className="text-3xl font-bold text-green-400">{generatedReport.score.toFixed(0)}%</div>
            </div>

            <div className="space-y-2">
              <h4 className="font-medium text-white text-sm">Achados</h4>
              {generatedReport.findings?.map((f, i) => (
                <div key={i} className={`flex items-start gap-3 p-3 rounded-lg ${
                  f.tipo === 'positivo' ? 'bg-green-900/10' : 'bg-red-900/10'
                }`}>
                  {f.tipo === 'positivo' ? (
                    <CheckCircle className="w-4 h-4 text-green-400 mt-0.5" />
                  ) : (
                    <XCircle className="w-4 h-4 text-red-400 mt-0.5" />
                  )}
                  <div>
                    <p className="text-sm text-gray-200">{f.descricao}</p>
                    <span className="text-xs text-gray-500">Impacto: {f.impacto}</span>
                  </div>
                </div>
              ))}
            </div>

            <div className="space-y-2">
              <h4 className="font-medium text-white text-sm">Recomendações</h4>
              {generatedReport.recommendations?.map((r, i) => (
                <div key={i} className="flex items-start gap-2 text-sm text-gray-300">
                  <span className="text-blue-400 mt-0.5">→</span>
                  {r}
                </div>
              ))}
            </div>

            <div className="flex justify-end gap-3">
              <Button variant="secondary" onClick={() => setGeneratedReport(null)}>Novo Relatório</Button>
              <Button variant="primary" onClick={() => {
                const json = JSON.stringify(generatedReport, null, 2)
                const blob = new Blob([json], { type: 'application/json' })
                const url = URL.createObjectURL(blob)
                const a = document.createElement('a')
                a.href = url
                a.download = `relatorio_${generatedReport.framework}_${new Date().toISOString().split('T')[0]}.json`
                a.click()
              }}>
                <Download className="w-4 h-4" /> Exportar
              </Button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  )
}
