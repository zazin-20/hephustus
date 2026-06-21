"""Built-in structural rules S-001 .. S-006 (see spec/rules/structural.md).

These check filesystem/frontmatter relationships only — no LLM. They read from
the OKFContext index via EvaluationContext.okf, never the disk. Each rule notes
where its logic adapts the spec to the per-issue-document OKF layout.
"""
from __future__ import annotations

from hephaestus.core import Severity, Violation, ViolationResult
from hephaestus.eval_context import EvaluationContext
from hephaestus.models import IssueStatus
from hephaestus.rules.base import HephaestusRule


class S001WorkerNeedsSpec(HephaestusRule):
    id = "S-001"
    name = "Worker must have issue spec before starting"
    severity = Severity.ERROR
    roles_involved = ["worker", "architect"]
    fix_hint = (
        "Create an issue spec at agents/architect/issues/<id>.md before any "
        "handoff, QA, or log artifact references that issue."
    )

    def check(self, ctx: EvaluationContext) -> ViolationResult:
        referenced = (
            {h.issue_id for h in ctx.okf.handoffs}
            | {e.issue_id for e in ctx.okf.qa_evidence}
            | {e.issue_id for e in ctx.okf.log_entries}
        )
        violations = [
            Violation(
                rule_id=self.id,
                severity=self.severity,
                message=f"Issue {iid} has downstream artifacts but no Architect spec",
                artifact=f"agents/architect/issues/{iid}.md",
                fix_hint=self.fix_hint,
            )
            for iid in sorted(referenced - ctx.okf.issue_ids)
        ]
        return ViolationResult.of(violations)


class S002WorkerMustLeaveHandoff(HephaestusRule):
    id = "S-002"
    name = "Worker must leave handoff after completing"
    severity = Severity.ERROR
    roles_involved = ["worker", "architect"]
    fix_hint = (
        "Create a handoff at agents/architect/handoffs/<id>.md before the issue "
        "is marked done."
    )

    def check(self, ctx: EvaluationContext) -> ViolationResult:
        done = {i.id for i in ctx.okf.issues if i.status == IssueStatus.DONE}
        handed = {h.issue_id for h in ctx.okf.handoffs}
        violations = [
            Violation(
                rule_id=self.id,
                severity=self.severity,
                message=f"Issue {iid} is done but has no handoff artifact",
                artifact=f"agents/architect/issues/{iid}.md",
                fix_hint=self.fix_hint,
            )
            for iid in sorted(done - handed)
        ]
        return ViolationResult.of(violations)


class S003QANeedsEvidence(HephaestusRule):
    id = "S-003"
    name = "QA must produce evidence before issue logged as done"
    severity = Severity.ERROR
    roles_involved = ["qa"]
    fix_hint = (
        "Add a QA evidence record at agents/qa/evidence/<id>.md before the issue "
        "appears in the completion log."
    )

    def check(self, ctx: EvaluationContext) -> ViolationResult:
        logged = {e.issue_id for e in ctx.okf.log_entries}
        evidenced = {e.issue_id for e in ctx.okf.qa_evidence}
        violations = [
            Violation(
                rule_id=self.id,
                severity=self.severity,
                message=f"Issue {iid} is in the completion log but has no QA evidence",
                artifact=f"agents/qa/evidence/{iid}.md",
                fix_hint=self.fix_hint,
            )
            for iid in sorted(logged - evidenced)
        ]
        return ViolationResult.of(violations)


class S004LogEntryForCompletion(HephaestusRule):
    id = "S-004"
    name = "Log entry must exist for every completed issue"
    severity = Severity.WARNING
    roles_involved = ["orchestrator"]
    fix_hint = "Add a completion record at agents/log/<id>.md for this issue."

    def check(self, ctx: EvaluationContext) -> ViolationResult:
        done_ids = {i.id for i in ctx.okf.issues if i.status == IssueStatus.DONE}
        done_with_evidence = {e.issue_id for e in ctx.okf.qa_evidence if e.issue_id in done_ids}
        logged = {e.issue_id for e in ctx.okf.log_entries}
        violations = [
            Violation(
                rule_id=self.id,
                severity=self.severity,
                message=f"Issue {iid} is done with QA evidence but has no log entry",
                artifact=f"agents/log/{iid}.md",
                fix_hint=self.fix_hint,
            )
            for iid in sorted(done_with_evidence - logged)
        ]
        return ViolationResult.of(violations)


class S005HandoffNeedsArchitectReview(HephaestusRule):
    id = "S-005"
    name = "Handoff must have Architect review before QA starts"
    severity = Severity.ERROR
    roles_involved = ["architect", "qa"]
    fix_hint = (
        "Architect must set 'reviewed_by: architect' on the handoff before QA "
        "evidence is created."
    )

    def check(self, ctx: EvaluationContext) -> ViolationResult:
        evidenced = {e.issue_id for e in ctx.okf.qa_evidence}
        violations = [
            Violation(
                rule_id=self.id,
                severity=self.severity,
                message=(
                    f"Issue {h.issue_id} has QA evidence but its handoff was not "
                    "reviewed by Architect"
                ),
                artifact=f"agents/architect/handoffs/{h.issue_id}.md",
                fix_hint=self.fix_hint,
            )
            for h in ctx.okf.handoffs
            if h.issue_id in evidenced and "architect" not in h.reviewed_by
        ]
        return ViolationResult.of(violations)


class S006SprintStateConsistent(HephaestusRule):
    id = "S-006"
    name = "Sprint state must be consistent (index vs log)"
    severity = Severity.WARNING
    roles_involved = ["orchestrator", "architect"]
    fix_hint = (
        "Reconcile agents/architect/issues/index.md against the completion log: "
        "close the issue in the index or reopen the sprint."
    )

    def check(self, ctx: EvaluationContext) -> ViolationResult:
        closed_sprints = {e.sprint for e in ctx.okf.log_entries if e.sprint_closed}
        violations = [
            Violation(
                rule_id=self.id,
                severity=self.severity,
                message=(
                    f"Issue {ref.id} is listed open in the index but sprint "
                    f"{ref.sprint} is marked closed in the log"
                ),
                artifact="agents/architect/issues/index.md",
                fix_hint=self.fix_hint,
            )
            for ref in ctx.okf.issues_index.open_issues
            if ref.sprint in closed_sprints
        ]
        return ViolationResult.of(violations)


ALL_STRUCTURAL_RULES: list[HephaestusRule] = [
    S001WorkerNeedsSpec(),
    S002WorkerMustLeaveHandoff(),
    S003QANeedsEvidence(),
    S004LogEntryForCompletion(),
    S005HandoffNeedsArchitectReview(),
    S006SprintStateConsistent(),
]
