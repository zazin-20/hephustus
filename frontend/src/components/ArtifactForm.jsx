import { useEffect, useState } from 'react'

const INPUT =
  'w-full rounded-lg border border-white/10 bg-black/20 px-2.5 py-1.5 text-sm text-slate-200 outline-none focus:border-white/25'

function Field({ label, children, note = null }) {
  return (
    <label className="block">
      <span className="mb-1 block text-xs uppercase tracking-wider text-slate-500">{label}</span>
      {children}
      {note ? <span className="mt-1 block text-[11px] text-slate-500">{note}</span> : null}
    </label>
  )
}

function formFromArtifact(artifact) {
  return {
    name: artifact?.name ?? '',
    tags_input: (artifact?.tags ?? []).join(', '),
    headings: (artifact?.headings ?? []).map((heading) => ({
      heading: heading.heading ?? '',
      required: Boolean(heading.required),
      min_items: heading.min_items ?? '',
    })),
    good_looks_like: artifact?.good_looks_like ?? '',
    antipatterns: artifact?.antipatterns ?? '',
    examples: artifact?.examples ?? '',
  }
}

export default function ArtifactForm({
  initialArtifact = null,
  onSubmit,
  onCancel,
  submitLabel,
  title,
}) {
  const [form, setForm] = useState(() => formFromArtifact(initialArtifact))
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    setForm(formFromArtifact(initialArtifact))
    setBusy(false)
    setError('')
  }, [initialArtifact])

  function updateField(key, value) {
    setForm((current) => ({ ...current, [key]: value }))
  }

  function addHeading() {
    setForm((current) => ({
      ...current,
      headings: [...current.headings, { heading: '', required: true, min_items: '' }],
    }))
  }

  function updateHeading(index, key, value) {
    setForm((current) => ({
      ...current,
      headings: current.headings.map((heading, headingIndex) => (
        headingIndex === index ? { ...heading, [key]: value } : heading
      )),
    }))
  }

  function removeHeading(index) {
    setForm((current) => ({
      ...current,
      headings: current.headings.filter((_, headingIndex) => headingIndex !== index),
    }))
  }

  async function submit(event) {
    event.preventDefault()
    if (!form.name.trim() || busy) return

    setBusy(true)
    setError('')
    try {
      await onSubmit({
        name: form.name.trim(),
        tags: form.tags_input.split(',').map((tag) => tag.trim()).filter(Boolean),
        headings: form.headings
          .map((heading) => ({
            heading: heading.heading.trim(),
            required: Boolean(heading.required),
            min_items: heading.min_items === '' ? null : Number.parseInt(heading.min_items, 10) || null,
          }))
          .filter((heading) => heading.heading),
        good_looks_like: form.good_looks_like.trim(),
        antipatterns: form.antipatterns.trim(),
        examples: form.examples.trim(),
      })
    } catch (err) {
      setError(err?.message || 'Failed to save artifact.')
      setBusy(false)
    }
  }

  return (
    <form onSubmit={submit} className="space-y-3 rounded-xl border border-white/5 bg-black/20 p-3">
      <div>
        <div className="text-sm font-semibold text-slate-100">{title}</div>
        <div className="text-xs text-slate-500">
          Author an artifact definition that can be bound to node inputs and outputs.
        </div>
      </div>

      <Field label="Name">
        <input
          required
          value={form.name}
          onChange={(event) => updateField('name', event.target.value)}
          className={INPUT}
          placeholder="Release Checklist"
        />
      </Field>

      <Field label="Tags">
        <input
          value={form.tags_input}
          onChange={(event) => updateField('tags_input', event.target.value)}
          className={INPUT}
          placeholder="release, qa"
        />
      </Field>

      <Field
        label="Required Headings"
        note="Reserved sections are added automatically: Predicates, Good Looks Like, Antipatterns, and Examples."
      >
        <div className="space-y-2">
          {form.headings.length ? (
            form.headings.map((heading, index) => (
              <div key={`${heading.heading}-${index}`} className="rounded-xl border border-white/5 bg-black/30 p-3">
                <div className="grid gap-2 md:grid-cols-[1.5fr_auto_auto_auto]">
                  <input
                    value={heading.heading}
                    onChange={(event) => updateHeading(index, 'heading', event.target.value)}
                    className={INPUT}
                    placeholder="Acceptance Criteria"
                  />
                  <label className="flex items-center gap-2 rounded-lg border border-white/10 px-3 text-sm text-slate-300">
                    <input
                      type="checkbox"
                      checked={heading.required}
                      onChange={(event) => updateHeading(index, 'required', event.target.checked)}
                    />
                    Required
                  </label>
                  <input
                    type="number"
                    min="1"
                    value={heading.min_items}
                    onChange={(event) => updateHeading(index, 'min_items', event.target.value)}
                    className={INPUT}
                    placeholder="min items"
                  />
                  <button
                    type="button"
                    onClick={() => removeHeading(index)}
                    className="rounded-lg border border-white/10 px-3 text-sm text-slate-300 hover:border-rose-500/30 hover:text-rose-300"
                  >
                    Remove
                  </button>
                </div>
              </div>
            ))
          ) : (
            <div className="rounded-xl border border-dashed border-white/10 bg-black/20 px-3 py-4 text-sm text-slate-500">
              No heading rules yet.
            </div>
          )}
          <button
            type="button"
            onClick={addHeading}
            className="rounded-lg border border-white/10 px-3 py-2 text-sm text-slate-300 hover:bg-white/5"
          >
            Add heading
          </button>
        </div>
      </Field>

      <Field label="Best Practices">
        <textarea
          value={form.good_looks_like}
          onChange={(event) => updateField('good_looks_like', event.target.value)}
          className={`${INPUT} min-h-24`}
          placeholder="Describe what good looks like."
        />
      </Field>

      <Field label="Antipatterns">
        <textarea
          value={form.antipatterns}
          onChange={(event) => updateField('antipatterns', event.target.value)}
          className={`${INPUT} min-h-24`}
          placeholder="Describe what to avoid."
        />
      </Field>

      <Field label="Examples">
        <textarea
          value={form.examples}
          onChange={(event) => updateField('examples', event.target.value)}
          className={`${INPUT} min-h-24`}
          placeholder="Add examples or sample bullets."
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
