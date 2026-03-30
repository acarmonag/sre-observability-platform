"""Product catalog endpoints."""
from __future__ import annotations

import asyncio
import random

from fastapi import APIRouter, HTTPException, Request
from opentelemetry import trace

from app.models.product import ProductResponse
from app.services.chaos_service import chaos_service
from app.services.product_service import product_service

router = APIRouter(prefix="/products", tags=["products"])
tracer = trace.get_tracer("sre.products")


@router.get("", response_model=list[ProductResponse])
async def list_products(request: Request) -> list[ProductResponse]:
    with tracer.start_as_current_span("list_products") as span:
        modes = chaos_service.active_modes()
        span.set_attribute("chaos_mode_active", str(bool(modes)))

        if chaos_service.is_latency_spike_active():
            extra_ms = random.uniform(2000, 5000)
            span.set_attribute("simulated_latency_ms", extra_ms)
            await asyncio.sleep(extra_ms / 1000)

        products = await product_service.list_products_async()
        return [ProductResponse(**p.model_dump()) for p in products]


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(product_id: str, request: Request) -> ProductResponse:
    with tracer.start_as_current_span("get_product") as span:
        span.set_attribute("product_id", product_id)

        if chaos_service.is_latency_spike_active():
            extra_ms = random.uniform(2000, 5000)
            span.set_attribute("simulated_latency_ms", extra_ms)
            await asyncio.sleep(extra_ms / 1000)

        product = await product_service.get_product_async(product_id)
        if product is None:
            raise HTTPException(status_code=404, detail=f"Product {product_id} not found")

        return ProductResponse(**product.model_dump())
