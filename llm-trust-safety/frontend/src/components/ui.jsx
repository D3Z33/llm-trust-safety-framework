/**
 * Componentes UI reutilizáveis - LLM Trust & Safety Framework PT-BR
 */
import { useState, useEffect } from 'react'
import { AlertTriangle, CheckCircle, Info, XCircle, X, Loader2 } from 'lucide-react'
import { RISK_COLORS, RISK_LABELS, SEVERITY_COLORS, SEVERITY_LABELS, STATUS_LABELS, STATUS_COLORS } from '../utils/helpers'
import clsx from 'clsx'

// ──────────────────────────── Loading ────────────────────────────
export function LoadingSpinner({ text = 'Carregando...' }) {
  return (
    <div className="flex flex-col items-center justify-center min-h-[300px] gap-4">
      <div className="relative">
        <div className="w-16 h-16 rounded-full border-4 border-blue-500/20 border-t-blue-500 animate-spin" />
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="w-8 h-8 rounded-full bg-blue-500/20 animate-pulse" />
        </div>
      </div>
      <p className="text-gray-400 text-sm animate-pulse">{text}</p>
    </div>
  )
}

// ──────────────────────────── Toast ────────────────────────────
const toastQueue = []
let toastListeners = []

export function toast(message, type = 'info', duration = 4000) {
  const id = Date.now()
  const item = { id, message, type, duration }
  toastQueue.push(item)
  toastListeners.forEach(fn => fn([...toastQueue]))
  setTimeout(() => {
    const idx = toastQueue.findIndex(t => t.id === id)
    if (idx > -1) {
      toastQueue.splice(idx, 1)
      toastListeners.forEach(fn => fn([...toastQueue]))
    }
  }, duration)
}

export function ToastContainer() {
  const [toasts, setToasts] = useState([])

  useEffect(() => {
    const listener = (items) => setToasts(items)
    toastListeners.push(listener)
    return () => { toastListeners = toastListeners.filter(l => l !== listener) }
  }, [])

  const icons = { success: CheckCircle, error: XCircle, warning: AlertTriangle, info: Info }
  const colors = {
    success: 'bg-green-900/90 border-green-500/40 text-green-100',
    error: 'bg-red-900/90 border-red-500/40 text-red-100',
    warning: 'bg-yellow-900/90 border-yellow-500/40 text-yellow-100',
    info: 'bg-blue-900/90 border-blue-500/40 text-blue-100',
  }

  return (
    <div className="fixed top-4 right-4 z-50 flex flex-col gap-2 pointer-events-none">
      {toasts.map(t => {
        const Icon = icons[t.type] || Info
        return (
          <div key={t.id} className={clsx(
            'flex items-center gap-3 px-4 py-3 rounded-xl border backdrop-blur-sm shadow-xl pointer-events-auto',
            'animate-slide-in max-w-sm text-sm font-medium',
            colors[t.type]
          )}>
            <Icon className="w-4 h-4 flex-shrink-0" />
            <span className="flex-1">{t.message}</span>
          </div>
        )
      })}
    </div>
  )
}

// ──────────────────────────── StatCard ────────────────────────────
export function StatCard({ label, value, subtitle, icon: Icon, color = '#3b82f6', trend, trendPositive, onClick }) {
  return (
    <div
      onClick={onClick}
      className={clsx(
        'bg-gray-800/60 border border-gray-700/50 rounded-2xl p-5 transition-all duration-200',
        'hover:border-gray-600/80 hover:bg-gray-800/80',
        onClick && 'cursor-pointer hover:scale-[1.02]'
      )}
    >
      <div className="flex items-start justify-between mb-3">
        {Icon && (
          <div className="w-11 h-11 rounded-xl flex items-center justify-center" style={{ backgroundColor: color + '22' }}>
            <Icon className="w-5 h-5" style={{ color }} />
          </div>
        )}
        {trend !== undefined && (
          <span className={clsx(
            'text-xs font-semibold px-2 py-1 rounded-full',
            trendPositive ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'
          )}>
            {trendPositive ? '↑' : '↓'} {Math.abs(trend)}%
          </span>
        )}
      </div>
      <div className="space-y-1">
        <div className="text-2xl font-bold text-white">{value}</div>
        <div className="text-sm font-medium text-gray-300">{label}</div>
        {subtitle && <div className="text-xs text-gray-500">{subtitle}</div>}
      </div>
    </div>
  )
}

// ──────────────────────────── RiskBadge ────────────────────────────
export function RiskBadge({ level, size = 'sm' }) {
  const color = RISK_COLORS[level] || '#6b7280'
  const label = RISK_LABELS[level] || level
  return (
    <span className={clsx(
      'inline-flex items-center font-semibold rounded-full border',
      size === 'sm' ? 'text-xs px-2 py-0.5' : 'text-sm px-3 py-1'
    )} style={{ color, borderColor: color + '40', backgroundColor: color + '18' }}>
      {label}
    </span>
  )
}

// ──────────────────────────── SeverityBadge ────────────────────────────
export function SeverityBadge({ severity, size = 'sm' }) {
  const color = SEVERITY_COLORS[severity] || '#6b7280'
  const label = SEVERITY_LABELS[severity] || severity
  return (
    <span className={clsx(
      'inline-flex items-center font-semibold rounded-full border',
      size === 'sm' ? 'text-xs px-2 py-0.5' : 'text-sm px-3 py-1'
    )} style={{ color, borderColor: color + '40', backgroundColor: color + '18' }}>
      {label}
    </span>
  )
}

// ──────────────────────────── StatusBadge ────────────────────────────
export function StatusBadge({ status }) {
  const color = STATUS_COLORS[status] || '#6b7280'
  const label = STATUS_LABELS[status] || status
  return (
    <span className="inline-flex items-center text-xs font-semibold rounded-full border px-2 py-0.5"
      style={{ color, borderColor: color + '40', backgroundColor: color + '18' }}>
      {label}
    </span>
  )
}

// ──────────────────────────── RiskMeter ────────────────────────────
export function RiskMeter({ score, size = 120 }) {
  const level = score >= 80 ? 'CRITICAL' : score >= 60 ? 'HIGH' : score >= 30 ? 'MEDIUM' : 'LOW'
  const color = RISK_COLORS[level]
  const label = RISK_LABELS[level]
  const pct = Math.min(100, Math.max(0, score))
  const circumference = 2 * Math.PI * 45
  const offset = circumference - (pct / 100) * circumference

  return (
    <div className="flex flex-col items-center gap-2">
      <div className="relative" style={{ width: size, height: size }}>
        <svg viewBox="0 0 100 100" className="transform -rotate-90" width={size} height={size}>
          <circle cx="50" cy="50" r="45" fill="none" stroke="#374151" strokeWidth="8" />
          <circle cx="50" cy="50" r="45" fill="none" stroke={color} strokeWidth="8"
            strokeDasharray={circumference} strokeDashoffset={offset}
            strokeLinecap="round" style={{ transition: 'stroke-dashoffset 0.8s ease' }} />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-2xl font-bold text-white">{Math.round(pct)}</span>
          <span className="text-xs text-gray-400">/ 100</span>
        </div>
      </div>
      <RiskBadge level={level} />
    </div>
  )
}

// ──────────────────────────── ScoreBar ────────────────────────────
export function ScoreBar({ label, score, max = 100, color }) {
  const pct = Math.min(100, (score / max) * 100)
  const col = color || (score >= 80 ? '#ef4444' : score >= 60 ? '#f97316' : score >= 30 ? '#f59e0b' : '#22c55e')
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-sm">
        <span className="text-gray-300">{label}</span>
        <span className="font-semibold" style={{ color: col }}>{score.toFixed(1)}%</span>
      </div>
      <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
        <div className="h-full rounded-full transition-all duration-500"
          style={{ width: `${pct}%`, backgroundColor: col }} />
      </div>
    </div>
  )
}

// ──────────────────────────── Modal ────────────────────────────
export function Modal({ isOpen, onClose, title, children, size = 'md' }) {
  if (!isOpen) return null
  const sizes = { sm: 'max-w-sm', md: 'max-w-lg', lg: 'max-w-2xl', xl: 'max-w-4xl', full: 'max-w-6xl' }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" onClick={onClose} />
      <div className={clsx('relative bg-gray-900 border border-gray-700 rounded-2xl shadow-2xl w-full', sizes[size])}>
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-700">
          <h2 className="text-lg font-semibold text-white">{title}</h2>
          <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-gray-700 text-gray-400 hover:text-white transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>
        <div className="p-6 overflow-y-auto max-h-[80vh]">{children}</div>
      </div>
    </div>
  )
}

// ──────────────────────────── Table ────────────────────────────
export function Table({ columns, data, loading, emptyMessage = 'Nenhum dado encontrado', onRowClick }) {
  if (loading) return <LoadingSpinner />
  return (
    <div className="overflow-x-auto rounded-xl border border-gray-700/50">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-gray-700/50 bg-gray-800/50">
            {columns.map((col) => (
              <th key={col.key} className="text-left px-4 py-3 text-gray-400 font-medium whitespace-nowrap">
                {col.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.length === 0 ? (
            <tr>
              <td colSpan={columns.length} className="text-center py-12 text-gray-500">{emptyMessage}</td>
            </tr>
          ) : (
            data.map((row, i) => (
              <tr
                key={i}
                onClick={() => onRowClick?.(row)}
                className={clsx(
                  'border-b border-gray-700/30 transition-colors',
                  onRowClick ? 'cursor-pointer hover:bg-gray-700/30' : '',
                  i % 2 === 0 ? 'bg-gray-800/20' : 'bg-transparent'
                )}
              >
                {columns.map((col) => (
                  <td key={col.key} className="px-4 py-3 text-gray-300">
                    {col.render ? col.render(row[col.key], row) : row[col.key] ?? '—'}
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  )
}

// ──────────────────────────── Button ────────────────────────────
export function Button({ children, onClick, variant = 'primary', size = 'md', disabled, loading, className, type = 'button' }) {
  const variants = {
    primary: 'bg-blue-600 hover:bg-blue-500 text-white border-blue-500/50',
    danger: 'bg-red-600/20 hover:bg-red-600/40 text-red-400 border-red-500/40',
    success: 'bg-green-600/20 hover:bg-green-600/40 text-green-400 border-green-500/40',
    secondary: 'bg-gray-700 hover:bg-gray-600 text-gray-300 border-gray-600',
    ghost: 'bg-transparent hover:bg-gray-700/50 text-gray-400 hover:text-white border-transparent',
  }
  const sizes = {
    xs: 'px-2.5 py-1.5 text-xs',
    sm: 'px-3 py-2 text-sm',
    md: 'px-4 py-2.5 text-sm',
    lg: 'px-6 py-3 text-base',
  }
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled || loading}
      className={clsx(
        'inline-flex items-center gap-2 rounded-xl border font-medium transition-all duration-200',
        'disabled:opacity-50 disabled:cursor-not-allowed',
        variants[variant], sizes[size], className
      )}
    >
      {loading && <Loader2 className="w-4 h-4 animate-spin" />}
      {children}
    </button>
  )
}

// ──────────────────────────── Input ────────────────────────────
export function Input({ label, error, className, ...props }) {
  return (
    <div className="space-y-1.5">
      {label && <label className="block text-sm font-medium text-gray-300">{label}</label>}
      <input
        {...props}
        className={clsx(
          'w-full bg-gray-800 border rounded-xl px-4 py-2.5 text-white text-sm',
          'focus:outline-none focus:ring-2 focus:ring-blue-500/50',
          'placeholder:text-gray-500 transition-colors',
          error ? 'border-red-500/50 focus:ring-red-500/30' : 'border-gray-700 focus:border-blue-500/50',
          className
        )}
      />
      {error && <p className="text-xs text-red-400">{error}</p>}
    </div>
  )
}

// ──────────────────────────── Select ────────────────────────────
export function Select({ label, error, className, children, ...props }) {
  return (
    <div className="space-y-1.5">
      {label && <label className="block text-sm font-medium text-gray-300">{label}</label>}
      <select
        {...props}
        className={clsx(
          'w-full bg-gray-800 border rounded-xl px-4 py-2.5 text-white text-sm',
          'focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-colors',
          error ? 'border-red-500/50' : 'border-gray-700 focus:border-blue-500/50',
          className
        )}
      >
        {children}
      </select>
      {error && <p className="text-xs text-red-400">{error}</p>}
    </div>
  )
}

// ──────────────────────────── Textarea ────────────────────────────
export function Textarea({ label, error, className, ...props }) {
  return (
    <div className="space-y-1.5">
      {label && <label className="block text-sm font-medium text-gray-300">{label}</label>}
      <textarea
        {...props}
        className={clsx(
          'w-full bg-gray-800 border rounded-xl px-4 py-2.5 text-white text-sm resize-none',
          'focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-colors',
          'placeholder:text-gray-500 min-h-[100px]',
          error ? 'border-red-500/50' : 'border-gray-700 focus:border-blue-500/50',
          className
        )}
      />
      {error && <p className="text-xs text-red-400">{error}</p>}
    </div>
  )
}

// ──────────────────────────── Pagination ────────────────────────────
export function Pagination({ page, pages, total, perPage, onPageChange }) {
  if (pages <= 1) return null
  return (
    <div className="flex items-center justify-between text-sm text-gray-400 mt-4">
      <span>Exibindo {(page - 1) * perPage + 1}-{Math.min(page * perPage, total)} de {total}</span>
      <div className="flex gap-1">
        <button onClick={() => onPageChange(1)} disabled={page === 1}
          className="px-2 py-1 rounded hover:bg-gray-700 disabled:opacity-40">«</button>
        <button onClick={() => onPageChange(page - 1)} disabled={page === 1}
          className="px-2 py-1 rounded hover:bg-gray-700 disabled:opacity-40">‹</button>
        {Array.from({ length: Math.min(5, pages) }, (_, i) => {
          const p = Math.max(1, Math.min(pages - 4, page - 2)) + i
          return (
            <button key={p} onClick={() => onPageChange(p)}
              className={clsx('px-2.5 py-1 rounded transition-colors', p === page ? 'bg-blue-600 text-white' : 'hover:bg-gray-700')}>
              {p}
            </button>
          )
        })}
        <button onClick={() => onPageChange(page + 1)} disabled={page === pages}
          className="px-2 py-1 rounded hover:bg-gray-700 disabled:opacity-40">›</button>
        <button onClick={() => onPageChange(pages)} disabled={page === pages}
          className="px-2 py-1 rounded hover:bg-gray-700 disabled:opacity-40">»</button>
      </div>
    </div>
  )
}

// ──────────────────────────── Toggle ────────────────────────────
export function Toggle({ checked, onChange, label, disabled }) {
  return (
    <label className="flex items-center gap-3 cursor-pointer group">
      <div className="relative">
        <input type="checkbox" className="sr-only" checked={checked} onChange={e => onChange(e.target.checked)} disabled={disabled} />
        <div className={clsx(
          'w-11 h-6 rounded-full transition-colors duration-200',
          checked ? 'bg-blue-600' : 'bg-gray-600',
          disabled && 'opacity-50 cursor-not-allowed'
        )} />
        <div className={clsx(
          'absolute top-1 left-1 w-4 h-4 bg-white rounded-full shadow transition-transform duration-200',
          checked && 'translate-x-5'
        )} />
      </div>
      {label && <span className="text-sm text-gray-300 group-hover:text-white transition-colors">{label}</span>}
    </label>
  )
}

// ──────────────────────────── Card ────────────────────────────
export function Card({ title, subtitle, children, className, actions, badge }) {
  return (
    <div className={clsx('bg-gray-800/60 border border-gray-700/50 rounded-2xl overflow-hidden', className)}>
      {(title || actions || badge) && (
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-700/50">
          <div>
            {title && <h3 className="font-semibold text-white">{title}</h3>}
            {subtitle && <p className="text-xs text-gray-400 mt-0.5">{subtitle}</p>}
          </div>
          <div className="flex items-center gap-3">
            {badge}
            {actions}
          </div>
        </div>
      )}
      <div className="p-6">{children}</div>
    </div>
  )
}

// ──────────────────────────── EmptyState ────────────────────────────
export function EmptyState({ icon: Icon, title, description, action }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 gap-4 text-center">
      {Icon && (
        <div className="w-16 h-16 rounded-2xl bg-gray-700/50 flex items-center justify-center">
          <Icon className="w-8 h-8 text-gray-500" />
        </div>
      )}
      <div>
        <h3 className="text-gray-300 font-medium">{title}</h3>
        {description && <p className="text-gray-500 text-sm mt-1">{description}</p>}
      </div>
      {action}
    </div>
  )
}
