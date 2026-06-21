import { useEffect, useState } from 'react'
import { listRepos, treeOf, readFile } from '../api.js'
import { CODE_MOCK } from '../mock.js'
import Highlight from './Highlight.jsx'

// Bridge calls fall back to mock data when running in a plain browser.
async function apiRepos() {
  return (await listRepos()) ?? CODE_MOCK.repos
}
async function apiTree(repo, path) {
  return (await treeOf(repo, path)) ?? CODE_MOCK.tree[path] ?? []
}
async function apiRead(repo, path) {
  return (await readFile(repo, path)) ?? CODE_MOCK.files[path] ?? null
}

function TreeNode({ repo, entry, depth, onOpen, selected }) {
  const [open, setOpen] = useState(false)
  const [children, setChildren] = useState(null)

  async function toggle() {
    if (entry.type !== 'dir') {
      onOpen(entry)
      return
    }
    const next = !open
    setOpen(next)
    if (next && children === null) setChildren(await apiTree(repo, entry.path))
  }

  const isSel = selected === entry.path
  return (
    <div>
      <button
        onClick={toggle}
        style={{ paddingLeft: depth * 12 + 10 }}
        className={`flex w-full items-center gap-1.5 py-1 pr-2 text-left text-[13px] hover:bg-white/5 ${
          isSel ? 'bg-white/10 text-slate-100' : 'text-slate-300'
        }`}
      >
        <span className="w-3 text-slate-500">
          {entry.type === 'dir' ? (open ? '▾' : '▸') : ''}
        </span>
        <span className="truncate">{entry.name}</span>
      </button>
      {open && children && children.map((c) => (
        <TreeNode key={c.path} repo={repo} entry={c} depth={depth + 1} onOpen={onOpen} selected={selected} />
      ))}
    </div>
  )
}

export default function CodeView() {
  const [repos, setRepos] = useState([])
  const [repo, setRepo] = useState(null)
  const [roots, setRoots] = useState([])
  const [file, setFile] = useState(null)

  useEffect(() => {
    (async () => {
      const rs = await apiRepos()
      setRepos(rs)
      if (rs[0]) {
        setRepo(rs[0].name)
        setRoots(await apiTree(rs[0].name, ''))
      }
    })()
  }, [])

  async function changeRepo(name) {
    setRepo(name)
    setFile(null)
    setRoots(await apiTree(name, ''))
  }

  async function openEntry(entry) {
    if (entry.type === 'file') setFile(await apiRead(repo, entry.path))
  }

  return (
    <div className="grid grid-cols-[280px_1fr] gap-4">
      <aside className="overflow-hidden rounded-2xl border border-white/5 bg-white/[0.02]">
        <div className="border-b border-white/5 px-3 py-2">
          <select
            value={repo || ''}
            onChange={(e) => changeRepo(e.target.value)}
            className="w-full bg-transparent text-sm text-slate-200 outline-none"
          >
            {repos.map((r) => (
              <option key={r.name} value={r.name} className="bg-[#0b0e14]">{r.name}</option>
            ))}
          </select>
        </div>
        <div className="max-h-[72vh] overflow-auto py-1">
          {roots.map((e) => (
            <TreeNode key={e.path} repo={repo} entry={e} depth={0} onOpen={openEntry} selected={file?.path} />
          ))}
        </div>
      </aside>

      <section className="overflow-hidden rounded-2xl border border-white/5 bg-white/[0.02]">
        {!file ? (
          <p className="px-5 py-12 text-center text-sm text-slate-500">Select a file to view.</p>
        ) : file.binary ? (
          <p className="px-5 py-12 text-center text-sm text-slate-500">Binary file ({file.size} bytes) — not shown.</p>
        ) : file.truncated ? (
          <p className="px-5 py-12 text-center text-sm text-slate-500">File too large to display ({file.size} bytes).</p>
        ) : (
          <>
            <header className="flex items-center justify-between border-b border-white/5 px-4 py-2.5">
              <span className="truncate font-mono text-xs text-slate-400">{file.path}</span>
              <span className="shrink-0 pl-3 text-[11px] text-slate-600">{file.language} · {file.size} B</span>
            </header>
            <Highlight code={file.content} language={file.language} />
          </>
        )}
      </section>
    </div>
  )
}
