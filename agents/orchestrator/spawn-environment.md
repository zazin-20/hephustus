---
title: Spawn Methods & CLI Environment Reference
role: orchestrator
updated: 2026-07-04
owner: orchestrator
---

# Spawn Methods & CLI Environment Reference

This is the Orchestrator's operating record for **how to talk to a subagent's
shell once it's spawned**, and for **known environment failures and their
fixes**. Every dispatch prompt the Orchestrator writes must be built against
the row for that agent's actual tool access below — not against whatever
shell conventions happen to work in the Orchestrator's own session. Check
this file FIRST whenever a command fails in an environment-shaped way, before
attempting any fix. Update it the moment a new environment issue is found —
do not let the fix live only in a chat transcript.

## Escalation protocol (read this before touching a failing command twice)

1. **Check this file first.** If the failure matches a known gotcha below,
   apply its documented fix once. Don't re-derive a fix from scratch for a
   problem already solved here.
2. **If it's not documented, do ONE minimal diagnostic** to identify the
   actual cause — not a cascade of different remediation attempts. E.g. one
   `icacls`/`Get-Acl` query to check whether a path is genuinely
   permission-locked, not `rm` then `icacls` then `takeown` then
   `Remove-Item` then `Get-Acl` in sequence hoping one works.
3. **If that diagnostic confirms the fix requires elevated/admin access (or
   anything else only the user can grant — credentials, UAC, physical
   access), stop immediately.** Do not keep trying alternate workarounds.
   State plainly what was checked and what it proved, then hand the user the
   exact copy-pasteable command(s) to run themselves.
4. **Never present "needs elevated access" as a guess.** Only conclude that
   after verifying with a real command (e.g. `Get-Acl`/`icacls` itself being
   denied is real evidence; a bare `PermissionError` on a normal `rm` is not
   enough on its own — confirm before escalating).
5. **After resolution (by either path), append a new dated entry here** with:
   what failed, the fix (or "needs elevation" + the exact commands), and
   where/when it was found. This file is the single source of truth for
   spawn-time environment knowledge.

## Spawn methods (Agent tool `subagent_type`)

| subagent_type | Shell tools available | Model | Use for |
|---|---|---|---|
| `fork` | inherits caller's tools, incl. PowerShell + Bash | inherits caller's model (override ignored) | Open-ended research/work that shares this conversation's context; output stays out of main context |
| `codex:codex-rescue` | **Bash only** — no PowerShell | n/a (forwards to Codex CLI) | Handing an implementation task to Codex. Pure forwarder: one `task` call, then returns stdout. Cannot poll/verify itself. |
| `claude` | Bash + PowerShell (`*`) | default | Catch-all general work, fresh context |
| `general-purpose` | Bash + PowerShell (`*`) | default | Multi-step research/implementation, fresh context |
| `Explore` | Bash + PowerShell (read-heavy; no Edit/Write/Agent) | default | Fast read-only code location |
| `Plan` | Bash + PowerShell (no Edit/Write/Agent) | default | Implementation planning, no file mutation |
| `claude-code-guide` | **none** — Glob, Grep, Read, WebFetch, WebSearch only | default | Questions about Claude Code / Agent SDK / API |
| `statusline-setup` | **none** — Read, Edit only | default | Statusline config only |

`isolation: "worktree"` on the Agent call itself is **not** the mechanism we
use for parallel Worker dispatch — it races under concurrency (see Known
Gotchas). We pre-create worktrees serially with `git worktree add` +
verify with `git worktree list` *before* any Agent call, then the dispatched
agent just `cd`s into an already-isolated directory.

`isolation: "remote"` (cloud sandbox) exists but has not been exercised or
verified in this project — treat as unverified until first use.

## Shell / CLI compatibility matrix

Tested directly, 2026-07-04, on this machine.

| Tool | Bash (Git Bash) bare name | Bash absolute path | PowerShell bare name |
|---|---|---|---|
| `git` | **FAILS** (command not found) | works | works |
| `node` | **FAILS** | works | works |
| `npm` | **FAILS** | works | works |
| `gh` | **FAILS** | works | works |
| `codex` | **FAILS** | works | works |
| `python` / `py` | **FAILS** | works (must be the project venv path, see below) | **resolves, but to the wrong thing** — Windows Store alias stub / py launcher, not the venv |
| core utils (`ls`, `cat`, `mkdir`, `rm`, ...) | **FAILS** | works (e.g. `/usr/bin/ls.exe`) | n/a (PowerShell has native cmdlets) |

### Root cause (Bash bare-name failures)

The Bash tool's `$PATH` is populated with **Windows-style** entries
(`C:\Program Files\Git\mingw64\bin;C:\Users\...`) joined by `;`. Bash's PATH
search splits on `:`, and every drive-letter colon (`C:`) is itself treated
as a separator — this shreds the entire variable into garbage fragments, so
*no* bare command resolves via PATH, not just project-specific tools. This is
a property of the Bash tool's launch environment on this machine, not
something a subagent can configure around — the only fix is to never rely on
bare-name PATH resolution in Bash; always use an absolute path.

### Verified working invocation patterns

**Bash — always use absolute paths, quoted if they contain spaces:**
```bash
"/c/Program Files/Git/mingw64/bin/git.exe" status
"/c/Program Files/nodejs/node.exe" "C:/path/to/script.mjs" arg1 arg2
"/c/Program Files/GitHub CLI/gh.exe" issue view 20 --repo zazin-20/hephustus
"C:\Users\kambala.jathin\Projects\hephustus\agents\.venv\Scripts\python.exe" -m pytest
```
Windows-style backslash absolute paths (e.g. the venv python path above) also
work directly in Bash — it's only *bare* names that fail, because those go
through PATH search; a path containing `/` or a drive letter is used as-is.

Within a single Bash tool call, local shell variables persist across
commands (shell state does *not* persist across separate tool calls), so
multi-step git workflows can alias once per call:
```bash
GIT="/c/Program Files/Git/mingw64/bin/git.exe"
"$GIT" add file1 file2
"$GIT" commit -m "..."
```

**PowerShell — bare names work for git/node/npm/gh/codex.** Never use bare
`python`/`py` — always the absolute venv path:
```powershell
git status
node "C:\path\to\script.mjs" status
& "C:\Users\kambala.jathin\Projects\hephustus\agents\.venv\Scripts\python.exe" -m pytest
```

## Fixed known-good absolute paths (this machine)

| Tool | Path |
|---|---|
| git.exe | `C:\Program Files\Git\mingw64\bin\git.exe` (Bash form: `/c/Program Files/Git/mingw64/bin/git.exe`) |
| node.exe | `C:\Program Files\nodejs\node.exe` (Bash form: `/c/Program Files/nodejs/node.exe`) |
| gh.exe | `C:\Program Files\GitHub CLI\gh.exe` |
| codex-companion.mjs | `C:\Users\kambala.jathin\.claude\plugins\cache\openai-codex\codex\1.0.4\scripts\codex-companion.mjs` |
| Project venv python | `C:\Users\kambala.jathin\Projects\hephustus\agents\.venv\Scripts\python.exe` — **never** bare `python`/`py` in either shell |

**Verified 2026-07-04**: `agents/.venv/Scripts/python.exe --version` → Python
3.12.10. `-m pip list` confirms it holds only third-party deps (pytest 9.1.1,
pydantic 2.13.4, PyYAML 6.0.3, jsonschema, claude-agent-sdk, mcp, pywebview,
etc.) and **no editable `hephaestus` install** — consistent with
`pyproject.toml`'s `pythonpath = ["."]` making this one venv safe to share
across every parallel worktree. This is the only Python environment any
spawned agent should ever use; there is no alternate/per-worktree venv.

## Known Gotchas

1. **Bash PATH is unusable for bare commands on this machine** (see Root
   cause above). Fix: absolute paths only, every time, in every
   `codex:codex-rescue` dispatch prompt (its only shell tool is Bash).
   Found: 2026-07-04, while diagnosing why a `codex:codex-rescue` dispatch
   for issue #20 appeared to hang/flail on `node codex-companion.mjs ...`
   before the user stopped it.
2. **Bare `py`/`python` resolve to a Windows Store App-Execution-Alias stub**
   (or the bare py launcher) in *both* shells — hangs indefinitely under a
   non-interactive/sandboxed shell. Fix: always the absolute venv path.
   Found: earlier wave (#15 dispatch).
3. **`Agent` tool's `isolation: "worktree"` races under concurrent dispatch.**
   Fix: pre-create worktrees serially via `git worktree add <path> -b <branch> main`,
   verify via `git worktree list`, dispatch into the already-made path instead.
   Found: T-004 (issue #15 wave).
4. **`codex:codex-rescue` cannot self-monitor.** It is a pure forwarder — one
   `task` call, return stdout, done. It cannot call `status`/`result`/`cancel`
   and will refuse if asked to poll. All polling/verification must happen
   from the main thread directly: `node codex-companion.mjs status [job-id]`
   (via the absolute path above, run through whichever shell the *caller*
   has — the Orchestrator itself has PowerShell, so use that). In practice,
   `status` is unreliable (see #5) — the most trustworthy signal is
   inspecting the target worktree directly (`git status --short`) and/or
   confirming the job's process is alive via
   `Get-CimInstance Win32_Process -Filter "Name='node.exe'"`.
5. **`node codex-companion.mjs status [job-id]` can fail to find a genuinely
   running job when queried from the Orchestrator's own session**, even
   immediately after a dispatch subagent reports the job started. Root
   cause: job state is stored per-workspace under `CLAUDE_PLUGIN_DATA`
   (`C:/Users/kambala.jathin/.claude/plugins/data/codex-openai-codex` on this
   machine), which appears scoped per agent invocation/session — a job's
   state file written under the dispatching subagent's env may be invisible
   to a `status` call from a different session. **Fix**: don't trust
   `status` polling alone; cross-check with `Get-CimInstance Win32_Process`
   for a live `codex-companion.mjs task-worker --job-id <id>` command line,
   and treat the worktree's own file/git changes as the primary signal.
   Found: 2026-07-04, issue #20 redispatch.
6. **A Codex worker session can complete all implementation work but still
   hit a session/time limit before running `git commit`,** leaving finished
   work sitting uncommitted in the worktree. Always check `git status` /
   `git diff --stat` in the worktree after a "session limit" or unexpected
   termination before assuming work was lost — recover and commit it
   (verifying independently first) rather than re-doing it from scratch.
   Found: 2026-07-04, issue #19 dispatch.
6a. **Codex's own execution sandbox can block `git commit` in a git
   worktree**, distinct from the session-limit case above. The worktree's
   git metadata lives at `<main-repo>\.git\worktrees\<worktree-name>\`,
   *outside* the worktree directory itself — and that path can be outside
   Codex's writable sandbox roots for a session. The code and handoff are
   otherwise complete and correct in this case. **Fix**: the Orchestrator
   independently verifies the tests/diff and performs the commit itself from
   its own (non-sandboxed) shell. Recurred on issues #21, #23, #24 — treat
   this as the default expectation for every `codex:codex-rescue` dispatch,
   not a one-off. Found: 2026-07-04, issue #21.
7. **A literal `"` inside a PowerShell `@'...'@` here-string body passed to
   `-m` on a native exe (e.g. `git commit -m @'...has a "quoted" word...'@`)
   can cause PowerShell to mis-split the argument** when re-quoting for the
   native process — git then errors with something like
   `error: pathspec '<tail of the message>' did not match any file(s)`,
   because everything after the embedded `"` got treated as a second
   argument. Fix: don't put literal double quotes inside a commit message
   built this way — rephrase without quotes, or use a different quoting
   character (backtick, single quote) inside the body. Found: 2026-07-04,
   committing recovered work for issue #22.
8. **A Codex worker's sandboxed process can leave a hard-deny security
   descriptor on directories it created (seen on `.pytest_cache` /
   `.pytest_tmp` inside its worktree), which survives the process exiting.**
   Confirmed this is not a normal ACL issue: `Get-Acl` itself is denied
   (`UnauthorizedAccessException`), and both non-elevated `takeown /R /D Y`
   and `icacls /reset /T` also fail with Access Denied — meaning the
   Orchestrator's own (non-elevated) session has no path to clear it. Do
   **not** cycle through `rm` → `icacls` → `takeown` → `Remove-Item` →
   `Get-Acl` hoping one works (wastes tokens on what is really one fact:
   elevation is required). **Diagnostic**: a single `Get-Acl` (or `icacls`)
   query on the specific stuck path either succeeds (normal permissions
   issue, keep debugging) or throws `UnauthorizedAccessException`/"Access is
   denied" on the query itself (confirms hard lock — stop here). **Fix**:
   this genuinely requires an elevated (Run as Administrator) session — hand
   the user this exact sequence rather than attempting more workarounds:
   ```powershell
   takeown /F "<path>" /R /D Y
   icacls "<path>" /reset /T /C
   Remove-Item -Recurse -Force "<path>"
   ```
   A reboot also tends to release the lock (releases whatever handle/token
   is holding it) if the user would rather avoid an elevated terminal. Not
   urgent to fix immediately — `git worktree remove --force` still succeeds
   at unregistering the worktree from git even when the directory itself
   can't be deleted; only the orphaned disk space is left behind. Found:
   2026-07-04, cleaning up worktrees after issues #23/#24 landed.

## Maintenance rule

Whenever a new subagent-environment issue surfaces (a tool that fails, a
quoting/escaping problem, a spawn-isolation race, anything a dispatch prompt
should have prevented), append a dated entry to **Known Gotchas** above with:
what failed, the fix, and where/when it was found. This file is the single
source of truth for spawn-time environment knowledge — do not let this
knowledge live only in a task file or a chat transcript.
