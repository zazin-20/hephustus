import { useEffect, useState } from 'react'
import Dashboard from './components/Dashboard.jsx'
import Violations from './components/Violations.jsx'
import CodeView from './components/CodeView.jsx'
import RunAgent from './components/RunAgent.jsx'
import { StatCard } from './components/ui.jsx'
import { onPush, whenReady, getState, rescan, hasBridge } from './api.js'
import { MOCK } from './mock.js'

export default function App() {
  const [snap, setSnap] = useState(null)
  const [live, setLive] = useState(false)
  const [busy, setBusy] = useState(false)
  const [view, setView] = useState('compliance')

  useEffect(() => {
    onPush(setSnap)
    whenReady(async () => {
      setLive(true)
      const s = await getState()
      if (s) setSnap(s)
    })
    // Browser preview fallback: if no bridge connected shortly, show mock data.
    const t = setTimeout(() => { if (!hasBridge()) setSnap(MOCK) }, 500)
    return () => clearTimeout(t)
  }, [])

  async function doRescan() {
    setBusy(true)
    const s = await rescan()
    if (s) setSnap(s)
    setBusy(false)
  }

  if (!snap) return <Splash />

  const sum = snap.summary
  return (
    <div className="min-h-full text-slate-200">
      <header className="sticky top-0 z-10 border-b border-white/5 bg-[#0b0e14]/80 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-3.5">
          <div className="flex items-center gap-3">
            <div className="grid h-9 w-9 place-items-center rounded-xl bg-gradient-to-br from-orange-500 to-amber-600 font-bold text-black shadow-lg shadow-orange-900/30">
              H
            </div>
            <div>
              <div className="text-sm font-semibold">Hephaestus</div>
              <div className="font-mono text-[11px] text-slate-500">{snap.root}</div>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <nav className="flex items-center gap-1 rounded-lg bg-white/5 p-0.5 text-xs">
              {['compliance', 'code', 'agent'].map((v) => (
                <button
                  key={v}
                  onClick={() => setView(v)}
                  className={`rounded-md px-3 py-1 font-medium capitalize transition ${
                    view === v ? 'bg-white/10 text-slate-100' : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  {v}
                </button>
              ))}
            </nav>
            <span className="flex items-center gap-1.5 text-xs text-slate-400">
              <span className={`h-2 w-2 rounded-full ${live ? 'animate-pulse bg-emerald-400' : 'bg-slate-600'}`} />
              {live ? 'Live' : 'Preview'}
            </span>
            {view === 'compliance' && (
              <button
                onClick={doRescan}
                disabled={busy || !live}
                className="rounded-lg border border-white/10 bg-white/5 px-3 py-1.5 text-xs font-medium text-slate-200 hover:bg-white/10 disabled:opacity-50"
              >
                {busy ? 'Scanning…' : 'Rescan'}
              </button>
            )}
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-6 py-6">
        {view === 'code' ? (
          <CodeView />
        ) : view === 'agent' ? (
          <RunAgent />
        ) : (
          <>
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
              <StatCard label="Issues" value={sum.issues} />
              <StatCard label="Open violations" value={sum.violations} tone={sum.violations ? 'warning' : 'ok'} />
              <StatCard label="Errors" value={sum.error} tone={sum.error ? 'error' : 'ok'} />
              <StatCard label="Warnings" value={sum.warning} tone={sum.warning ? 'warning' : 'ok'} />
            </div>

            <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-2">
              <Dashboard issues={snap.issues} />
              <Violations violations={snap.violations} />
            </div>
          </>
        )}
      </main>
    </div>
  )
}

function Splash() {
  return (
    <div className="grid h-full place-items-center text-slate-500">
      <div className="text-sm">Connecting to Hephaestus core…</div>
    </div>
  )
}
