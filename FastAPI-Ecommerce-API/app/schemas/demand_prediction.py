from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from enum import Enum


class HolidayEnum(str, Enum):
    NoHoliday = "No Holiday"
    Christmas = "Christmas"
    NewYear = "New Year"
    Easter = "Easter"
    Thanksgiving = "Thanksgiving"
    BlackFriday = "Black Friday"
    CyberMonday = "Cyber Monday"
    ValentinesDay = "Valentine's Day"
    MothersDay = "Mother's Day"
    FathersDay = "Father's Day"
    Independence = "Independence Day"


class WeatherEnum(str, Enum):
    Overcast = "Overcast"
    Sunny = "Sunny"
    Rainy = "Rainy"
    Cloudy = "Cloudy"
    Stormy = "Stormy"
    Snowy = "Snowy"
    Clear = "Clear"


class DemandLevelEnum(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    very_high = "very_high"


# Base config for all schemas
class BaseConfig:
    from_attributes = True


# Request schema for demand prediction
class DemandPredictionRequest(BaseModel):
    """Input schema for demand prediction"""
    product_id: int = Field(..., description="Product ID to predict demand for")
    holiday: HolidayEnum = Field(default=HolidayEnum.NoHoliday, description="Holiday condition")
    weather: WeatherEnum = Field(default=WeatherEnum.Overcast, description="Weather condition")

    class Config:
        json_schema_extra = {
            "example": {
                "product_id": 1,
                "holiday": "No Holiday",
                "weather": "Overcast"
            }
        }


# Request schema for bulk demand prediction
class BulkDemandPredictionRequest(BaseModel):
    """Input schema for bulk demand prediction"""
    product_ids: Optional[List[int]] = Field(default=None, description="List of product IDs to predict. If empty, predict for all products")
    holiday: HolidayEnum = Field(default=HolidayEnum.NoHoliday, description="Holiday condition")
    weather: WeatherEnum = Field(default=WeatherEnum.Overcast, description="Weather condition")


# Response schema for prediction
class DemandPredictionResult(BaseModel):
    product_id: int
    product_title: str
    product_thumbnail: Optional[str] = None
    base_forecast: float
    trend_score: Optional[float] = None
    sentiment_score: Optional[float] = None
    multiplier: float = 1.0
    adjusted_forecast: float
    demand_level: str
    demand_change_pct: Optional[float] = None

    class Config(BaseConfig):
        pass


class DemandPredictionResponse(BaseModel):
    success: bool
    history_id: int
    prediction: DemandPredictionResult
    message: str

    class Config(BaseConfig):
        pass


class BulkDemandPredictionResponse(BaseModel):
    success: bool
    total_products: int
    predictions: List[DemandPredictionResult]
    message: str

    class Config(BaseConfig):
        pass


# History item schema
class DemandPredictionHistoryItem(BaseModel):
    id: int
    product_id: int
    admin_id: Optional[int] = None
    holiday_input: str
    weather_input: str
    base_forecast: float
    trend_score: Optional[float] = None
    sentiment_score: Optional[float] = None
    multiplier: float = 1.0
    adjusted_forecast: float
    demand_level: str
    demand_change_pct: Optional[float] = None
    status: str
    created_at: datetime
    acknowledged_at: Optional[datetime] = None
    product_title: Optional[str] = None
    product_thumbnail: Optional[str] = None
    product_price: Optional[float] = None
    product_stock: Optional[int] = None

    class Config(BaseConfig):
        pass


class DemandPredictionHistoryListResponse(BaseModel):
    message: str
    data: List[DemandPredictionHistoryItem]

    class Config(BaseConfig):
        pass


# Product with demand info for admin view
class ProductDemandInfo(BaseModel):
    id: int
    title: str
    price: int
    stock: int
    brand: str
    thumbnail: str
    category_name: Optional[str] = None
    latest_forecast: Optional[float] = None
    latest_demand_level: Optional[str] = None
    pending_predictions: int = 0

    class Config(BaseConfig):
        pass


class ProductsDemandListResponse(BaseModel):
    message: str
    data: List[ProductDemandInfo]

    class Config(BaseConfig):
        pass


# Trending products for carousel
class TrendingProduct(BaseModel):
    id: int
    product_id: int
    product_title: str
    product_thumbnail: str
    product_price: float
    product_stock: int
    brand: str
    category_name: Optional[str] = None
    adjusted_forecast: float
    demand_level: str
    demand_change_pct: Optional[float] = None
    trend_direction: str = "stable"  # up, down, stable
    trend_score: Optional[float] = None

    class Config(BaseConfig):
        pass


class TrendingProductsResponse(BaseModel):
    message: str
    data: List[TrendingProduct]

    class Config(BaseConfig):
        pass
