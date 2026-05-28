/**
 * Helpers e utilitários PT-BR
 */

export const RISK_COLORS = {
  LOW: '#22c55e',
  MEDIUM: '#f59e0b',
  HIGH: '#f97316',
  CRITICAL: '#ef4444',
}

export const RISK_LABELS = {
  LOW: 'Baixo',
  MEDIUM: 'Médio',
  HIGH: 'Alto',
  CRITICAL: 'Crítico',
}

export const SEVERITY_COLORS = {
  critical: '#ef4444',
  high: '#f97316',
  medium: '#f59e0b',
  low: '#22c55e',
  info: '#3b82f6',
}

export const SEVERITY_LABELS = {
  critical: 'Crítico',
  high: 'Alto',
  medium: 'Médio',
  low: 'Baixo',
  info: 'Info',
}

export const STATUS_LABELS = {
  open: 'Aberto',
  acknowledged: 'Reconhecido',
  resolved: 'Resolvido',
  false_positive: 'Falso Positivo',
}

export const STATUS_COLORS = {
  open: '#ef4444',
  acknowledged: '#f59e0b',
  resolved: '#22c55e',
  false_positive: '#6b7280',
}

export const ROLE_LABELS = {
  admin: 'Administrador',
  analyst: 'Analista',
  viewer: 'Visualizador',
  api_user: 'Usuário API',
}

export const SESSION_STATE_LABELS = {
  NORMAL: 'Normal',
  SUSPICIOUS: 'Suspeito',
  BLOCKED: 'Bloqueado',
  TERMINATED: 'Encerrado',
}

export const SESSION_STATE_COLORS = {
  NORMAL: '#22c55e',
  SUSPICIOUS: '#f59e0b',
  BLOCKED: '#ef4444',
  TERMINATED: '#6b7280',
}

export const LABEL_NAMES = {
  prompt_injection: 'Injeção de Prompt',
  jailbreak: 'Jailbreak',
  goal_hijacking: 'Sequestro de Objetivo',
  data_exfiltration: 'Exfiltração de Dados',
  obfuscation: 'Ofuscação',
  policy_evasion: 'Evasão de Política',
  multi_step_deception: 'Engano Multi-passo',
  tool_abuse: 'Abuso de Ferramenta',
  context_hijacking: 'Sequestro de Contexto',
  critical_content: 'Conteúdo Crítico',
  'STATE_CHANGE:NORMAL->SUSPICIOUS': 'Sessão Suspeita',
  'STATE_CHANGE:SUSPICIOUS->BLOCKED': 'Sessão Bloqueada',
  MULTI_ATTACK_PATTERN: 'Padrão de Multi-Ataque',
}

export function getRiskColor(level) {
  return RISK_COLORS[level] || '#6b7280'
}

export function getRiskLabel(level) {
  return RISK_LABELS[level] || level
}

export function getLabelName(label) {
  return LABEL_NAMES[label] || label
}

export function formatDate(date) {
  if (!date) return '—'
  return new Date(date).toLocaleString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export function formatDateShort(date) {
  if (!date) return '—'
  return new Date(date).toLocaleDateString('pt-BR')
}

export function formatRelative(date) {
  if (!date) return '—'
  const now = new Date()
  const d = new Date(date)
  const diff = Math.floor((now - d) / 1000)

  if (diff < 60) return `${diff}s atrás`
  if (diff < 3600) return `${Math.floor(diff / 60)}min atrás`
  if (diff < 86400) return `${Math.floor(diff / 3600)}h atrás`
  return `${Math.floor(diff / 86400)}d atrás`
}

export function formatBytes(bytes) {
  if (!bytes) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`
}

export function formatLatency(ms) {
  if (!ms) return '0ms'
  return ms < 1000 ? `${Math.round(ms)}ms` : `${(ms / 1000).toFixed(1)}s`
}

export function truncate(text, max = 80) {
  if (!text) return ''
  return text.length > max ? text.slice(0, max) + '...' : text
}

export function scoreToGrade(score) {
  if (score >= 90) return { grade: 'A+', color: '#22c55e' }
  if (score >= 80) return { grade: 'A', color: '#22c55e' }
  if (score >= 70) return { grade: 'B', color: '#84cc16' }
  if (score >= 60) return { grade: 'C', color: '#f59e0b' }
  if (score >= 50) return { grade: 'D', color: '#f97316' }
  return { grade: 'F', color: '#ef4444' }
}

export function generateId() {
  return Math.random().toString(36).substring(2, 11)
}

export function copyToClipboard(text) {
  navigator.clipboard.writeText(text).catch(console.error)
}
