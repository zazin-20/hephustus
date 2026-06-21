const STAT_TONE = {
  default: 'text-slate-100',
  error: 'text-rose-400',
  warning: 'text-amber-400',
  ok: 'text-emerald-400',
}

export function StatCard({ label, value, tone = 'default' }) {
  return (
    <div className="rounded-xl border border-white/5 bg-white/[0.03] px-5 py-4">
      <div className="text-xs uppercase tracking-wider text-slate-500">{label}</div>
      <div className={`mt-1 text-2xl font-semibold tabular-nums ${STAT_TONE[tone]}`}>{value}</div>
    </div>
  )
}

const STAGE_STYLE = {
  ok: 'bg-emerald-500/15 text-emerald-300 ring-emerald-500/30',
  pending: 'bg-amber-500/15 text-amber-300 ring-amber-500/30',
  none: 'bg-slate-700/20 text-slate-600 ring-white/5',
}

export function StagePill({ label, state }) {
  return (
    <span
      title={`${label}: ${state}`}
      className={`inline-flex items-center rounded-md px-2 py-0.5 text-[11px] font-medium ring-1 ring-inset ${STAGE_STYLE[state] || STAGE_STYLE.none}`}
    >
      {label}
    </span>
  )
}

const STATE_STYLE = {
  OPEN: 'bg-slate-600/30 text-slate-300',
  IN_PROGRESS: 'bg-sky-500/15 text-sky-300',
  HANDOFF_PENDING: 'bg-amber-500/15 text-amber-300',
  QA_PENDING: 'bg-violet-500/15 text-violet-300',
  DONE: 'bg-emerald-500/15 text-emerald-300',
}

export function StateBadge({ state }) {
  return (
    <span className={`rounded-full px-2.5 py-0.5 text-[11px] font-semibold ${STATE_STYLE[state] || 'bg-slate-600/30 text-slate-300'}`}>
      {state.replace(/_/g, ' ')}
    </span>
  )
}
