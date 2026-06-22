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
      content: 'class IssueSpec(OKFModel):\n    id: str\n    status: IssueStatus\n    role: str\n    sprint: str',
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
    agent_id: 'arch-001',
    name: 'Systems Architect',
    role: 'architect',
    rules: ['S-001', 'S-002'],
    model: 'claude-opus',
    effort: 'high',
    working_dir: 'services/api',
    created_at: '2026-06-22T00:00:00Z',
    status: 'idle',
  },
  {
    agent_id: 'work-001',
    name: 'Implementation Worker',
    role: 'worker',
    rules: ['TDD', 'lint'],
    model: 'gpt-5',
    effort: 'medium',
    working_dir: 'frontend',
    created_at: '2026-06-22T00:05:00Z',
    status: 'idle',
  },
  {
    agent_id: 'qa-001',
    name: 'Evidence QA',
    role: 'qa',
    rules: ['QA-Checklist'],
    model: null,
    effort: 'low',
    working_dir: 'tests',
    created_at: '2026-06-22T00:08:00Z',
    status: 'idle',
  },
]
