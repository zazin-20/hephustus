"""Watchdog-driven validation pipeline (spec/architecture.md §5.4).

Layering:

    watchdog observer (its own thread)
        -> OKFEventHandler  (filters to *.md writes)
        -> AsyncDebouncer   (coalesces bursts; marshals onto the asyncio loop)
        -> ComplianceMonitor.refresh()
        -> on_change(ViolationDelta)

`watchdog` is an optional dependency (`pip install -e .[app]`); importing this
module without it still works — only `OKFWatcher.start()` requires it.
"""
from __future__ import annotations

import asyncio
import time
from pathlib import Path
from typing import Callable

from hephaestus.monitor import ComplianceMonitor, ViolationDelta

try:
    from watchdog.events import FileSystemEventHandler
    from watchdog.observers import Observer

    HAS_WATCHDOG = True
except ImportError:  # pragma: no cover - exercised only when extra is absent
    FileSystemEventHandler = object  # type: ignore[assignment,misc]
    Observer = None  # type: ignore[assignment]
    HAS_WATCHDOG = False


class AsyncDebouncer:
    """Coalesce rapid triggers into one callback after a quiet period.

    `trigger()` is thread-safe — it marshals onto the loop via
    `call_soon_threadsafe`, so the watchdog observer thread can call it directly.
    """

    def __init__(self, loop: asyncio.AbstractEventLoop, delay: float, callback: Callable[[], None]):
        self._loop = loop
        self._delay = delay
        self._callback = callback
        self._handle: asyncio.TimerHandle | None = None

    def _fire(self) -> None:
        self._handle = None
        self._callback()

    def _reschedule(self) -> None:
        if self._handle is not None:
            self._handle.cancel()
        self._handle = self._loop.call_later(self._delay, self._fire)

    def trigger(self) -> None:
        self._loop.call_soon_threadsafe(self._reschedule)


class OKFEventHandler(FileSystemEventHandler):
    """Filters watchdog events down to OKF markdown writes."""

    def __init__(self, debouncer: AsyncDebouncer):
        self._debouncer = debouncer

    def on_any_event(self, event) -> None:  # noqa: ANN001 (watchdog event type)
        if getattr(event, "is_directory", False):
            return
        paths = (getattr(event, "src_path", ""), getattr(event, "dest_path", ""))
        if any(str(p).endswith(".md") for p in paths):
            self._debouncer.trigger()


class OKFWatcher:
    """Watches the agents/ tree and emits a ViolationDelta on debounced changes."""

    def __init__(
        self,
        root: str | Path,
        on_change: Callable[[ViolationDelta], None],
        *,
        delay: float = 0.2,
        enabled: set[str] | None = None,
        loop: asyncio.AbstractEventLoop | None = None,
    ):
        self.monitor = ComplianceMonitor(root, enabled=enabled)
        self._root = Path(root)
        self._on_change = on_change
        self._delay = delay
        self._loop = loop
        self._observer = None
        self._debouncer: AsyncDebouncer | None = None

    def _watch_dir(self) -> Path:
        agents = self._root / "agents"
        return agents if agents.is_dir() else self._root

    async def start(self) -> ViolationDelta:
        """Emit a baseline delta, then begin watching. Returns the baseline."""
        if not HAS_WATCHDOG:
            raise RuntimeError("watchdog is not installed; run: pip install -e .[app]")
        loop = self._loop or asyncio.get_running_loop()
        self._debouncer = AsyncDebouncer(loop, self._delay, self._run)
        baseline = self.monitor.refresh()
        self._on_change(baseline)
        self._observer = Observer()
        self._observer.schedule(OKFEventHandler(self._debouncer), str(self._watch_dir()), recursive=True)
        self._observer.start()
        return baseline

    def _run(self) -> None:
        delta = self.monitor.refresh()
        if delta.changed:
            self._on_change(delta)

    async def stop(self) -> None:
        if self._observer is not None:
            self._observer.stop()
            self._observer.join()
            self._observer = None


# --------------------------------------------------------------------------- #
# Tiny CLI so the pipeline can be run live:  py -m hephaestus.watch <root>
# --------------------------------------------------------------------------- #

def _format(delta: ViolationDelta) -> str:
    lines = []
    for v in delta.added:
        lines.append(f"  + [{v.severity.value:7}] {v.rule_id}  {v.artifact} — {v.message}")
    for v in delta.resolved:
        lines.append(f"  - resolved          {v.rule_id}  {v.artifact}")
    return "\n".join(lines)


async def _amain(root: str) -> None:
    def on_change(delta: ViolationDelta) -> None:
        ts = time.strftime("%H:%M:%S")
        print(f"[{ts}] +{len(delta.added)} -{len(delta.resolved)}  ({len(delta.current)} open)")
        body = _format(delta)
        if body:
            print(body)

    watcher = OKFWatcher(root, on_change)
    await watcher.start()
    print(f"watching {root} … Ctrl-C to stop")
    try:
        while True:
            await asyncio.sleep(3600)
    finally:
        await watcher.stop()


def main(argv: list[str] | None = None) -> int:
    import sys

    args = argv if argv is not None else sys.argv[1:]
    root = args[0] if args else "."
    if not HAS_WATCHDOG:
        print("watchdog not installed. Install with: pip install -e .[app]")
        return 1
    try:
        asyncio.run(_amain(root))
    except KeyboardInterrupt:
        print("\nstopped.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
