import { useState } from 'react'
import { authAPI } from '../utils/api'
import { useAuth } from '../hooks/useAuth'
import { Card, Button, Input, Toggle, toast, Modal } from '../components/ui'
import { Settings, User, Lock, Bell, Globe, Palette, Shield, CheckCircle } from 'lucide-react'

export default function ConfiguracoesPage() {
  const { user } = useAuth()
  const [activeTab, setActiveTab] = useState('perfil')
  const [senhaForm, setSenhaForm] = useState({ current_password: '', new_password: '', confirm: '' })
  const [savingPassword, setSavingPassword] = useState(false)
  const [notificacoes, setNotificacoes] = useState({
    email_criticos: true,
    email_diario: false,
    browser_alerts: true,
    slack_webhook: false,
  })

  const handleAlterarSenha = async () => {
    if (senhaForm.new_password !== senhaForm.confirm) {
      toast('As senhas não coincidem', 'error')
      return
    }
    if (senhaForm.new_password.length < 8) {
      toast('Senha deve ter mínimo 8 caracteres', 'error')
      return
    }
    setSavingPassword(true)
    try {
      await authAPI.alterarSenha({
        current_password: senhaForm.current_password,
        new_password: senhaForm.new_password,
      })
      toast('Senha alterada com sucesso!', 'success')
      setSenhaForm({ current_password: '', new_password: '', confirm: '' })
    } catch (e) {
      toast(e.response?.data?.detail || 'Erro ao alterar senha', 'error')
    } finally {
      setSavingPassword(false)
    }
  }

  const TABS = [
    { id: 'perfil', label: 'Meu Perfil', icon: User },
    { id: 'seguranca', label: 'Segurança', icon: Lock },
    { id: 'notificacoes', label: 'Notificações', icon: Bell },
    { id: 'sistema', label: 'Sobre o Sistema', icon: Shield },
  ]

  return (
    <div className="p-6 space-y-6 bg-gray-950 min-h-screen">
      <div>
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <Settings className="w-6 h-6 text-gray-400" />
          Configurações
        </h1>
        <p className="text-gray-400 text-sm mt-1">Gerencie suas preferências e configurações de conta</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 bg-gray-800/50 rounded-xl p-1 w-fit">
        {TABS.map(tab => (
          <button key={tab.id} onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
              activeTab === tab.id ? 'bg-blue-600 text-white' : 'text-gray-400 hover:text-white'
            }`}>
            <tab.icon className="w-4 h-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Perfil */}
      {activeTab === 'perfil' && (
        <Card title="Informações do Perfil">
          <div className="flex items-center gap-6 mb-6 p-4 bg-gray-700/20 rounded-xl">
            <div className="w-16 h-16 rounded-2xl flex items-center justify-center text-white text-2xl font-bold"
              style={{ backgroundColor: user?.avatar_color || '#3b82f6' }}>
              {(user?.full_name || user?.username || 'U').charAt(0).toUpperCase()}
            </div>
            <div>
              <div className="text-xl font-bold text-white">{user?.full_name || user?.username}</div>
              <div className="text-gray-400">@{user?.username}</div>
              <div className="text-sm text-gray-500 mt-1">
                <span className="capitalize bg-gray-700 px-2 py-0.5 rounded text-xs">{user?.role}</span>
                {user?.department && <span className="ml-2">{user?.department}</span>}
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className="text-sm text-gray-400">Username</label>
              <div className="bg-gray-700/30 border border-gray-700 rounded-xl px-4 py-2.5 text-gray-300 text-sm">
                @{user?.username}
              </div>
            </div>
            <div className="space-y-2">
              <label className="text-sm text-gray-400">E-mail</label>
              <div className="bg-gray-700/30 border border-gray-700 rounded-xl px-4 py-2.5 text-gray-300 text-sm">
                {user?.email}
              </div>
            </div>
            <div className="space-y-2">
              <label className="text-sm text-gray-400">Perfil de Acesso</label>
              <div className="bg-gray-700/30 border border-gray-700 rounded-xl px-4 py-2.5 text-gray-300 text-sm capitalize">
                {user?.role === 'admin' ? '👑 Administrador' : user?.role === 'analyst' ? '🔍 Analista' : '👁️ Visualizador'}
              </div>
            </div>
            <div className="space-y-2">
              <label className="text-sm text-gray-400">Departamento</label>
              <div className="bg-gray-700/30 border border-gray-700 rounded-xl px-4 py-2.5 text-gray-300 text-sm">
                {user?.department || '—'}
              </div>
            </div>
          </div>
        </Card>
      )}

      {/* Segurança */}
      {activeTab === 'seguranca' && (
        <div className="space-y-6">
          <Card title="Alterar Senha">
            <div className="space-y-4 max-w-md">
              <Input
                label="Senha Atual"
                type="password"
                value={senhaForm.current_password}
                onChange={e => setSenhaForm(f => ({ ...f, current_password: e.target.value }))}
                placeholder="Digite sua senha atual"
              />
              <Input
                label="Nova Senha"
                type="password"
                value={senhaForm.new_password}
                onChange={e => setSenhaForm(f => ({ ...f, new_password: e.target.value }))}
                placeholder="Mínimo 8 caracteres"
              />
              <Input
                label="Confirmar Nova Senha"
                type="password"
                value={senhaForm.confirm}
                onChange={e => setSenhaForm(f => ({ ...f, confirm: e.target.value }))}
                placeholder="Repita a nova senha"
              />
              {senhaForm.new_password && senhaForm.confirm && senhaForm.new_password !== senhaForm.confirm && (
                <p className="text-xs text-red-400">As senhas não coincidem</p>
              )}
              <Button
                variant="primary"
                onClick={handleAlterarSenha}
                loading={savingPassword}
                disabled={!senhaForm.current_password || !senhaForm.new_password || !senhaForm.confirm}
              >
                <Lock className="w-4 h-4" />
                Alterar Senha
              </Button>
            </div>
          </Card>

          <Card title="Sessão Atual">
            <div className="space-y-3">
              <div className="flex items-center justify-between p-3 bg-green-900/10 border border-green-700/30 rounded-xl">
                <div className="flex items-center gap-3">
                  <CheckCircle className="w-4 h-4 text-green-400" />
                  <div>
                    <p className="text-sm font-medium text-white">Sessão Ativa</p>
                    <p className="text-xs text-gray-400">Token JWT válido</p>
                  </div>
                </div>
                <Button variant="danger" size="xs" onClick={() => {
                  localStorage.clear()
                  window.location.href = '/login'
                }}>
                  Encerrar Sessão
                </Button>
              </div>
            </div>
          </Card>
        </div>
      )}

      {/* Notificações */}
      {activeTab === 'notificacoes' && (
        <Card title="Preferências de Notificação">
          <div className="space-y-4">
            {[
              { key: 'email_criticos', label: 'E-mail para Alertas Críticos', desc: 'Receba notificações por e-mail para eventos críticos' },
              { key: 'email_diario', label: 'Relatório Diário por E-mail', desc: 'Resumo diário de atividades às 8h' },
              { key: 'browser_alerts', label: 'Alertas no Navegador', desc: 'Notificações push do navegador' },
              { key: 'slack_webhook', label: 'Integração com Slack', desc: 'Enviar alertas para canal do Slack (requer webhook)' },
            ].map(({ key, label, desc }) => (
              <div key={key} className="flex items-center justify-between p-4 bg-gray-800/30 rounded-xl">
                <div>
                  <p className="text-sm font-medium text-white">{label}</p>
                  <p className="text-xs text-gray-500 mt-0.5">{desc}</p>
                </div>
                <Toggle
                  checked={notificacoes[key]}
                  onChange={v => {
                    setNotificacoes(n => ({ ...n, [key]: v }))
                    toast(`${v ? 'Ativado' : 'Desativado'}: ${label}`, 'info')
                  }}
                />
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Sistema */}
      {activeTab === 'sistema' && (
        <div className="space-y-6">
          <Card title="Sobre o LLM Trust & Safety Framework">
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                {[
                  { label: 'Versão', value: 'Enterprise v2.0.0' },
                  { label: 'Ambiente', value: 'Produção' },
                  { label: 'LLM Provider', value: 'Mock (Dev)' },
                  { label: 'Banco de Dados', value: 'SQLite (Dev) / PostgreSQL' },
                  { label: 'Autenticação', value: 'JWT + RBAC' },
                  { label: 'Deploy', value: 'Docker Compose' },
                ].map(({ label, value }) => (
                  <div key={label} className="p-3 bg-gray-700/30 rounded-xl">
                    <div className="text-xs text-gray-500">{label}</div>
                    <div className="text-sm font-medium text-white mt-1">{value}</div>
                  </div>
                ))}
              </div>
            </div>
          </Card>

          <Card title="Frameworks Suportados">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {[
                { name: 'OWASP LLM Top-10', desc: '10 categorias de vulnerabilidades em LLMs', color: '#ef4444' },
                { name: 'NIST AI RMF 1.0', desc: 'Framework de gestão de riscos de IA', color: '#3b82f6' },
                { name: 'ISO/IEC 42001:2023', desc: 'Sistema de gestão de inteligência artificial', color: '#f59e0b' },
                { name: 'ISO/IEC 27001:2022', desc: 'Gestão de segurança da informação', color: '#8b5cf6' },
                { name: 'LGPD (Lei 13.709/2018)', desc: 'Lei Geral de Proteção de Dados do Brasil', color: '#10b981' },
                { name: 'MITRE ATLAS', desc: 'Táticas e técnicas de adversários de IA', color: '#06b6d4' },
              ].map(({ name, desc, color }) => (
                <div key={name} className="flex items-start gap-3 p-3 bg-gray-800/30 rounded-xl">
                  <div className="w-2 h-2 rounded-full mt-2 flex-shrink-0" style={{ backgroundColor: color }} />
                  <div>
                    <p className="text-sm font-semibold text-white">{name}</p>
                    <p className="text-xs text-gray-500 mt-0.5">{desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </div>
      )}
    </div>
  )
}
