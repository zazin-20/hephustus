import { useEffect, useRef, useState } from 'react'
import {
  createProfile,
  deleteProfile,
  evaluateSpawn,
  getCatalog,
  getTrace,
  getTranscript,
  hasBridge,
  listProfiles,
  listRules,
  listThreads,
  onAgent,
  parseHandoffMarker,
  pickDirectory,
  sendMessage,
  setTurnIncluded,
} from '../api.js'
import { CATALOG_MOCK, COORDINATOR_MOCK, RULES_MOCK } from '../mock.js'

const INPUT =
  'w-full rounded-lg border border-white/10 bg-black/20 px-2.5 py-1.5 text-sm text-slate-200 outline-none focus:border-white/25'

const ROLE_OPTIONS = ['architect', 'worker', 'qa', 'orchestrator']

const ROLE_STYLE = {
  architect: 'bg-sky-500/15 text-sky-300 ring-sky-500/30',
  worker: 'bg-orange-500/15 text-orange-300 ring-orange-500/30',
  qa: 'bg-emerald-500/15 text-emerald-300 ring-emerald-500/30',
  orchestrator: 'bg-fuchsia-500/15 text-fuchsia-300 ring-fuchsia-500/30',
}

const STATUS_STYLE = {
  idle: 'bg-slate-500/15 text-slate-300 ring-white/10',
}

const TURN_STYLE = {
  user: 'border-orange-500/20 bg-orange-500/10 text-orange-100',
  assistant: 'border-white/10 bg-black/20 text-slate-200',
  tool: 'border-sky-500/20 bg-sky-500/10 text-sky-100',
}

const EMPTY_FORM = {
  name: '',
  role: 'architect',
  rules: [],
  model: '',
  effort: '',
  working_dir: '',
}

function Field({ label, children }) {
  return (
    <label className="block">
      <span className="mb-1 block text-xs uppercase tracking-wider text-slate-500">{label}</span>
      {children}
    </label>
  )
}

function RolePill({ role }) {
  return (
    <span
      className={`inline-flex rounded-full px-2 py-0.5 text-[11px] font-semibold capitalize ring-1 ring-inset ${
        ROLE_STYLE[role] || 'bg-slate-500/15 text-slate-300 ring-white/10'
      }`}
    >
      {role}
    </span>
  )
}

function StatusBadge({ status }) {
  return (
    <span
      className={`inline-flex rounded-full px-2 py-0.5 text-[11px] font-semibold capitalize ring-1 ring-inset ${
        STATUS_STYLE[status] || STATUS_STYLE.idle
      }`}
    >
      {status}
    </span>
  )
}

function nextMockId(profiles, role) {
  const prefix = role.slice(0, 4)
  const counters = profiles
    .map((profile) => profile.agent_id)
    .filter((agentId) => agentId.startsWith(`${prefix}-`))
    .map((agentId) => Number.parseInt(agentId.split('-')[1], 10))
    .filter(Number.isFinite)
  const next = counters.length ? Math.max(...counters) + 1 : 1
  return `${prefix}-${String(next).padStart(3, '0')}`
}

function renderTurnRole(turn) {
  if (turn.role === 'user') return 'user'
  if (turn.role === 'tool') return 'tool'
  return 'assistant'
}

export default function Coordinator() {
  const [profiles, setProfiles] = useState([])
  const [selectedId, setSelectedId] = useState(null)
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState(EMPTY_FORM)
  const [catalog, setCatalog] = useState(CATALOG_MOCK)
  const [ruleSet, setRuleSet] = useState(RULES_MOCK)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [threads, setThreads] = useState([])
  const [selectedThreadId, setSelectedThreadId] = useState(null)
  const [transcript, setTranscript] = useState([])
  const [draft, setDraft] = useState('')
  const [issueId, setIssueId] = useState('')
  const [sending, setSending] = useState(false)
  const [traceEvents, setTraceEvents] = useState([])
  const [showTrace, setShowTrace] = useState(false)
  const [spawnCard, setSpawnCard] = useState(null)
  const activeRunId = useRef(null)
  const activeAgentId = useRef(null)
  const activeThreadId = useRef(null)

  useEffect(() => {
    loadProfiles()
    if (hasBridge()) {
      void getCatalog().then((c) => c && setCatalog(c))
      void listRules().then((r) => r && setRuleSet(r))
    }
  }, [])

  useEffect(() => {
    activeAgentId.current = selectedId
  }, [selectedId])

  useEffect(() => {
    activeThreadId.current = selectedThreadId
  }, [selectedThreadId])

  useEffect(() => {
    onAgent((ev) => {
      if (ev.run_id !== activeRunId.current) return
      if (ev.kind === 'done') {
        setSending(false)
        if (activeAgentId.current) void loadThreadsFor(activeAgentId.current, activeThreadId.current)
        if (activeRunId.current && hasBridge()) {
          void getTrace(activeRunId.current, null).then(setTraceEvents)
        }
        return
      }
      if (ev.kind === 'text' && hasBridge() && ev.text) {
        void parseHandoffMarker(ev.text).then((marker) => {
          if (!marker) return
          void evaluateSpawn(marker.role, marker.task, marker.issue_id).then((card) => {
            if (card) setSpawnCard({ ...card, marker })
          })
        })
      }
      if (ev.kind === 'tool_call') {
        setTraceEvents((current) => [
          ...current,
          { id: `live-${current.length}`, action: ev.text, target_path: null, ts: new Date().toISOString() },
        ])
      }
      setTranscript((current) => [
        ...current,
        {
          id: `${ev.run_id}-${current.length}`,
          role: ev.kind === 'tool' || ev.kind === 'tool_call' ? 'tool' : 'assistant',
          kind: ev.kind,
          text: ev.text,
        },
      ])
    })
    return () => {
      window.__hephaestus_agent__ = null
    }
  }, [])

  useEffect(() => {
    if (!selectedId) {
      setThreads([])
      setTranscript([])
      setTraceEvents([])
      setSelectedThreadId(null)
      setIssueId('')
      return
    }
    void loadThreadsFor(selectedId, null)
  }, [selectedId])

  async function loadProfiles() {
    if (!hasBridge()) {
      setProfiles(COORDINATOR_MOCK)
      setSelectedId((current) => current ?? COORDINATOR_MOCK[0]?.agent_id ?? null)
      return
    }

    const rows = await listProfiles()
    const nextProfiles = rows || []
    setProfiles(nextProfiles)
    setSelectedId((current) => {
      if (current && nextProfiles.some((profile) => profile.agent_id === current)) return current
      return nextProfiles[0]?.agent_id ?? null
    })
  }

  async function loadThreadsFor(agentId, preferredThreadId) {
    if (!hasBridge()) {
      setThreads([])
      setTranscript([])
      setSelectedThreadId(null)
      return
    }

    const rows = (await listThreads(agentId)) || []
    setThreads(rows)
    const nextThreadId =
      preferredThreadId ||
      (activeThreadId.current && rows.some((thread) => thread.id === activeThreadId.current)
        ? activeThreadId.current
        : rows[0]?.id || null)

    setSelectedThreadId(nextThreadId)
    const activeThread = rows.find((thread) => thread.id === nextThreadId) || null
    setIssueId(activeThread?.issue_id || '')

    if (!nextThreadId) {
      setTranscript([])
      return
    }

    const turns = (await getTranscript(nextThreadId)) || []
    setTranscript(turns)
  }

  function updateField(key, value) {
    setForm((current) => ({ ...current, [key]: value }))
  }

  function toggleRule(ruleId) {
    setForm((current) => {
      const has = current.rules.includes(ruleId)
      return {
        ...current,
        rules: has ? current.rules.filter((r) => r !== ruleId) : [...current.rules, ruleId],
      }
    })
  }

  async function browseDirectory() {
    if (!hasBridge()) return
    const chosen = await pickDirectory()
    if (chosen) updateField('working_dir', chosen)
  }

  function selectModel(model) {
    setForm((current) => {
      const picked = catalog.providers.flatMap((g) => g.models).find((m) => m.id === model)
      const efforts = picked?.efforts || []
      const effort = efforts.includes(current.effort) ? current.effort : ''
      return { ...current, model, effort }
    })
  }

  async function submit(event) {
    event.preventDefault()
    if (!form.name.trim() || busy) return

    setBusy(true)
    setError('')
    const payload = {
      name: form.name.trim(),
      role: form.role,
      rules: form.rules,
      model: form.model || null,
      effort: form.effort || null,
      working_dir: form.working_dir.trim() || null,
    }

    try {
      if (hasBridge()) {
        const created = await createProfile(
          payload.name,
          payload.role,
          payload.rules,
          payload.model,
          payload.effort,
          payload.working_dir,
        )
        await loadProfiles()
        setSelectedId(created?.agent_id || null)
      } else {
        const created = {
          ...payload,
          agent_id: nextMockId(profiles, payload.role),
          created_at: new Date().toISOString(),
          status: 'idle',
        }
        setProfiles((current) => [...current, created])
        setSelectedId(created.agent_id)
      }
      setForm(EMPTY_FORM)
      setShowForm(false)
    } catch (err) {
      setError(err?.message || 'Failed to create profile.')
    } finally {
      setBusy(false)
    }
  }

  async function removeProfile(agentId) {
    setBusy(true)
    setError('')
    try {
      if (hasBridge()) {
        await deleteProfile(agentId)
        await loadProfiles()
      } else {
        const nextProfiles = profiles.filter((profile) => profile.agent_id !== agentId)
        setProfiles(nextProfiles)
        setSelectedId((current) => {
          if (current && current !== agentId) return current
          return nextProfiles[0]?.agent_id ?? null
        })
      }
    } catch (err) {
      setError(err?.message || 'Failed to delete profile.')
    } finally {
      setBusy(false)
    }
  }

  async function toggleTurn(turn) {
    const next = turn.included === false ? true : false
    if (hasBridge()) {
      await setTurnIncluded(turn.id, next)
      if (selectedThreadId) {
        const turns = (await getTranscript(selectedThreadId)) || []
        setTranscript(turns)
      }
    } else {
      setTranscript((current) =>
        current.map((t) => (t.id === turn.id ? { ...t, included: next } : t)),
      )
    }
  }

  async function submitMessage(event) {
    event.preventDefault()
    if (!selectedId || !draft.trim() || sending) return

    const message = draft.trim()
    const threadIssue = threads.find((thread) => thread.id === selectedThreadId)?.issue_id || ''
    const nextIssue = issueId.trim() || threadIssue || null

    setSending(true)
    setError('')
    setDraft('')
    setTraceEvents([])
    setSpawnCard(null)
    setTranscript((current) => [
      ...current,
      {
        id: `draft-${Date.now()}`,
        role: 'user',
        kind: 'text',
        text: message,
      },
    ])

    if (!hasBridge()) {
      setTranscript((current) => [
        ...current,
        {
          id: `preview-${Date.now()}`,
          role: 'assistant',
          kind: 'text',
          text: `Preview mode: ${message}`,
        },
      ])
      setSending(false)
      return
    }

    try {
      const res = await sendMessage(selectedId, message, nextIssue, null)
      activeRunId.current = res?.run_id || null
      if (res?.thread_id) {
        setSelectedThreadId(res.thread_id)
        activeThreadId.current = res.thread_id
      }
      if (nextIssue) setIssueId(nextIssue)
    } catch (err) {
      setSending(false)
      setError(err?.message || 'Failed to send message.')
    }
  }

  const selectedModel = catalog.providers.flatMap((group) => group.models).find((m) => m.id === form.model)
  const effortOptions = selectedModel ? selectedModel.efforts || [] : []

  const selected = profiles.find((profile) => profile.agent_id === selectedId) || null

  return (
    <div className="grid grid-cols-1 gap-4 lg:grid-cols-[280px_1fr]">
      <aside className="flex min-h-[70vh] flex-col overflow-hidden rounded-2xl border border-white/5 bg-white/[0.02]">
        <div className="border-b border-white/5 px-4 py-3">
          <div className="text-sm font-semibold text-slate-200">Roster</div>
          <div className="text-xs text-slate-500">{profiles.length} profiles</div>
        </div>

        <div className="flex-1 space-y-3 overflow-y-auto p-3">
          {profiles.length === 0 ? (
            <div className="rounded-xl border border-dashed border-white/10 bg-black/20 px-4 py-8 text-center text-sm text-slate-500">
              No profiles yet.
            </div>
          ) : (
            profiles.map((profile) => (
              <div
                key={profile.agent_id}
                className={`block w-full rounded-xl border p-3 text-left transition ${
                  selectedId === profile.agent_id
                    ? 'border-orange-500/40 bg-orange-500/10 shadow-lg shadow-orange-950/20'
                    : 'border-white/5 bg-black/20 hover:border-white/10 hover:bg-white/[0.03]'
                }`}
              >
                <div className="flex items-start justify-between gap-3">
                  <button
                    type="button"
                    onClick={() => setSelectedId(profile.agent_id)}
                    className="min-w-0 flex-1 text-left"
                  >
                    <div className="truncate text-sm font-semibold text-slate-100">{profile.name}</div>
                    <div className="mt-1 font-mono text-[11px] text-slate-500">{profile.agent_id}</div>
                  </button>
                  <button
                    type="button"
                    onClick={() => void removeProfile(profile.agent_id)}
                    className="rounded-md border border-white/10 px-2 py-1 text-[11px] font-medium text-slate-400 hover:border-rose-500/30 hover:text-rose-300"
                    aria-label={`Delete ${profile.name}`}
                  >
                    Delete
                  </button>
                </div>

                <div className="mt-3 flex items-center gap-2">
                  <RolePill role={profile.role} />
                  <StatusBadge status={profile.status || 'idle'} />
                </div>
              </div>
            ))
          )}
        </div>

        <div className="border-t border-white/5 p-3">
          {showForm ? (
            <form onSubmit={submit} className="space-y-3 rounded-xl border border-white/5 bg-black/20 p-3">
              <Field label="Name">
                <input
                  required
                  value={form.name}
                  onChange={(event) => updateField('name', event.target.value)}
                  className={INPUT}
                  placeholder="Agent name"
                />
              </Field>
              <Field label="Role">
                <select
                  value={form.role}
                  onChange={(event) => updateField('role', event.target.value)}
                  className={INPUT}
                >
                  {ROLE_OPTIONS.map((role) => (
                    <option key={role} value={role} className="bg-[#0b0e14]">
                      {role}
                    </option>
                  ))}
                </select>
              </Field>
              <Field label="Rules">
                <div className="flex flex-wrap gap-1.5">
                  {ruleSet.map((rule) => {
                    const on = form.rules.includes(rule.id)
                    return (
                      <button
                        key={rule.id}
                        type="button"
                        onClick={() => toggleRule(rule.id)}
                        title={rule.name}
                        className={`rounded-full border px-2 py-0.5 font-mono text-[11px] transition ${
                          on
                            ? 'border-orange-400/40 bg-orange-500/15 text-orange-200'
                            : 'border-white/10 bg-black/20 text-slate-400 hover:border-white/20 hover:text-slate-200'
                        }`}
                      >
                        {rule.id}
                      </button>
                    )
                  })}
                </div>
              </Field>
              <Field label="Model">
                <select
                  value={form.model}
                  onChange={(event) => selectModel(event.target.value)}
                  className={INPUT}
                >
                  <option value="" className="bg-[#0b0e14]">
                    (provider default)
                  </option>
                  {catalog.providers.map((group) => (
                    <optgroup key={group.provider} label={group.provider} className="bg-[#0b0e14]">
                      {group.models.map((model) => (
                        <option key={model.id} value={model.id} className="bg-[#0b0e14]">
                          {model.label}
                        </option>
                      ))}
                    </optgroup>
                  ))}
                </select>
              </Field>
              <Field label="Effort">
                <select
                  value={form.effort}
                  onChange={(event) => updateField('effort', event.target.value)}
                  disabled={!form.model}
                  className={`${INPUT} disabled:opacity-40`}
                >
                  <option value="" className="bg-[#0b0e14]">
                    {form.model ? '(default)' : 'select a model first'}
                  </option>
                  {effortOptions.map((level) => (
                    <option key={level} value={level} className="bg-[#0b0e14]">
                      {level}
                    </option>
                  ))}
                </select>
              </Field>
              <Field label="Working Directory">
                <div className="flex gap-2">
                  <input
                    value={form.working_dir}
                    onChange={(event) => updateField('working_dir', event.target.value)}
                    className={INPUT}
                    placeholder="path/to/repo"
                  />
                  {hasBridge() ? (
                    <button
                      type="button"
                      onClick={() => void browseDirectory()}
                      className="shrink-0 rounded-lg border border-white/10 px-3 text-sm text-slate-300 hover:bg-white/5"
                    >
                      Browse
                    </button>
                  ) : null}
                </div>
              </Field>
              {error ? <div className="text-xs text-rose-300">{error}</div> : null}
              <div className="flex gap-2">
                <button
                  type="submit"
                  disabled={busy || !form.name.trim()}
                  className="flex-1 rounded-lg bg-gradient-to-br from-orange-500 to-amber-600 px-3 py-2 text-sm font-semibold text-black hover:opacity-90 disabled:opacity-40"
                >
                  {busy ? 'Saving...' : 'Create'}
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setShowForm(false)
                    setForm(EMPTY_FORM)
                    setError('')
                  }}
                  className="rounded-lg border border-white/10 px-3 py-2 text-sm font-medium text-slate-300 hover:bg-white/5"
                >
                  Cancel
                </button>
              </div>
            </form>
          ) : (
            <button
              type="button"
              onClick={() => setShowForm(true)}
              className="w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm font-medium text-slate-200 hover:bg-white/10"
            >
              Add Profile
            </button>
          )}
        </div>
      </aside>

      <section className="rounded-2xl border border-white/5 bg-white/[0.02] p-6">
        {selected ? (
          <div className="flex min-h-[70vh] flex-col gap-4">
            <div className="border-b border-white/5 pb-4">
              <div className="flex items-center gap-3">
                <div className="text-lg font-semibold text-slate-100">{selected.name}</div>
                <RolePill role={selected.role} />
                <StatusBadge status={selected.status || 'idle'} />
              </div>
              <div className="mt-2 font-mono text-xs text-slate-500">{selected.agent_id}</div>
              <div className="mt-4">
                <div className="mb-2 text-xs uppercase tracking-wider text-slate-500">Threads</div>
                <div className="flex flex-wrap gap-2">
                  {threads.length ? (
                    threads.map((thread) => (
                      <button
                        key={thread.id}
                        type="button"
                        onClick={() => void loadThreadsFor(selected.agent_id, thread.id)}
                        className={`rounded-full border px-3 py-1 text-xs transition ${
                          selectedThreadId === thread.id
                            ? 'border-orange-400/40 bg-orange-500/10 text-orange-100'
                            : 'border-white/10 bg-black/20 text-slate-400 hover:border-white/20 hover:text-slate-200'
                        }`}
                      >
                        {thread.issue_id || thread.name}
                      </button>
                    ))
                  ) : (
                    <span className="text-sm text-slate-500">No persisted threads yet.</span>
                  )}
                </div>
              </div>
            </div>

            <div className="flex-1 overflow-hidden rounded-2xl border border-white/5 bg-black/20">
              <div className="border-b border-white/5 px-4 py-3 text-sm font-semibold text-slate-200">
                Conversation
              </div>
              <div className="max-h-[48vh] space-y-3 overflow-auto p-4">
                {transcript.length ? (
                  transcript.map((turn) => {
                    const excluded = turn.included === false
                    const tone = TURN_STYLE[renderTurnRole(turn)] || TURN_STYLE.assistant
                    return (
                      <div
                        key={turn.id}
                        className={`rounded-xl border p-3 transition-opacity ${tone} ${excluded ? 'opacity-40' : ''}`}
                      >
                        <div className="mb-2 flex items-center justify-between gap-3 text-[11px] uppercase tracking-wider text-slate-400">
                          <span>{renderTurnRole(turn)}</span>
                          <div className="flex items-center gap-2">
                            <span>{turn.kind || 'text'}</span>
                            <button
                              type="button"
                              onClick={() => void toggleTurn(turn)}
                              className="rounded border border-white/10 px-1.5 py-0.5 text-[10px] font-medium text-slate-500 hover:border-white/20 hover:text-slate-300"
                            >
                              {excluded ? 'Include' : 'Exclude'}
                            </button>
                          </div>
                        </div>
                        <div className="whitespace-pre-wrap text-sm leading-relaxed">{turn.text}</div>
                      </div>
                    )
                  })
                ) : (
                  <div className="grid min-h-[220px] place-items-center text-center text-sm text-slate-500">
                    Open a profile thread or send the first message to start one.
                  </div>
                )}
              </div>
            </div>

            <div className="rounded-2xl border border-white/5 bg-black/20 overflow-hidden">
              <button
                type="button"
                onClick={() => setShowTrace((v) => !v)}
                className="flex w-full items-center justify-between px-4 py-3 text-left text-sm font-semibold text-slate-300 hover:bg-white/5"
              >
                <span>Trace {traceEvents.length ? `(${traceEvents.length})` : ''}</span>
                <span className="text-slate-500 text-xs">{showTrace ? '▲ hide' : '▼ show'}</span>
              </button>
              {showTrace && (
                <div className="border-t border-white/5 max-h-48 overflow-auto p-3 space-y-1.5">
                  {traceEvents.length === 0 ? (
                    <div className="text-xs text-slate-500 text-center py-4">No trace events for this run.</div>
                  ) : (
                    traceEvents.map((ev, i) => {
                      const actionStyle =
                        ev.action === 'write_file' || ev.action === 'Write'
                          ? 'bg-orange-500/15 text-orange-300 ring-orange-500/30'
                          : ev.action === 'read_file' || ev.action === 'Read'
                          ? 'bg-sky-500/15 text-sky-300 ring-sky-500/30'
                          : 'bg-slate-500/15 text-slate-300 ring-white/10'
                      return (
                        <div key={ev.id || i} className="flex items-center gap-2 text-xs">
                          <span className={`shrink-0 inline-flex rounded-full px-2 py-0.5 text-[10px] font-semibold ring-1 ring-inset ${actionStyle}`}>
                            {ev.action}
                          </span>
                          {ev.target_path && (
                            <span className="truncate font-mono text-slate-400">{ev.target_path}</span>
                          )}
                          <span className="ml-auto shrink-0 text-slate-600">{ev.ts ? ev.ts.slice(11, 19) : ''}</span>
                        </div>
                      )
                    })
                  )}
                </div>
              )}
            </div>

            {spawnCard && (
              <div className={`rounded-2xl border p-4 ${spawnCard.gating === 'green' ? 'border-emerald-500/30 bg-emerald-500/5' : 'border-amber-500/30 bg-amber-500/5'}`}>
                <div className="mb-2 flex items-center gap-2">
                  <span className={`inline-flex rounded-full px-2 py-0.5 text-[11px] font-semibold ring-1 ring-inset ${spawnCard.gating === 'green' ? 'bg-emerald-500/15 text-emerald-300 ring-emerald-500/30' : 'bg-amber-500/15 text-amber-300 ring-amber-500/30'}`}>
                    {spawnCard.gating === 'green' ? '✓ Ready to Spawn' : '⚠ Spawn (with failures)'}
                  </span>
                  <span className="text-xs text-slate-400">→ <strong>{spawnCard.prefill_role}</strong>: {spawnCard.prefill_task}</span>
                </div>
                {spawnCard.failures?.length > 0 && (
                  <ul className="mb-3 space-y-1">
                    {spawnCard.failures.map((f, i) => (
                      <li key={i} className="text-xs text-amber-300">
                        <span className="font-mono">{f.rule_id}</span> — {f.message}
                        {f.fix_hint && <span className="ml-1 text-amber-400/60">({f.fix_hint})</span>}
                      </li>
                    ))}
                  </ul>
                )}
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={() => {
                      setDraft(spawnCard.prefill_task)
                      setSpawnCard(null)
                    }}
                    className="rounded-lg bg-gradient-to-br from-emerald-500 to-teal-600 px-3 py-1.5 text-xs font-semibold text-black hover:opacity-90"
                  >
                    Confirm Spawn
                  </button>
                  <button
                    type="button"
                    onClick={() => setSpawnCard(null)}
                    className="rounded-lg border border-white/10 px-3 py-1.5 text-xs text-slate-400 hover:text-slate-200"
                  >
                    Dismiss
                  </button>
                </div>
              </div>
            )}

            <form onSubmit={submitMessage} className="space-y-3 rounded-2xl border border-white/5 bg-black/20 p-4">
              <Field label="Issue (optional)">
                <input
                  value={issueId}
                  onChange={(event) => setIssueId(event.target.value)}
                  className={INPUT}
                  placeholder="issue-003"
                />
              </Field>
              <Field label="Message">
                <textarea
                  value={draft}
                  onChange={(event) => setDraft(event.target.value)}
                  rows={5}
                  className={`${INPUT} resize-y font-mono`}
                  placeholder="Send a message to this agent..."
                />
              </Field>
              {error ? <div className="text-xs text-rose-300">{error}</div> : null}
              <button
                type="submit"
                disabled={sending || !draft.trim()}
                className="rounded-lg bg-gradient-to-br from-orange-500 to-amber-600 px-4 py-2 text-sm font-semibold text-black hover:opacity-90 disabled:opacity-40"
              >
                {sending ? 'Sending...' : 'Send message'}
              </button>
            </form>
          </div>
        ) : (
          <div className="grid min-h-[70vh] place-items-center rounded-2xl border border-dashed border-white/10 bg-black/20 px-6 text-center text-sm text-slate-500">
            Select a profile to start a conversation
          </div>
        )}
      </section>
    </div>
  )
}
