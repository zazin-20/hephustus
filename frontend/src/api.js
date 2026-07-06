// Bridge to the Python core (spec/architecture.md §5.4).
// JS -> Python via window.pywebview.api; Python -> JS via window.__hephaestus_push__.

export function onPush(cb) {
  window.__hephaestus_push__ = cb
}

export function whenReady(cb) {
  if (window.pywebview && window.pywebview.api) { cb(); return }
  window.addEventListener('pywebviewready', cb, { once: true })
}

export async function getState() {
  if (window.pywebview?.api?.get_state) return await window.pywebview.api.get_state()
  return null
}

export async function rescan() {
  if (window.pywebview?.api?.rescan) return await window.pywebview.api.rescan()
  return null
}

export const hasBridge = () => Boolean(window.pywebview && window.pywebview.api)

// --- Workflow canvas ---

export async function listWorkflows() {
  if (window.pywebview?.api?.list_workflows) return await window.pywebview.api.list_workflows()
  return null
}

export async function saveWorkflow(payload, suffix = '.yaml') {
  if (window.pywebview?.api?.save_workflow) return await window.pywebview.api.save_workflow(payload, suffix)
  return null
}

export async function runWorkflow(workflowId, prompts = {}) {
  if (window.pywebview?.api?.run_workflow) return await window.pywebview.api.run_workflow(workflowId, prompts)
  return null
}

// --- Code viewer (read-only) ---
export async function listRepos() {
  if (window.pywebview?.api?.list_repos) return await window.pywebview.api.list_repos()
  return null
}

export async function treeOf(repo, subpath = '') {
  if (window.pywebview?.api?.tree) return await window.pywebview.api.tree(repo, subpath)
  return null
}

export async function readFile(repo, relpath) {
  if (window.pywebview?.api?.read_file) return await window.pywebview.api.read_file(repo, relpath)
  return null
}

// --- Agents (§5) ---
export async function runAgent(provider, tags, prompt, issue, cwd, model, effort = null) {
  if (window.pywebview?.api?.run_agent) {
    return await window.pywebview.api.run_agent(
      provider,
      tags,
      prompt,
      issue || null,
      cwd || null,
      model || null,
      effort || null,
    )
  }
  return null
}

export function onAgent(cb) {
  window.__hephaestus_agent__ = cb
}

export async function listThreads(agentId) {
  if (window.pywebview?.api?.list_threads) return await window.pywebview.api.list_threads(agentId)
  return null
}

export async function getTranscript(threadId) {
  if (window.pywebview?.api?.get_transcript) return await window.pywebview.api.get_transcript(threadId)
  return null
}

export async function sendMessage(agentId, prompt, issueId, model) {
  if (window.pywebview?.api?.send_message) {
    return await window.pywebview.api.send_message(agentId, prompt, issueId || null, model || null)
  }
  return null
}

// --- Coordinator / catalog + rules ---
export async function getCatalog() {
  if (window.pywebview?.api?.get_catalog) return await window.pywebview.api.get_catalog()
  return null
}

export async function listRules() {
  if (window.pywebview?.api?.list_rules) return await window.pywebview.api.list_rules()
  return null
}

export async function pickDirectory() {
  if (window.pywebview?.api?.pick_directory) return await window.pywebview.api.pick_directory()
  return null
}

// --- Coordinator / nodes ---
export async function listNodes() {
  if (window.pywebview?.api?.list_nodes) return await window.pywebview.api.list_nodes()
  return null
}

export async function createNode(
  name,
  provider,
  tags,
  rules,
  model,
  effort,
  workingDir,
  inputs = [],
  outputs = [],
  skills = [],
  skillObligations = [],
  allowedPaths = [],
  allowedTools = [],
  contextPolicy = null,
) {
  if (window.pywebview?.api?.create_node) {
    return await window.pywebview.api.create_node(
      name,
      provider,
      tags,
      rules,
      model || null,
      effort || null,
      workingDir || null,
      inputs,
      outputs,
      skills,
      skillObligations,
      allowedPaths,
      allowedTools,
      contextPolicy || null,
    )
  }
  return null
}

export async function updateNode(
  nodeId,
  name,
  provider,
  tags,
  rules,
  model,
  effort,
  workingDir,
  inputs = [],
  outputs = [],
  skills = [],
  skillObligations = [],
  allowedPaths = [],
  allowedTools = [],
  contextPolicy = null,
) {
  if (window.pywebview?.api?.update_node) {
    return await window.pywebview.api.update_node(
      nodeId,
      name,
      provider,
      tags,
      rules,
      model || null,
      effort || null,
      workingDir || null,
      inputs,
      outputs,
      skills,
      skillObligations,
      allowedPaths,
      allowedTools,
      contextPolicy || null,
    )
  }
  return null
}

export async function deleteNode(nodeId) {
  if (window.pywebview?.api?.delete_node) {
    return await window.pywebview.api.delete_node(nodeId)
  }
  return null
}

export async function setTurnIncluded(turnId, included) {
  if (window.pywebview?.api?.set_turn_included)
    return await window.pywebview.api.set_turn_included(turnId, included)
  return null
}

export async function getTrace(runId, nodeId, threadId) {
  if (window.pywebview?.api?.get_trace)
    return await window.pywebview.api.get_trace(runId || null, nodeId || null, threadId || null)
  return []
}

// --- Handoff / gated Spawn ---
export async function parseHandoffMarker(text) {
  if (window.pywebview?.api?.parse_handoff_marker)
    return await window.pywebview.api.parse_handoff_marker(text)
  return null
}

export async function evaluateSpawn(role, task, issueId) {
  if (window.pywebview?.api?.evaluate_spawn)
    return await window.pywebview.api.evaluate_spawn(role, task, issueId)
  return null
}

// --- Corrections ---
export async function saveCorrection(violationId, nodeId, issueId, note) {
  if (window.pywebview?.api?.save_correction)
    return await window.pywebview.api.save_correction(violationId, nodeId, issueId, note)
  return null
}

export async function getCorrections(nodeId, issueId) {
  if (window.pywebview?.api?.get_corrections)
    return await window.pywebview.api.get_corrections(nodeId || null, issueId || null)
  return []
}
