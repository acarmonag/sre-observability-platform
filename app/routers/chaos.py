"""Chaos engineering injection endpoints."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from app.middleware.metrics import update_chaos_gauges
from app.services.chaos_service import chaos_service

router = APIRouter(prefix="/chaos", tags=["chaos"])


def _sync_gauges() -> None:
    update_chaos_gauges(chaos_service.active_modes())


@router.post("/memory-leak")
async def trigger_memory_leak() -> dict[str, Any]:
    result = chaos_service.start_memory_leak()
    _sync_gauges()
    return result


@router.post("/latency-spike")
async def trigger_latency_spike(duration_seconds: int = 60) -> dict[str, Any]:
    result = chaos_service.start_latency_spike(duration_seconds)
    _sync_gauges()
    return result


@router.post("/error-rate")
async def trigger_error_rate(duration_seconds: int = 60) -> dict[str, Any]:
    result = chaos_service.start_error_rate(duration_seconds)
    _sync_gauges()
    return result


@router.post("/cpu-spike")
async def trigger_cpu_spike(duration_seconds: int = 30) -> dict[str, Any]:
    result = chaos_service.start_cpu_spike(duration_seconds)
    _sync_gauges()
    return result


@router.delete("/reset")
async def reset_chaos() -> dict[str, Any]:
    result = chaos_service.reset_all()
    _sync_gauges()
    return result


@router.get("/status")
async def chaos_status() -> dict[str, Any]:
    modes = chaos_service.active_modes()
    return {
        "active_modes": modes,
        "chaos_active": len(modes) > 0,
        "modes": {
            "memory_leak": chaos_service.is_memory_leak_active(),
            "latency_spike": chaos_service.is_latency_spike_active(),
            "error_rate": chaos_service.is_error_rate_active(),
            "cpu_spike": chaos_service.is_cpu_spike_active(),
        },
    }
