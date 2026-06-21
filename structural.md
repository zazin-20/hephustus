---
title: Hephaestus — Structural Compliance Rules
version: 0.2.0
status: active
created: 2026-06-21
updated: 2026-06-21
owner: architect
layer: spec
---

# Structural Compliance Rules

Structural rules are checkable purely from the filesystem and OKF frontmatter —
no LLM required. They form the MVP compliance layer of Hephaestus.

## Rule Interface

Every rule (built-in or custom) implements this interface:

```python
class HephaestusRule:
    id: str
    name: str
    layer: Literal["structural", "behavioral"]
    severity: Literal["error", "warning", "info"]
    roles_involved: list[str]
    auto_fixable: bool
    fix_hint: str

    def check(self, context: OKFContext) -> ViolationResult:
        ...

class ViolationResult:
    passed: bool
    violations: list[Violation]

class Violation:
    rule_id: str
    severity: str
    message: str
    artifact: str       # file path that triggered the violation
    fix_hint: str
    auto_fixable: bool
```

The `OKFContext` passed to every rule contains:

```python
class OKFContext:
    issues: list[IssueSpec]          # parsed from agents/architect/issues/
    handoffs: list[Handoff]          # parsed from agents/architect/handoffs/
    log_entries: list[LogEntry]      # parsed from agents/log/*.md
    qa_evidence: list[QAEvidence]    # parsed from agents/qa/evidence/*.md
    issues_index: IssuesIndex        # parsed from agents/architect/issues/index.md
```

---

## Built-in Rule Library (MVP)

These 6 rules cover one complete pipeline loop: spec → worker → handoff → QA → log.

---

### S-001 — Worker Must Have Issue Spec Before Starting

**ID:** `structural.worker-needs-spec`
**Severity:** `error`
**Roles:** `worker`, `architect`
**Auto-fixable:** No

**Description:**
A Worker session must have a corresponding Architect issue spec file before
it can be marked `in-progress`. If a handoff or in-progress issue exists
without a matching spec, the worker started without proper direction.

**Check Logic:**
```python
def check(self, ctx: OKFContext) -> ViolationResult:
    violations = []
    for issue in ctx.issues:
        if issue.status in ("in-progress", "done"):
            spec_path = f"agents/architect/issues/{issue.id}.md"
            if not spec_path.exists():
                violations.append(Violation(
                    rule_id="S-001",
                    severity="error",
                    message=f"Issue {issue.id} is {issue.status} but has no Architect spec",
                    artifact=spec_path,
                    fix_hint="Create an issue spec in agents/architect/issues/ "
                             "before the Worker starts. Use the standard spec template.",
                    auto_fixable=False
                ))
    return ViolationResult(passed=len(violations) == 0, violations=violations)
```

**Fix Hint for Human:**
Create a spec file at `agents/architect/issues/{issue_id}.md` using the standard
issue spec template. The Architect subagent should produce this before Worker is spawned.

---

### S-002 — Worker Must Leave Handoff After Completing

**ID:** `structural.worker-must-leave-handoff`
**Severity:** `error`
**Roles:** `worker`, `architect`
**Auto-fixable:** No

**Description:**
When a Worker marks an issue as `done`, a corresponding handoff file must exist
in `agents/architect/handoffs/`. A completed issue with no handoff means the
Architect cannot review the work before QA starts.

**Check Logic:**
```python
def check(self, ctx: OKFContext) -> ViolationResult:
    violations = []
    completed_ids = {i.id for i in ctx.issues if i.status == "done"}
    handoff_ids = {h.issue_id for h in ctx.handoffs}
    missing = completed_ids - handoff_ids
    for issue_id in missing:
        violations.append(Violation(
            rule_id="S-002",
            severity="error",
            message=f"Issue {issue_id} is marked done but has no handoff artifact",
            artifact=f"agents/architect/issues/{issue_id}.md",
            fix_hint="Worker must create a handoff file at "
                     "agents/architect/handoffs/{issue_id}.md before closing.",
            auto_fixable=False
        ))
    return ViolationResult(passed=len(violations) == 0, violations=violations)
```

**Fix Hint for Human:**
Instruct the Worker (or manually create) a handoff at
`agents/architect/handoffs/{issue_id}.md` with the standard handoff template.
Then re-open the issue as `handoff-pending` until Architect reviews.

---

### S-003 — QA Must Produce Evidence Before Issue Logged as Done

**ID:** `structural.qa-needs-evidence`
**Severity:** `error`
**Roles:** `qa`
**Auto-fixable:** No

**Description:**
An issue cannot be marked complete in the completion log unless QA evidence exists
for it. Evidence is a per-issue document at `agents/qa/evidence/{issue_id}.md`.

**Check Logic:**
```python
def check(self, ctx: OKFContext) -> ViolationResult:
    violations = []
    logged_ids = {e.issue_id for e in ctx.log_entries}
    evidenced_ids = {e.issue_id for e in ctx.qa_evidence}
    missing_evidence = logged_ids - evidenced_ids
    for issue_id in missing_evidence:
        violations.append(Violation(
            rule_id="S-003",
            severity="error",
            message=f"Issue {issue_id} is in the completion log but has no QA evidence",
            artifact=f"agents/qa/evidence/{issue_id}.md",
            fix_hint="QA must add an evidence record at agents/qa/evidence/{issue_id}.md "
                     "referencing this issue before it can be logged as complete.",
            auto_fixable=False
        ))
    return ViolationResult(passed=len(violations) == 0, violations=violations)
```

**Fix Hint for Human:**
Either add QA evidence retroactively (if QA was done but not recorded), or
reopen the issue and run QA before re-logging it as complete.

---

### S-004 — Log Entry Must Exist for Every Completed Issue

**ID:** `structural.log-entry-for-completion`
**Severity:** `warning`
**Roles:** `orchestrator`
**Auto-fixable:** No

**Description:**
Every issue spec with `status: done` and a QA evidence entry must have a
corresponding completion record at `agents/log/{issue_id}.md`. This ensures traceability is complete
and sprint history is accurate.

**Check Logic:**
```python
def check(self, ctx: OKFContext) -> ViolationResult:
    violations = []
    done_with_evidence = {
        e.issue_id for e in ctx.qa_evidence
        if any(i.id == e.issue_id and i.status == "done" for i in ctx.issues)
    }
    logged_ids = {e.issue_id for e in ctx.log_entries}
    missing_log = done_with_evidence - logged_ids
    for issue_id in missing_log:
        violations.append(Violation(
            rule_id="S-004",
            severity="warning",
            message=f"Issue {issue_id} has QA evidence and is done "
                    "but has no completion log entry",
            artifact=f"agents/log/{issue_id}.md",
            fix_hint="Add a completion record at agents/log/{issue_id}.md for this issue. "
                     "Include: issue_id, sprint, date, summary, worker, qa.",
            auto_fixable=False
        ))
    return ViolationResult(passed=len(violations) == 0, violations=violations)
```

**Fix Hint for Human:**
Create a completion record at `agents/log/{issue_id}.md` manually or instruct the
Orchestrator to close out the issue formally.

---

### S-005 — Handoff Must Have Architect Review Before QA Starts

**ID:** `structural.handoff-needs-architect-review`
**Severity:** `error`
**Roles:** `architect`, `qa`
**Auto-fixable:** No

**Description:**
A handoff file must have `reviewed_by: architect` in its frontmatter before
QA evidence can be created for that issue. QA should not start verifying
work that the Architect has not reviewed.

**Check Logic:**
```python
def check(self, ctx: OKFContext) -> ViolationResult:
    violations = []
    evidenced_ids = {e.issue_id for e in ctx.qa_evidence}
    for handoff in ctx.handoffs:
        if handoff.issue_id in evidenced_ids:
            if not handoff.reviewed_by or "architect" not in handoff.reviewed_by:
                violations.append(Violation(
                    rule_id="S-005",
                    severity="error",
                    message=f"Issue {handoff.issue_id} has QA evidence but "
                            "handoff was not reviewed by Architect",
                    artifact=f"agents/architect/handoffs/{handoff.issue_id}.md",
                    fix_hint="Architect must review the handoff and set "
                             "'reviewed_by: architect' in frontmatter before QA starts.",
                    auto_fixable=False
                ))
    return ViolationResult(passed=len(violations) == 0, violations=violations)
```

**Fix Hint for Human:**
Spawn an Architect subagent to review the handoff at
`agents/architect/handoffs/{issue_id}.md` and update the `reviewed_by` field.

---

### S-006 — Sprint State Must Be Consistent

**ID:** `structural.sprint-state-consistent`
**Severity:** `warning`
**Roles:** `orchestrator`, `architect`
**Auto-fixable:** No

**Description:**
The issue list in `agents/architect/issues/index.md` must be consistent with the
completion records in `agents/log/`. If a completion record marks a sprint as
closed, no issues from that
sprint should appear as `open` in the index. This is the specific drift that
triggered this rule (Sprint 02 example).

**Check Logic:**
```python
def check(self, ctx: OKFContext) -> ViolationResult:
    violations = []
    closed_sprints = {e.sprint for e in ctx.log_entries if e.sprint_closed}
    for issue in ctx.issues_index.open_issues:
        if issue.sprint in closed_sprints:
            violations.append(Violation(
                rule_id="S-006",
                severity="warning",
                message=f"Issue {issue.id} listed as open in index but "
                        f"sprint {issue.sprint} is marked closed in the completion log",
                artifact="agents/architect/issues/index.md",
                fix_hint="Reconcile issues/index.md against the completion log. "
                         "Either close the issue in the index or reopen the sprint.",
                auto_fixable=False
            ))
    return ViolationResult(passed=len(violations) == 0, violations=violations)
```

**Fix Hint for Human:**
Run a manual reconciliation pass on `agents/architect/issues/index.md`.
Update status of stale open items to match what the completion log actually records.

---

## Rule Registry

All rules are registered here. Toggle `enabled` to activate/deactivate per project.

```toml
# hephaestus.toml — rule configuration

[rules]

[rules.S-001]
enabled = true
severity_override = null   # set to "warning" to downgrade from "error"

[rules.S-002]
enabled = true
severity_override = null

[rules.S-003]
enabled = true
severity_override = null

[rules.S-004]
enabled = true
severity_override = null

[rules.S-005]
enabled = true
severity_override = null

[rules.S-006]
enabled = true
severity_override = null
```

---

## Adding Custom Rules (Future)

The custom rule slot is reserved. Future implementation options:

**Option A — Python function:**
```python
# hephaestus/custom_rules/my_rule.py
from hephaestus.rules import HephaestusRule, ViolationResult

class WorkerHandoffHasSummary(HephaestusRule):
    id = "custom.worker-handoff-has-summary"
    name = "Worker handoff must include a summary section"
    layer = "structural"
    severity = "warning"
    roles_involved = ["worker"]
    auto_fixable = False
    fix_hint = "Add a ## Summary section to the handoff file."

    def check(self, ctx):
        violations = []
        for handoff in ctx.handoffs:
            if "## Summary" not in handoff.raw_content:
                violations.append(...)
        return ViolationResult(...)
```

**Option B — YAML rule (no-code, future):**
```yaml
# agents/hephaestus/rules/custom/handoff-has-summary.yaml
id: custom.handoff-has-summary
name: Worker handoff must include a summary section
layer: structural
severity: warning
check:
  type: content_contains
  target: agents/architect/handoffs/*.md
  must_contain: "## Summary"
fix_hint: Add a ## Summary section to the handoff file.
```

**Option C — Behavioral rule (LLM-judged, future):**
```yaml
id: behavioral.tdd-playbook-followed
name: Worker must follow TDD playbook
layer: behavioral
severity: warning
check:
  type: llm_judge
  prompt_template: |
    Review this handoff artifact and determine if the Worker
    followed the TDD playbook defined in agents/worker/tdd.md.
    Return JSON: {"passed": bool, "reason": str}
  target: agents/architect/handoffs/{issue_id}.md
  reference: agents/worker/tdd.md
```

---

## Violation Severity Guide

| Severity | Meaning | Dashboard Treatment |
|---|---|---|
| `error` | Blocks pipeline progression. Work should not continue until resolved. | Red badge, issue card blocked |
| `warning` | Drift detected. Should be resolved but does not block. | Yellow badge, issue card flagged |
| `info` | Informational. No action required but worth knowing. | Grey badge, collapsible |
