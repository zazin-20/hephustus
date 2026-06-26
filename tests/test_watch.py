from __future__ import annotations

import asyncio

import pytest

from hephaestus.watch import AsyncDebouncer, OKFEventHandler


def test_debouncer_coalesces_burst_to_single_call():
    async def run():
        loop = asyncio.get_running_loop()
        calls = []
        d = AsyncDebouncer(loop, 0.05, lambda: calls.append(1))
        for _ in range(5):
            d.trigger()
        await asyncio.sleep(0.2)
        return calls

    assert asyncio.run(run()) == [1]


def test_debouncer_fires_again_after_quiet_period():
    async def run():
        loop = asyncio.get_running_loop()
        calls = []
        d = AsyncDebouncer(loop, 0.05, lambda: calls.append(1))
        d.trigger()
        await asyncio.sleep(0.15)
        d.trigger()
        await asyncio.sleep(0.15)
        return calls

    assert asyncio.run(run()) == [1, 1]


class _FakeEvent:
    def __init__(self, src, is_directory=False, dest=""):
        self.src_path = src
        self.is_directory = is_directory
        self.dest_path = dest


class _Recorder:
    def __init__(self):
        self.count = 0

    def trigger(self):
        self.count += 1


def test_handler_triggers_only_on_markdown_files():
    rec = _Recorder()
    handler = OKFEventHandler(rec)
    handler.on_any_event(_FakeEvent("agents/architect/issues/issue-1.md"))
    handler.on_any_event(_FakeEvent("agents/notes.txt"))
    handler.on_any_event(_FakeEvent("agents/architect", is_directory=True))
    assert rec.count == 1


def test_handler_triggers_on_markdown_rename():
    rec = _Recorder()
    handler = OKFEventHandler(rec)
    handler.on_any_event(_FakeEvent("agents/tmp", dest="agents/issue-2.md"))
    assert rec.count == 1


def test_watcher_prefers_agents_subtree_when_present(tmp_path):
    root = tmp_path / "workspace"
    agents = root / "agents"
    agents.mkdir(parents=True)

    from hephaestus.watch import OKFWatcher

    watcher = OKFWatcher(root, lambda delta: None)

    assert watcher._watch_dir() == agents


def test_watcher_accepts_agents_root_directly(tmp_path):
    agents = tmp_path / "workspace" / "agents"
    agents.mkdir(parents=True)

    from hephaestus.watch import OKFWatcher

    watcher = OKFWatcher(agents, lambda delta: None)

    assert watcher._watch_dir() == agents


def test_watcher_end_to_end_detects_a_new_violation(clean_tree):
    pytest.importorskip("watchdog")
    from hephaestus.watch import OKFWatcher

    async def run():
        deltas = []
        watcher = OKFWatcher(clean_tree, deltas.append, delay=0.05)
        await watcher.start()  # emits clean baseline as deltas[0]

        # Write a malformed document -> a Tier-1 schema load error.
        broken = clean_tree / "agents" / "architect" / "issues" / "broken.md"
        broken.write_text("---\nid: x\nunterminated", encoding="utf-8")

        for _ in range(60):  # up to ~3s for the FS event + debounce
            await asyncio.sleep(0.05)
            if len(deltas) >= 2:
                break
        await watcher.stop()
        return deltas

    deltas = asyncio.run(run())
    assert len(deltas) >= 2
    added_ids = {v.rule_id for d in deltas[1:] for v in d.added}
    assert "schema" in added_ids
