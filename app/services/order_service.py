"""Simulated order processing service."""
from __future__ import annotations

import asyncio
import random
import uuid
from datetime import datetime
from typing import Optional

from app.models.order import CreateOrderRequest, Order, OrderItem, OrderStatus
from app.services.product_service import product_service


class OrderService:
    def __init__(self) -> None:
        self._orders: dict[str, Order] = {}
        self._seed_orders()

    def _seed_orders(self) -> None:
        """Pre-populate with some sample orders."""
        products = product_service.list_products()
        customers = ["cust-001", "cust-002", "cust-003", "cust-042", "cust-099"]
        statuses = [OrderStatus.completed, OrderStatus.processing, OrderStatus.pending]

        for i in range(10):
            product = random.choice(products)
            qty = random.randint(1, 5)
            items = [OrderItem(product_id=product.id, quantity=qty, unit_price=product.price)]
            order = Order(
                customer_id=random.choice(customers),
                items=items,
                status=random.choice(statuses),
                total_price=product.price * qty,
                created_at=datetime(2026, 3, random.randint(1, 29), random.randint(0, 23)),
                updated_at=datetime(2026, 3, 30),
            )
            self._orders[order.id] = order

    async def list_orders(self) -> list[Order]:
        # Simulate DB query latency: 50-200ms
        await asyncio.sleep(random.uniform(0.05, 0.20))
        return list(self._orders.values())

    async def create_order(self, req: CreateOrderRequest) -> Order:
        # Simulate order processing: 100-300ms
        await asyncio.sleep(random.uniform(0.10, 0.30))

        # Validate products exist
        for item in req.items:
            product = product_service.get_product(item.product_id)
            if product is None:
                raise ValueError(f"Product {item.product_id} not found")

        order = Order(
            id=str(uuid.uuid4()),
            customer_id=req.customer_id,
            items=req.items,
            status=OrderStatus.processing,
            total_price=sum(i.unit_price * i.quantity for i in req.items),
            notes=req.notes,
        )
        self._orders[order.id] = order

        # Simulate async processing completing
        asyncio.create_task(self._process_order(order.id))
        return order

    async def _process_order(self, order_id: str) -> None:
        await asyncio.sleep(random.uniform(0.5, 2.0))
        if order_id in self._orders:
            order = self._orders[order_id]
            order.status = OrderStatus.completed
            order.updated_at = datetime.utcnow()

    async def get_order(self, order_id: str) -> Optional[Order]:
        # Simulate lookup: 20-100ms
        await asyncio.sleep(random.uniform(0.02, 0.10))
        return self._orders.get(order_id)


# Module-level singleton
order_service = OrderService()
