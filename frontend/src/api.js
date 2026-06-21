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
export async function runAgent(role, prompt, issue, cwd, model) {
  if (window.pywebview?.api?.run_agent) {
    return await window.pywebview.api.run_agent(role, prompt, issue || null, cwd || null, model || null)
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

// --- Coordinator / profiles ---
export async function listProfiles() {
  if (window.pywebview?.api?.list_profiles) return await window.pywebview.api.list_profiles()
  return null
}

export async function createProfile(name, role, rules, model, effort, workingDir) {
  if (window.pywebview?.api?.create_profile) {
    return await window.pywebview.api.create_profile(
      name,
      role,
      rules,
      model || null,
      effort || null,
      workingDir || null,
    )
  }
  return null
}

export async function deleteProfile(agentId) {
  if (window.pywebview?.api?.delete_profile) {
    return await window.pywebview.api.delete_profile(agentId)
  }
  return null
}

export async function getTrace(runId, agentId) {
  if (window.pywebview?.api?.get_trace)
    return await window.pywebview.api.get_trace(runId || null, agentId || null)
  return []
}
