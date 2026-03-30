from __future__ import annotations

import uuid
from typing import Optional

from pydantic import BaseModel, Field


class Product(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = None
    price: float = Field(ge=0)
    category: str
    in_stock: bool = True
    stock_quantity: int = Field(ge=0, default=100)
    sku: str = ""

    def model_post_init(self, __context: object) -> None:
        if not self.sku:
            self.sku = f"SKU-{self.id[:8].upper()}"


class ProductResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    price: float
    category: str
    in_stock: bool
    stock_quantity: int
    sku: str
