import { NavLink, useLocation } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import {
  LayoutDashboard, Shield, FileText, Users2, Bell, BookOpen,
  Activity, Settings, LogOut, Brain, Zap, ChevronRight,
  ShieldAlert, Globe, Key, BarChart3, Eye
} from 'lucide-react'
import clsx from 'clsx'

const NAV_ITEMS = [
  { group: 'Principal', items: [
    { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard', description: 'Visão geral do sistema' },
    { to: '/avaliar', icon: Shield, label: 'Avaliar Prompt', description: 'Testar proteções' },
    { to: '/analytics', icon: BarChart3, label: 'Analytics', description: 'Análises avançadas' },
  ]},
  { group: 'Segurança', items: [
    { to: '/logs', icon: FileText, label: 'Logs de Auditoria', description: 'Histórico de avaliações' },
    { to: '/sessoes', icon: Activity, label: 'Sessões', description: 'Monitoramento de sessões' },
    { to: '/alertas', icon: Bell, label: 'Alertas', description: 'Gestão de alertas', badge: true },
    { to: '/ameacas', icon: ShieldAlert, label: 'Threat Intelligence', description: 'IOCs e indicadores' },
  ]},
  { group: 'Compliance', items: [
    { to: '/conformidade', icon: Globe, label: 'Conformidade', description: 'NIST, ISO, LGPD' },
    { to: '/owasp', icon: BookOpen, label: 'OWASP Top-10', description: 'Cobertura de riscos' },
    { to: '/politicas', icon: Eye, label: 'Políticas', description: 'Regras de segurança', minRole: 'analyst' },
  ]},
  { group: 'Administração', items: [
    { to: '/usuarios', icon: Users2, label: 'Usuários', description: 'Gerenciar usuários', minRole: 'admin' },
    { to: '/configuracoes', icon: Settings, label: 'Configurações', description: 'Preferências do sistema', minRole: 'analyst' },
  ]},
]

const ROLE_RANK = { admin: 3, analyst: 2, viewer: 1, api_user: 1 }

const ROLE_BADGE = {
  admin:    { label: 'ADMIN',    cls: 'bg-red-500/20 text-red-400 border-red-500/30' },
  analyst:  { label: 'ANALYST',  cls: 'bg-blue-500/20 text-blue-400 border-blue-500/30' },
  viewer:   { label: 'VIEWER',   cls: 'bg-gray-500/20 text-gray-400 border-gray-500/30' },
  api_user: { label: 'API',      cls: 'bg-violet-500/20 text-violet-400 border-violet-500/30' },
}

export default function Sidebar() {
  const { user, logout } = useAuth()
  const location = useLocation()

  const isActive = (path) => location.pathname === path

  return (
    <aside className="w-64 h-screen flex flex-col bg-gray-900 border-r border-gray-800/80 flex-shrink-0">
      {/* Logo / Branding */}
      <div className="px-4 py-4 border-b border-gray-800/80">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-600 to-violet-600 flex items-center justify-center shadow-lg shadow-blue-900/40 flex-shrink-0">
            <Brain className="w-5 h-5 text-white" />
          </div>
          <div className="min-w-0">
            <div className="text-white font-bold text-sm leading-tight">Plataforma LLM</div>
            <div className="text-gray-500 text-[10px] leading-tight">LLM Trust &amp; Safety</div>
          </div>
        </div>
      </div>

      {/* Status + version */}
      <div className="px-4 py-2.5 border-b border-gray-800/60 space-y-1.5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-[10px]">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-60"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-green-400"></span>
            </span>
            <span className="text-green-400 font-semibold">Sistema Ativo</span>
          </div>
          <div className="flex items-center gap-1 bg-blue-900/25 border border-blue-700/25 rounded-md px-2 py-0.5">
            <Zap className="w-2.5 h-2.5 text-blue-400" />
            <span className="text-[9px] text-blue-400 font-semibold">v2.0</span>
          </div>
        </div>
      </div>

      {/* Navegação */}
      <nav className="flex-1 overflow-y-auto px-3 py-2 space-y-4">
        {NAV_ITEMS.map((group) => (
          <div key={group.group}>
            <div className="px-2 py-1 text-xs font-semibold text-gray-600 uppercase tracking-wider mb-1">
              {group.group}
            </div>
            <div className="space-y-0.5">
              {group.items.map((item) => {
                const userRank = ROLE_RANK[user?.role] || 0
                const requiredRank = item.minRole ? (ROLE_RANK[item.minRole] || 0) : 0
                if (requiredRank > userRank) return null
                const active = isActive(item.to)
                return (
                  <NavLink
                    key={item.to}
                    to={item.to}
                    className={clsx(
                      'flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all duration-150 group relative',
                      active
                        ? 'bg-blue-600/20 text-blue-400 border border-blue-500/30'
                        : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800/60 border border-transparent'
                    )}
                  >
                    <item.icon className={clsx('w-4 h-4 flex-shrink-0', active && 'text-blue-400')} />
                    <span className="text-sm font-medium flex-1">{item.label}</span>
                    {active && <ChevronRight className="w-3.5 h-3.5 text-blue-400" />}
                  </NavLink>
                )
              })}
            </div>
          </div>
        ))}
      </nav>

      {/* Usuário */}
      <div className="border-t border-gray-800 p-3">
        <div className="flex items-center gap-3 p-2 rounded-xl hover:bg-gray-800/60 transition-colors">
          <div className="w-8 h-8 rounded-lg flex items-center justify-center text-white text-sm font-bold"
            style={{ backgroundColor: user?.avatar_color || '#3b82f6' }}>
            {(user?.full_name || user?.username || 'U').charAt(0).toUpperCase()}
          </div>
          <div className="flex-1 min-w-0">
            <div className="text-sm font-medium text-white truncate">
              {user?.full_name || user?.username}
            </div>
            <div className="flex items-center gap-1.5 mt-0.5">
              {user?.role && ROLE_BADGE[user.role] && (
                <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded border ${ROLE_BADGE[user.role].cls}`}>
                  {ROLE_BADGE[user.role].label}
                </span>
              )}
              {user?.department && (
                <span className="text-[10px] text-gray-600 truncate">{user.department}</span>
              )}
            </div>
          </div>
          <button
            onClick={logout}
            className="p-1.5 rounded-lg text-gray-500 hover:text-red-400 hover:bg-red-500/10 transition-colors"
            title="Sair"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </aside>
  )
}
