import { useMemo, useState } from 'react'

const INPUT =
  'w-full rounded-lg border border-white/10 bg-black/20 px-2.5 py-1.5 text-sm text-slate-200 outline-none focus:border-white/25'

function labelForBinding(binding, artifacts) {
  const artifact = artifacts.find((item) => item.artifact_id === binding)
  if (!artifact) return binding
  return `${artifact.name} (${artifact.artifact_id})`
}

export default function ArtifactBindingEditor({
  label,
  value,
  onChange,
  artifacts = [],
  placeholder,
}) {
  const [artifactDraft, setArtifactDraft] = useState('')
  const [pathDraft, setPathDraft] = useState('')
  const artifactOptions = useMemo(
    () => artifacts.filter((artifact) => !value.includes(artifact.artifact_id)),
    [artifacts, value],
  )

  function removeItem(index) {
    onChange(value.filter((_, itemIndex) => itemIndex !== index))
  }

  function addArtifact() {
    if (!artifactDraft || value.includes(artifactDraft)) return
    onChange([...value, artifactDraft])
    setArtifactDraft('')
  }

  function addPath() {
    const next = pathDraft.trim()
    if (!next || value.includes(next)) return
    onChange([...value, next])
    setPathDraft('')
  }

  return (
    <label className="block">
      <span className="mb-1 block text-xs uppercase tracking-wider text-slate-500">{label}</span>
      <div className="space-y-2">
        <div className="flex flex-wrap gap-1.5">
          {value.length ? (
            value.map((item, index) => {
              const artifact = artifacts.find((entry) => entry.artifact_id === item)
              return (
                <span
                  key={`${item}-${index}`}
                  className="inline-flex items-center gap-1 rounded-full border border-white/10 bg-white/5 px-2 py-1 text-[11px] text-slate-300"
                >
                  <span className="rounded-full bg-white/10 px-1.5 py-0.5 text-[10px] uppercase tracking-[0.18em] text-slate-500">
                    {artifact ? 'artifact' : 'path'}
                  </span>
                  <span className="font-mono">{labelForBinding(item, artifacts)}</span>
                  <button
                    type="button"
                    onClick={() => removeItem(index)}
                    className="text-slate-500 hover:text-rose-300"
                    aria-label={`Remove ${item}`}
                  >
                    x
                  </button>
                </span>
              )
            })
          ) : (
            <span className="text-xs text-slate-600">No bindings yet.</span>
          )}
        </div>

        <div className="grid gap-2 md:grid-cols-[1fr_auto]">
          <select
            value={artifactDraft}
            onChange={(event) => setArtifactDraft(event.target.value)}
            className={INPUT}
            disabled={!artifactOptions.length}
          >
            <option value="" className="bg-[#0b0e14]">
              {artifactOptions.length ? 'Select an artifact definition' : 'No authored artifacts yet'}
            </option>
            {artifactOptions.map((artifact) => (
              <option key={artifact.artifact_id} value={artifact.artifact_id} className="bg-[#0b0e14]">
                {artifact.name} ({artifact.artifact_id})
              </option>
            ))}
          </select>
          <button
            type="button"
            onClick={addArtifact}
            disabled={!artifactDraft}
            className="rounded-lg border border-white/10 px-3 text-sm text-slate-300 hover:bg-white/5 disabled:opacity-40"
          >
            Add artifact
          </button>
        </div>

        <div className="grid gap-2 md:grid-cols-[1fr_auto]">
          <input
            value={pathDraft}
            onChange={(event) => setPathDraft(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === 'Enter') {
                event.preventDefault()
                addPath()
              }
            }}
            className={INPUT}
            placeholder={placeholder}
          />
          <button
            type="button"
            onClick={addPath}
            disabled={!pathDraft.trim()}
            className="rounded-lg border border-white/10 px-3 text-sm text-slate-300 hover:bg-white/5 disabled:opacity-40"
          >
            Add path
          </button>
        </div>
      </div>
    </label>
  )
}
