import { useEffect, useMemo, useRef, useState } from 'react'

import { hasBridge, runWorkflow, saveWorkflow } from '../api.js'
import { useToast } from './Toast.jsx'

const PANEL = 'rounded-2xl border border-white/5 bg-white/[0.02]'
const INPUT =
  'w-full rounded-lg border border-white/10 bg-black/20 px-2.5 py-1.5 text-sm text-slate-200 outline-none focus:border-white/25'

const STATUS_STYLE = {
  not_started: 'bg-slate-700/40 text-slate-300 ring-white/10',
  running: 'bg-sky-500/15 text-sky-300 ring-sky-500/30',
  waiting_human: 'bg-amber-500/15 text-amber-300 ring-amber-500/30',
  blocked: 'bg-rose-500/15 text-rose-300 ring-rose-500/30',
  awaiting_confirm: 'bg-emerald-500/15 text-emerald-300 ring-emerald-500/30',
  done: 'bg-emerald-500/10 text-emerald-200 ring-emerald-500/20',
}

const EDGE_STYLE = {
  idle: 'stroke-slate-700',
  active: 'stroke-sky-400',
  blocked: 'stroke-rose-400',
  awaiting_confirm: 'stroke-emerald-400',
  done: 'stroke-emerald-500/70',
}

const PROVIDER_STYLE = {
  claude: 'border-sky-500/40 bg-sky-500/10 text-sky-200 shadow-sky-900/20',
  codex: 'border-orange-500/40 bg-orange-500/10 text-orange-100 shadow-orange-900/30',
  builtin: 'border-slate-500/40 bg-slate-500/10 text-slate-200 shadow-black/20',
}

function Field({ label, children }) {
  return (
    <label className="block">
      <span className="mb-1 block text-[11px] uppercase tracking-[0.18em] text-slate-500">{label}</span>
      {children}
    </label>
  )
}

function normalizeWorkflow(workflow) {
  if (!workflow) return null
  return {
    workflow_id: workflow.workflow_id,
    version: workflow.version ?? 1,
    run: workflow.run ?? { workflow_run_id: null, status: null },
    placements: (workflow.placements ?? []).map((placement) => ({
      ...placement,
      interactivity: placement.interactivity ?? 'afk',
      status: placement.status ?? 'not_started',
      detail: placement.detail ?? {
        gates: [],
        artifacts: [],
        transcript: [],
        trace: [],
        failures: [],
        spawn_card: null,
      },
    })),
    edges: (workflow.edges ?? []).map((edge) => ({
      ...edge,
      advance: edge.advance ?? 'allow',
      guard: edge.guard ?? null,
      label: edge.label ?? edge.guard?.label ?? null,
      state: edge.state ?? 'idle',
    })),
  }
}

function nextWorkflowId(workflows) {
  const taken = new Set(workflows.map((workflow) => workflow.workflow_id))
  let index = workflows.length + 25
  while (taken.has(`issue-${String(index).padStart(3, '0')}`)) index += 1
  return `issue-${String(index).padStart(3, '0')}`
}

function nextPlacementId(workflow, nodeId) {
  const base = nodeId.replace(/^node-/, 'step-')
  let index = 1
  let candidate = `${base}-${String(index).padStart(2, '0')}`
  const taken = new Set((workflow?.placements ?? []).map((placement) => placement.placement_id))
  while (taken.has(candidate)) {
    index += 1
    candidate = `${base}-${String(index).padStart(2, '0')}`
  }
  return candidate
}

function executorLabel(executor) {
  if (!executor) return 'Unresolved executor'
  if (executor.kind === 'builtin') return executor.name || 'builtin'
  return executor.model || executor.provider || 'engine'
}

function statusTone(status) {
  return STATUS_STYLE[status] || STATUS_STYLE.not_started
}

function edgeColor(state) {
  return EDGE_STYLE[state] || EDGE_STYLE.idle
}

function providerTone(executor) {
  if (!executor) return PROVIDER_STYLE.builtin
  if (executor.kind === 'builtin') return PROVIDER_STYLE.builtin
  return PROVIDER_STYLE[executor.provider] || 'border-violet-500/30 bg-violet-500/10 text-violet-200 shadow-violet-950/30'
}

function gateTone(status) {
  if (status === 'pass') return 'bg-emerald-500/10 text-emerald-300 ring-emerald-500/20'
  if (status === 'fail') return 'bg-rose-500/10 text-rose-300 ring-rose-500/20'
  return 'bg-slate-700/30 text-slate-400 ring-white/5'
}

function describePlacement(workflow, placementId) {
  return workflow?.placements?.find((placement) => placement.placement_id === placementId)?.name || placementId || '—'
}

function GraphNode({ placement, selected, editable, onSelect, onPointerDown }) {
  const executor = placement.executor
  const builtin = executor?.kind === 'builtin'
  return (
    <button
      type="button"
      onClick={() => onSelect(placement.placement_id)}
      onMouseDown={editable ? (event) => onPointerDown(event, placement.placement_id) : undefined}
      className={`absolute w-40 rounded-2xl border px-4 py-3 text-left shadow-xl transition ${
        selected ? 'ring-2 ring-amber-400/80' : 'ring-1 ring-transparent'
      } ${providerTone(executor)}`}
      style={{ left: placement.x, top: placement.y, cursor: editable ? 'grab' : 'pointer' }}
    >
      <div className="mb-2 flex items-start justify-between gap-2">
        <span
          className={`inline-flex h-8 w-8 items-center justify-center rounded-xl border border-white/10 bg-black/20 text-xs font-semibold uppercase ${
            builtin ? 'rotate-45 rounded-sm' : ''
          }`}
        >
          <span className={builtin ? '-rotate-45' : ''}>{builtin ? 'B' : (executor?.provider || 'E').slice(0, 1)}</span>
        </span>
        <span className={`rounded-full px-2 py-0.5 text-[10px] font-semibold ring-1 ring-inset ${statusTone(placement.status)}`}>
          {placement.status.replace(/_/g, ' ')}
        </span>
      </div>
      <div className="text-sm font-semibold text-slate-100">{placement.name}</div>
      <div className="mt-1 text-[11px] uppercase tracking-[0.16em] text-slate-400">{executorLabel(executor)}</div>
      <div className="mt-2 flex items-center justify-between text-[11px] text-slate-400">
        <span>{placement.placement_id}</span>
        <span>{placement.interactivity}</span>
      </div>
    </button>
  )
}

function GraphCanvas({ workflow, mode, selectedPlacementId, onSelectPlacement, onPointerDown }) {
  const positions = Object.fromEntries((workflow?.placements ?? []).map((placement) => [placement.placement_id, placement]))

  return (
    <div className="relative min-h-[640px] overflow-hidden rounded-[28px] border border-white/5 bg-[radial-gradient(circle_at_top_left,_rgba(249,115,22,0.12),_transparent_30%),linear-gradient(180deg,_rgba(15,23,42,0.8),_rgba(2,6,23,0.96))]">
      <div className="absolute inset-0 bg-[linear-gradient(rgba(148,163,184,0.07)_1px,transparent_1px),linear-gradient(90deg,rgba(148,163,184,0.07)_1px,transparent_1px)] bg-[size:48px_48px]" />
      <svg className="absolute inset-0 h-full w-full">
        {(workflow?.edges ?? []).map((edge, index) => {
          const from = positions[edge.from_placement_id]
          const to = positions[edge.to_placement_id]
          if (!from || !to) return null
          const x1 = from.x + 160
          const y1 = from.y + 48
          const x2 = to.x
          const y2 = to.y + 48
          const midX = (x1 + x2) / 2
          const midY = (y1 + y2) / 2
          return (
            <g key={`${edge.from_placement_id}-${edge.to_placement_id}-${index}`}>
              <path
                d={`M ${x1} ${y1} C ${midX} ${y1}, ${midX} ${y2}, ${x2} ${y2}`}
                className={`${edgeColor(edge.state)} fill-none`}
                strokeWidth="3"
                strokeLinecap="round"
                strokeDasharray={edge.state === 'awaiting_confirm' ? '8 7' : undefined}
              />
              <text x={midX} y={midY - 8} textAnchor="middle" className="fill-slate-400 text-[11px] uppercase tracking-[0.16em]">
                {edge.label || edge.advance}
              </text>
            </g>
          )
        })}
      </svg>
      {(workflow?.placements ?? []).map((placement) => (
        <GraphNode
          key={placement.placement_id}
          placement={placement}
          selected={selectedPlacementId === placement.placement_id}
          editable={mode === 'author'}
          onSelect={onSelectPlacement}
          onPointerDown={onPointerDown}
        />
      ))}
      {(workflow?.placements ?? []).length === 0 && (
        <div className="absolute inset-0 grid place-items-center text-center">
          <div>
            <div className="text-sm font-medium text-slate-300">No placements yet</div>
            <div className="mt-1 text-xs text-slate-500">Add a node from the palette to author a workflow.</div>
          </div>
        </div>
      )}
    </div>
  )
}

export default function WorkflowCanvas({ workflowCanvas, live }) {
  const { addToast } = useToast()
  const availableNodes = workflowCanvas?.available_nodes ?? []
  const incomingWorkflows = useMemo(
    () => (workflowCanvas?.workflows ?? []).map(normalizeWorkflow).filter(Boolean),
    [workflowCanvas],
  )
  const [mode, setMode] = useState('author')
  const [workflows, setWorkflows] = useState(incomingWorkflows)
  const [selectedWorkflowId, setSelectedWorkflowId] = useState(incomingWorkflows[0]?.workflow_id ?? null)
  const [selectedPlacementId, setSelectedPlacementId] = useState(incomingWorkflows[0]?.placements?.[0]?.placement_id ?? null)
  const [saveFormat, setSaveFormat] = useState('.yaml')
  const [edgeDraft, setEdgeDraft] = useState({
    from_placement_id: '',
    to_placement_id: '',
    from_output: 'agents/artifacts/output.md',
    to_input: 'agents/artifacts/output.md',
    guard_label: '',
    guard_condition: '',
    advance: 'allow',
  })
  const [prompts, setPrompts] = useState({})
  const dragState = useRef(null)

  useEffect(() => {
    setWorkflows(incomingWorkflows)
    setSelectedWorkflowId((current) => {
      if (current && incomingWorkflows.some((workflow) => workflow.workflow_id === current)) return current
      return incomingWorkflows[0]?.workflow_id ?? null
    })
  }, [incomingWorkflows])

  const workflow = useMemo(
    () => workflows.find((item) => item.workflow_id === selectedWorkflowId) ?? null,
    [workflows, selectedWorkflowId],
  )

  useEffect(() => {
    if (!workflow) {
      setSelectedPlacementId(null)
      return
    }
    setSelectedPlacementId((current) => {
      if (current && workflow.placements.some((placement) => placement.placement_id === current)) return current
      return workflow.placements[0]?.placement_id ?? null
    })
    setEdgeDraft((current) => ({
      ...current,
      from_placement_id: current.from_placement_id || workflow.placements[0]?.placement_id || '',
      to_placement_id: current.to_placement_id || workflow.placements[1]?.placement_id || '',
    }))
  }, [workflow])

  useEffect(() => {
    if (!workflow) return
    setPrompts((current) => {
      const next = { ...current }
      for (const placement of workflow.placements) {
        if (!next[placement.placement_id]) {
          next[placement.placement_id] = `Execute workflow step ${placement.name}.`
        }
      }
      return next
    })
  }, [workflow])

  useEffect(() => {
    function onMove(event) {
      if (!dragState.current) return
      const { workflowId, placementId, offsetX, offsetY } = dragState.current
      setWorkflows((current) =>
        current.map((item) => {
          if (item.workflow_id !== workflowId) return item
          return {
            ...item,
            placements: item.placements.map((placement) =>
              placement.placement_id === placementId
                ? {
                    ...placement,
                    x: Math.max(24, event.clientX - offsetX),
                    y: Math.max(24, event.clientY - offsetY - 72),
                  }
                : placement,
            ),
          }
        }),
      )
    }

    function onUp() {
      dragState.current = null
    }

    window.addEventListener('mousemove', onMove)
    window.addEventListener('mouseup', onUp)
    return () => {
      window.removeEventListener('mousemove', onMove)
      window.removeEventListener('mouseup', onUp)
    }
  }, [])

  const selectedPlacement = workflow?.placements.find((placement) => placement.placement_id === selectedPlacementId) ?? null

  function updateWorkflow(mutator) {
    if (!workflow) return
    setWorkflows((current) =>
      current.map((item) => (item.workflow_id === workflow.workflow_id ? normalizeWorkflow(mutator(item)) : item)),
    )
  }

  function createWorkflow() {
    const created = normalizeWorkflow({
      workflow_id: nextWorkflowId(workflows),
      version: 1,
      run: { workflow_run_id: null, status: null },
      placements: [],
      edges: [],
    })
    setWorkflows((current) => [...current, created])
    setSelectedWorkflowId(created.workflow_id)
    setSelectedPlacementId(null)
  }

  function addPlacement(node) {
    if (!workflow) return
    const placementId = nextPlacementId(workflow, node.node_id)
    updateWorkflow((current) => ({
      ...current,
      placements: [
        ...current.placements,
        {
          placement_id: placementId,
          node_id: node.node_id,
          name: node.name,
          x: 64 + current.placements.length * 180,
          y: 120 + (current.placements.length % 2) * 120,
          interactivity: 'afk',
          executor: node.executor,
          status: 'not_started',
          detail: { gates: [], artifacts: [], transcript: [], trace: [], failures: [], spawn_card: null },
        },
      ],
    }))
    setSelectedPlacementId(placementId)
    setEdgeDraft((current) => ({ ...current, from_placement_id: current.from_placement_id || placementId }))
  }

  function addEdge() {
    if (!workflow || !edgeDraft.from_placement_id || !edgeDraft.to_placement_id) return
    updateWorkflow((current) => ({
      ...current,
      edges: [
        ...current.edges,
        {
          from_placement_id: edgeDraft.from_placement_id,
          to_placement_id: edgeDraft.to_placement_id,
          from_output: edgeDraft.from_output.trim(),
          to_input: edgeDraft.to_input.trim(),
          advance: edgeDraft.advance,
          guard: edgeDraft.guard_condition.trim()
            ? {
                condition: edgeDraft.guard_condition.trim(),
                label: edgeDraft.guard_label.trim() || null,
              }
            : null,
          label: edgeDraft.guard_label.trim() || null,
          state: 'idle',
        },
      ],
    }))
  }

  function removePlacement() {
    if (!workflow || !selectedPlacementId) return
    updateWorkflow((current) => ({
      ...current,
      placements: current.placements.filter((placement) => placement.placement_id !== selectedPlacementId),
      edges: current.edges.filter(
        (edge) =>
          edge.from_placement_id !== selectedPlacementId && edge.to_placement_id !== selectedPlacementId,
      ),
    }))
    setSelectedPlacementId(null)
  }

  async function persistWorkflow() {
    if (!workflow) return
    if (!hasBridge()) {
      addToast({
        id: `${workflow.workflow_id}:saved`,
        severity: 'info',
        message: `Saved ${workflow.workflow_id} in preview mode.`,
        allowCorrection: false,
      })
      return
    }
    const result = await saveWorkflow(
      {
        workflow_id: workflow.workflow_id,
        version: workflow.version,
        placements: workflow.placements.map((placement) => ({
          placement_id: placement.placement_id,
          node_id: placement.node_id,
          x: Math.round(placement.x),
          y: Math.round(placement.y),
          interactivity: placement.interactivity,
        })),
        edges: workflow.edges.map((edge) => ({
          from_placement_id: edge.from_placement_id,
          from_output: edge.from_output,
          to_placement_id: edge.to_placement_id,
          to_input: edge.to_input,
          advance: edge.advance,
          guard: edge.guard,
        })),
      },
      saveFormat,
    )
    if (result?.workflow) {
      setWorkflows((current) =>
        current.map((item) =>
          item.workflow_id === workflow.workflow_id ? normalizeWorkflow(result.workflow) : item,
        ),
      )
    }
    addToast({
      id: `${workflow.workflow_id}:saved:${saveFormat}`,
      severity: 'ok',
      message: `Saved ${workflow.workflow_id} to ${saveFormat}.`,
      allowCorrection: false,
    })
  }

  async function launchWorkflow() {
    if (!workflow) return
    if (!hasBridge()) {
      addToast({
        id: `${workflow.workflow_id}:preview-run`,
        severity: 'info',
        message: 'Preview mode uses static mock run-state. Open the desktop app for live execution.',
        allowCorrection: false,
      })
      return
    }
    await runWorkflow(
      workflow.workflow_id,
      Object.fromEntries(workflow.placements.map((placement) => [placement.placement_id, prompts[placement.placement_id] || ''])),
    )
  }

  function onPointerDown(event, placementId) {
    dragState.current = {
      workflowId: workflow.workflow_id,
      placementId,
      offsetX: event.nativeEvent.offsetX,
      offsetY: event.nativeEvent.offsetY,
    }
  }

  return (
    <div className="grid grid-cols-1 gap-4 xl:grid-cols-[320px_1fr_360px]">
      <aside className={`${PANEL} space-y-4 p-4`}>
        <div className="flex items-center justify-between">
          <div>
            <div className="text-sm font-semibold text-slate-100">Workflow canvas</div>
            <div className="text-xs text-slate-500">{live ? 'Desktop bridge connected' : 'Preview mode with mock data'}</div>
          </div>
          <button
            type="button"
            onClick={createWorkflow}
            className="rounded-lg border border-white/10 px-3 py-1.5 text-xs font-medium text-slate-300 hover:bg-white/5"
          >
            New graph
          </button>
        </div>

        <div className="grid grid-cols-2 gap-2 rounded-xl bg-black/20 p-1">
          {['author', 'run'].map((value) => (
            <button
              key={value}
              type="button"
              onClick={() => setMode(value)}
              className={`rounded-lg px-3 py-2 text-xs font-semibold uppercase tracking-[0.2em] ${
                mode === value ? 'bg-white/10 text-slate-100' : 'text-slate-500 hover:text-slate-300'
              }`}
            >
              {value}
            </button>
          ))}
        </div>

        <Field label="Workflow">
          <select
            value={selectedWorkflowId || ''}
            onChange={(event) => setSelectedWorkflowId(event.target.value)}
            className={INPUT}
          >
            {(workflows ?? []).map((item) => (
              <option key={item.workflow_id} value={item.workflow_id} className="bg-[#0b0e14]">
                {item.workflow_id}
              </option>
            ))}
          </select>
        </Field>

        <div className="grid grid-cols-2 gap-2">
          <Field label="Save format">
            <select value={saveFormat} onChange={(event) => setSaveFormat(event.target.value)} className={INPUT}>
              {['.yaml', '.json'].map((value) => (
                <option key={value} value={value} className="bg-[#0b0e14]">
                  {value}
                </option>
              ))}
            </select>
          </Field>
          <Field label="Run status">
            <div className={`${INPUT} flex items-center text-xs capitalize`}>
              {workflow?.run?.status ? workflow.run.status.replace(/_/g, ' ') : 'idle'}
            </div>
          </Field>
        </div>

        {mode === 'author' ? (
          <>
            <div className="space-y-2">
              <div className="text-xs uppercase tracking-[0.18em] text-slate-500">Node palette</div>
              <div className="space-y-2">
                {availableNodes.map((node) => (
                  <button
                    key={node.node_id}
                    type="button"
                    onClick={() => addPlacement(node)}
                    className={`w-full rounded-xl border px-3 py-3 text-left ${providerTone(node.executor)}`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-semibold text-slate-100">{node.name}</span>
                      <span className="font-mono text-[11px] text-slate-400">{node.node_id}</span>
                    </div>
                    <div className="mt-1 text-[11px] uppercase tracking-[0.16em] text-slate-400">
                      {executorLabel(node.executor)}
                    </div>
                  </button>
                ))}
              </div>
            </div>

            <div className="space-y-3 rounded-xl border border-white/5 bg-black/20 p-3">
              <div className="text-xs uppercase tracking-[0.18em] text-slate-500">Wire edge</div>
              <Field label="From">
                <select
                  value={edgeDraft.from_placement_id}
                  onChange={(event) => setEdgeDraft((current) => ({ ...current, from_placement_id: event.target.value }))}
                  className={INPUT}
                >
                  <option value="" className="bg-[#0b0e14]">Choose a source</option>
                  {(workflow?.placements ?? []).map((placement) => (
                    <option key={placement.placement_id} value={placement.placement_id} className="bg-[#0b0e14]">
                      {placement.name}
                    </option>
                  ))}
                </select>
              </Field>
              <Field label="To">
                <select
                  value={edgeDraft.to_placement_id}
                  onChange={(event) => setEdgeDraft((current) => ({ ...current, to_placement_id: event.target.value }))}
                  className={INPUT}
                >
                  <option value="" className="bg-[#0b0e14]">Choose a target</option>
                  {(workflow?.placements ?? []).map((placement) => (
                    <option key={placement.placement_id} value={placement.placement_id} className="bg-[#0b0e14]">
                      {placement.name}
                    </option>
                  ))}
                </select>
              </Field>
              <Field label="Artifact path">
                <input
                  value={edgeDraft.from_output}
                  onChange={(event) =>
                    setEdgeDraft((current) => ({
                      ...current,
                      from_output: event.target.value,
                      to_input: event.target.value,
                    }))
                  }
                  className={INPUT}
                />
              </Field>
              <div className="grid grid-cols-2 gap-2">
                <Field label="Advance">
                  <select
                    value={edgeDraft.advance}
                    onChange={(event) => setEdgeDraft((current) => ({ ...current, advance: event.target.value }))}
                    className={INPUT}
                  >
                    {['allow', 'ask'].map((value) => (
                      <option key={value} value={value} className="bg-[#0b0e14]">
                        {value}
                      </option>
                    ))}
                  </select>
                </Field>
                <Field label="Guard label">
                  <input
                    value={edgeDraft.guard_label}
                    onChange={(event) => setEdgeDraft((current) => ({ ...current, guard_label: event.target.value }))}
                    className={INPUT}
                    placeholder="optional"
                  />
                </Field>
              </div>
              <Field label="Guard condition">
                <input
                  value={edgeDraft.guard_condition}
                  onChange={(event) => setEdgeDraft((current) => ({ ...current, guard_condition: event.target.value }))}
                  className={INPUT}
                  placeholder="needs_review()"
                />
              </Field>
              <button
                type="button"
                onClick={addEdge}
                className="w-full rounded-lg bg-gradient-to-br from-orange-500 to-amber-600 px-3 py-2 text-sm font-semibold text-black hover:opacity-90"
              >
                Add edge
              </button>
            </div>

            <div className="flex gap-2">
              <button
                type="button"
                onClick={persistWorkflow}
                disabled={!workflow}
                className="flex-1 rounded-lg bg-gradient-to-br from-emerald-500 to-lime-500 px-3 py-2 text-sm font-semibold text-black hover:opacity-90 disabled:opacity-40"
              >
                Save workflow
              </button>
              <button
                type="button"
                onClick={removePlacement}
                disabled={!selectedPlacement}
                className="rounded-lg border border-white/10 px-3 py-2 text-sm font-medium text-slate-300 hover:bg-white/5 disabled:opacity-40"
              >
                Remove node
              </button>
            </div>
          </>
        ) : (
          <div className="space-y-3">
            <button
              type="button"
              onClick={launchWorkflow}
              disabled={!workflow}
              className="w-full rounded-lg bg-gradient-to-br from-orange-500 to-amber-600 px-3 py-2 text-sm font-semibold text-black hover:opacity-90 disabled:opacity-40"
            >
              Start workflow run
            </button>
            <div className="rounded-xl border border-white/5 bg-black/20 p-3 text-xs text-slate-400">
              Run mode overlays live node state from the desktop snapshot. Select a node to inspect gates, artifacts,
              transcript, and trace.
            </div>
          </div>
        )}
      </aside>

      <section className={`${PANEL} overflow-hidden p-4`}>
        <div className="mb-3 flex items-center justify-between">
          <div>
            <div className="text-sm font-semibold text-slate-100">{workflow?.workflow_id || 'No workflow selected'}</div>
            <div className="text-xs text-slate-500">Author mode drags nodes; run mode shows edge and node overlay states.</div>
          </div>
          <div className="rounded-full border border-white/10 px-3 py-1 text-[11px] uppercase tracking-[0.18em] text-slate-400">
            {mode}
          </div>
        </div>
        <GraphCanvas
          workflow={workflow}
          mode={mode}
          selectedPlacementId={selectedPlacementId}
          onSelectPlacement={setSelectedPlacementId}
          onPointerDown={onPointerDown}
        />
      </section>

      <aside className={`${PANEL} space-y-4 p-4`}>
        {selectedPlacement ? (
          <>
            <div>
              <div className="flex items-center justify-between gap-3">
                <div>
                  <div className="text-sm font-semibold text-slate-100">{selectedPlacement.name}</div>
                  <div className="mt-1 text-[11px] uppercase tracking-[0.18em] text-slate-500">
                    {executorLabel(selectedPlacement.executor)} · {selectedPlacement.placement_id}
                  </div>
                </div>
                <span className={`rounded-full px-2.5 py-1 text-[11px] font-semibold ring-1 ring-inset ${statusTone(selectedPlacement.status)}`}>
                  {selectedPlacement.status.replace(/_/g, ' ')}
                </span>
              </div>
            </div>

            <Field label="Interactivity">
              <select
                value={selectedPlacement.interactivity}
                onChange={(event) =>
                  updateWorkflow((current) => ({
                    ...current,
                    placements: current.placements.map((placement) =>
                      placement.placement_id === selectedPlacement.placement_id
                        ? { ...placement, interactivity: event.target.value }
                        : placement,
                    ),
                  }))
                }
                className={INPUT}
                disabled={mode !== 'author'}
              >
                {['afk', 'hitl'].map((value) => (
                  <option key={value} value={value} className="bg-[#0b0e14]">
                    {value}
                  </option>
                ))}
              </select>
            </Field>

            <Field label="Run prompt">
              <textarea
                value={prompts[selectedPlacement.placement_id] || ''}
                onChange={(event) =>
                  setPrompts((current) => ({ ...current, [selectedPlacement.placement_id]: event.target.value }))
                }
                rows={4}
                className={`${INPUT} resize-y font-mono text-[12px]`}
              />
            </Field>

            <div className="space-y-2">
              <div className="text-xs uppercase tracking-[0.18em] text-slate-500">Gate checklist</div>
              <div className="space-y-2">
                {(selectedPlacement.detail?.gates ?? []).length === 0 ? (
                  <div className="rounded-xl border border-white/5 bg-black/20 px-3 py-3 text-sm text-slate-500">
                    No gate details yet.
                  </div>
                ) : (
                  selectedPlacement.detail.gates.map((gate, index) => (
                    <div
                      key={`${gate.kind}-${gate.label}-${index}`}
                      className="flex items-center justify-between rounded-xl border border-white/5 bg-black/20 px-3 py-2.5"
                    >
                      <div>
                        <div className="text-sm text-slate-200">{gate.label}</div>
                        <div className="text-[11px] uppercase tracking-[0.18em] text-slate-500">{gate.kind}</div>
                      </div>
                      <span className={`rounded-full px-2 py-0.5 text-[10px] font-semibold ring-1 ring-inset ${gateTone(gate.status)}`}>
                        {gate.status}
                      </span>
                    </div>
                  ))
                )}
              </div>
            </div>

            <div className="space-y-2">
              <div className="text-xs uppercase tracking-[0.18em] text-slate-500">Produced artifacts</div>
              <div className="space-y-2">
                {(selectedPlacement.detail?.artifacts ?? []).length === 0 ? (
                  <div className="rounded-xl border border-white/5 bg-black/20 px-3 py-3 text-sm text-slate-500">
                    No artifacts recorded.
                  </div>
                ) : (
                  selectedPlacement.detail.artifacts.map((artifact) => (
                    <div key={artifact.path} className="rounded-xl border border-white/5 bg-black/20 p-3">
                      <div className="flex items-center justify-between gap-3">
                        <div className="truncate font-mono text-[11px] text-slate-400">{artifact.path}</div>
                        <span className={`rounded-full px-2 py-0.5 text-[10px] font-semibold ${
                          artifact.exists ? 'bg-emerald-500/10 text-emerald-300' : 'bg-slate-700/40 text-slate-400'
                        }`}>
                          {artifact.exists ? 'present' : 'missing'}
                        </span>
                      </div>
                      {artifact.preview && (
                        <pre className="mt-2 overflow-auto rounded-lg bg-[#06080d] p-2 text-[11px] text-slate-300">
                          {artifact.preview}
                        </pre>
                      )}
                    </div>
                  ))
                )}
              </div>
            </div>

            <div className="space-y-2">
              <div className="text-xs uppercase tracking-[0.18em] text-slate-500">Conversation + trace</div>
              <div className="space-y-2">
                {(selectedPlacement.detail?.transcript ?? []).map((turn) => (
                  <div key={turn.id} className="rounded-xl border border-white/5 bg-black/20 p-3">
                    <div className="mb-1 text-[11px] uppercase tracking-[0.18em] text-slate-500">{turn.role} · {turn.kind || 'text'}</div>
                    <div className="whitespace-pre-wrap text-sm text-slate-200">{turn.text}</div>
                  </div>
                ))}
                {(selectedPlacement.detail?.trace ?? []).map((event) => (
                  <div key={event.id} className="rounded-xl border border-white/5 bg-black/20 p-3">
                    <div className="mb-1 text-[11px] uppercase tracking-[0.18em] text-slate-500">{event.action}</div>
                    <div className="font-mono text-[11px] text-slate-400">{event.target_path || 'no target path'}</div>
                  </div>
                ))}
                {(selectedPlacement.detail?.transcript ?? []).length === 0 && (selectedPlacement.detail?.trace ?? []).length === 0 && (
                  <div className="rounded-xl border border-white/5 bg-black/20 px-3 py-3 text-sm text-slate-500">
                    No run transcript yet.
                  </div>
                )}
              </div>
            </div>

            {selectedPlacement.detail?.spawn_card && (
              <div className="rounded-xl border border-white/5 bg-black/20 p-3">
                <div className="text-xs uppercase tracking-[0.18em] text-slate-500">Next edge</div>
                <div className="mt-2 text-sm text-slate-200">
                  {describePlacement(workflow, selectedPlacement.detail.spawn_card.marker.role)}
                </div>
                <div className="mt-1 font-mono text-[11px] text-slate-400">
                  {selectedPlacement.detail.spawn_card.marker.task}
                </div>
              </div>
            )}
          </>
        ) : (
          <div className="grid min-h-[320px] place-items-center text-center">
            <div>
              <div className="text-sm font-medium text-slate-300">Select a node</div>
              <div className="mt-1 text-xs text-slate-500">Drill-in details render here for gates, artifacts, transcript, and trace.</div>
            </div>
          </div>
        )}
      </aside>
    </div>
  )
}
