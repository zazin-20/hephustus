// Sample snapshot used only when running in a plain browser (no pywebview bridge),
// so the UI can be developed/previewed with `npm run dev`.
export const MOCK = {
  root: 'C:/Users/you/Projects/hephaestus (preview)',
  issues: [
    {
      id: 'issue-001', title: 'Auth module refactor', status: 'done', sprint: 'sprint-01',
      state: 'DONE',
      stages: { spec: 'ok', handoff: 'ok', review: 'ok', qa: 'ok', log: 'ok' },
      violations: [],
    },
    {
      id: 'issue-002', title: 'SQL agent migration', status: 'in-progress', sprint: 'sprint-02',
      state: 'IN_PROGRESS',
      stages: { spec: 'ok', handoff: 'none', review: 'none', qa: 'none', log: 'none' },
      violations: [],
    },
    {
      id: 'issue-010', title: 'API rate limiting', status: 'done', sprint: 'sprint-03',
      state: 'HANDOFF_PENDING',
      stages: { spec: 'ok', handoff: 'pending', review: 'none', qa: 'none', log: 'pending' },
      violations: ['S-002'],
    },
    {
      id: 'issue-012', title: 'Webhook retries', status: 'done', sprint: 'sprint-03',
      state: 'QA_PENDING',
      stages: { spec: 'ok', handoff: 'ok', review: 'pending', qa: 'ok', log: 'pending' },
      violations: ['S-004', 'S-005'],
    },
  ],
  violations: [
    {
      rule_id: 'S-002', severity: 'error', issue_id: 'issue-010',
      message: 'Issue issue-010 is done but has no handoff artifact',
      artifact: 'agents/architect/issues/issue-010.md',
      fix_hint: 'Create a handoff at agents/architect/handoffs/<id>.md before the issue is marked done.',
    },
    {
      rule_id: 'S-005', severity: 'error', issue_id: 'issue-012',
      message: 'Issue issue-012 has QA evidence but its handoff was not reviewed by Architect',
      artifact: 'agents/architect/handoffs/issue-012.md',
      fix_hint: "Architect must set 'reviewed_by: architect' on the handoff before QA evidence is created.",
    },
    {
      rule_id: 'S-004', severity: 'warning', issue_id: 'issue-012',
      message: 'Issue issue-012 is done with QA evidence but has no log entry',
      artifact: 'agents/log/issue-012.md',
      fix_hint: 'Add a completion record at agents/log/<id>.md for this issue.',
    },
  ],
  workflow_canvas: {
    available_nodes: [
      {
        node_id: 'node-001',
        name: 'Draft ADR',
        provider: 'codex',
        model: 'gpt-5.4',
        effort: 'medium',
        tags: ['worker', 'draft'],
        inputs: ['agents/artifacts/issue-025.md'],
        outputs: ['agents/specs/adr-spec.md'],
        executor: { kind: 'engine', provider: 'codex', model: 'gpt-5.4', effort: 'medium' },
      },
      {
        node_id: 'node-002',
        name: 'Gate Notify',
        provider: 'builtin',
        model: null,
        effort: null,
        tags: ['builtin', 'notify'],
        inputs: [],
        outputs: [],
        executor: { kind: 'builtin', name: 'notify' },
      },
      {
        node_id: 'node-003',
        name: 'Architect Review',
        provider: 'claude',
        model: 'opus',
        effort: 'high',
        tags: ['architect', 'review'],
        inputs: ['agents/artifacts/adr.md'],
        outputs: [],
        executor: { kind: 'engine', provider: 'claude', model: 'opus', effort: 'high' },
      },
    ],
    workflows: [
      {
        workflow_id: 'issue-025',
        version: 1,
        run: { workflow_run_id: 'run-025', status: 'awaiting_confirm' },
        placements: [
          {
            placement_id: 'draft',
            node_id: 'node-001',
            name: 'Draft ADR',
            x: 120,
            y: 160,
            interactivity: 'afk',
            executor: { kind: 'engine', provider: 'codex', model: 'gpt-5.4', effort: 'medium' },
            status: 'awaiting_confirm',
            detail: {
              gates: [
                { kind: 'entry', label: 'agents/artifacts/issue-025.md', status: 'pass' },
                { kind: 'artifact', label: 'agents/artifacts/adr.md', status: 'pass' },
              ],
              artifacts: [
                {
                  path: 'C:/Users/you/Projects/hephaestus/agents/artifacts/adr.md',
                  exists: true,
                  preview: '# ADR\n\nDraft is ready for architectural review.',
                },
              ],
              transcript: [
                { id: 'turn-1', role: 'assistant', kind: 'text', text: 'ADR drafted and ready for review.' },
              ],
              trace: [
                { id: 'trace-1', ts: '2026-07-04T08:00:00Z', action: 'write_file', target_path: 'agents/artifacts/adr.md' },
              ],
              failures: [],
              spawn_card: {
                gating: 'green',
                marker: { role: 'review', task: 'agents/artifacts/adr.md', issue_id: 'issue-025' },
                failures: [],
              },
            },
          },
          {
            placement_id: 'notify',
            node_id: 'node-002',
            name: 'Gate Notify',
            x: 400,
            y: 84,
            interactivity: 'afk',
            executor: { kind: 'builtin', name: 'notify' },
            status: 'done',
            detail: {
              gates: [],
              artifacts: [],
              transcript: [{ id: 'turn-2', role: 'assistant', kind: 'text', text: 'Architect notified.' }],
              trace: [{ id: 'trace-2', ts: '2026-07-04T08:01:00Z', action: 'notify', target_path: null }],
              failures: [],
              spawn_card: null,
            },
          },
          {
            placement_id: 'review',
            node_id: 'node-003',
            name: 'Architect Review',
            x: 680,
            y: 160,
            interactivity: 'hitl',
            executor: { kind: 'engine', provider: 'claude', model: 'opus', effort: 'high' },
            status: 'not_started',
            detail: { gates: [], artifacts: [], transcript: [], trace: [], failures: [], spawn_card: null },
          },
        ],
        edges: [
          {
            from_placement_id: 'draft',
            from_output: 'agents/artifacts/adr.md',
            to_placement_id: 'notify',
            to_input: 'agents/artifacts/adr.md',
            advance: 'allow',
            guard: null,
            label: null,
            state: 'done',
          },
          {
            from_placement_id: 'draft',
            from_output: 'agents/artifacts/adr.md',
            to_placement_id: 'review',
            to_input: 'agents/artifacts/adr.md',
            advance: 'ask',
            guard: { condition: 'has_summary()', label: 'summary-ready' },
            label: 'summary-ready',
            state: 'awaiting_confirm',
          },
        ],
      },
    ],
    notifications: [
      {
        id: 'run-025:draft:node_done_green',
        placement_id: 'draft',
        kind: 'node_done_green',
        severity: 'ok',
        message: 'Draft ADR is done and awaiting confirmation.',
      },
    ],
  },
  summary: { issues: 4, violations: 3, error: 2, warning: 1, info: 0 },
}

// Code-viewer preview data (browser mode only).
export const CODE_MOCK = {
  repos: [{ name: 'hephaestus', path: '(preview)' }],
  tree: {
    '': [
      { name: 'hephaestus', type: 'dir', path: 'hephaestus' },
      { name: 'README.md', type: 'file', path: 'README.md' },
    ],
    hephaestus: [
      { name: 'rules', type: 'dir', path: 'hephaestus/rules' },
      { name: 'models.py', type: 'file', path: 'hephaestus/models.py' },
    ],
    'hephaestus/rules': [
      { name: 'structural.py', type: 'file', path: 'hephaestus/rules/structural.py' },
    ],
  },
  files: {
    'README.md': {
      language: 'markdown', size: 42, binary: false, truncated: false,
      content: '# Hephaestus\n\nOKF system manager and agent compliance layer.',
    },
    'hephaestus/models.py': {
      language: 'python', size: 88, binary: false, truncated: false,
      content: 'class NodeSpec(OKFModel):\n    id: str\n    tags: list[str]\n    provider: str\n    sprint: str',
    },
    'hephaestus/rules/structural.py': {
      language: 'python', size: 70, binary: false, truncated: false,
      content: 'class S001WorkerNeedsSpec(HephaestusRule):\n    id = "S-001"\n    severity = Severity.ERROR',
    },
  },
}

// Catalog + rule set fallbacks for browser-preview mode (no bridge).
// Effort is carried per-model (Codex per-model from its cache; Claude shares one list).
const CLAUDE_EFFORTS = ['low', 'medium', 'high', 'xhigh', 'max']
export const CATALOG_MOCK = {
  providers: [
    {
      provider: 'claude',
      models: [
        { id: 'opus', label: 'Opus (latest)', efforts: CLAUDE_EFFORTS },
        { id: 'sonnet', label: 'Sonnet (latest)', efforts: CLAUDE_EFFORTS },
        { id: 'haiku', label: 'Haiku (latest)', efforts: CLAUDE_EFFORTS },
        { id: 'fable', label: 'Fable (latest)', efforts: CLAUDE_EFFORTS },
      ],
    },
    {
      provider: 'codex',
      models: [{ id: 'gpt-5.4', label: 'GPT-5.4', efforts: ['low', 'medium', 'high', 'xhigh'] }],
    },
  ],
}

export const RULES_MOCK = [
  { id: 'S-001', name: 'Worker must have issue spec before starting', severity: 'error', fix_hint: '' },
  { id: 'S-002', name: 'Worker must leave handoff after completing', severity: 'error', fix_hint: '' },
  { id: 'S-003', name: 'QA must produce evidence before issue logged as done', severity: 'error', fix_hint: '' },
  { id: 'S-004', name: 'Log entry must exist for every completed issue', severity: 'warning', fix_hint: '' },
  { id: 'S-005', name: 'Handoff must have Architect review before QA starts', severity: 'error', fix_hint: '' },
  { id: 'S-006', name: 'Sprint state must be consistent (index vs log)', severity: 'warning', fix_hint: '' },
  { id: 'G-001', name: 'Agent must not write outside its allowed paths', severity: 'error', fix_hint: '' },
  { id: 'G-002', name: 'Run must use the contracted model', severity: 'error', fix_hint: '' },
]

export const COORDINATOR_MOCK = [
  {
    node_id: 'node-001',
    name: 'Systems Architect',
    provider: 'claude',
    tags: ['architect', 'design'],
    rules: ['S-001', 'S-002'],
    model: 'claude-opus',
    effort: 'high',
    working_dir: 'services/api',
    created_at: '2026-06-22T00:00:00Z',
    status: 'idle',
  },
  {
    node_id: 'node-002',
    name: 'Implementation Worker',
    provider: 'codex',
    tags: ['worker', 'frontend'],
    rules: ['TDD', 'lint'],
    model: 'gpt-5',
    effort: 'medium',
    working_dir: 'frontend',
    created_at: '2026-06-22T00:05:00Z',
    status: 'idle',
  },
  {
    node_id: 'node-003',
    name: 'Evidence QA',
    provider: 'claude',
    tags: ['qa'],
    rules: ['QA-Checklist'],
    model: null,
    effort: 'low',
    working_dir: 'tests',
    created_at: '2026-06-22T00:08:00Z',
    status: 'idle',
  },
]
