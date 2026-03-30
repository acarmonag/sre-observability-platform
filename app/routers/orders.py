"""Order management endpoints."""
from __future__ import annotations

import asyncio
import random

from fastapi import APIRouter, HTTPException, Request
from opentelemetry import trace

from app.middleware.metrics import orders_created_total, orders_processed_total
from app.models.order import CreateOrderRequest, OrderResponse
from app.services.chaos_service import chaos_service
from app.services.order_service import order_service

router = APIRouter(prefix="/orders", tags=["orders"])
tracer = trace.get_tracer("sre.orders")


@router.get("", response_model=list[OrderResponse])
async def list_orders(request: Request) -> list[OrderResponse]:
    with tracer.start_as_current_span("list_orders") as span:
        modes = chaos_service.active_modes()
        span.set_attribute("chaos_mode_active", str(bool(modes)))
        span.set_attribute("chaos_modes", ",".join(modes))

        if chaos_service.is_latency_spike_active():
            extra_ms = random.uniform(2000, 5000)
            span.set_attribute("simulated_latency_ms", extra_ms)
            await asyncio.sleep(extra_ms / 1000)

        if chaos_service.is_error_rate_active() and random.random() < 0.5:
            raise HTTPException(status_code=500, detail="Simulated server error (chaos: error_rate)")

        orders = await order_service.list_orders()
        return [OrderResponse(**o.model_dump()) for o in orders]


@router.post("", response_model=OrderResponse, status_code=201)
async def create_order(req: CreateOrderRequest, request: Request) -> OrderResponse:
    with tracer.start_as_current_span("create_order") as span:
        modes = chaos_service.active_modes()
        span.set_attribute("chaos_mode_active", str(bool(modes)))
        span.set_attribute("customer_id", req.customer_id)

        if chaos_service.is_latency_spike_active():
            extra_ms = random.uniform(2000, 5000)
            span.set_attribute("simulated_latency_ms", extra_ms)
            await asyncio.sleep(extra_ms / 1000)

        if chaos_service.is_error_rate_active() and random.random() < 0.5:
            raise HTTPException(status_code=500, detail="Simulated server error (chaos: error_rate)")

        try:
            order = await order_service.create_order(req)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

        span.set_attribute("order_id", order.id)
        orders_created_total.inc()
        orders_processed_total.inc()
        return OrderResponse(**order.model_dump())


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(order_id: str, request: Request) -> OrderResponse:
    with tracer.start_as_current_span("get_order") as span:
        span.set_attribute("order_id", order_id)
        modes = chaos_service.active_modes()
        span.set_attribute("chaos_mode_active", str(bool(modes)))

        if chaos_service.is_latency_spike_active():
            extra_ms = random.uniform(2000, 5000)
            span.set_attribute("simulated_latency_ms", extra_ms)
            await asyncio.sleep(extra_ms / 1000)

        order = await order_service.get_order(order_id)
        if order is None:
            raise HTTPException(status_code=404, detail=f"Order {order_id} not found")

        return OrderResponse(**order.model_dump())
