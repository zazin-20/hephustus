import { useEffect, useRef, useState } from 'react'
import CodeView from './components/CodeView.jsx'
import RunAgent from './components/RunAgent.jsx'
import Coordinator from './components/Coordinator.jsx'
import WorkflowCanvas from './components/WorkflowCanvas.jsx'
import { ToastProvider, useToast } from './components/Toast.jsx'
import { onPush, whenReady, getState, hasBridge } from './api.js'
import { MOCK } from './mock.js'

function AppInner() {
  const [snap, setSnap] = useState(null)
  const [live, setLive] = useState(false)
  const [view, setView] = useState('coordinator')
  const { addToast } = useToast()
  const seenViolations = useRef(new Set())
  const seenWorkflowNotifications = useRef(new Set())

  useEffect(() => {
      onPush((incoming) => {
        setSnap(incoming)
        pushViolationToasts(incoming?.violations ?? [])
        pushWorkflowToasts(incoming?.workflow_canvas?.notifications ?? [])
      })
      whenReady(async () => {
        setLive(true)
        const s = await getState()
        if (s) {
          setSnap(s)
          pushViolationToasts(s.violations ?? [])
          pushWorkflowToasts(s.workflow_canvas?.notifications ?? [])
        }
      })
    const t = setTimeout(() => { if (!hasBridge()) setSnap(MOCK) }, 500)
    return () => clearTimeout(t)
  }, [addToast])

  function pushViolationToasts(violations) {
    for (const v of violations) {
      const key = v.id || `${v.rule_id}-${v.artifact}`
      if (seenViolations.current.has(key)) continue
      seenViolations.current.add(key)
      addToast({
        id: key,
        severity: v.severity || 'warning',
        rule_id: v.rule_id,
        issue_id: v.issue_id || null,
        node_id: v.node_id || null,
        message: v.message,
      })
    }
  }

  function pushWorkflowToasts(notifications) {
    for (const item of notifications) {
      if (!item?.id || seenWorkflowNotifications.current.has(item.id)) continue
      seenWorkflowNotifications.current.add(item.id)
      addToast({
        id: item.id,
        severity: item.severity || 'info',
        node_id: item.placement_id || null,
        message: item.message,
        allowCorrection: false,
      })
    }
  }

  if (!snap) return <Splash />

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
              {['coordinator', 'canvas', 'code', 'agent'].map((v) => (
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
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-6 py-6">
        {view === 'code' ? (
          <CodeView />
        ) : view === 'agent' ? (
          <RunAgent />
        ) : view === 'canvas' ? (
          <WorkflowCanvas workflowCanvas={snap.workflow_canvas} live={live} />
        ) : (
          <Coordinator />
        )}
      </main>
    </div>
  )
}

export default function App() {
  return (
    <ToastProvider>
      <AppInner />
    </ToastProvider>
  )
}

function Splash() {
  return (
    <div className="grid h-full place-items-center text-slate-500">
      <div className="text-sm">Connecting to Hephaestus core…</div>
    </div>
  )
}
