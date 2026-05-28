import { useState, useEffect, useRef } from 'react'
import { FileDown, FileText, Loader2, ChevronDown } from 'lucide-react'
import { relatoriosAPI } from '../utils/api'
import { toast } from './ui'

/**
 * Botão dropdown reutilizável para exportar relatórios PDF.
 *
 * Props:
 *  - days        : janela em dias passada ao backend (default 30)
 *  - tipos       : array opcional de tipos a exibir (filtro). Se vazio, mostra todos.
 *  - label       : rótulo do botão (default "Exportar PDF")
 *  - compact     : versão compacta (apenas ícone + dropdown)
 *  - className   : classes extras para o botão principal
 */
export default function ExportPDFMenu({
  days = 30,
  tipos = null,
  label = 'Exportar PDF',
  compact = false,
  className = '',
}) {
  const [open, setOpen] = useState(false)
  const [list, setList] = useState([])
  const [loadingTipo, setLoadingTipo] = useState(null)
  const [loadingList, setLoadingList] = useState(false)
  const ref = useRef(null)

  // Busca catálogo na primeira abertura
  useEffect(() => {
    if (open && list.length === 0 && !loadingList) {
      setLoadingList(true)
      relatoriosAPI.lista()
        .then(res => setList(res.data?.relatorios || []))
        .catch(() => toast('Não foi possível carregar a lista de relatórios.', 'error'))
        .finally(() => setLoadingList(false))
    }
  }, [open]) // eslint-disable-line

  // Fecha ao clicar fora
  useEffect(() => {
    if (!open) return
    const onClick = (e) => {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false)
    }
    document.addEventListener('mousedown', onClick)
    return () => document.removeEventListener('mousedown', onClick)
  }, [open])

  const filtered = tipos
    ? list.filter(r => tipos.includes(r.tipo))
    : list

  const baixar = async (tipo, titulo) => {
    setLoadingTipo(tipo)
    try {
      const res = await relatoriosAPI.baixarPDF(tipo, days)
      // Extrai filename do header
      const cd = res.headers['content-disposition'] || ''
      const match = cd.match(/filename="([^"]+)"/)
      const filename = match
        ? match[1]
        : `phoenix_${tipo}_${days}d.pdf`

      const url = window.URL.createObjectURL(new Blob([res.data], { type: 'application/pdf' }))
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      document.body.appendChild(a)
      a.click()
      a.remove()
      window.URL.revokeObjectURL(url)

      toast(`${titulo} baixado.`, 'success')
      setOpen(false)
    } catch (err) {
      console.error(err)
      toast('Falha ao gerar o relatório PDF.', 'error')
    } finally {
      setLoadingTipo(null)
    }
  }

  return (
    <div className="relative inline-block" ref={ref}>
      <button
        onClick={() => setOpen(v => !v)}
        className={
          'flex items-center gap-2 text-xs font-semibold px-3 py-2 rounded-xl ' +
          'border border-blue-500/30 bg-blue-500/10 text-blue-300 ' +
          'hover:bg-blue-500/20 hover:border-blue-500/50 transition-all ' +
          className
        }
      >
        <FileDown className="w-3.5 h-3.5" />
        {!compact && <span>{label}</span>}
        <ChevronDown className={`w-3 h-3 transition-transform ${open ? 'rotate-180' : ''}`} />
      </button>

      {open && (
        <div className="absolute right-0 mt-2 w-80 bg-gray-900 border border-gray-700 rounded-xl shadow-2xl z-50 overflow-hidden">
          <div className="px-3 py-2 border-b border-gray-800">
            <p className="text-[10px] uppercase tracking-widest text-gray-500 font-semibold">
              Relatórios disponíveis
            </p>
            <p className="text-[10px] text-gray-600 mt-0.5">
              Janela: últimos {days} dias
            </p>
          </div>

          {loadingList && (
            <div className="px-3 py-4 flex items-center gap-2 text-xs text-gray-500">
              <Loader2 className="w-3.5 h-3.5 animate-spin" /> Carregando catálogo…
            </div>
          )}

          {!loadingList && filtered.length === 0 && (
            <p className="px-3 py-4 text-xs text-gray-500">Nenhum relatório disponível.</p>
          )}

          <ul className="max-h-96 overflow-y-auto">
            {filtered.map(r => (
              <li key={r.tipo}>
                <button
                  onClick={() => baixar(r.tipo, r.titulo)}
                  disabled={loadingTipo === r.tipo}
                  className="w-full text-left px-3 py-2.5 hover:bg-gray-800 border-b border-gray-800/60 last:border-0 transition-colors disabled:opacity-60"
                >
                  <div className="flex items-start gap-2.5">
                    <div className="mt-0.5 w-7 h-7 rounded-lg bg-blue-500/15 border border-blue-500/30 flex items-center justify-center shrink-0">
                      {loadingTipo === r.tipo
                        ? <Loader2 className="w-3.5 h-3.5 animate-spin text-blue-400" />
                        : <FileText className="w-3.5 h-3.5 text-blue-400" />}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-semibold text-gray-100 leading-tight">
                        {r.titulo}
                      </p>
                      <p className="text-[10px] text-gray-500 mt-0.5 leading-snug">
                        {r.descricao}
                      </p>
                    </div>
                  </div>
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
