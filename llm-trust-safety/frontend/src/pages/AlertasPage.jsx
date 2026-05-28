import { useState, useEffect, useCallback } from 'react'
import { alertsAPI } from '../utils/api'
import { formatRelative, formatDate } from '../utils/helpers'
import {
  LoadingSpinner, Card, Button, SeverityBadge, StatusBadge,
  Modal, Select, Textarea, toast, Pagination, EmptyState, StatCard
} from '../components/ui'
import ExportPDFMenu from '../components/ExportPDFMenu'
import {
  Bell, BellOff, CheckCircle, XCircle, AlertTriangle, Filter,
  RefreshCw, Plus, Eye, Clock, Shield, Activity
} from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, LineChart, Line, CartesianGrid } from 'recharts'

const CATEGORY_LABELS = {
  attack: 'Ataque',
  pii: 'PII',
  session: 'Sessão',
  policy: 'Política',
  system: 'Sistema',
}

const SEVERITY_ICONS = {
  critical: '🔴',
  high: '🟠',
  medium: '🟡',
  low: '🟢',
  info: '🔵',
}

export default function AlertasPage() {
  const [alertas, setAlertas] = useState([])
  const [resumo, setResumo] = useState(null)
  const [loading, setLoading] = useState(true)
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const [totalPages, setTotalPages] = useState(1)
  const [filters, setFilters] = useState({ severity: '', status: '', category: '' })
  const [selectedAlert, setSelectedAlert] = useState(null)
  const [resolveModal, setResolveModal] = useState(null)
  const [resolveNotes, setResolveNotes] = useState('')
  const [processing, setProcessing] = useState(false)

  const fetchAlertas = useCallback(async () => {
    setLoading(true)
    try {
      const [alertsRes, resumoRes] = await Promise.all([
        alertsAPI.listar({ page, per_page: 15, ...filters }),
        alertsAPI.resumo(),
      ])
      setAlertas(alertsRes.data.alertas)
      setTotal(alertsRes.data.total)
      setTotalPages(alertsRes.data.pages)
      setResumo(resumoRes.data)
    } catch (e) {
      toast('Erro ao carregar alertas', 'error')
    } finally {
      setLoading(false)
    }
  }, [page, filters])

  useEffect(() => { fetchAlertas() }, [fetchAlertas])

  const handleReconhecer = async (alertId) => {
    setProcessing(true)
    try {
      await alertsAPI.reconhecer(alertId)
      toast('Alerta reconhecido', 'success')
      fetchAlertas()
    } catch (e) {
      toast('Erro ao reconhecer alerta', 'error')
    } finally {
      setProcessing(false)
    }
  }

  const handleResolver = async () => {
    if (!resolveModal) return
    setProcessing(true)
    try {
      await alertsAPI.resolver(resolveModal.alert_id, { resolution_notes: resolveNotes })
      toast('Alerta resolvido com sucesso!', 'success')
      setResolveModal(null)
      setResolveNotes('')
      fetchAlertas()
    } catch (e) {
      toast('Erro ao resolver alerta', 'error')
    } finally {
      setProcessing(false)
    }
  }

  const handleFalsoPositivo = async (alertId) => {
    try {
      await alertsAPI.falsoPositivo(alertId)
      toast('Marcado como falso positivo', 'info')
      fetchAlertas()
    } catch (e) {
      toast('Erro ao atualizar alerta', 'error')
    }
  }

  const r = resumo || {}
  const stats = [
    { label: 'Alertas Abertos', value: r.por_status?.open || 0, color: '#ef4444', icon: Bell },
    { label: 'Reconhecidos', value: r.por_status?.acknowledged || 0, color: '#f59e0b', icon: Eye },
    { label: 'Resolvidos', value: r.por_status?.resolved || 0, color: '#22c55e', icon: CheckCircle },
    { label: 'Falsos Positivos', value: r.por_status?.false_positive || 0, color: '#6b7280', icon: BellOff },
  ]

  const byCategory = Object.entries(r.por_categoria || {}).map(([k, v]) => ({
    name: CATEGORY_LABELS[k] || k, count: v
  }))

  const timelineData = (r.timeline || []).slice(-24).map(t => ({
    hora: t.hora?.split(' ')[1] || t.hora,
    total: t.total
  }))

  return (
    <div className="p-6 space-y-6 bg-gray-950 min-h-screen">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Bell className="w-6 h-6 text-red-400" />
            Central de Alertas
          </h1>
          <p className="text-gray-400 text-sm mt-1">Gerenciamento e triagem de alertas de segurança</p>
        </div>
        <div className="flex items-center gap-2">
          <Button onClick={fetchAlertas} variant="secondary" size="sm">
            <RefreshCw className="w-4 h-4" /> Atualizar
          </Button>
          <ExportPDFMenu days={30} tipos={["sessoes_alertas", "tecnico", "executivo"]} />
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((s, i) => <StatCard key={i} {...s} />)}
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card title="Alertas por Categoria" subtitle="Últimos 7 dias">
          <ResponsiveContainer width="100%" height={180}>
            <BarChart data={byCategory}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="name" tick={{ fill: '#6b7280', fontSize: 12 }} />
              <YAxis tick={{ fill: '#6b7280', fontSize: 12 }} />
              <Tooltip contentStyle={{ background: '#1f2937', border: '1px solid #374151', borderRadius: '12px' }} />
              <Bar dataKey="count" name="Alertas" fill="#ef4444" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </Card>

        <Card title="Timeline de Alertas" subtitle="Últimas 24 horas">
          <ResponsiveContainer width="100%" height={180}>
            <LineChart data={timelineData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="hora" tick={{ fill: '#6b7280', fontSize: 11 }} />
              <YAxis tick={{ fill: '#6b7280', fontSize: 11 }} />
              <Tooltip contentStyle={{ background: '#1f2937', border: '1px solid #374151', borderRadius: '12px' }} />
              <Line type="monotone" dataKey="total" name="Alertas" stroke="#f59e0b" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </Card>
      </div>

      {/* Filtros */}
      <Card title="Lista de Alertas"
        actions={
          <div className="flex items-center gap-2">
            <Select
              value={filters.severity}
              onChange={e => { setFilters(f => ({ ...f, severity: e.target.value })); setPage(1) }}
              className="text-xs py-1.5 px-2 min-w-[120px]"
            >
              <option value="">Severidade</option>
              <option value="critical">Crítico</option>
              <option value="high">Alto</option>
              <option value="medium">Médio</option>
              <option value="low">Baixo</option>
            </Select>
            <Select
              value={filters.status}
              onChange={e => { setFilters(f => ({ ...f, status: e.target.value })); setPage(1) }}
              className="text-xs py-1.5 px-2 min-w-[120px]"
            >
              <option value="">Status</option>
              <option value="open">Aberto</option>
              <option value="acknowledged">Reconhecido</option>
              <option value="resolved">Resolvido</option>
            </Select>
          </div>
        }
      >
        {loading ? <LoadingSpinner /> : (
          <div className="space-y-3">
            {alertas.length === 0 ? (
              <EmptyState icon={Bell} title="Nenhum alerta encontrado" description="Ajuste os filtros ou aguarde novas ocorrências" />
            ) : (
              alertas.map((alert) => (
                <div
                  key={alert.alert_id}
                  className="flex items-start gap-4 p-4 rounded-xl bg-gray-800/40 border border-gray-700/30 hover:border-gray-600/50 transition-all"
                >
                  <div className="text-xl mt-0.5">{SEVERITY_ICONS[alert.severity]}</div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <h4 className="font-medium text-white text-sm">{alert.title}</h4>
                      <SeverityBadge severity={alert.severity} />
                      <StatusBadge status={alert.status} />
                      {alert.owasp_category && (
                        <span className="text-xs bg-blue-900/40 text-blue-300 border border-blue-800/50 px-2 py-0.5 rounded-full">
                          {alert.owasp_category.split(':')[0]}
                        </span>
                      )}
                    </div>
                    {alert.description && (
                      <p className="text-xs text-gray-400 mt-1 line-clamp-2">{alert.description}</p>
                    )}
                    <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
                      <span className="flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {formatRelative(alert.created_at)}
                      </span>
                      {alert.risk_score && (
                        <span className="flex items-center gap-1">
                          <Activity className="w-3 h-3" />
                          Score: {alert.risk_score.toFixed(0)}
                        </span>
                      )}
                      <span className="capitalize">{CATEGORY_LABELS[alert.category] || alert.category}</span>
                    </div>
                  </div>

                  {/* Ações */}
                  {alert.status === 'open' && (
                    <div className="flex gap-2 flex-shrink-0">
                      <Button
                        onClick={() => handleReconhecer(alert.alert_id)}
                        variant="secondary" size="xs" loading={processing}
                      >
                        <Eye className="w-3 h-3" />
                        Reconhecer
                      </Button>
                      <Button
                        onClick={() => { setResolveModal(alert); setResolveNotes('') }}
                        variant="success" size="xs"
                      >
                        <CheckCircle className="w-3 h-3" />
                        Resolver
                      </Button>
                      <Button
                        onClick={() => handleFalsoPositivo(alert.alert_id)}
                        variant="ghost" size="xs"
                      >
                        <XCircle className="w-3 h-3" />
                        FP
                      </Button>
                    </div>
                  )}
                  {alert.status === 'acknowledged' && (
                    <Button onClick={() => { setResolveModal(alert); setResolveNotes('') }} variant="success" size="xs">
                      <CheckCircle className="w-3 h-3" /> Resolver
                    </Button>
                  )}
                  {alert.resolution_notes && (
                    <div className="text-xs text-gray-500 italic max-w-xs truncate">{alert.resolution_notes}</div>
                  )}
                </div>
              ))
            )}

            <Pagination
              page={page} pages={totalPages} total={total} perPage={15}
              onPageChange={setPage}
            />
          </div>
        )}
      </Card>

      {/* Modal Resolver */}
      <Modal isOpen={!!resolveModal} onClose={() => setResolveModal(null)} title="Resolver Alerta">
        {resolveModal && (
          <div className="space-y-4">
            <div className="p-4 bg-gray-800/50 rounded-xl">
              <p className="text-white font-medium">{resolveModal.title}</p>
              <p className="text-gray-400 text-sm mt-1">{resolveModal.description}</p>
            </div>
            <Textarea
              label="Notas de Resolução"
              placeholder="Descreva como o alerta foi investigado e resolvido..."
              value={resolveNotes}
              onChange={e => setResolveNotes(e.target.value)}
              rows={4}
            />
            <div className="flex gap-3 justify-end">
              <Button variant="secondary" onClick={() => setResolveModal(null)}>Cancelar</Button>
              <Button variant="success" onClick={handleResolver} loading={processing}>
                <CheckCircle className="w-4 h-4" />
                Marcar como Resolvido
              </Button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  )
}
