import asyncio
import logging
import time
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
        self.last_cycle_duration_ms: float | None = None
        self.successful_cycles = 0
        self.failed_cycles = 0
        self.consecutive_failures = 0
        self._logger = logging.getLogger('netsentinel.scheduler')

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
            started = time.perf_counter()
            self._logger.info('cycle_start')
            try:
                results = await asyncio.to_thread(run_probe_cycle, self.app, None)
                self.last_cycle_duration_ms = round((time.perf_counter() - started) * 1000, 3)
                self.last_run = datetime.now(UTC)
                self.last_error = None
                self.successful_cycles += 1
                self.consecutive_failures = 0
                up_count = sum(1 for result in results if result.status == 'up')
                down_count = len(results) - up_count
                self._logger.info(
                    'cycle_complete',
                    extra={
                        'duration_ms': self.last_cycle_duration_ms,
                        'probed_nodes': len(results),
                        'up_count': up_count,
                        'down_count': down_count,
                    },
                )
                return len(results)
            except Exception as exc:
                self.last_cycle_duration_ms = round((time.perf_counter() - started) * 1000, 3)
                self.last_error = str(exc)
                self.failed_cycles += 1
                self.consecutive_failures += 1
                self._logger.error(
                    'cycle_failed',
                    extra={
                        'duration_ms': self.last_cycle_duration_ms,
                        'error': self.last_error,
                    },
                )
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
