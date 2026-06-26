// REUSABLE — the node-level status surface. The row × stage-pill grid is exactly
// the "PRD ✓, ADR ✓, issues ✓, handoff ✓, verified" feedback for user-authored
// workflows (issue→workflow-node, the hardcoded stages→the workflow's gates).
// Renders empty until a workflow/node model feeds `issues`. See
// docs/design/governance-engine.md.
import { StagePill, StateBadge } from './ui.jsx'

const STAGES = [
  ['spec', 'Spec'],
  ['handoff', 'Handoff'],
  ['review', 'Review'],
  ['qa', 'QA'],
  ['log', 'Log'],
]

export default function Dashboard({ issues }) {
  return (
    <section className="rounded-2xl border border-white/5 bg-white/[0.02]">
      <header className="flex items-center justify-between border-b border-white/5 px-5 py-3.5">
        <h2 className="text-sm font-semibold text-slate-200">Pipeline Dashboard</h2>
        <span className="text-xs text-slate-500">{issues.length} issues</span>
      </header>

      {issues.length === 0 ? (
        <p className="px-5 py-10 text-center text-sm text-slate-500">
          No issues found in this OKF tree.
        </p>
      ) : (
        <div className="divide-y divide-white/5">
          {issues.map((it) => (
            <div key={it.id} className="grid grid-cols-[1fr_auto] items-center gap-4 px-5 py-3.5 hover:bg-white/[0.02]">
              <div className="min-w-0">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="font-mono text-xs text-slate-500">{it.id}</span>
                  <StateBadge state={it.state} />
                  {it.violations.length > 0 && (
                    <span className="font-mono text-[11px] text-rose-400">⚠ {it.violations.join(', ')}</span>
                  )}
                </div>
                <div className="mt-0.5 truncate text-sm text-slate-200">{it.title}</div>
                <div className="font-mono text-[11px] text-slate-600">{it.sprint}</div>
              </div>
              <div className="flex items-center gap-1.5">
                {STAGES.map(([key, label]) => (
                  <StagePill key={key} label={label} state={it.stages[key]} />
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </section>
  )
}
