import { useState } from 'react'
import { useAuth } from '../hooks/useAuth'
import { Brain, Shield, Lock, Eye, EyeOff, Zap, Globe, CheckCircle } from 'lucide-react'

export default function LoginPage() {
  const { login } = useAuth()
  const [form, setForm] = useState({ username: '', password: '' })
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [demoUser, setDemoUser] = useState(null)

  const DEMO_USERS = [
    { username: 'admin', password: 'admin123', role: 'Administrador', color: '#ef4444', icon: '👑' },
    { username: 'analyst', password: 'analyst123', role: 'Analista', color: '#3b82f6', icon: '🔍' },
    { username: 'viewer', password: 'viewer123', role: 'Visualizador', color: '#10b981', icon: '👁️' },
  ]

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await login(form.username, form.password)
    } catch (err) {
      setError(err.response?.data?.detail || 'Credenciais inválidas. Tente novamente.')
    } finally {
      setLoading(false)
    }
  }

  const handleDemoLogin = async (user) => {
    setDemoUser(user.username)
    setError('')
    try {
      await login(user.username, user.password)
    } catch (err) {
      setError('Erro ao fazer login')
    } finally {
      setDemoUser(null)
    }
  }

  const FEATURES = [
    { label: 'InputGuard', desc: 'Detecção de Prompt Injection e Jailbreak', color: '#3b82f6' },
    { label: 'OutputGuard', desc: 'Mascaramento de PII e dados sensíveis', color: '#f59e0b' },
    { label: 'SessionWatch', desc: 'FSM de monitoramento de ataques encadeados', color: '#8b5cf6' },
    { label: 'Data Exposure Mirror', desc: 'Rastreamento de exposição de dados pessoais', color: '#ec4899' },
    { label: 'Risk Aggregator', desc: 'Score consolidado de risco 0–100', color: '#ef4444' },
    { label: 'Compliance Engine', desc: 'NIST AI RMF · ISO 42001 · LGPD · OWASP', color: '#22c55e' },
  ]

  return (
    <div className="min-h-screen bg-gray-950 flex bg-grid">
      {/* Painel Esquerdo - Info */}
      <div className="hidden lg:flex flex-col w-1/2 p-12 relative overflow-hidden">
        {/* Glow effects */}
        <div className="absolute top-0 left-0 w-96 h-96 bg-blue-600/10 rounded-full blur-3xl -translate-x-1/2 -translate-y-1/2" />
        <div className="absolute bottom-0 right-0 w-96 h-96 bg-violet-600/10 rounded-full blur-3xl translate-x-1/2 translate-y-1/2" />

        <div className="relative z-10">
          {/* Logo */}
          <div className="flex items-center gap-4 mb-8">
            <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-blue-600 to-violet-600 flex items-center justify-center shadow-xl">
              <Brain className="w-7 h-7 text-white" />
            </div>
            <div>
              <div className="text-white font-bold text-xl">Plataforma LLM</div>
              <div className="text-gray-400 text-sm">Confiança, Segurança e Auditoria</div>
            </div>
          </div>

          {/* Headline */}
          <div className="mb-10">
            <div className="inline-flex items-center gap-2 bg-blue-500/10 border border-blue-500/20 rounded-full px-4 py-1.5 mb-6">
              <Zap className="w-3.5 h-3.5 text-blue-400" />
              <span className="text-blue-300 text-sm font-medium">Framework Enterprise v2.0</span>
            </div>
            <h1 className="text-4xl font-bold text-white leading-tight mb-4">
              Firewall Semântico
              <br />
              <span className="text-gradient">para LLMs</span>
            </h1>
            <p className="text-gray-400 text-base leading-relaxed">
              Pipeline de segurança em tempo real para LLMs corporativos — detecta ataques, 
              protege dados, monitora sessões e gera compliance automático.
            </p>
          </div>

          {/* Features */}
          <div className="space-y-2">
            {FEATURES.map((f, i) => (
              <div key={i} className="flex items-center gap-3 p-2.5 rounded-xl hover:bg-white/3 transition-colors">
                <div className="w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0" style={{ backgroundColor: f.color + '20' }}>
                  <CheckCircle className="w-3.5 h-3.5" style={{ color: f.color }} />
                </div>
                <div>
                  <span className="text-gray-200 text-sm font-semibold">{f.label}</span>
                  <span className="text-gray-500 text-xs ml-2">{f.desc}</span>
                </div>
              </div>
            ))}
          </div>

          {/* Frameworks */}
          <div className="mt-12 flex items-center gap-3 flex-wrap">
            {['OWASP', 'NIST AI RMF', 'ISO 42001', 'ISO 27001', 'LGPD'].map(f => (
              <span key={f} className="text-xs bg-gray-800/80 text-gray-400 border border-gray-700 px-3 py-1.5 rounded-lg">
                {f}
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* Painel Direito - Login */}
      <div className="flex-1 flex flex-col items-center justify-center p-8">
        <div className="w-full max-w-md">
          {/* Logo mobile */}
          <div className="lg:hidden flex items-center gap-3 mb-8 justify-center">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-600 to-violet-600 flex items-center justify-center">
              <Brain className="w-6 h-6 text-white" />
            </div>
            <div>
              <div className="text-white font-bold">Plataforma LLM Trust &amp; Safety</div>
              <div className="text-gray-400 text-xs">Edição corporativa v2.0</div>
            </div>
          </div>

          {/* Card de Login */}
          <div className="bg-gray-900/80 backdrop-blur-sm border border-gray-800 rounded-3xl p-8 shadow-2xl">
            <div className="mb-8">
              <h2 className="text-2xl font-bold text-white">Bem-vindo de volta</h2>
              <p className="text-gray-400 mt-1">Entre com suas credenciais para acessar o painel</p>
            </div>

            {error && (
              <div className="flex items-center gap-3 bg-red-900/30 border border-red-700/50 rounded-xl p-4 mb-6">
                <Shield className="w-5 h-5 text-red-400 flex-shrink-0" />
                <p className="text-red-300 text-sm">{error}</p>
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-1.5">
                <label className="block text-sm font-medium text-gray-300">Username</label>
                <input
                  type="text"
                  autoComplete="username"
                  value={form.username}
                  onChange={e => setForm(f => ({ ...f, username: e.target.value }))}
                  placeholder="admin"
                  required
                  className="w-full bg-gray-800 border border-gray-700 rounded-xl px-4 py-3
                    text-white placeholder:text-gray-600 focus:outline-none focus:ring-2
                    focus:ring-blue-500/50 focus:border-blue-500/50 transition-all text-sm"
                />
              </div>

              <div className="space-y-1.5">
                <label className="block text-sm font-medium text-gray-300">Senha</label>
                <div className="relative">
                  <input
                    type={showPassword ? 'text' : 'password'}
                    autoComplete="current-password"
                    value={form.password}
                    onChange={e => setForm(f => ({ ...f, password: e.target.value }))}
                    placeholder="••••••••"
                    required
                    className="w-full bg-gray-800 border border-gray-700 rounded-xl px-4 py-3 pr-12
                      text-white placeholder:text-gray-600 focus:outline-none focus:ring-2
                      focus:ring-blue-500/50 focus:border-blue-500/50 transition-all text-sm"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300 transition-colors"
                  >
                    {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                  </button>
                </div>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full bg-gradient-to-r from-blue-600 to-violet-600 hover:from-blue-500 hover:to-violet-500
                  text-white font-semibold py-3 rounded-xl transition-all duration-200
                  disabled:opacity-60 disabled:cursor-not-allowed shadow-lg
                  flex items-center justify-center gap-2 text-sm mt-2"
              >
                {loading ? (
                  <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                ) : (
                  <Lock className="w-4 h-4" />
                )}
                {loading ? 'Entrando...' : 'Entrar no Sistema'}
              </button>
            </form>

            {/* Demo Users */}
            <div className="mt-8">
              <div className="flex items-center gap-3 mb-4">
                <div className="flex-1 h-px bg-gray-700" />
                <span className="text-xs text-gray-500">Acesso de Demonstração</span>
                <div className="flex-1 h-px bg-gray-700" />
              </div>

              <div className="space-y-2">
                {DEMO_USERS.map((user) => (
                  <button
                    key={user.username}
                    onClick={() => handleDemoLogin(user)}
                    disabled={loading || demoUser !== null}
                    className="w-full flex items-center gap-3 p-3 rounded-xl
                      bg-gray-800/50 hover:bg-gray-800 border border-gray-700/50 hover:border-gray-600
                      transition-all text-sm text-left disabled:opacity-50"
                  >
                    <span className="text-lg">{user.icon}</span>
                    <div className="flex-1">
                      <span className="text-white font-medium">{user.username}</span>
                      <span className="text-gray-500 text-xs ml-2">· {user.role}</span>
                    </div>
                    {demoUser === user.username ? (
                      <div className="w-4 h-4 border-2 border-gray-400/30 border-t-gray-400 rounded-full animate-spin" />
                    ) : (
                      <span className="text-xs text-gray-600">Entrar →</span>
                    )}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Footer */}
          <p className="text-center text-xs text-gray-600 mt-6">
            Plataforma LLM Trust &amp; Safety &copy; 2025 · Edição corporativa
          </p>
        </div>
      </div>
    </div>
  )
}
