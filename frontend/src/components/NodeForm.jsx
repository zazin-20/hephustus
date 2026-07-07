import { useEffect, useMemo, useState } from 'react'
import ArtifactBindingEditor from './ArtifactBindingEditor.jsx'

const INPUT =
  'w-full rounded-lg border border-white/10 bg-black/20 px-2.5 py-1.5 text-sm text-slate-200 outline-none focus:border-white/25'

// Human-readable labels for the runtime governance rules. The G-00x id stays
// visible as a small tag (violations reference it) but the plain-language label
// leads, so a workflow author understands what each guardrail enforces.
const RULE_LABELS = {
  'G-001': 'Path scope',
  'G-002': 'Model lock',
  'G-003': 'Skill proof',
}

function Field({ label, children, note = null }) {
  return (
    <label className="block">
      <span className="mb-1 block text-xs uppercase tracking-wider text-slate-500">{label}</span>
      {children}
      {note ? <span className="mt-1 block text-[11px] text-slate-500">{note}</span> : null}
    </label>
  )
}

function ListEditor({ label, value, onChange, placeholder }) {
  const [draft, setDraft] = useState('')

  function addItem() {
    const next = draft.trim()
    if (!next) return
    if (value.includes(next)) {
      setDraft('')
      return
    }
    onChange([...value, next])
    setDraft('')
  }

  function removeItem(index) {
    onChange(value.filter((_, itemIndex) => itemIndex !== index))
  }

  return (
    <Field label={label}>
      <div className="space-y-2">
        <div className="flex flex-wrap gap-1.5">
          {value.length ? (
            value.map((item, index) => (
              <span
                key={`${item}-${index}`}
                className="inline-flex items-center gap-1 rounded-full border border-white/10 bg-white/5 px-2 py-1 text-[11px] text-slate-300"
              >
                <span className="font-mono">{item}</span>
                <button
                  type="button"
                  onClick={() => removeItem(index)}
                  className="text-slate-500 hover:text-rose-300"
                  aria-label={`Remove ${item}`}
                >
                  x
                </button>
              </span>
            ))
          ) : (
            <span className="text-xs text-slate-600">No entries yet.</span>
          )}
        </div>
        <div className="flex gap-2">
          <input
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === 'Enter') {
                event.preventDefault()
                addItem()
              }
            }}
            className={INPUT}
            placeholder={placeholder}
          />
          <button
            type="button"
            onClick={addItem}
            className="shrink-0 rounded-lg border border-white/10 px-3 text-sm text-slate-300 hover:bg-white/5"
          >
            Add
          </button>
        </div>
      </div>
    </Field>
  )
}

function formFromNode(node, catalog) {
  return {
    name: node?.name ?? '',
    provider: node?.provider ?? catalog.providers?.[0]?.provider ?? 'claude',
    tags_input: (node?.tags ?? []).join(', '),
    rules: [...(node?.rules ?? [])],
    model: node?.model ?? '',
    effort: node?.effort ?? '',
    working_dir: node?.working_dir ?? '',
    inputs: [...(node?.inputs ?? [])],
    outputs: [...(node?.outputs ?? [])],
    skills: [...(node?.skills ?? [])],
    skill_obligations: [...(node?.skill_obligations ?? [])],
    allowed_paths: [...(node?.allowed_paths ?? [])],
    allowed_tools: [...(node?.allowed_tools ?? [])],
    context_policy: node?.context_policy ?? '',
  }
}

export default function NodeForm({
  initialNode = null,
  catalog,
  ruleSet,
  artifacts = [],
  live,
  onSubmit,
  onCancel,
  onPickDirectory,
  submitLabel,
  title,
}) {
  const [form, setForm] = useState(() => formFromNode(initialNode, catalog))
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    setForm(formFromNode(initialNode, catalog))
    setError('')
    setBusy(false)
  }, [initialNode, catalog])

  const selectedModel = useMemo(
    () => catalog.providers.flatMap((group) => group.models).find((model) => model.id === form.model),
    [catalog, form.model],
  )
  const effortOptions = selectedModel?.efforts ?? []

  function updateField(key, value) {
    setForm((current) => ({ ...current, [key]: value }))
  }

  function toggleRule(ruleId) {
    setForm((current) => {
      const hasRule = current.rules.includes(ruleId)
      return {
        ...current,
        rules: hasRule
          ? current.rules.filter((item) => item !== ruleId)
          : [...current.rules, ruleId],
      }
    })
  }

  function selectModel(model) {
    setForm((current) => {
      const picked = catalog.providers.flatMap((group) => group.models).find((item) => item.id === model)
      const nextEffort = picked?.efforts?.includes(current.effort) ? current.effort : ''
      return { ...current, model, effort: nextEffort }
    })
  }

  async function browseDirectory() {
    if (!live || !onPickDirectory) return
    const chosen = await onPickDirectory()
    if (chosen) updateField('working_dir', chosen)
  }

  async function submit(event) {
    event.preventDefault()
    if (!form.name.trim() || busy) return

    setBusy(true)
    setError('')
    try {
      await onSubmit({
        name: form.name.trim(),
        provider: form.provider,
        tags: form.tags_input.split(',').map((tag) => tag.trim()).filter(Boolean),
        rules: form.rules,
        model: form.model || null,
        effort: form.effort || null,
        working_dir: form.working_dir.trim() || null,
        inputs: form.inputs,
        outputs: form.outputs,
        skills: form.skills,
        skill_obligations: form.skill_obligations,
        allowed_paths: form.allowed_paths,
        allowed_tools: form.allowed_tools,
        context_policy: form.context_policy || null,
      })
    } catch (err) {
      setError(err?.message || 'Failed to save node.')
      setBusy(false)
    }
  }

  return (
    <form onSubmit={submit} className="space-y-3 rounded-xl border border-white/5 bg-black/20 p-3">
      <div>
        <div className="text-sm font-semibold text-slate-100">{title}</div>
        <div className="text-xs text-slate-500">
          Full node contract authoring for the desktop coordinator.
        </div>
      </div>

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
          placeholder="architect, review"
        />
      </Field>

      <Field label="Rules" note="Runtime guardrails enforced against this node's authored config.">
        <div className="flex flex-wrap gap-1.5">
          {ruleSet.map((rule) => {
            const active = form.rules.includes(rule.id)
            return (
              <button
                key={rule.id}
                type="button"
                onClick={() => toggleRule(rule.id)}
                title={`${rule.id} — ${rule.name}`}
                className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-[11px] transition ${
                  active
                    ? 'border-orange-400/40 bg-orange-500/15 text-orange-200'
                    : 'border-white/10 bg-black/20 text-slate-400 hover:border-white/20 hover:text-slate-200'
                }`}
              >
                {RULE_LABELS[rule.id] || rule.name}
                <span className="font-mono text-[10px] opacity-50">{rule.id}</span>
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
          {live ? (
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

      <ArtifactBindingEditor
        label="Inputs"
        value={form.inputs}
        onChange={(value) => updateField('inputs', value)}
        artifacts={artifacts}
        placeholder="agents/specs/028.md"
      />
      <ArtifactBindingEditor
        label="Outputs"
        value={form.outputs}
        onChange={(value) => updateField('outputs', value)}
        artifacts={artifacts}
        placeholder="agents/handoffs/028.md"
      />
      <ListEditor
        label="Skills"
        value={form.skills}
        onChange={(value) => updateField('skills', value)}
        placeholder="skill:tdd"
      />
      <ListEditor
        label="Skill Obligations"
        value={form.skill_obligations}
        onChange={(value) => updateField('skill_obligations', value)}
        placeholder="skill:tdd"
      />
      <ListEditor
        label="Allowed Paths"
        value={form.allowed_paths}
        onChange={(value) => updateField('allowed_paths', value)}
        placeholder="frontend/src"
      />
      <ListEditor
        label="Allowed Tools"
        value={form.allowed_tools}
        onChange={(value) => updateField('allowed_tools', value)}
        placeholder="shell_command"
      />

      <Field
        label="Context Policy"
        note="Reserved - no runtime effect until context compression lands (see T-prompt-compression)"
      >
        <input
          value={form.context_policy}
          disabled
          readOnly
          className={`${INPUT} cursor-not-allowed opacity-50`}
          placeholder="reserved"
        />
      </Field>

      {error ? <div className="text-xs text-rose-300">{error}</div> : null}

      <div className="flex gap-2">
        <button
          type="submit"
          disabled={busy || !form.name.trim()}
          className="flex-1 rounded-lg bg-gradient-to-br from-orange-500 to-amber-600 px-3 py-2 text-sm font-semibold text-black hover:opacity-90 disabled:opacity-40"
        >
          {busy ? 'Saving...' : submitLabel}
        </button>
        <button
          type="button"
          onClick={onCancel}
          className="rounded-lg border border-white/10 px-3 py-2 text-sm font-medium text-slate-300 hover:bg-white/5"
        >
          Cancel
        </button>
      </div>
    </form>
  )
}
