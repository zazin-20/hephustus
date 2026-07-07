import { useEffect, useRef, useState } from 'react'
import {
  evaluateSpawn,
  getTrace,
  getTranscript,
  hasBridge,
  listNodes,
  listThreads,
  onAgent,
  parseHandoffMarker,
  sendMessage,
  setTurnIncluded,
} from '../api.js'
import { NODES_MOCK } from '../mock.js'

const INPUT =
  'w-full rounded-lg border border-white/10 bg-black/20 px-2.5 py-1.5 text-sm text-slate-200 outline-none focus:border-white/25'

const PROVIDER_STYLE = {
  claude: 'bg-sky-500/15 text-sky-300 ring-sky-500/30',
  codex: 'bg-orange-500/15 text-orange-300 ring-orange-500/30',
}

const STATUS_STYLE = {
  idle: 'bg-slate-500/15 text-slate-300 ring-white/10',
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

export default function Console() {
  const [profiles, setProfiles] = useState([])
  const [selectedId, setSelectedId] = useState(null)
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
  const [error, setError] = useState('')
  const activeRunId = useRef(null)
  const activeAgentId = useRef(null)
  const activeThreadId = useRef(null)

  useEffect(() => {
    void loadNodes()
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
      setProfiles(NODES_MOCK)
      setSelectedId((current) => current ?? NODES_MOCK[0]?.node_id ?? null)
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
    const trace = (await getTrace(null, null, nextThreadId)) || []
    setTraceEvents(trace)
  }

  function toggleTraceRow(id) {
    setOpenTrace((current) => (current.includes(id) ? current.filter((item) => item !== id) : [...current, id]))
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
        current.map((item) => (item.id === turn.id ? { ...item, included: next } : item)),
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

  const conversationLines = transcript.filter((turn) => {
    if (!turn.conversation) return false
    return (turn.text || '').trim()
  })

  const selected = profiles.find((profile) => profile.node_id === selectedId) || null

  return (
    <div className="grid grid-cols-1 gap-4 lg:grid-cols-[280px_1fr]">
      <aside className="flex min-h-[70vh] flex-col overflow-hidden rounded-2xl border border-white/5 bg-white/[0.02]">
        <div className="border-b border-white/5 px-4 py-3">
          <div className="text-xs uppercase tracking-[0.18em] text-slate-500">Node picker</div>
          <div className="mt-2 text-xs text-slate-500">{profiles.length} nodes</div>
        </div>

        <div className="flex-1 space-y-3 overflow-y-auto p-3">
          {profiles.length === 0 ? (
            <div className="rounded-xl border border-dashed border-white/10 bg-black/20 px-4 py-8 text-center text-sm text-slate-500">
              No nodes yet.
            </div>
          ) : (
            profiles.map((profile) => (
              <button
                key={profile.node_id}
                type="button"
                onClick={() => setSelectedId(profile.node_id)}
                className={`block w-full rounded-xl border p-3 text-left transition ${
                  selectedId === profile.node_id
                    ? 'border-orange-500/40 bg-orange-500/10 shadow-lg shadow-orange-950/20'
                    : 'border-white/5 bg-black/20 hover:border-white/10 hover:bg-white/[0.03]'
                }`}
              >
                <div className="truncate text-sm font-semibold text-slate-100">{profile.name}</div>
                <div className="mt-1 font-mono text-[11px] text-slate-500">{profile.node_id}</div>
                <div className="mt-3 flex items-center gap-2">
                  <ProviderPill provider={profile.provider} />
                  <TagPills tags={profile.tags} />
                  <StatusBadge status={profile.status || 'idle'} />
                </div>
              </button>
            ))
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

            <div className="overflow-hidden rounded-2xl border border-white/5 bg-black/20">
              <button
                type="button"
                onClick={() => setShowTrace((value) => !value)}
                className="flex w-full items-center justify-between px-4 py-3 text-left text-sm font-semibold text-slate-300 hover:bg-white/5"
              >
                <span>Trace {traceEvents.length ? `(${traceEvents.length})` : ''}</span>
                <span className="text-xs text-slate-500">{showTrace ? '▲ hide' : '▼ show'}</span>
              </button>
              {showTrace ? (
                <div className="max-h-64 space-y-1 overflow-auto border-t border-white/5 p-3">
                  {traceEvents.length === 0 ? (
                    <div className="py-4 text-center text-xs text-slate-500">No tool calls yet.</div>
                  ) : (
                    traceEvents.map((ev, index) => {
                      const id = ev.id || `t-${index}`
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
                            <span
                              className={`inline-flex shrink-0 rounded-full px-2 py-0.5 text-[10px] font-semibold ring-1 ring-inset ${actionStyle}`}
                            >
                              {ev.action}
                            </span>
                            <span className="flex-1 truncate font-mono text-slate-400">{command}</span>
                            {exit !== undefined && exit !== null ? (
                              <span
                                className={`shrink-0 rounded px-1.5 py-0.5 text-[10px] font-medium ${exit === 0 ? 'text-emerald-400' : 'text-rose-400'}`}
                              >
                                exit {exit}
                              </span>
                            ) : null}
                            <span className="shrink-0 text-slate-600">{ev.ts ? ev.ts.slice(11, 19) : ''}</span>
                            {hasDetail ? <span className="shrink-0 text-slate-600">{open ? '▲' : '▼'}</span> : null}
                          </button>
                          {open ? (
                            <div className="border-t border-white/5 px-2 py-1.5 font-mono text-[11px]">
                              {command ? <div className="whitespace-pre-wrap break-words text-slate-300">$ {command}</div> : null}
                              {output ? (
                                <pre className="mt-1 max-h-60 overflow-auto whitespace-pre-wrap break-words text-slate-500">{output}</pre>
                              ) : (
                                <div className="mt-1 text-slate-600">(no output captured)</div>
                              )}
                            </div>
                          ) : null}
                        </div>
                      )
                    })
                  )}
                </div>
              ) : null}
            </div>

            {spawnCard ? (
              <div
                className={`rounded-2xl border p-4 ${spawnCard.gating === 'green' ? 'border-emerald-500/30 bg-emerald-500/5' : 'border-amber-500/30 bg-amber-500/5'}`}
              >
                <div className="mb-2 flex items-center gap-2">
                  <span
                    className={`inline-flex rounded-full px-2 py-0.5 text-[11px] font-semibold ring-1 ring-inset ${spawnCard.gating === 'green' ? 'bg-emerald-500/15 text-emerald-300 ring-emerald-500/30' : 'bg-amber-500/15 text-amber-300 ring-amber-500/30'}`}
                  >
                    {spawnCard.gating === 'green' ? '✓ Ready to Spawn' : '⚠ Spawn (with failures)'}
                  </span>
                  <span className="text-xs text-slate-400">
                    → <strong>target</strong>: {spawnCard.prefill_role} · {spawnCard.prefill_task}
                  </span>
                </div>
                {spawnCard.failures?.length > 0 ? (
                  <ul className="mb-3 space-y-1">
                    {spawnCard.failures.map((failure, index) => (
                      <li key={`${failure.rule_id}-${index}`} className="text-xs text-amber-300">
                        <span className="font-mono">{failure.rule_id}</span> - {failure.message}
                        {failure.fix_hint ? <span className="ml-1 text-amber-400/60">({failure.fix_hint})</span> : null}
                      </li>
                    ))}
                  </ul>
                ) : null}
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
            ) : null}

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
