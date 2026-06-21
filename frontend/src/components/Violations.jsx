const SEV = {
  error: { dot: 'bg-rose-500', text: 'text-rose-300', ring: 'ring-rose-500/30' },
  warning: { dot: 'bg-amber-500', text: 'text-amber-300', ring: 'ring-amber-500/30' },
  info: { dot: 'bg-sky-500', text: 'text-sky-300', ring: 'ring-sky-500/30' },
}
const ORDER = { error: 0, warning: 1, info: 2 }

export default function Violations({ violations }) {
  const sorted = [...violations].sort(
    (a, b) => (ORDER[a.severity] - ORDER[b.severity]) || a.rule_id.localeCompare(b.rule_id),
  )

  return (
    <section className="rounded-2xl border border-white/5 bg-white/[0.02]">
      <header className="flex items-center justify-between border-b border-white/5 px-5 py-3.5">
        <h2 className="text-sm font-semibold text-slate-200">Compliance Monitor</h2>
        <span className="text-xs text-slate-500">{violations.length} open</span>
      </header>

      {sorted.length === 0 ? (
        <div className="px-5 py-12 text-center">
          <div className="text-2xl text-emerald-400">✓</div>
          <p className="mt-1 text-sm text-emerald-300">All checks passing</p>
          <p className="text-xs text-slate-500">No compliance violations in the OKF tree.</p>
        </div>
      ) : (
        <ul className="divide-y divide-white/5">
          {sorted.map((v, i) => {
            const s = SEV[v.severity] || SEV.info
            return (
              <li key={i} className="px-5 py-3.5">
                <div className="flex items-center gap-2">
                  <span className={`h-1.5 w-1.5 rounded-full ${s.dot}`} />
                  <span className={`rounded px-1.5 py-0.5 font-mono text-[11px] ring-1 ring-inset ${s.ring} ${s.text}`}>
                    {v.rule_id}
                  </span>
                  <span className="text-[11px] uppercase tracking-wide text-slate-500">{v.severity}</span>
                  {v.issue_id && <span className="font-mono text-[11px] text-slate-600">{v.issue_id}</span>}
                </div>
                <p className="mt-1.5 text-sm text-slate-200">{v.message}</p>
                {v.fix_hint && <p className="mt-1 text-xs text-slate-500">{v.fix_hint}</p>}
                <p className="mt-1 truncate font-mono text-[11px] text-slate-600">{v.artifact}</p>
              </li>
            )
          })}
        </ul>
      )}
    </section>
  )
}
