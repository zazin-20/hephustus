import { useEffect, useState } from 'react'
import { createProfile, deleteProfile, hasBridge, listProfiles } from '../api.js'
import { COORDINATOR_MOCK } from '../mock.js'

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

const EMPTY_FORM = {
  name: '',
  role: 'architect',
  rules: '',
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

function splitRules(value) {
  return value
    .split(',')
    .map((rule) => rule.trim())
    .filter(Boolean)
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

export default function Coordinator() {
  const [profiles, setProfiles] = useState([])
  const [selectedId, setSelectedId] = useState(null)
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState(EMPTY_FORM)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    loadProfiles()
  }, [])

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

  function updateField(key, value) {
    setForm((current) => ({ ...current, [key]: value }))
  }

  async function submit(event) {
    event.preventDefault()
    if (!form.name.trim() || busy) return

    setBusy(true)
    setError('')
    const payload = {
      name: form.name.trim(),
      role: form.role,
      rules: splitRules(form.rules),
      model: form.model.trim() || null,
      effort: form.effort.trim() || null,
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
                <input
                  value={form.rules}
                  onChange={(event) => updateField('rules', event.target.value)}
                  className={INPUT}
                  placeholder="S-001, S-002"
                />
              </Field>
              <Field label="Model">
                <input
                  value={form.model}
                  onChange={(event) => updateField('model', event.target.value)}
                  className={INPUT}
                  placeholder="claude-opus, gpt-5, ..."
                />
              </Field>
              <Field label="Effort">
                <input
                  value={form.effort}
                  onChange={(event) => updateField('effort', event.target.value)}
                  className={INPUT}
                  placeholder="high"
                />
              </Field>
              <Field label="Working Directory">
                <input
                  value={form.working_dir}
                  onChange={(event) => updateField('working_dir', event.target.value)}
                  className={INPUT}
                  placeholder="path/to/repo"
                />
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
          <div className="space-y-4">
            <div className="border-b border-white/5 pb-4">
              <div className="flex items-center gap-3">
                <div className="text-lg font-semibold text-slate-100">{selected.name}</div>
                <RolePill role={selected.role} />
                <StatusBadge status={selected.status || 'idle'} />
              </div>
              <div className="mt-2 font-mono text-xs text-slate-500">{selected.agent_id}</div>
              <div className="mt-3 flex flex-wrap gap-2">
                {(selected.rules || []).length ? (
                  selected.rules.map((rule) => (
                    <span
                      key={rule}
                      className="rounded-full bg-white/5 px-2 py-0.5 font-mono text-[11px] text-slate-300 ring-1 ring-inset ring-white/10"
                    >
                      {rule}
                    </span>
                  ))
                ) : (
                  <span className="text-sm text-slate-500">No explicit rules attached.</span>
                )}
              </div>
            </div>

            <div className="grid gap-3 text-sm text-slate-400 sm:grid-cols-2">
              <div className="rounded-xl border border-white/5 bg-black/20 p-4">
                <div className="text-xs uppercase tracking-wider text-slate-500">Model</div>
                <div className="mt-1 text-slate-200">{selected.model || 'Not set'}</div>
              </div>
              <div className="rounded-xl border border-white/5 bg-black/20 p-4">
                <div className="text-xs uppercase tracking-wider text-slate-500">Effort</div>
                <div className="mt-1 text-slate-200">{selected.effort || 'Not set'}</div>
              </div>
              <div className="rounded-xl border border-white/5 bg-black/20 p-4 sm:col-span-2">
                <div className="text-xs uppercase tracking-wider text-slate-500">Working Directory</div>
                <div className="mt-1 break-all text-slate-200">{selected.working_dir || 'Not set'}</div>
              </div>
            </div>

            <div className="grid min-h-[240px] place-items-center rounded-2xl border border-dashed border-white/10 bg-black/20 px-6 text-center text-sm text-slate-500">
              Select a profile to start a conversation
            </div>
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
