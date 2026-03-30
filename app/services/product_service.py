"""Simulated product catalog service."""
from __future__ import annotations

import asyncio
import random
import uuid
from typing import Optional

from app.models.product import Product


# Fixed catalog of products for consistency across runs
_CATALOG = [
    Product(id="prod-0001", name="Laptop Pro 15", description="High-performance laptop", price=1299.99, category="Electronics", stock_quantity=50, sku="SKU-LAPTOP01"),
    Product(id="prod-0002", name="Wireless Mouse", description="Ergonomic wireless mouse", price=49.99, category="Electronics", stock_quantity=200, sku="SKU-MOUSE01"),
    Product(id="prod-0003", name="USB-C Hub 7-in-1", description="Multi-port USB-C hub", price=79.99, category="Electronics", stock_quantity=150, sku="SKU-HUB001"),
    Product(id="prod-0004", name="Mechanical Keyboard", description="Tactile mechanical switches", price=149.99, category="Electronics", stock_quantity=75, sku="SKU-KB001"),
    Product(id="prod-0005", name="4K Monitor 27\"", description="Ultra-wide color gamut", price=599.99, category="Electronics", stock_quantity=30, sku="SKU-MON001"),
    Product(id="prod-0006", name="Running Shoes", description="Lightweight trail runners", price=119.99, category="Footwear", stock_quantity=120, sku="SKU-SHOE01"),
    Product(id="prod-0007", name="Yoga Mat", description="Non-slip premium mat", price=39.99, category="Sports", stock_quantity=180, sku="SKU-YOGA01"),
    Product(id="prod-0008", name="Coffee Maker", description="12-cup programmable", price=89.99, category="Kitchen", stock_quantity=60, sku="SKU-COFF01"),
    Product(id="prod-0009", name="Desk Lamp LED", description="Adjustable color temperature", price=59.99, category="Office", stock_quantity=90, sku="SKU-LAMP01"),
    Product(id="prod-0010", name="Backpack 30L", description="Waterproof hiking backpack", price=79.99, category="Outdoor", stock_quantity=110, sku="SKU-PACK01"),
]


class ProductService:
    def __init__(self) -> None:
        self._products: dict[str, Product] = {p.id: p for p in _CATALOG}

    def list_products(self) -> list[Product]:
        return list(self._products.values())

    def get_product(self, product_id: str) -> Optional[Product]:
        return self._products.get(product_id)

    async def list_products_async(self) -> list[Product]:
        # Simulate catalog query: 30-150ms
        await asyncio.sleep(random.uniform(0.03, 0.15))
        return self.list_products()

    async def get_product_async(self, product_id: str) -> Optional[Product]:
        await asyncio.sleep(random.uniform(0.01, 0.05))
        return self.get_product(product_id)


# Module-level singleton
product_service = ProductService()
