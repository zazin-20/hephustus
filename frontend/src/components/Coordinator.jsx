import { useEffect, useRef, useState } from 'react'
import {
  createNode,
  deleteNode,
  evaluateSpawn,
  getCatalog,
  getTrace,
  getTranscript,
  hasBridge,
  listNodes,
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

const PROVIDER_STYLE = {
  claude: 'bg-sky-500/15 text-sky-300 ring-sky-500/30',
  codex: 'bg-orange-500/15 text-orange-300 ring-orange-500/30',
}

const STATUS_STYLE = {
  idle: 'bg-slate-500/15 text-slate-300 ring-white/10',
}

const EMPTY_FORM = {
  name: '',
  provider: 'claude',
  tags_input: 'architect',
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

function ProviderPill({ provider }) {
  return (
    <span
      className={`inline-flex rounded-full px-2 py-0.5 text-[11px] font-semibold capitalize ring-1 ring-inset ${
        PROVIDER_STYLE[provider] || 'bg-slate-500/15 text-slate-300 ring-white/10'
      }`}
    >
      {provider}
    </span>
  )
}

function TagPills({ tags }) {
  return (
    <>
      {(tags || []).map((tag) => (
        <span
          key={tag}
          className="inline-flex rounded-full bg-white/5 px-2 py-0.5 text-[11px] font-medium text-slate-300 ring-1 ring-inset ring-white/10"
        >
          {tag}
        </span>
      ))}
    </>
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

function nextMockId(profiles) {
  const counters = profiles
    .map((profile) => profile.node_id)
    .filter((nodeId) => nodeId.startsWith('node-'))
    .map((nodeId) => Number.parseInt(nodeId.split('-')[1], 10))
    .filter(Number.isFinite)
  const next = counters.length ? Math.max(...counters) + 1 : 1
  return `node-${String(next).padStart(3, '0')}`
}

async function copyToClipboard(text) {
  try {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(text)
      return true
    }
  } catch {
    /* fall through to the execCommand path (webviews without async clipboard) */
  }
  try {
    const ta = document.createElement('textarea')
    ta.value = text
    ta.style.position = 'fixed'
    ta.style.opacity = '0'
    document.body.appendChild(ta)
    ta.select()
    const ok = document.execCommand('copy')
    document.body.removeChild(ta)
    return ok
  } catch {
    return false
  }
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
  const [openTrace, setOpenTrace] = useState([])
  const [copied, setCopied] = useState(false)
  const [spawnCard, setSpawnCard] = useState(null)
  const activeRunId = useRef(null)
  const activeAgentId = useRef(null)
  const activeThreadId = useRef(null)

  useEffect(() => {
    loadNodes()
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
      if (ev.category === 'transport') {
        setSending(false)
        // loadThreadsFor reloads the persisted trace for the thread (full command
        // + output), replacing the lighter live entries.
        if (activeAgentId.current) void loadThreadsFor(activeAgentId.current, activeThreadId.current)
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
      if (ev.category === 'tool') {
        setTraceEvents((current) => [
          ...current,
          {
            id: `live-${current.length}`,
            action: ev.raw?.action || ev.text,
            target_path: ev.raw?.input?.command || ev.raw?.input?.path || ev.raw?.input?.file_path || null,
            raw: ev.raw || null,
            ts: new Date().toISOString(),
          },
        ])
      }
      setTranscript((current) => [
        ...current,
        {
          id: `${ev.run_id}-${current.length}`,
          role: ev.transcript_role || 'assistant',
          kind: ev.kind,
          text: ev.text,
          category: ev.category,
          persist: ev.persist,
          label: ev.label,
          conversation: ev.conversation,
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

  async function loadNodes() {
    if (!hasBridge()) {
      setProfiles(COORDINATOR_MOCK)
      setSelectedId((current) => current ?? COORDINATOR_MOCK[0]?.node_id ?? null)
      return
    }

    const rows = await listNodes()
    const nextProfiles = rows || []
    setProfiles(nextProfiles)
    setSelectedId((current) => {
      if (current && nextProfiles.some((profile) => profile.node_id === current)) return current
      return nextProfiles[0]?.node_id ?? null
    })
  }

  async function loadThreadsFor(nodeId, preferredThreadId) {
    if (!hasBridge()) {
      setThreads([])
      setTranscript([])
      setSelectedThreadId(null)
      return
    }

    const rows = (await listThreads(nodeId)) || []
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
      setTraceEvents([])
      return
    }

    const turns = (await getTranscript(nextThreadId)) || []
    setTranscript(turns)
    // Load the thread's persisted trace (tool calls across all its runs) so it
    // survives reopening the thread, not just the live run.
    const trace = (await getTrace(null, null, nextThreadId)) || []
    setTraceEvents(trace)
  }

  function updateField(key, value) {
    setForm((current) => ({ ...current, [key]: value }))
  }

  function toggleTraceRow(id) {
    setOpenTrace((cur) => (cur.includes(id) ? cur.filter((x) => x !== id) : [...cur, id]))
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

  async function copyConversation() {
    const text = conversationLines
      .map((turn) => {
        const body = (turn.text || '').trim() || `[${turn.kind || 'event'}]`
        return `${turn.label || 'agent'}: ${body}`
      })
      .join('\n')
    if (!text) return
    if (await copyToClipboard(text)) {
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)
    }
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
      provider: form.provider,
      tags: form.tags_input.split(',').map((tag) => tag.trim()).filter(Boolean),
      rules: form.rules,
      model: form.model || null,
      effort: form.effort || null,
      working_dir: form.working_dir.trim() || null,
    }

    try {
      if (hasBridge()) {
        const created = await createNode(
          payload.name,
          payload.provider,
          payload.tags,
          payload.rules,
          payload.model,
          payload.effort,
          payload.working_dir,
        )
        await loadNodes()
        setSelectedId(created?.node_id || null)
      } else {
        const created = {
          ...payload,
          node_id: nextMockId(profiles),
          created_at: new Date().toISOString(),
          status: 'idle',
        }
        setProfiles((current) => [...current, created])
        setSelectedId(created.node_id)
      }
      setForm(EMPTY_FORM)
      setShowForm(false)
    } catch (err) {
      setError(err?.message || 'Failed to create node.')
    } finally {
      setBusy(false)
    }
  }

  async function removeNode(nodeId) {
    setBusy(true)
    setError('')
    try {
      if (hasBridge()) {
        await deleteNode(nodeId)
        await loadNodes()
      } else {
        const nextProfiles = profiles.filter((profile) => profile.node_id !== nodeId)
        setProfiles(nextProfiles)
        setSelectedId((current) => {
          if (current && current !== nodeId) return current
          return nextProfiles[0]?.node_id ?? null
        })
      }
    } catch (err) {
      setError(err?.message || 'Failed to delete node.')
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
        category: 'user',
        persist: true,
        label: 'user',
        conversation: true,
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
          category: 'content',
          persist: true,
          label: 'agent',
          conversation: true,
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

  // Flat conversation: user prompts + agent content (text/thinking/error) only.
  // Tool calls live in the Trace bucket; lifecycle envelopes (system/result) and
  // empty turns are dropped — they carry no content (the real reasoning is `thinking`).
  const conversationLines = transcript.filter((t) => {
    if (!t.conversation) return false
    return (t.text || '').trim()
  })

  const selected = profiles.find((profile) => profile.node_id === selectedId) || null

  return (
    <div className="grid grid-cols-1 gap-4 lg:grid-cols-[280px_1fr]">
      <aside className="flex min-h-[70vh] flex-col overflow-hidden rounded-2xl border border-white/5 bg-white/[0.02]">
        <div className="border-b border-white/5 px-4 py-3">
          <div className="text-sm font-semibold text-slate-200">Roster</div>
          <div className="text-xs text-slate-500">{profiles.length} nodes</div>
        </div>

        <div className="flex-1 space-y-3 overflow-y-auto p-3">
          {profiles.length === 0 ? (
            <div className="rounded-xl border border-dashed border-white/10 bg-black/20 px-4 py-8 text-center text-sm text-slate-500">
              No nodes yet.
            </div>
          ) : (
            profiles.map((profile) => (
              <div
                key={profile.node_id}
                className={`block w-full rounded-xl border p-3 text-left transition ${
                  selectedId === profile.node_id
                    ? 'border-orange-500/40 bg-orange-500/10 shadow-lg shadow-orange-950/20'
                    : 'border-white/5 bg-black/20 hover:border-white/10 hover:bg-white/[0.03]'
                }`}
              >
                <div className="flex items-start justify-between gap-3">
                  <button
                    type="button"
                    onClick={() => setSelectedId(profile.node_id)}
                    className="min-w-0 flex-1 text-left"
                  >
                    <div className="truncate text-sm font-semibold text-slate-100">{profile.name}</div>
                    <div className="mt-1 font-mono text-[11px] text-slate-500">{profile.node_id}</div>
                  </button>
                  <button
                    type="button"
                    onClick={() => void removeNode(profile.node_id)}
                    className="rounded-md border border-white/10 px-2 py-1 text-[11px] font-medium text-slate-400 hover:border-rose-500/30 hover:text-rose-300"
                    aria-label={`Delete ${profile.name}`}
                  >
                    Delete
                  </button>
                </div>

                <div className="mt-3 flex items-center gap-2">
                  <ProviderPill provider={profile.provider} />
                  <TagPills tags={profile.tags} />
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
              <Field label="Provider">
                <select
                  value={form.provider}
                  onChange={(event) => updateField('provider', event.target.value)}
                  className={INPUT}
                >
                  {catalog.providers.map((group) => (
                    <option key={group.provider} value={group.provider} className="bg-[#0b0e14]">
                      {group.provider}
                    </option>
                  ))}
                </select>
              </Field>
              <Field label="Tags">
                <input
                  value={form.tags_input}
                  onChange={(event) => updateField('tags_input', event.target.value)}
                  className={INPUT}
                  placeholder="architect, design"
                />
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
              Add Node
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
                <ProviderPill provider={selected.provider} />
                <TagPills tags={selected.tags} />
                <StatusBadge status={selected.status || 'idle'} />
              </div>
              <div className="mt-2 font-mono text-xs text-slate-500">{selected.node_id}</div>
              <div className="mt-4">
                <div className="mb-2 text-xs uppercase tracking-wider text-slate-500">Threads</div>
                <div className="flex flex-wrap gap-2">
                  {threads.length ? (
                    threads.map((thread) => (
                      <button
                        key={thread.id}
                        type="button"
                        onClick={() => void loadThreadsFor(selected.node_id, thread.id)}
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

            <div className="flex-1 overflow-hidden rounded-2xl border border-white/5 bg-black/40">
              <div className="flex items-center justify-between border-b border-white/5 px-4 py-3">
                <span className="text-sm font-semibold text-slate-200">Conversation</span>
                <div className="flex items-center gap-3">
                  <span className="text-[11px] text-slate-600">tool calls → Trace</span>
                  <button
                    type="button"
                    onClick={() => void copyConversation()}
                    disabled={!conversationLines.length}
                    className="rounded border border-white/10 px-2 py-0.5 text-[11px] font-medium text-slate-400 hover:border-white/20 hover:text-slate-200 disabled:opacity-40"
                  >
                    {copied ? 'Copied' : 'Copy'}
                  </button>
                </div>
              </div>
              <div className="max-h-[48vh] overflow-auto p-4 font-mono text-[13px] leading-relaxed">
                {conversationLines.length ? (
                  conversationLines.map((turn) => {
                    const excluded = turn.included === false
                    const isUser = turn.label === 'user'
                    const isThinking = turn.category === 'thinking'
                    const isError = turn.category === 'error'
                    const label = turn.label || 'agent'
                    const labelTone = isUser
                      ? 'text-orange-500/70'
                      : isThinking
                        ? 'text-violet-500/60'
                        : isError
                          ? 'text-rose-500/70'
                          : 'text-emerald-500/70'
                    const textTone = isUser
                      ? 'text-orange-200'
                      : isThinking
                        ? 'text-slate-500 italic'
                        : isError
                          ? 'text-rose-300'
                          : 'text-slate-200'
                    return (
                      <div key={turn.id} className={`group flex gap-3 py-0.5 ${excluded ? 'opacity-30' : ''}`}>
                        <span className={`w-12 shrink-0 select-none text-right ${labelTone}`}>{label}</span>
                        <span className={`flex-1 whitespace-pre-wrap break-words ${textTone}`}>{turn.text}</span>
                        <button
                          type="button"
                          onClick={() => void toggleTurn(turn)}
                          title={excluded ? 'include this turn in the agent context' : 'exclude this turn from the agent context'}
                          className={`shrink-0 select-none rounded border px-2 py-0.5 text-[11px] font-medium transition ${
                            excluded
                              ? 'border-emerald-500/40 bg-emerald-500/10 text-emerald-300 hover:bg-emerald-500/20'
                              : 'border-white/10 text-slate-500 hover:border-white/25 hover:text-slate-200'
                          }`}
                        >
                          {excluded ? 'include' : 'exclude'}
                        </button>
                      </div>
                    )
                  })
                ) : (
                  <div className="grid min-h-[220px] place-items-center text-center text-slate-600">
                    Open a node thread or send the first message to start one.
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
                <div className="border-t border-white/5 max-h-64 overflow-auto p-3 space-y-1">
                  {traceEvents.length === 0 ? (
                    <div className="text-xs text-slate-500 text-center py-4">No tool calls yet.</div>
                  ) : (
                    traceEvents.map((ev, i) => {
                      const id = ev.id || `t-${i}`
                      const open = openTrace.includes(id)
                      const command =
                        ev.target_path || ev.raw?.input?.command || ev.raw?.input?.path || ev.raw?.input?.file_path || ''
                      const output = ev.raw?.output
                      const exit = ev.raw?.exit_code
                      const hasDetail = Boolean(command || output)
                      const actionStyle =
                        ev.action === 'write_file' || ev.action === 'Write'
                          ? 'bg-orange-500/15 text-orange-300 ring-orange-500/30'
                          : ev.action === 'read_file' || ev.action === 'Read'
                          ? 'bg-sky-500/15 text-sky-300 ring-sky-500/30'
                          : ev.action === 'shell'
                          ? 'bg-violet-500/15 text-violet-300 ring-violet-500/30'
                          : 'bg-slate-500/15 text-slate-300 ring-white/10'
                      return (
                        <div key={id} className="rounded-lg border border-white/5 bg-black/20">
                          <button
                            type="button"
                            onClick={() => hasDetail && toggleTraceRow(id)}
                            className={`flex w-full items-center gap-2 px-2 py-1.5 text-left text-xs ${hasDetail ? 'hover:bg-white/5' : 'cursor-default'}`}
                          >
                            <span className={`shrink-0 inline-flex rounded-full px-2 py-0.5 text-[10px] font-semibold ring-1 ring-inset ${actionStyle}`}>
                              {ev.action}
                            </span>
                            <span className="flex-1 truncate font-mono text-slate-400">{command}</span>
                            {exit !== undefined && exit !== null && (
                              <span className={`shrink-0 rounded px-1.5 py-0.5 text-[10px] font-medium ${exit === 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                                exit {exit}
                              </span>
                            )}
                            <span className="shrink-0 text-slate-600">{ev.ts ? ev.ts.slice(11, 19) : ''}</span>
                            {hasDetail && <span className="shrink-0 text-slate-600">{open ? '▲' : '▼'}</span>}
                          </button>
                          {open && (
                            <div className="border-t border-white/5 px-2 py-1.5 font-mono text-[11px]">
                              {command && <div className="whitespace-pre-wrap break-words text-slate-300">$ {command}</div>}
                              {output ? (
                                <pre className="mt-1 max-h-60 overflow-auto whitespace-pre-wrap break-words text-slate-500">{output}</pre>
                              ) : (
                                <div className="mt-1 text-slate-600">(no output captured)</div>
                              )}
                            </div>
                          )}
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
                  <span className="text-xs text-slate-400">→ <strong>target</strong>: {spawnCard.prefill_role} · {spawnCard.prefill_task}</span>
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
            Select a node to start a conversation
          </div>
        )}
      </section>
    </div>
  )
}
