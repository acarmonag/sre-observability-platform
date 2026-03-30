from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class OrderStatus(str, Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class OrderItem(BaseModel):
    product_id: str
    quantity: int = Field(ge=1)
    unit_price: float


class Order(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    customer_id: str
    items: list[OrderItem]
    status: OrderStatus = OrderStatus.pending
    total_price: float = 0.0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    notes: Optional[str] = None

    def model_post_init(self, __context: object) -> None:
        if self.total_price == 0.0 and self.items:
            self.total_price = sum(i.unit_price * i.quantity for i in self.items)


class CreateOrderRequest(BaseModel):
    customer_id: str
    items: list[OrderItem]
    notes: Optional[str] = None


class OrderResponse(BaseModel):
    id: str
    customer_id: str
    items: list[OrderItem]
    status: OrderStatus
    total_price: float
    created_at: datetime
    updated_at: datetime
    notes: Optional[str] = None
