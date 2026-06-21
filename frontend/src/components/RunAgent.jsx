import { useEffect, useRef, useState } from 'react'
import { runAgent, onAgent } from '../api.js'

const ROLES = ['orchestrator', 'product-manager', 'architect', 'worker', 'qa', 'design-system', 'devops']

const KIND_STYLE = {
  text: 'text-slate-200',
  system: 'text-slate-500',
  result: 'text-emerald-300',
  error: 'text-rose-300',
}

const INPUT = 'w-full rounded-lg border border-white/10 bg-black/20 px-2.5 py-1.5 text-sm text-slate-200 outline-none focus:border-white/25'

function Field({ label, children }) {
  return (
    <label className="block">
      <span className="mb-1 block text-xs uppercase tracking-wider text-slate-500">{label}</span>
      {children}
    </label>
  )
}

export default function RunAgent() {
  const [role, setRole] = useState('architect')
  const [issue, setIssue] = useState('')
  const [cwd, setCwd] = useState('')
  const [prompt, setPrompt] = useState('')
  const [running, setRunning] = useState(false)
  const [meta, setMeta] = useState(null)
  const [events, setEvents] = useState([])
  const runId = useRef(null)

  useEffect(() => {
    onAgent((ev) => {
      if (ev.run_id !== runId.current) return
      if (ev.kind === 'done') { setRunning(false); return }
      setEvents((cur) => [...cur, ev])
    })
    return () => { window.__hephaestus_agent__ = null }
  }, [])

  async function start() {
    if (!prompt.trim() || running) return
    setEvents([]); setMeta(null); setRunning(true)
    const res = await runAgent(role, prompt, issue, cwd, null)
    if (!res) {
      setRunning(false)
      setEvents([{ kind: 'error', text: 'Agent bridge unavailable — run inside the desktop app.' }])
      return
    }
    runId.current = res.run_id
    setMeta(res)
  }

  return (
    <div className="grid grid-cols-1 gap-4 lg:grid-cols-[340px_1fr]">
      <aside className="space-y-3 rounded-2xl border border-white/5 bg-white/[0.02] p-4">
        <Field label="Role">
          <select value={role} onChange={(e) => setRole(e.target.value)} className={INPUT}>
            {ROLES.map((r) => <option key={r} value={r} className="bg-[#0b0e14]">{r}</option>)}
          </select>
        </Field>
        <Field label="Issue (optional)">
          <input value={issue} onChange={(e) => setIssue(e.target.value)} placeholder="issue-003" className={INPUT} />
        </Field>
        <Field label="Working dir (optional)">
          <input value={cwd} onChange={(e) => setCwd(e.target.value)} placeholder="path to target repo" className={INPUT} />
        </Field>
        <Field label="Prompt">
          <textarea value={prompt} onChange={(e) => setPrompt(e.target.value)} rows={7}
            placeholder="What should the agent do?" className={`${INPUT} resize-y font-mono`} />
        </Field>
        <button
          onClick={start}
          disabled={running || !prompt.trim()}
          className="w-full rounded-lg bg-gradient-to-br from-orange-500 to-amber-600 px-3 py-2 text-sm font-semibold text-black hover:opacity-90 disabled:opacity-40"
        >
          {running ? 'Running…' : 'Run agent'}
        </button>
        {meta && (
          <div className="rounded-lg border border-white/5 bg-black/20 p-2.5 text-[11px] text-slate-500">
            routed to <span className="font-medium text-slate-300">{meta.tool}</span> · context{' '}
            {meta.context.length ? meta.context.join(', ') : '—'}
            {meta.missing?.length ? <div className="text-amber-400/80">missing: {meta.missing.join(', ')}</div> : null}
          </div>
        )}
      </aside>

      <section className="overflow-hidden rounded-2xl border border-white/5 bg-white/[0.02]">
        <header className="flex items-center justify-between border-b border-white/5 px-4 py-2.5">
          <h2 className="text-sm font-semibold text-slate-200">Agent Output</h2>
          {running && (
            <span className="flex items-center gap-1.5 text-xs text-emerald-400">
              <span className="h-2 w-2 animate-pulse rounded-full bg-emerald-400" />streaming
            </span>
          )}
        </header>
        {events.length === 0 ? (
          <p className="px-5 py-12 text-center text-sm text-slate-500">
            Configure a task and run an agent. Output streams here.
          </p>
        ) : (
          <div className="max-h-[70vh] space-y-0.5 overflow-auto p-4 font-mono text-[12.5px] leading-relaxed">
            {events.map((ev, i) => (
              <div key={i} className={KIND_STYLE[ev.kind] || 'text-slate-400'}>
                <span className="select-none text-slate-600">[{ev.kind}] </span>
                <span className="whitespace-pre-wrap break-words">{ev.text}</span>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  )
}
