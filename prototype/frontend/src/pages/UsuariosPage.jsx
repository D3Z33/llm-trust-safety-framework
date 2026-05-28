import { useState, useEffect } from 'react'
import { usuariosAPI } from '../utils/api'
import { formatDate, formatRelative, ROLE_LABELS } from '../utils/helpers'
import { LoadingSpinner, Card, Button, Input, Select, Modal, Toggle, toast, EmptyState } from '../components/ui'
import { Users2, Plus, Pencil, UserX, UserCheck, Key, Copy, RefreshCw, Shield } from 'lucide-react'
import { useAuth } from '../hooks/useAuth'

export default function UsuariosPage() {
  const { user: currentUser } = useAuth()
  const [usuarios, setUsuarios] = useState([])
  const [apiKeys, setApiKeys] = useState([])
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('usuarios')
  const [novoModal, setNovoModal] = useState(false)
  const [editModal, setEditModal] = useState(null)
  const [novaKeyModal, setNovaKeyModal] = useState(false)
  const [novaKeyResult, setNovaKeyResult] = useState(null)

  const [novoForm, setNovoForm] = useState({
    username: '', email: '', full_name: '', password: '',
    role: 'analyst', department: '',
  })

  const [novaKeyForm, setNovaKeyForm] = useState({
    name: '', scopes: ['evaluate', 'read'], expires_days: '',
    rate_limit_per_min: 60,
  })

  const fetchData = async () => {
    setLoading(true)
    try {
      const [usersRes, keysRes] = await Promise.all([
        usuariosAPI.listar(),
        usuariosAPI.minhasAPIKeys(),
      ])
      setUsuarios(usersRes.data)
      setApiKeys(keysRes.data)
    } catch (e) {
      toast('Erro ao carregar usuários', 'error')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchData() }, [])

  const handleCriar = async () => {
    try {
      await usuariosAPI.criar(novoForm)
      toast('Usuário criado com sucesso!', 'success')
      setNovoModal(false)
      setNovoForm({ username: '', email: '', full_name: '', password: '', role: 'analyst', department: '' })
      fetchData()
    } catch (e) {
      toast(e.response?.data?.detail || 'Erro ao criar usuário', 'error')
    }
  }

  const handleToggleActive = async (id, isActive) => {
    try {
      await usuariosAPI.atualizar(id, { is_active: !isActive })
      toast(`Usuário ${!isActive ? 'ativado' : 'desativado'}`, 'success')
      fetchData()
    } catch (e) {
      toast('Erro ao atualizar', 'error')
    }
  }

  const handleSaveEdit = async () => {
    try {
      await usuariosAPI.atualizar(editModal.id, {
        full_name: editModal.full_name,
        email: editModal.email,
        role: editModal.role,
        department: editModal.department,
      })
      toast('Usuário atualizado!', 'success')
      setEditModal(null)
      fetchData()
    } catch (e) {
      toast('Erro ao atualizar', 'error')
    }
  }

  const handleCriarAPIKey = async () => {
    try {
      const res = await usuariosAPI.criarAPIKey({
        ...novaKeyForm,
        expires_days: novaKeyForm.expires_days ? Number(novaKeyForm.expires_days) : null,
      })
      setNovaKeyResult(res.data)
      fetchData()
    } catch (e) {
      toast('Erro ao criar API Key', 'error')
    }
  }

  const handleRevogarKey = async (id) => {
    if (!confirm('Revogar esta API Key? Esta ação não pode ser desfeita.')) return
    try {
      await usuariosAPI.revogarAPIKey(id)
      toast('API Key revogada', 'info')
      fetchData()
    } catch (e) {
      toast('Erro ao revogar', 'error')
    }
  }

  if (loading) return <LoadingSpinner text="Carregando usuários..." />

  const ROLE_COLORS = {
    admin: '#ef4444',
    analyst: '#3b82f6',
    viewer: '#6b7280',
    api_user: '#8b5cf6',
  }

  return (
    <div className="p-6 space-y-6 bg-gray-950 min-h-screen">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Users2 className="w-6 h-6 text-blue-400" />
            Gerenciamento de Usuários
          </h1>
          <p className="text-gray-400 text-sm mt-1">
            {usuarios.length} usuários cadastrados • {usuarios.filter(u => u.is_active).length} ativos
          </p>
        </div>
        <div className="flex gap-2">
          <Button onClick={fetchData} variant="secondary" size="sm">
            <RefreshCw className="w-4 h-4" />
          </Button>
          {currentUser?.role === 'admin' && (
            <Button onClick={() => setNovoModal(true)} variant="primary" size="sm">
              <Plus className="w-4 h-4" />
              Novo Usuário
            </Button>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 bg-gray-800/50 rounded-xl p-1 w-fit">
        {['usuarios', 'api-keys'].map(tab => (
          <button key={tab} onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
              activeTab === tab ? 'bg-blue-600 text-white' : 'text-gray-400 hover:text-white'
            }`}>
            {tab === 'usuarios' ? 'Usuários' : 'API Keys'}
          </button>
        ))}
      </div>

      {activeTab === 'usuarios' && (
        <div className="grid gap-4">
          {/* Stats de roles */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {Object.entries(ROLE_LABELS).map(([role, label]) => {
              const count = usuarios.filter(u => u.role === role).length
              return (
                <div key={role} className="bg-gray-800/60 border border-gray-700/50 rounded-2xl p-4">
                  <div className="text-2xl font-bold text-white">{count}</div>
                  <div className="text-sm font-medium mt-1" style={{ color: ROLE_COLORS[role] }}>{label}</div>
                </div>
              )
            })}
          </div>

          {/* Lista */}
          <Card title="Lista de Usuários">
            <div className="space-y-3">
              {usuarios.map((u) => (
                <div key={u.id} className={`flex items-center gap-4 p-4 rounded-xl border transition-all ${
                  u.is_active ? 'bg-gray-800/30 border-gray-700/30' : 'bg-gray-800/10 border-gray-700/20 opacity-60'
                }`}>
                  {/* Avatar */}
                  <div
                    className="w-10 h-10 rounded-xl flex items-center justify-center text-white font-bold flex-shrink-0"
                    style={{ backgroundColor: u.avatar_color || '#3b82f6' }}
                  >
                    {(u.full_name || u.username).charAt(0).toUpperCase()}
                  </div>

                  {/* Info */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-semibold text-white">{u.full_name || u.username}</span>
                      <span className="text-xs bg-gray-700 text-gray-300 px-2 py-0.5 rounded-full font-mono">
                        @{u.username}
                      </span>
                      <span className="text-xs px-2 py-0.5 rounded-full font-medium"
                        style={{ color: ROLE_COLORS[u.role], backgroundColor: ROLE_COLORS[u.role] + '22' }}>
                        {ROLE_LABELS[u.role] || u.role}
                      </span>
                      {!u.is_active && (
                        <span className="text-xs bg-gray-700 text-gray-500 px-2 py-0.5 rounded-full">
                          Inativo
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-4 mt-1 text-xs text-gray-500">
                      <span>{u.email}</span>
                      {u.department && <span>{u.department}</span>}
                      <span>{u.login_count} logins</span>
                      {u.last_login && <span>Último: {formatRelative(u.last_login)}</span>}
                    </div>
                  </div>

                  {/* Ações */}
                  {currentUser?.role === 'admin' && (
                    <div className="flex gap-1.5 flex-shrink-0">
                      <Button onClick={() => setEditModal({ ...u })} variant="ghost" size="xs">
                        <Pencil className="w-3.5 h-3.5" />
                      </Button>
                      {u.id !== currentUser?.id && (
                        <Button
                          onClick={() => handleToggleActive(u.id, u.is_active)}
                          variant={u.is_active ? 'danger' : 'success'} size="xs"
                        >
                          {u.is_active ? <UserX className="w-3.5 h-3.5" /> : <UserCheck className="w-3.5 h-3.5" />}
                        </Button>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </Card>
        </div>
      )}

      {activeTab === 'api-keys' && (
        <div className="space-y-4">
          <div className="flex justify-between">
            <p className="text-gray-400 text-sm">{apiKeys.length} API Keys cadastradas</p>
            <Button onClick={() => { setNovaKeyModal(true); setNovaKeyResult(null) }} variant="primary" size="sm">
              <Key className="w-4 h-4" />
              Nova API Key
            </Button>
          </div>

          <Card title="Suas API Keys">
            <div className="space-y-3">
              {apiKeys.length === 0 ? (
                <EmptyState icon={Key} title="Nenhuma API Key" description="Crie uma API Key para integrar com sistemas externos" />
              ) : (
                apiKeys.map((key) => (
                  <div key={key.id} className={`p-4 rounded-xl border ${
                    key.is_active ? 'bg-gray-800/40 border-gray-700/40' : 'bg-gray-800/10 border-gray-700/20 opacity-60'
                  }`}>
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-semibold text-white">{key.name}</span>
                          {!key.is_active && (
                            <span className="text-xs bg-red-900/30 text-red-400 px-2 py-0.5 rounded">Revogada</span>
                          )}
                        </div>
                        <div className="font-mono text-xs text-gray-400 bg-gray-900/50 px-2 py-1 rounded mt-1">
                          {key.key_prefix}••••••••••••••••••••••••
                        </div>
                        <div className="flex gap-4 mt-2 text-xs text-gray-500">
                          <span>Escopos: {key.scopes?.join(', ')}</span>
                          <span>{key.use_count} usos</span>
                          {key.last_used && <span>Último uso: {formatRelative(key.last_used)}</span>}
                          {key.expires_at && <span>Expira: {formatDate(key.expires_at)}</span>}
                        </div>
                      </div>
                      {key.is_active && (
                        <Button onClick={() => handleRevogarKey(key.id)} variant="danger" size="xs">
                          Revogar
                        </Button>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>
          </Card>
        </div>
      )}

      {/* Modal Novo Usuário */}
      <Modal isOpen={novoModal} onClose={() => setNovoModal(false)} title="Novo Usuário" size="md">
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <Input label="Username *" value={novoForm.username} onChange={e => setNovoForm(f => ({ ...f, username: e.target.value }))} placeholder="joao.silva" />
            <Input label="Nome Completo" value={novoForm.full_name} onChange={e => setNovoForm(f => ({ ...f, full_name: e.target.value }))} placeholder="João da Silva" />
          </div>
          <Input label="E-mail *" type="email" value={novoForm.email} onChange={e => setNovoForm(f => ({ ...f, email: e.target.value }))} placeholder="joao@empresa.com" />
          <Input label="Senha *" type="password" value={novoForm.password} onChange={e => setNovoForm(f => ({ ...f, password: e.target.value }))} placeholder="Mínimo 8 caracteres" />
          <div className="grid grid-cols-2 gap-4">
            <Select label="Perfil" value={novoForm.role} onChange={e => setNovoForm(f => ({ ...f, role: e.target.value }))}>
              <option value="analyst">Analista</option>
              <option value="viewer">Visualizador</option>
              <option value="admin">Administrador</option>
            </Select>
            <Input label="Departamento" value={novoForm.department} onChange={e => setNovoForm(f => ({ ...f, department: e.target.value }))} placeholder="TI / Segurança" />
          </div>
          <div className="flex justify-end gap-3">
            <Button variant="secondary" onClick={() => setNovoModal(false)}>Cancelar</Button>
            <Button variant="primary" onClick={handleCriar} disabled={!novoForm.username || !novoForm.email || !novoForm.password}>
              <Plus className="w-4 h-4" />
              Criar Usuário
            </Button>
          </div>
        </div>
      </Modal>

      {/* Modal Editar */}
      <Modal isOpen={!!editModal} onClose={() => setEditModal(null)} title="Editar Usuário">
        {editModal && (
          <div className="space-y-4">
            <Input label="Nome Completo" value={editModal.full_name || ''} onChange={e => setEditModal(m => ({ ...m, full_name: e.target.value }))} />
            <Input label="E-mail" value={editModal.email || ''} onChange={e => setEditModal(m => ({ ...m, email: e.target.value }))} />
            <Select label="Perfil" value={editModal.role} onChange={e => setEditModal(m => ({ ...m, role: e.target.value }))}>
              <option value="analyst">Analista</option>
              <option value="viewer">Visualizador</option>
              <option value="admin">Administrador</option>
            </Select>
            <Input label="Departamento" value={editModal.department || ''} onChange={e => setEditModal(m => ({ ...m, department: e.target.value }))} />
            <div className="flex justify-end gap-3">
              <Button variant="secondary" onClick={() => setEditModal(null)}>Cancelar</Button>
              <Button variant="primary" onClick={handleSaveEdit}>Salvar</Button>
            </div>
          </div>
        )}
      </Modal>

      {/* Modal Nova API Key */}
      <Modal isOpen={novaKeyModal} onClose={() => { setNovaKeyModal(false); setNovaKeyResult(null) }} title="Nova API Key">
        {!novaKeyResult ? (
          <div className="space-y-4">
            <Input label="Nome da Chave *" value={novaKeyForm.name} onChange={e => setNovaKeyForm(f => ({ ...f, name: e.target.value }))} placeholder="Ex: Integração Produção" />
            <Input label="Expiração (dias)" type="number" value={novaKeyForm.expires_days} onChange={e => setNovaKeyForm(f => ({ ...f, expires_days: e.target.value }))} placeholder="Deixe vazio para sem expiração" />
            <Input label="Rate Limit (req/min)" type="number" value={novaKeyForm.rate_limit_per_min} onChange={e => setNovaKeyForm(f => ({ ...f, rate_limit_per_min: Number(e.target.value) }))} />
            <div className="flex justify-end gap-3">
              <Button variant="secondary" onClick={() => setNovaKeyModal(false)}>Cancelar</Button>
              <Button variant="primary" onClick={handleCriarAPIKey} disabled={!novaKeyForm.name}>
                <Key className="w-4 h-4" />
                Gerar API Key
              </Button>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="p-4 bg-green-900/20 border border-green-700/30 rounded-xl">
              <p className="text-green-400 font-semibold mb-2">✅ API Key gerada com sucesso!</p>
              <p className="text-xs text-gray-400 mb-3">
                ⚠️ Copie agora! Esta chave não será exibida novamente.
              </p>
              <div className="flex items-center gap-2 bg-gray-900/80 rounded-lg p-3">
                <code className="text-green-400 text-sm flex-1 break-all font-mono">{novaKeyResult.key}</code>
                <button
                  onClick={() => { navigator.clipboard.writeText(novaKeyResult.key); toast('Copiado!', 'success') }}
                  className="p-2 rounded-lg hover:bg-gray-700 text-gray-400 hover:text-white transition-colors"
                >
                  <Copy className="w-4 h-4" />
                </button>
              </div>
            </div>
            <Button variant="primary" onClick={() => { setNovaKeyModal(false); setNovaKeyResult(null) }} className="w-full">
              Fechar
            </Button>
          </div>
        )}
      </Modal>
    </div>
  )
}
