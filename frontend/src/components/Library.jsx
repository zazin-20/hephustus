import { useEffect, useState } from 'react'
import {
  createArtifact,
  createNode,
  deleteArtifact,
  deleteNode,
  getCatalog,
  hasBridge,
  listArtifacts,
  listNodes,
  listRules,
  pickDirectory,
  updateArtifact,
  updateNode,
} from '../api.js'
import { ARTIFACTS_MOCK, CATALOG_MOCK, NODES_MOCK, RULES_MOCK } from '../mock.js'
import ArtifactForm from './ArtifactForm.jsx'
import NodeForm from './NodeForm.jsx'

const PROVIDER_STYLE = {
  claude: 'bg-sky-500/15 text-sky-300 ring-sky-500/30',
  codex: 'bg-orange-500/15 text-orange-300 ring-orange-500/30',
}

const STATUS_STYLE = {
  idle: 'bg-slate-500/15 text-slate-300 ring-white/10',
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

function DetailCard({ label, children }) {
  return (
    <div className="rounded-2xl border border-white/5 bg-black/20 p-4">
      <div className="text-xs uppercase tracking-[0.18em] text-slate-500">{label}</div>
      <div className="mt-3">{children}</div>
    </div>
  )
}

function ChipList({ items, emptyLabel = 'None.' }) {
  if (!items?.length) return <div className="text-sm text-slate-500">{emptyLabel}</div>
  return (
    <div className="flex flex-wrap gap-2">
      {items.map((item) => (
        <span
          key={item}
          className="rounded-full border border-white/10 bg-black/30 px-2 py-1 font-mono text-[11px] text-slate-300"
        >
          {item}
        </span>
      ))}
    </div>
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

function nextMockArtifactId(artifacts) {
  const counters = artifacts
    .map((artifact) => artifact.artifact_id)
    .filter((artifactId) => artifactId.startsWith('artifact-'))
    .map((artifactId) => Number.parseInt(artifactId.split('-')[1], 10))
    .filter(Number.isFinite)
  const next = counters.length ? Math.max(...counters) + 1 : 1
  return `artifact-${String(next).padStart(3, '0')}`
}

export default function Library() {
  const [catalogMode, setCatalogMode] = useState('nodes')
  const [profiles, setProfiles] = useState([])
  const [selectedId, setSelectedId] = useState(null)
  const [showForm, setShowForm] = useState(false)
  const [editingNode, setEditingNode] = useState(null)
  const [artifacts, setArtifacts] = useState([])
  const [selectedArtifactId, setSelectedArtifactId] = useState(null)
  const [showArtifactForm, setShowArtifactForm] = useState(false)
  const [editingArtifact, setEditingArtifact] = useState(null)
  const [catalog, setCatalog] = useState(CATALOG_MOCK)
  const [ruleSet, setRuleSet] = useState(RULES_MOCK)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    void loadNodes()
    void loadArtifacts()
    if (hasBridge()) {
      void getCatalog().then((nextCatalog) => nextCatalog && setCatalog(nextCatalog))
      void listRules().then((nextRules) => nextRules && setRuleSet(nextRules))
    }
  }, [])

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

  async function loadArtifacts() {
    if (!hasBridge()) {
      setArtifacts(ARTIFACTS_MOCK)
      setSelectedArtifactId((current) => current ?? ARTIFACTS_MOCK[0]?.artifact_id ?? null)
      return
    }

    const rows = await listArtifacts()
    const nextArtifacts = rows || []
    setArtifacts(nextArtifacts)
    setSelectedArtifactId((current) => {
      if (current && nextArtifacts.some((artifact) => artifact.artifact_id === current)) return current
      return nextArtifacts[0]?.artifact_id ?? null
    })
  }

  async function browseDirectory() {
    if (!hasBridge()) return null
    return await pickDirectory()
  }

  function openCreateForm() {
    setEditingNode(null)
    setShowForm(true)
    setError('')
  }

  function openEditForm(node) {
    setEditingNode(node)
    setShowForm(true)
    setError('')
  }

  function closeForm() {
    setEditingNode(null)
    setShowForm(false)
    setError('')
  }

  function openCreateArtifactForm() {
    setEditingArtifact(null)
    setShowArtifactForm(true)
    setError('')
  }

  function openEditArtifactForm(artifact) {
    setEditingArtifact(artifact)
    setShowArtifactForm(true)
    setError('')
  }

  function closeArtifactForm() {
    setEditingArtifact(null)
    setShowArtifactForm(false)
    setError('')
  }

  async function saveNode(payload) {
    setBusy(true)
    setError('')

    try {
      if (hasBridge()) {
        const saved = editingNode
          ? await updateNode(
              editingNode.node_id,
              payload.name,
              payload.provider,
              payload.tags,
              payload.rules,
              payload.model,
              payload.effort,
              payload.working_dir,
              payload.inputs,
              payload.outputs,
              payload.skills,
              payload.skill_obligations,
              payload.allowed_paths,
              payload.allowed_tools,
              payload.context_policy,
            )
          : await createNode(
              payload.name,
              payload.provider,
              payload.tags,
              payload.rules,
              payload.model,
              payload.effort,
              payload.working_dir,
              payload.inputs,
              payload.outputs,
              payload.skills,
              payload.skill_obligations,
              payload.allowed_paths,
              payload.allowed_tools,
              payload.context_policy,
            )
        await loadNodes()
        setSelectedId(saved?.node_id || null)
      } else {
        const saved = editingNode
          ? {
              ...editingNode,
              ...payload,
              node_id: editingNode.node_id,
              created_at: editingNode.created_at,
              status: editingNode.status || 'idle',
            }
          : {
              ...payload,
              node_id: nextMockId(profiles),
              created_at: new Date().toISOString(),
              status: 'idle',
            }
        setProfiles((current) =>
          editingNode
            ? current.map((profile) => (profile.node_id === saved.node_id ? saved : profile))
            : [...current, saved],
        )
        setSelectedId(saved.node_id)
      }
      setEditingNode(null)
      setShowForm(false)
    } catch (err) {
      setError(err?.message || `Failed to ${editingNode ? 'update' : 'create'} node.`)
      throw err
    } finally {
      setBusy(false)
    }
  }

  async function saveArtifact(payload) {
    setBusy(true)
    setError('')

    try {
      if (hasBridge()) {
        const saved = editingArtifact
          ? await updateArtifact(
              editingArtifact.artifact_id,
              payload.name,
              payload.headings,
              payload.tags,
              payload.good_looks_like,
              payload.antipatterns,
              payload.examples,
            )
          : await createArtifact(
              payload.name,
              payload.headings,
              payload.tags,
              payload.good_looks_like,
              payload.antipatterns,
              payload.examples,
            )
        await loadArtifacts()
        setSelectedArtifactId(saved?.artifact_id || null)
      } else {
        const nextArtifactId = nextMockArtifactId(artifacts)
        const saved = editingArtifact
          ? {
              ...editingArtifact,
              ...payload,
              artifact_id: editingArtifact.artifact_id,
              path: editingArtifact.path,
              created_at: editingArtifact.created_at,
            }
          : {
              ...payload,
              artifact_id: nextArtifactId,
              path: `agents/artifacts/${nextArtifactId}.md`,
              created_at: new Date().toISOString(),
            }
        setArtifacts((current) =>
          editingArtifact
            ? current.map((artifact) => (artifact.artifact_id === saved.artifact_id ? saved : artifact))
            : [...current, saved],
        )
        setSelectedArtifactId(saved.artifact_id)
      }
      setEditingArtifact(null)
      setShowArtifactForm(false)
    } catch (err) {
      setError(err?.message || `Failed to ${editingArtifact ? 'update' : 'create'} artifact.`)
      throw err
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

  async function removeArtifact(artifactId) {
    setBusy(true)
    setError('')
    try {
      if (hasBridge()) {
        await deleteArtifact(artifactId)
        await loadArtifacts()
      } else {
        const nextArtifacts = artifacts.filter((artifact) => artifact.artifact_id !== artifactId)
        setArtifacts(nextArtifacts)
        setSelectedArtifactId((current) => {
          if (current && current !== artifactId) return current
          return nextArtifacts[0]?.artifact_id ?? null
        })
      }
    } catch (err) {
      setError(err?.message || 'Failed to delete artifact.')
    } finally {
      setBusy(false)
    }
  }

  const selected = profiles.find((profile) => profile.node_id === selectedId) || null
  const selectedArtifact = artifacts.find((artifact) => artifact.artifact_id === selectedArtifactId) || null

  return (
    <div className="grid grid-cols-1 gap-4 lg:grid-cols-[280px_1fr]">
      <aside className="flex min-h-[70vh] flex-col overflow-hidden rounded-2xl border border-white/5 bg-white/[0.02]">
        <div className="border-b border-white/5 px-4 py-3">
          <div className="flex gap-2">
            {[
              { id: 'nodes', label: 'Nodes' },
              { id: 'artifacts', label: 'Artifacts' },
            ].map((item) => (
              <button
                key={item.id}
                type="button"
                onClick={() => setCatalogMode(item.id)}
                className={`rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] transition ${
                  catalogMode === item.id
                    ? 'bg-orange-500/15 text-orange-200 ring-1 ring-inset ring-orange-500/30'
                    : 'bg-black/20 text-slate-500 ring-1 ring-inset ring-white/10 hover:text-slate-200'
                }`}
              >
                {item.label}
              </button>
            ))}
          </div>
          <div className="mt-2 text-xs text-slate-500">
            {catalogMode === 'nodes' ? `${profiles.length} nodes` : `${artifacts.length} artifacts`}
          </div>
        </div>

        <div className="flex-1 space-y-3 overflow-y-auto p-3">
          {catalogMode === 'nodes' ? (
            profiles.length === 0 ? (
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
                      onClick={() => openEditForm(profile)}
                      className="rounded-md border border-white/10 px-2 py-1 text-[11px] font-medium text-slate-400 hover:border-white/20 hover:text-slate-200"
                      aria-label={`Edit ${profile.name}`}
                    >
                      Edit
                    </button>
                  </div>

                  <div className="mt-3 flex items-center gap-2">
                    <ProviderPill provider={profile.provider} />
                    <TagPills tags={profile.tags} />
                    <StatusBadge status={profile.status || 'idle'} />
                  </div>

                  <div className="mt-3">
                    <button
                      type="button"
                      onClick={() => void removeNode(profile.node_id)}
                      disabled={busy}
                      className="rounded-md border border-white/10 px-2 py-1 text-[11px] font-medium text-slate-400 hover:border-rose-500/30 hover:text-rose-300 disabled:opacity-40"
                      aria-label={`Delete ${profile.name}`}
                    >
                      Delete
                    </button>
                  </div>
                </div>
              ))
            )
          ) : artifacts.length === 0 ? (
            <div className="rounded-xl border border-dashed border-white/10 bg-black/20 px-4 py-8 text-center text-sm text-slate-500">
              No artifacts yet.
            </div>
          ) : (
            artifacts.map((artifact) => (
              <div
                key={artifact.artifact_id}
                className={`block w-full rounded-xl border p-3 text-left transition ${
                  selectedArtifactId === artifact.artifact_id
                    ? 'border-orange-500/40 bg-orange-500/10 shadow-lg shadow-orange-950/20'
                    : 'border-white/5 bg-black/20 hover:border-white/10 hover:bg-white/[0.03]'
                }`}
              >
                <div className="flex items-start justify-between gap-3">
                  <button
                    type="button"
                    onClick={() => setSelectedArtifactId(artifact.artifact_id)}
                    className="min-w-0 flex-1 text-left"
                  >
                    <div className="truncate text-sm font-semibold text-slate-100">{artifact.name}</div>
                    <div className="mt-1 font-mono text-[11px] text-slate-500">{artifact.artifact_id}</div>
                  </button>
                  <button
                    type="button"
                    onClick={() => openEditArtifactForm(artifact)}
                    className="rounded-md border border-white/10 px-2 py-1 text-[11px] font-medium text-slate-400 hover:border-white/20 hover:text-slate-200"
                    aria-label={`Edit ${artifact.name}`}
                  >
                    Edit
                  </button>
                </div>

                <div className="mt-3 flex items-center gap-2">
                  <TagPills tags={artifact.tags} />
                </div>
                <div className="mt-2 text-[11px] text-slate-500">
                  {artifact.headings.length} heading rule{artifact.headings.length === 1 ? '' : 's'}
                </div>

                <div className="mt-3">
                  <button
                    type="button"
                    onClick={() => void removeArtifact(artifact.artifact_id)}
                    disabled={busy}
                    className="rounded-md border border-white/10 px-2 py-1 text-[11px] font-medium text-slate-400 hover:border-rose-500/30 hover:text-rose-300 disabled:opacity-40"
                    aria-label={`Delete ${artifact.name}`}
                  >
                    Delete
                  </button>
                </div>
              </div>
            ))
          )}
        </div>

        <div className="border-t border-white/5 p-3">
          {catalogMode === 'nodes' ? (
            showForm ? (
              <NodeForm
                initialNode={editingNode}
                catalog={catalog}
                ruleSet={ruleSet}
                artifacts={artifacts}
                live={hasBridge()}
                onSubmit={saveNode}
                onCancel={closeForm}
                onPickDirectory={browseDirectory}
                submitLabel={editingNode ? 'Save' : 'Create'}
                title={editingNode ? `Edit ${editingNode.name}` : 'Create node'}
              />
            ) : (
              <button
                type="button"
                onClick={openCreateForm}
                className="w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm font-medium text-slate-200 hover:bg-white/10"
              >
                Add Node
              </button>
            )
          ) : showArtifactForm ? (
            <ArtifactForm
              initialArtifact={editingArtifact}
              onSubmit={saveArtifact}
              onCancel={closeArtifactForm}
              submitLabel={editingArtifact ? 'Save' : 'Create'}
              title={editingArtifact ? `Edit ${editingArtifact.name}` : 'Create artifact'}
            />
          ) : (
            <button
              type="button"
              onClick={openCreateArtifactForm}
              className="w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm font-medium text-slate-200 hover:bg-white/10"
            >
              Add Artifact
            </button>
          )}
        </div>
      </aside>

      <section className="rounded-2xl border border-white/5 bg-white/[0.02] p-6">
        {error ? <div className="mb-4 text-xs text-rose-300">{error}</div> : null}
        {catalogMode === 'artifacts' ? (
          selectedArtifact ? (
            <div className="flex min-h-[70vh] flex-col gap-6">
              <div className="border-b border-white/5 pb-4">
                <div className="flex items-center gap-3">
                  <div className="text-lg font-semibold text-slate-100">{selectedArtifact.name}</div>
                  <TagPills tags={selectedArtifact.tags} />
                </div>
                <div className="mt-2 font-mono text-xs text-slate-500">{selectedArtifact.artifact_id}</div>
                <div className="mt-1 font-mono text-xs text-slate-600">{selectedArtifact.path}</div>
              </div>

              <div className="grid gap-4 lg:grid-cols-2">
                <DetailCard label="Heading rules">
                  <div className="space-y-2">
                    {selectedArtifact.headings.length ? (
                      selectedArtifact.headings.map((heading) => (
                        <div key={heading.heading} className="rounded-xl border border-white/5 bg-black/30 p-3">
                          <div className="text-sm font-semibold text-slate-100">{heading.heading}</div>
                          <div className="mt-2 flex flex-wrap gap-2 text-[11px] text-slate-400">
                            <span className="rounded-full border border-white/10 px-2 py-0.5">
                              {heading.required ? 'required' : 'optional'}
                            </span>
                            {heading.min_items ? (
                              <span className="rounded-full border border-white/10 px-2 py-0.5">
                                min_items: {heading.min_items}
                              </span>
                            ) : null}
                          </div>
                        </div>
                      ))
                    ) : (
                      <div className="text-sm text-slate-500">No custom heading rules.</div>
                    )}
                  </div>
                </DetailCard>

                <div className="space-y-4">
                  {[
                    ['Best Practices', selectedArtifact.good_looks_like],
                    ['Antipatterns', selectedArtifact.antipatterns],
                    ['Examples', selectedArtifact.examples],
                  ].map(([label, value]) => (
                    <DetailCard key={label} label={label}>
                      <div className="whitespace-pre-wrap text-sm text-slate-300">{value || 'No content yet.'}</div>
                    </DetailCard>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="grid min-h-[70vh] place-items-center text-center text-slate-500">
              Select an artifact to inspect its authored rules and guidance.
            </div>
          )
        ) : selected ? (
          <div className="flex min-h-[70vh] flex-col gap-6">
            <div className="border-b border-white/5 pb-4">
              <div className="flex items-center gap-3">
                <div className="text-lg font-semibold text-slate-100">{selected.name}</div>
                <ProviderPill provider={selected.provider} />
                <TagPills tags={selected.tags} />
                <StatusBadge status={selected.status || 'idle'} />
              </div>
              <div className="mt-2 font-mono text-xs text-slate-500">{selected.node_id}</div>
            </div>

            <div className="grid gap-4 lg:grid-cols-2">
              <DetailCard label="Runtime">
                <div className="grid gap-3 sm:grid-cols-2">
                  {[
                    ['Model', selected.model || 'Default'],
                    ['Effort', selected.effort || 'Default'],
                    ['Working dir', selected.working_dir || 'Not set'],
                    ['Created', selected.created_at || 'Unknown'],
                  ].map(([label, value]) => (
                    <div key={label}>
                      <div className="text-[11px] uppercase tracking-[0.18em] text-slate-600">{label}</div>
                      <div className="mt-1 break-words font-mono text-sm text-slate-300">{value}</div>
                    </div>
                  ))}
                </div>
              </DetailCard>

              <DetailCard label="Rules">
                <ChipList items={selected.rules || []} emptyLabel="No runtime rules selected." />
              </DetailCard>

              <DetailCard label="Inputs">
                <ChipList items={selected.inputs || []} emptyLabel="No inputs configured." />
              </DetailCard>

              <DetailCard label="Outputs">
                <ChipList items={selected.outputs || []} emptyLabel="No outputs configured." />
              </DetailCard>

              <DetailCard label="Skills">
                <ChipList items={selected.skills || []} emptyLabel="No required skills." />
              </DetailCard>

              <DetailCard label="Skill obligations">
                <ChipList items={selected.skill_obligations || []} emptyLabel="No skill obligations." />
              </DetailCard>

              <DetailCard label="Allowed paths">
                <ChipList items={selected.allowed_paths || []} emptyLabel="No path restrictions authored." />
              </DetailCard>

              <DetailCard label="Allowed tools">
                <ChipList items={selected.allowed_tools || []} emptyLabel="No tool restrictions authored." />
              </DetailCard>
            </div>

            <DetailCard label="Context policy">
              <div className="whitespace-pre-wrap text-sm text-slate-300">
                {selected.context_policy || 'No explicit context policy.'}
              </div>
            </DetailCard>
          </div>
        ) : (
          <div className="grid min-h-[70vh] place-items-center rounded-2xl border border-dashed border-white/10 bg-black/20 px-6 text-center text-sm text-slate-500">
            Select a node to inspect its authored configuration.
          </div>
        )}
      </section>
    </div>
  )
}
