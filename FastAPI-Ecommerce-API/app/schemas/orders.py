from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class BaseConfig:
    from_attributes = True


# Order Item schemas
class OrderItemBase(BaseModel):
    id: int
    order_id: int
    product_id: Optional[int]
    product_title: str
    product_price: float
    discount_percentage: float
    discount_amount: float
    quantity: int
    subtotal: float

    class Config(BaseConfig):
        pass


# Order schemas
class OrderBase(BaseModel):
    id: int
    user_id: int
    total_amount: float
    status: str
    created_at: datetime
    order_items: List[OrderItemBase]

    class Config(BaseConfig):
        pass


class OrderOut(BaseModel):
    message: str
    data: OrderBase

    class Config(BaseConfig):
        pass


class OrdersOut(BaseModel):
    message: str
    data: List[OrderBase]

    class Config(BaseConfig):
        pass


class OrderCreate(BaseModel):
    # Order is created from cart, no fields needed
    pass

    class Config(BaseConfig):
        pass
