from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Literal
from enum import Enum


class PricingStatusEnum(str, Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class BrandTierEnum(str, Enum):
    Budget = "Budget"
    Premium = "Premium"
    Luxury = "Luxury"


class SeasonEnum(str, Enum):
    Spring = "Spring"
    Summer = "Summer"
    Fall = "Fall"
    Winter = "Winter"


class CategoryEnum(str, Enum):
    Electronics = "Electronics"
    Wearables = "Wearables"
    Gaming = "Gaming"
    Home = "Home"
    Fashion = "Fashion"
    Beauty = "Beauty"


# Base config for all schemas
class BaseConfig:
    from_attributes = True


# Request schema for ML prediction
class DynamicPricingPredictRequest(BaseModel):
    """Input schema for dynamic price prediction"""
    product_id: int = Field(..., description="Product ID to predict price for")
    
    # ML Input Features
    category: CategoryEnum = Field(..., description="Product category")
    brand_tier: BrandTierEnum = Field(..., description="Brand tier")
    msrp: float = Field(..., gt=0, description="Manufacturer's Suggested Retail Price")
    cogs: float = Field(..., gt=0, description="Cost of Goods Sold")
    min_margin_req: float = Field(0.1, ge=0, le=1, description="Minimum margin requirement (0-1)")
    inventory_qty: int = Field(..., ge=0, description="Current inventory quantity")
    weeks_of_cover: float = Field(..., ge=0, description="Weeks of inventory cover")
    sell_through_rate: float = Field(..., ge=0, le=1, description="Sell-through rate (0-1)")
    stock_age_days: int = Field(..., ge=0, description="Age of stock in days")
    daily_sales_velocity: float = Field(..., ge=0, description="Daily sales velocity")
    conversion_rate: float = Field(..., ge=0, le=1, description="Conversion rate (0-1)")
    cart_abandon_rate: float = Field(..., ge=0, le=1, description="Cart abandonment rate (0-1)")
    competitor_price: float = Field(..., gt=0, description="Competitor's price")
    competitor_price_diff_pct: float = Field(..., description="Price diff pct from competitor")
    competitor_stock_status: Literal[0, 1] = Field(..., description="Competitor stock status (0=Out, 1=In)")
    market_saturation: float = Field(..., ge=0, le=1, description="Market saturation (0-1)")
    season: SeasonEnum = Field(..., description="Current season")
    holiday_event: Literal[0, 1] = Field(..., description="Holiday event flag")
    marketing_spend_boost: Literal[0, 1] = Field(..., description="Marketing spend boost flag")

    class Config:
        json_schema_extra = {
            "example": {
                "product_id": 1,
                "category": "Electronics",
                "brand_tier": "Luxury",
                "msrp": 1302.0,
                "cogs": 800.19,
                "min_margin_req": 0.1,
                "inventory_qty": 254,
                "weeks_of_cover": 0.6,
                "sell_through_rate": 0.6,
                "stock_age_days": 48,
                "daily_sales_velocity": 57.3,
                "conversion_rate": 0.078,
                "cart_abandon_rate": 0.74,
                "competitor_price": 1117.99,
                "competitor_price_diff_pct": 0.165,
                "competitor_stock_status": 1,
                "market_saturation": 0.34,
                "season": "Fall",
                "holiday_event": 1,
                "marketing_spend_boost": 0,
            }
        }


# Response schema for prediction
class PricingAnalysis(BaseModel):
    margin: float
    margin_percentage: float
    discount_from_msrp_pct: float
    meets_min_margin: bool


class DynamicPricingPredictResponse(BaseModel):
    success: bool
    history_id: int
    product_id: int
    product_title: str
    original_price: float
    predicted_price: float
    discount_percentage: float
    savings_amount: float
    pricing_analysis: PricingAnalysis
    status: str = "pending"
    message: str

    class Config(BaseConfig):
        pass


# Schema for approve/reject
class DynamicPricingDecision(BaseModel):
    history_id: int


# History item schema
class DynamicPricingHistoryBase(BaseModel):
    id: int
    product_id: int
    admin_id: Optional[int]
    predicted_price: float
    original_price: float
    discount_from_original: float
    status: str
    category: str
    brand_tier: str
    msrp: float
    cogs: float
    min_margin_req: float
    inventory_qty: int
    weeks_of_cover: float
    sell_through_rate: float
    stock_age_days: int
    daily_sales_velocity: float
    conversion_rate: float
    cart_abandon_rate: float
    competitor_price: float
    competitor_price_diff_pct: float
    competitor_stock_status: int
    market_saturation: float
    season: str
    holiday_event: int
    marketing_spend_boost: int
    created_at: datetime
    decided_at: Optional[datetime]

    class Config(BaseConfig):
        pass


class DynamicPricingHistoryWithProduct(DynamicPricingHistoryBase):
    """History with product info"""
    product_title: Optional[str] = None
    product_thumbnail: Optional[str] = None

    class Config(BaseConfig):
        pass


# List response
class DynamicPricingHistoryListResponse(BaseModel):
    message: str
    data: List[DynamicPricingHistoryWithProduct]

    class Config(BaseConfig):
        pass


# Single response
class DynamicPricingHistoryResponse(BaseModel):
    message: str
    data: DynamicPricingHistoryWithProduct

    class Config(BaseConfig):
        pass


# Product with dynamic pricing info for admin view
class ProductDynamicPricingInfo(BaseModel):
    id: int
    title: str
    price: int
    base_price: Optional[float]
    dynamic_price: Optional[float]
    is_dynamic_pricing_active: bool
    discount_percentage: float
    stock: int
    brand: str
    thumbnail: str
    category_name: Optional[str] = None
    pending_predictions: int = 0

    class Config(BaseConfig):
        pass


class ProductsDynamicPricingListResponse(BaseModel):
    message: str
    data: List[ProductDynamicPricingInfo]

    class Config(BaseConfig):
        pass


# Deactivate dynamic pricing
class DeactivateDynamicPricingResponse(BaseModel):
    success: bool
    message: str
    product_id: int
    product_title: str
