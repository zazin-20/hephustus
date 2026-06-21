"""Governance rules G001/G002 — run-time scope and model enforcement."""
from __future__ import annotations

from hephaestus.core import Severity, Violation, ViolationResult
from hephaestus.rules.base import HephaestusRule

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
                        f"Agent {ctx.actor or event.agent_id} wrote outside allowed paths: "
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


ALL_GOVERNANCE_RULES: list[HephaestusRule] = [
    G001ScopeAdherence(),
    G002ModelCompliance(),
]
