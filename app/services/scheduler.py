import asyncio
from datetime import UTC, datetime

from fastapi import FastAPI

from app.api.probes import run_probe_cycle


class MonitoringScheduler:
    def __init__(self, app: FastAPI, interval_s: float) -> None:
        self.app = app
        self.interval_s = interval_s
        self._task: asyncio.Task[None] | None = None
        self._stop_event = asyncio.Event()
        self._run_lock = asyncio.Lock()
        self.last_run: datetime | None = None
        self.last_error: str | None = None

    @property
    def running(self) -> bool:
        return self._task is not None and not self._task.done()

    async def start(self) -> None:
        if self.running:
            return
        self._stop_event = asyncio.Event()
        self._task = asyncio.create_task(self._loop())

    async def stop(self) -> None:
        if self._task is None:
            return
        self._stop_event.set()
        self._task.cancel()
        try:
            await self._task
        except asyncio.CancelledError:
            pass
        self._task = None

    async def run_once(self) -> int:
        async with self._run_lock:
            try:
                results = await asyncio.to_thread(run_probe_cycle, self.app, None)
                self.last_run = datetime.now(UTC)
                self.last_error = None
                return len(results)
            except Exception as exc:
                self.last_error = str(exc)
                raise

    async def _loop(self) -> None:
        try:
            while not self._stop_event.is_set():
                await asyncio.sleep(self.interval_s)
                if self._stop_event.is_set():
                    break
                try:
                    await self.run_once()
                except Exception:
                    continue
        except asyncio.CancelledError:
            return
