import { createContext, useCallback, useContext, useEffect, useRef, useState } from 'react'
import { saveCorrection } from '../api.js'

const ToastCtx = createContext({ addToast: () => {}, removeToast: () => {} })

export function useToast() {
  return useContext(ToastCtx)
}

const SEVERITY_STYLE = {
  error: 'bg-rose-500/15 text-rose-300 ring-rose-500/30',
  warning: 'bg-amber-500/15 text-amber-300 ring-amber-500/30',
  info: 'bg-sky-500/15 text-sky-300 ring-sky-500/30',
  ok: 'bg-emerald-500/15 text-emerald-300 ring-emerald-500/30',
}

function CorrectionBox({ toast, onClose }) {
  const [note, setNote] = useState('')
  const [saving, setSaving] = useState(false)

  async function submit(e) {
    e.preventDefault()
    if (!note.trim() || saving) return
    setSaving(true)
    await saveCorrection(toast.rule_id || null, toast.node_id || null, toast.issue_id || null, note.trim())
    setSaving(false)
    onClose()
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="w-full max-w-md rounded-2xl border border-white/10 bg-[#0b0e14] p-6 shadow-2xl">
        <div className="mb-4 text-sm font-semibold text-slate-100">Correction Box</div>
        <div className="mb-4 space-y-2 rounded-xl border border-white/5 bg-black/30 p-3 text-xs">
          {toast.rule_id && <div><span className="text-slate-500">Rule: </span><span className="font-mono text-slate-300">{toast.rule_id}</span></div>}
          {toast.node_id && <div><span className="text-slate-500">Node: </span><span className="font-mono text-slate-300">{toast.node_id}</span></div>}
          {toast.issue_id && <div><span className="text-slate-500">Issue: </span><span className="font-mono text-slate-300">{toast.issue_id}</span></div>}
          <div><span className="text-slate-500">Violation: </span><span className="text-slate-300">{toast.message}</span></div>
        </div>
        <form onSubmit={submit} className="space-y-3">
          <label className="block">
            <span className="mb-1 block text-xs uppercase tracking-wider text-slate-500">Your note</span>
            <textarea
              value={note}
              onChange={e => setNote(e.target.value)}
              rows={4}
              className="w-full rounded-lg border border-white/10 bg-black/20 px-3 py-2 text-sm text-slate-200 outline-none focus:border-white/25 resize-none"
              placeholder="Describe what should have happened…"
              autoFocus
            />
          </label>
          <div className="flex gap-2">
            <button
              type="submit"
              disabled={saving || !note.trim()}
              className="flex-1 rounded-lg bg-gradient-to-br from-orange-500 to-amber-600 px-3 py-2 text-sm font-semibold text-black hover:opacity-90 disabled:opacity-40"
            >
              {saving ? 'Saving…' : 'Save correction'}
            </button>
            <button
              type="button"
              onClick={onClose}
              className="rounded-lg border border-white/10 px-3 py-2 text-sm font-medium text-slate-300 hover:bg-white/5"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

function ToastCard({ toast, onDismiss }) {
  const [correcting, setCorrecting] = useState(false)
  const timerRef = useRef(null)

  useEffect(() => {
    timerRef.current = setTimeout(onDismiss, 8000)
    return () => clearTimeout(timerRef.current)
  }, [onDismiss])

  function pauseTimer() { clearTimeout(timerRef.current) }
  function resumeTimer() { timerRef.current = setTimeout(onDismiss, 4000) }

  const sev = toast.severity || 'info'
  const badge = SEVERITY_STYLE[sev] || SEVERITY_STYLE.info
  const canCorrect = toast.allowCorrection !== false && Boolean(toast.rule_id || toast.issue_id || toast.node_id)

  return (
    <>
      <div
        className="w-80 rounded-2xl border border-white/10 bg-[#0b0e14]/95 p-4 shadow-2xl backdrop-blur"
        onMouseEnter={pauseTimer}
        onMouseLeave={resumeTimer}
      >
        <div className="mb-2 flex items-start gap-2">
          <span className={`mt-0.5 inline-flex rounded-full px-2 py-0.5 text-[10px] font-semibold ring-1 ring-inset ${badge}`}>
            {sev}
          </span>
          {toast.rule_id && (
            <span className="font-mono text-[11px] text-slate-400">{toast.rule_id}</span>
          )}
        </div>
        <p className="mb-3 text-sm text-slate-200">{toast.message}</p>
        <div className="mb-3 flex flex-wrap gap-1.5">
          {toast.issue_id && (
            <span className="rounded-full bg-sky-500/10 px-2 py-0.5 text-[10px] text-sky-300 ring-1 ring-sky-500/20">{toast.issue_id}</span>
          )}
          {toast.node_id && (
            <span className="rounded-full bg-fuchsia-500/10 px-2 py-0.5 text-[10px] text-fuchsia-300 ring-1 ring-fuchsia-500/20">{toast.node_id}</span>
          )}
        </div>
        <div className="flex gap-2">
          {canCorrect && (
            <button
              type="button"
              onClick={() => { pauseTimer(); setCorrecting(true) }}
              className="flex-1 rounded-lg border border-orange-500/30 bg-orange-500/10 px-2 py-1.5 text-xs font-medium text-orange-300 hover:bg-orange-500/20"
            >
              Correct →
            </button>
          )}
          <button
            type="button"
            onClick={onDismiss}
            className={`${canCorrect ? '' : 'flex-1 '}rounded-lg border border-white/10 px-2 py-1.5 text-xs font-medium text-slate-400 hover:bg-white/5`}
          >
            Dismiss
          </button>
        </div>
      </div>
      {correcting && canCorrect && <CorrectionBox toast={toast} onClose={() => { setCorrecting(false); onDismiss() }} />}
    </>
  )
}

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([])

  const addToast = useCallback((toast) => {
    setToasts(prev => [...prev, { ...toast, id: toast.id || Math.random().toString(36).slice(2) }])
  }, [])

  const removeToast = useCallback((id) => {
    setToasts(prev => prev.filter(t => t.id !== id))
  }, [])

  return (
    <ToastCtx.Provider value={{ addToast, removeToast }}>
      {children}
      <div className="fixed right-4 top-4 z-40 flex flex-col gap-3">
        {toasts.map(t => (
          <ToastCard key={t.id} toast={t} onDismiss={() => removeToast(t.id)} />
        ))}
      </div>
    </ToastCtx.Provider>
  )
}
