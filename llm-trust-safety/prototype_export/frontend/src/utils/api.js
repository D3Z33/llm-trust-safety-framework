import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 30000,
})

// Interceptor para adicionar token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('ltf_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Interceptor para tratar erros
api.interceptors.response.use(
  (res) => res,
  async (error) => {
    if (error.response?.status === 401) {
      // Tentar refresh token
      const refreshToken = localStorage.getItem('ltf_refresh')
      if (refreshToken && !error.config._retry) {
        error.config._retry = true
        try {
          const resp = await axios.post(`${BASE_URL}/api/auth/refresh`, { refresh_token: refreshToken })
          const newToken = resp.data.access_token
          localStorage.setItem('ltf_token', newToken)
          error.config.headers.Authorization = `Bearer ${newToken}`
          return api(error.config)
        } catch {
          localStorage.clear()
          window.location.href = '/login'
        }
      } else {
        localStorage.clear()
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

// ──────────────────────────── Auth ────────────────────────────
export const authAPI = {
  login: (username, password) =>
    api.post('/api/auth/login/json', { username, password }),
  logout: () => {
    localStorage.clear()
    window.location.href = '/login'
  },
  eu: () => api.get('/api/auth/eu'),
  alterarSenha: (data) => api.post('/api/auth/alterar-senha', data),
}

// ──────────────────────────── Dashboard ────────────────────────────
export const dashboardAPI = {
  getDashboard: (hours = 24) => api.get(`/api/dashboard?hours=${hours}`),
  getLogs: (params = {}) => api.get('/api/logs', { params }),
  getSessions: () => api.get('/api/sessions'),
  getOWASP: () => api.get('/api/owasp'),
  getOWASPDetails: (days = 30) => api.get(`/api/owasp/details?days=${days}`),
  exportLogs: (format = 'csv') => api.get(`/api/logs/export?format=${format}`, { responseType: 'blob' }),
}

// ──────────────────────────── Evaluate ────────────────────────────
export const evaluateAPI = {
  evaluate: (data) => api.post('/api/evaluate', data),
}

// ──────────────────────────── Logs ────────────────────────────
export const logsAPI = {
  getLogs: (params = {}) => api.get('/api/logs', { params }),
  getLog: (id) => api.get(`/api/logs/${id}`),
}

// ──────────────────────────── Sessions ────────────────────────────
export const sessionsAPI = {
  getSessions: () => api.get('/api/sessions'),
  getSession: (id) => api.get(`/api/sessions/${id}`),
  getTimeline: (id) => api.get(`/api/sessions/${id}/timeline`),
}

// ──────────────────────────── Alertas ────────────────────────────
export const alertsAPI = {
  listar: (params = {}) => api.get('/api/alertas', { params }),
  resumo: () => api.get('/api/alertas/resumo'),
  criar: (data) => api.post('/api/alertas', data),
  reconhecer: (id) => api.put(`/api/alertas/${id}/reconhecer`),
  resolver: (id, data) => api.put(`/api/alertas/${id}/resolver`, data),
  falsoPositivo: (id) => api.put(`/api/alertas/${id}/falso-positivo`),
}

// ──────────────────────────── Conformidade ────────────────────────────
export const conformidadeAPI = {
  visaoGeral: () => api.get('/api/conformidade/visao-geral'),
  nist: () => api.get('/api/conformidade/nist'),
  lgpd: () => api.get('/api/conformidade/lgpd'),
  owasp: () => api.get('/api/conformidade/owasp'),
  gerarRelatorio: (data) => api.post('/api/conformidade/gerar-relatorio', data),
}

// ──────────────────────────── Threat Intel ────────────────────────────
export const threatIntelAPI = {
  listar: (params = {}) => api.get('/api/ameacas', { params }),
  estatisticas: (days = 30) => api.get(`/api/ameacas/estatisticas?days=${days}`),
  adicionar: (data) => api.post('/api/ameacas', data),
  desativar: (id) => api.put(`/api/ameacas/${id}/desativar`),
}

// ──────────────────────────── Políticas ────────────────────────────
export const politicasAPI = {
  listar: (params = {}) => api.get('/api/politicas', { params }),
  criar: (data) => api.post('/api/politicas', data),
  atualizar: (id, data) => api.put(`/api/politicas/${id}`, data),
  toggle: (id) => api.put(`/api/politicas/${id}/toggle`),
  deletar: (id) => api.delete(`/api/politicas/${id}`),
}

// ──────────────────────────── Analytics ────────────────────────────
export const analyticsAPI = {
  visaoGeral: (days = 30) => api.get(`/api/analytics/visao-geral?days=${days}`),
  heatmap: (days = 7) => api.get(`/api/analytics/heatmap?days=${days}`),
  tendencias: (days = 30) => api.get(`/api/analytics/tendencias?days=${days}`),
  topSessoes: () => api.get('/api/analytics/top-sessoes-risco'),
  latencia: () => api.get('/api/analytics/latencia'),
  exposicaoDados: (days = 30) => api.get(`/api/analytics/exposicao-dados?days=${days}`),
}

// ──────────────────────────── Relatórios PDF ────────────────────────────
export const relatoriosAPI = {
  lista: () => api.get('/api/relatorios/lista'),
  baixarPDF: (tipo, days = 30) =>
    api.get(`/api/relatorios/pdf/${tipo}`, {
      params: { days },
      responseType: 'blob',
    }),
}

// ──────────────────────────── Usuários ────────────────────────────
export const usuariosAPI = {
  listar: () => api.get('/api/usuarios'),
  criar: (data) => api.post('/api/usuarios', data),
  atualizar: (id, data) => api.put(`/api/usuarios/${id}`, data),
  desativar: (id) => api.delete(`/api/usuarios/${id}`),
  eu: () => api.get('/api/usuarios/eu'),
  atualizarPerfil: (data) => api.put('/api/usuarios/eu', data),
  minhasAPIKeys: () => api.get('/api/usuarios/apikeys/minhas'),
  criarAPIKey: (data) => api.post('/api/usuarios/apikeys', data),
  revogarAPIKey: (id) => api.delete(`/api/usuarios/apikeys/${id}`),
}

export default api
