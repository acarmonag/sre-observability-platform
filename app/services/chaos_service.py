"""Thread-safe chaos engineering state management."""
from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class ChaosState:
    memory_leak_active: bool = False
    latency_spike_active: bool = False
    latency_spike_expires: float = 0.0
    error_rate_active: bool = False
    error_rate_expires: float = 0.0
    cpu_spike_active: bool = False

    # For memory leak simulation — hold references so GC doesn't free them
    _leaked_buffers: list = field(default_factory=list, repr=False)

    def active_modes(self) -> list[str]:
        modes = []
        now = time.time()
        if self.memory_leak_active:
            modes.append("memory_leak")
        if self.latency_spike_active and now < self.latency_spike_expires:
            modes.append("latency_spike")
        elif self.latency_spike_active and now >= self.latency_spike_expires:
            self.latency_spike_active = False
        if self.error_rate_active and now < self.error_rate_expires:
            modes.append("error_rate")
        elif self.error_rate_active and now >= self.error_rate_expires:
            self.error_rate_active = False
        if self.cpu_spike_active:
            modes.append("cpu_spike")
        return modes


class ChaosService:
    """Manages chaos engineering injection state in a thread-safe manner."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._state = ChaosState()
        self._memory_leak_thread: Optional[threading.Thread] = None
        self._cpu_spike_thread: Optional[threading.Thread] = None

    # ------------------------------------------------------------------
    # Read helpers
    # ------------------------------------------------------------------

    def get_state(self) -> ChaosState:
        with self._lock:
            return self._state

    def active_modes(self) -> list[str]:
        with self._lock:
            return self._state.active_modes()

    def is_latency_spike_active(self) -> bool:
        with self._lock:
            now = time.time()
            if self._state.latency_spike_active and now >= self._state.latency_spike_expires:
                self._state.latency_spike_active = False
            return self._state.latency_spike_active

    def is_error_rate_active(self) -> bool:
        with self._lock:
            now = time.time()
            if self._state.error_rate_active and now >= self._state.error_rate_expires:
                self._state.error_rate_active = False
            return self._state.error_rate_active

    def is_memory_leak_active(self) -> bool:
        with self._lock:
            return self._state.memory_leak_active

    def is_cpu_spike_active(self) -> bool:
        with self._lock:
            return self._state.cpu_spike_active

    # ------------------------------------------------------------------
    # Chaos activation
    # ------------------------------------------------------------------

    def start_memory_leak(self) -> dict:
        with self._lock:
            if self._state.memory_leak_active:
                return {"status": "already_active", "mode": "memory_leak"}
            self._state.memory_leak_active = True

        thread = threading.Thread(target=self._memory_leak_worker, daemon=True)
        thread.start()
        with self._lock:
            self._memory_leak_thread = thread

        logger.warning("CHAOS: Memory leak simulation started")
        return {"status": "started", "mode": "memory_leak", "description": "Allocating ~1MB every 2s"}

    def start_latency_spike(self, duration_seconds: int = 60) -> dict:
        with self._lock:
            self._state.latency_spike_active = True
            self._state.latency_spike_expires = time.time() + duration_seconds

        logger.warning("CHAOS: Latency spike activated for %ds", duration_seconds)
        return {
            "status": "started",
            "mode": "latency_spike",
            "duration_seconds": duration_seconds,
            "description": "Adding 2-5s random latency to all endpoints",
        }

    def start_error_rate(self, duration_seconds: int = 60) -> dict:
        with self._lock:
            self._state.error_rate_active = True
            self._state.error_rate_expires = time.time() + duration_seconds

        logger.warning("CHAOS: Error rate injection activated for %ds", duration_seconds)
        return {
            "status": "started",
            "mode": "error_rate",
            "duration_seconds": duration_seconds,
            "description": "50% of /orders requests will return HTTP 500",
        }

    def start_cpu_spike(self, duration_seconds: int = 30) -> dict:
        with self._lock:
            if self._state.cpu_spike_active:
                return {"status": "already_active", "mode": "cpu_spike"}
            self._state.cpu_spike_active = True

        thread = threading.Thread(
            target=self._cpu_spike_worker,
            args=(duration_seconds,),
            daemon=True,
        )
        thread.start()
        with self._lock:
            self._cpu_spike_thread = thread

        logger.warning("CHAOS: CPU spike simulation started for %ds", duration_seconds)
        return {
            "status": "started",
            "mode": "cpu_spike",
            "duration_seconds": duration_seconds,
            "description": "CPU-intensive computation running in background",
        }

    def reset_all(self) -> dict:
        with self._lock:
            self._state.memory_leak_active = False
            self._state.latency_spike_active = False
            self._state.latency_spike_expires = 0.0
            self._state.error_rate_active = False
            self._state.error_rate_expires = 0.0
            self._state.cpu_spike_active = False
            self._state._leaked_buffers.clear()  # Release leaked memory

        logger.warning("CHAOS: All chaos modes reset to normal")
        return {"status": "reset", "message": "All chaos modes disabled"}

    # ------------------------------------------------------------------
    # Background workers
    # ------------------------------------------------------------------

    def _memory_leak_worker(self) -> None:
        """Allocate ~1MB every 2 seconds until stopped."""
        while True:
            with self._lock:
                if not self._state.memory_leak_active:
                    break
                # Allocate ~1MB buffer and hold a reference
                buf = bytearray(1024 * 1024)
                self._state._leaked_buffers.append(buf)
                leaked_mb = len(self._state._leaked_buffers)

            logger.warning("CHAOS: Memory leak — total leaked: %dMB", leaked_mb)
            time.sleep(2)

    def _cpu_spike_worker(self, duration_seconds: int) -> None:
        """Spin CPU for the given duration."""
        deadline = time.time() + duration_seconds
        while time.time() < deadline:
            with self._lock:
                if not self._state.cpu_spike_active:
                    break
            # Busy computation — intentionally wasting CPU
            _ = sum(i * i for i in range(50_000))

        with self._lock:
            self._state.cpu_spike_active = False
        logger.warning("CHAOS: CPU spike ended")


# Module-level singleton
chaos_service = ChaosService()
