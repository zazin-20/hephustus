import { useMemo } from 'react'
import hljs from 'highlight.js/lib/core'
import python from 'highlight.js/lib/languages/python'
import javascript from 'highlight.js/lib/languages/javascript'
import typescript from 'highlight.js/lib/languages/typescript'
import json from 'highlight.js/lib/languages/json'
import markdown from 'highlight.js/lib/languages/markdown'
import css from 'highlight.js/lib/languages/css'
import xml from 'highlight.js/lib/languages/xml'
import bash from 'highlight.js/lib/languages/bash'
import yaml from 'highlight.js/lib/languages/yaml'
import ini from 'highlight.js/lib/languages/ini'
import 'highlight.js/styles/github-dark.css'

for (const [name, lang] of Object.entries({
  python, javascript, typescript, json, markdown, css, xml, bash, yaml, ini,
})) {
  hljs.registerLanguage(name, lang)
}

function escapeHtml(s) {
  return s.replace(/[&<>]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c]))
}

export default function Highlight({ code, language }) {
  const html = useMemo(() => {
    try {
      if (language && hljs.getLanguage(language)) {
        return hljs.highlight(code, { language }).value
      }
      return escapeHtml(code)
    } catch {
      return escapeHtml(code)
    }
  }, [code, language])

  return (
    <pre className="max-h-[72vh] overflow-auto px-4 py-3 text-[12.5px] leading-relaxed">
      <code className="hljs bg-transparent" dangerouslySetInnerHTML={{ __html: html }} />
    </pre>
  )
}
