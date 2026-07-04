"""Governance rules G001/G002 — run-time scope and model enforcement."""
from __future__ import annotations

from hephaestus.core import Severity, Violation, ViolationResult
from hephaestus.handoff import has_skill_completion
from hephaestus.okf_layout import OKFLayout
from hephaestus.rules.base import HephaestusRule
from hephaestus.skills import resolve_skill_ref

_WRITE_ACTIONS = frozenset({"write_file", "bash"})


class G001ScopeAdherence(HephaestusRule):
    id = "G-001"
    name = "Agent must not write outside its allowed paths"
    layer = "governance"
    trigger = "on_run"
    scope = "issue"
    severity = Severity.ERROR
    roles_involved = ["worker", "architect"]
    fix_hint = "Restrict write operations to the paths listed in ExecutionContract.allowed_paths."

    def check(self, ctx) -> ViolationResult:
        allowed = ctx.contract.get("allowed_paths", [])
        if not allowed:
            return ViolationResult.of([])
        violations = []
        for event in ctx.trace:
            if event.action not in _WRITE_ACTIONS:
                continue
            path = event.target_path or ""
            if not any(path.startswith(p) for p in allowed):
                violations.append(Violation(
                    rule_id=self.id,
                    severity=self.severity,
                    message=(
                        f"Agent {ctx.actor or event.node_id} wrote outside allowed paths: "
                        f"{path!r} (allowed: {allowed})"
                    ),
                    artifact=path,
                    fix_hint=self.fix_hint,
                ))
        return ViolationResult.of(violations)


class G002ModelCompliance(HephaestusRule):
    id = "G-002"
    name = "Run must use the contracted model"
    layer = "governance"
    trigger = "on_run"
    scope = "issue"
    severity = Severity.WARNING
    roles_involved = []
    fix_hint = "Ensure the runner invokes the model specified in ExecutionContract.model."

    def check(self, ctx) -> ViolationResult:
        contracted = ctx.contract.get("model")
        if not contracted:
            return ViolationResult.of([])
        actual = ctx.contract.get("actual_model")
        if actual is None or actual == contracted:
            return ViolationResult.of([])
        return ViolationResult.of([
            Violation(
                rule_id=self.id,
                severity=self.severity,
                message=(
                    f"Agent {ctx.actor} ran with model {actual!r} "
                    f"but contract requires {contracted!r}"
                ),
                artifact="",
                fix_hint=self.fix_hint,
            )
        ])


class G003SkillObligation(HephaestusRule):
    id = "G-003"
    name = "Enforced skill obligations must emit completion markers"
    layer = "governance"
    trigger = "on_run"
    scope = "issue"
    severity = Severity.ERROR
    roles_involved = []
    fix_hint = (
        "Emit a @@HEPHAESTUS@@ skill_complete marker with ok=true for each enforced skill."
    )

    def check(self, ctx) -> ViolationResult:
        obligations = ctx.contract.get("skill_obligations", [])
        if not obligations:
            return ViolationResult.of([])

        layout = OKFLayout.for_existing_root(ctx.okf.root)
        violations = []
        for ref in obligations:
            skill_id = resolve_skill_ref(layout, ref).skill_id
            if has_skill_completion(skill_id, turns=ctx.turns, trace=ctx.trace):
                continue
            violations.append(
                Violation(
                    rule_id=self.id,
                    severity=self.severity,
                    message=(
                        f"Agent {ctx.actor} did not emit the required skill completion "
                        f"marker for {skill_id!r}"
                    ),
                    artifact=skill_id,
                    fix_hint=self.fix_hint,
                )
            )
        return ViolationResult.of(violations)


ALL_GOVERNANCE_RULES: list[HephaestusRule] = [
    G001ScopeAdherence(),
    G002ModelCompliance(),
    G003SkillObligation(),
]
