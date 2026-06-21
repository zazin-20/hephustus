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
