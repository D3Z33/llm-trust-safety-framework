import { useState, useEffect } from 'react'
import { politicasAPI } from '../utils/api'
import { LoadingSpinner, Card, Button, Toggle, Modal, Input, Textarea, Select, toast, EmptyState } from '../components/ui'
import { Eye, Plus, Pencil, Trash2, Shield, RefreshCw } from 'lucide-react'

const CATEGORY_LABELS = {
  input: 'Entrada (InputGuard)',
  output: 'Saída (OutputGuard)',
  session: 'Sessão (SessionWatch)',
  global: 'Global',
}

const CATEGORY_COLORS = {
  input: '#3b82f6',
  output: '#8b5cf6',
  session: '#f59e0b',
  global: '#06b6d4',
}

export default function PoliticasPage() {
  const [politicas, setPoliticas] = useState([])
  const [loading, setLoading] = useState(true)
  const [toggling, setToggling] = useState({})
  const [editModal, setEditModal] = useState(null)
  const [novaModal, setNovaModal] = useState(false)
  const [savingId, setSavingId] = useState(null)

  const [novaForm, setNovaForm] = useState({
    name: '', description: '', category: 'input',
    block_threshold: 75, alert_threshold: 50,
    keywords: '', patterns: '',
    action_block: true, action_alert: true, action_log: true,
    owasp_mapping: '', nist_mapping: '', priority: 5,
  })

  const fetchPoliticas = async () => {
    setLoading(true)
    try {
      const res = await politicasAPI.listar()
      setPoliticas(res.data)
    } catch (e) {
      toast('Erro ao carregar políticas', 'error')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchPoliticas() }, [])

  const handleToggle = async (id) => {
    setToggling(t => ({ ...t, [id]: true }))
    try {
      await politicasAPI.toggle(id)
      setPoliticas(ps => ps.map(p => p.id === id ? { ...p, is_active: !p.is_active } : p))
      toast('Status da política atualizado', 'success')
    } catch (e) {
      toast('Erro ao atualizar política', 'error')
    } finally {
      setToggling(t => ({ ...t, [id]: false }))
    }
  }

  const handleSaveEdit = async () => {
    if (!editModal) return
    setSavingId(editModal.id)
    try {
      await politicasAPI.atualizar(editModal.id, {
        description: editModal.description,
        block_threshold: editModal.block_threshold,
        alert_threshold: editModal.alert_threshold,
        priority: editModal.priority,
      })
      toast('Política atualizada!', 'success')
      setEditModal(null)
      fetchPoliticas()
    } catch (e) {
      toast('Erro ao atualizar', 'error')
    } finally {
      setSavingId(null)
    }
  }

  const handleCriar = async () => {
    try {
      await politicasAPI.criar({
        ...novaForm,
        keywords: novaForm.keywords.split('\n').filter(Boolean),
        patterns: novaForm.patterns.split('\n').filter(Boolean),
        owasp_mapping: novaForm.owasp_mapping.split(',').map(s => s.trim()).filter(Boolean),
        nist_mapping: novaForm.nist_mapping.split(',').map(s => s.trim()).filter(Boolean),
      })
      toast('Política criada com sucesso!', 'success')
      setNovaModal(false)
      fetchPoliticas()
    } catch (e) {
      toast('Erro ao criar política', 'error')
    }
  }

  const handleDeletar = async (id, name) => {
    if (!confirm(`Remover política "${name}"?`)) return
    try {
      await politicasAPI.deletar(id)
      toast('Política removida', 'info')
      fetchPoliticas()
    } catch (e) {
      toast('Erro ao remover política', 'error')
    }
  }

  if (loading) return <LoadingSpinner text="Carregando políticas..." />

  const byCategory = ['input', 'output', 'session', 'global']
  const activeCount = politicas.filter(p => p.is_active).length

  return (
    <div className="p-6 space-y-6 bg-gray-950 min-h-screen">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Eye className="w-6 h-6 text-cyan-400" />
            Políticas de Segurança
          </h1>
          <p className="text-gray-400 text-sm mt-1">
            Configure regras de detecção e bloqueio • {activeCount}/{politicas.length} ativas
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button onClick={fetchPoliticas} variant="secondary" size="sm">
            <RefreshCw className="w-4 h-4" />
          </Button>
          <Button onClick={() => setNovaModal(true)} variant="primary" size="sm">
            <Plus className="w-4 h-4" />
            Nova Política
          </Button>
        </div>
      </div>

      {/* Stats por categoria */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {byCategory.map(cat => {
          const count = politicas.filter(p => p.category === cat).length
          const activeC = politicas.filter(p => p.category === cat && p.is_active).length
          return (
            <div key={cat} className="bg-gray-800/60 border border-gray-700/50 rounded-2xl p-4">
              <div className="w-8 h-8 rounded-lg mb-3 flex items-center justify-center"
                style={{ backgroundColor: CATEGORY_COLORS[cat] + '22' }}>
                <Shield className="w-4 h-4" style={{ color: CATEGORY_COLORS[cat] }} />
              </div>
              <div className="text-xl font-bold text-white">{activeC}/{count}</div>
              <div className="text-sm text-gray-300">{CATEGORY_LABELS[cat]}</div>
            </div>
          )
        })}
      </div>

      {/* Lista de Políticas */}
      {byCategory.map(cat => {
        const catPoliticas = politicas.filter(p => p.category === cat)
        if (catPoliticas.length === 0) return null
        return (
          <Card
            key={cat}
            title={CATEGORY_LABELS[cat]}
            subtitle={`${catPoliticas.filter(p => p.is_active).length}/${catPoliticas.length} ativas`}
          >
            <div className="space-y-3">
              {catPoliticas
                .sort((a, b) => b.priority - a.priority)
                .map((politica) => (
                  <div
                    key={politica.id}
                    className={`flex items-start gap-4 p-4 rounded-xl border transition-all ${
                      politica.is_active
                        ? 'bg-gray-800/30 border-gray-700/40'
                        : 'bg-gray-800/10 border-gray-700/20 opacity-60'
                    }`}
                  >
                    {/* Toggle */}
                    <div className="mt-0.5">
                      <Toggle
                        checked={politica.is_active}
                        onChange={() => handleToggle(politica.id)}
                        disabled={toggling[politica.id]}
                      />
                    </div>

                    {/* Info */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <h4 className="font-semibold text-white">{politica.name}</h4>
                        <span className="text-xs bg-gray-700 text-gray-300 px-2 py-0.5 rounded">
                          Prioridade {politica.priority}
                        </span>
                        {politica.action_block && (
                          <span className="text-xs bg-red-900/30 text-red-400 border border-red-800/40 px-2 py-0.5 rounded">
                            Bloqueia
                          </span>
                        )}
                        {politica.action_alert && (
                          <span className="text-xs bg-yellow-900/30 text-yellow-400 border border-yellow-800/40 px-2 py-0.5 rounded">
                            Alerta
                          </span>
                        )}
                      </div>
                      {politica.description && (
                        <p className="text-sm text-gray-400 mt-1">{politica.description}</p>
                      )}
                      <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
                        <span>Bloqueio: ≥{politica.block_threshold}%</span>
                        <span>Alerta: ≥{politica.alert_threshold}%</span>
                        {politica.owasp_mapping?.length > 0 && (
                          <div className="flex gap-1">
                            {politica.owasp_mapping.slice(0, 2).map((o, i) => (
                              <span key={i} className="bg-blue-900/30 text-blue-400 px-1.5 py-0.5 rounded">
                                {o.split(':')[0]}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Ações */}
                    <div className="flex gap-1.5 flex-shrink-0">
                      <Button onClick={() => setEditModal({ ...politica })} variant="ghost" size="xs">
                        <Pencil className="w-3.5 h-3.5" />
                      </Button>
                      <Button onClick={() => handleDeletar(politica.id, politica.name)} variant="danger" size="xs">
                        <Trash2 className="w-3.5 h-3.5" />
                      </Button>
                    </div>
                  </div>
                ))}
            </div>
          </Card>
        )
      })}

      {/* Modal Editar */}
      <Modal isOpen={!!editModal} onClose={() => setEditModal(null)} title="Editar Política">
        {editModal && (
          <div className="space-y-4">
            <Textarea
              label="Descrição"
              value={editModal.description || ''}
              onChange={e => setEditModal(m => ({ ...m, description: e.target.value }))}
              rows={3}
            />
            <div className="grid grid-cols-2 gap-4">
              <Input
                label="Limiar de Bloqueio (%)"
                type="number" min={0} max={100}
                value={editModal.block_threshold}
                onChange={e => setEditModal(m => ({ ...m, block_threshold: Number(e.target.value) }))}
              />
              <Input
                label="Limiar de Alerta (%)"
                type="number" min={0} max={100}
                value={editModal.alert_threshold}
                onChange={e => setEditModal(m => ({ ...m, alert_threshold: Number(e.target.value) }))}
              />
            </div>
            <Input
              label="Prioridade (1-10)"
              type="number" min={1} max={10}
              value={editModal.priority}
              onChange={e => setEditModal(m => ({ ...m, priority: Number(e.target.value) }))}
            />
            <div className="flex justify-end gap-3">
              <Button variant="secondary" onClick={() => setEditModal(null)}>Cancelar</Button>
              <Button variant="primary" onClick={handleSaveEdit} loading={savingId === editModal.id}>
                Salvar Alterações
              </Button>
            </div>
          </div>
        )}
      </Modal>

      {/* Modal Nova Política */}
      <Modal isOpen={novaModal} onClose={() => setNovaModal(false)} title="Nova Política de Segurança" size="lg">
        <div className="space-y-4">
          <Input
            label="Nome da Política *"
            value={novaForm.name}
            onChange={e => setNovaForm(f => ({ ...f, name: e.target.value }))}
            placeholder="Ex: Bloqueio de Código Malicioso"
          />
          <Select
            label="Categoria"
            value={novaForm.category}
            onChange={e => setNovaForm(f => ({ ...f, category: e.target.value }))}
          >
            {byCategory.map(c => <option key={c} value={c}>{CATEGORY_LABELS[c]}</option>)}
          </Select>
          <Textarea
            label="Descrição"
            value={novaForm.description}
            onChange={e => setNovaForm(f => ({ ...f, description: e.target.value }))}
            placeholder="Descreva o propósito da política..."
            rows={2}
          />
          <div className="grid grid-cols-2 gap-4">
            <Input label="Limiar Bloqueio (%)" type="number"
              value={novaForm.block_threshold}
              onChange={e => setNovaForm(f => ({ ...f, block_threshold: Number(e.target.value) }))} />
            <Input label="Limiar Alerta (%)" type="number"
              value={novaForm.alert_threshold}
              onChange={e => setNovaForm(f => ({ ...f, alert_threshold: Number(e.target.value) }))} />
          </div>
          <Textarea
            label="Palavras-chave (uma por linha)"
            value={novaForm.keywords}
            onChange={e => setNovaForm(f => ({ ...f, keywords: e.target.value }))}
            placeholder="jailbreak&#10;bypass security&#10;ignore instructions"
            rows={3}
          />
          <Textarea
            label="Padrões Regex (um por linha)"
            value={novaForm.patterns}
            onChange={e => setNovaForm(f => ({ ...f, patterns: e.target.value }))}
            placeholder="ignore\s+all\s+previous\s+instructions"
            rows={3}
          />
          <Input
            label="Categorias OWASP (separadas por vírgula)"
            value={novaForm.owasp_mapping}
            onChange={e => setNovaForm(f => ({ ...f, owasp_mapping: e.target.value }))}
            placeholder="LLM01:PromptInjection, LLM06:SensitiveInformationDisclosure"
          />
          <div className="flex gap-6">
            <Toggle
              checked={novaForm.action_block}
              onChange={v => setNovaForm(f => ({ ...f, action_block: v }))}
              label="Bloquear"
            />
            <Toggle
              checked={novaForm.action_alert}
              onChange={v => setNovaForm(f => ({ ...f, action_alert: v }))}
              label="Alertar"
            />
            <Toggle
              checked={novaForm.action_log}
              onChange={v => setNovaForm(f => ({ ...f, action_log: v }))}
              label="Registrar Log"
            />
          </div>
          <div className="flex justify-end gap-3">
            <Button variant="secondary" onClick={() => setNovaModal(false)}>Cancelar</Button>
            <Button variant="primary" onClick={handleCriar} disabled={!novaForm.name}>
              <Plus className="w-4 h-4" />
              Criar Política
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  )
}
