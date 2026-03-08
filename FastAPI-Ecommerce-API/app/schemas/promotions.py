from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum


class PromotionStatus(str, Enum):
    draft = "draft"      # Just created, pending admin review
    live = "live"        # Approved and showing on carousel
    expired = "expired"  # Past expiry or manually deactivated


class PromotionBase(BaseModel):
    product_id: int
    product_title: str
    product_description: str
    product_thumbnail: str
    product_brand: str
    category_name: str
    original_price: float
    dynamic_price: float
    discount_percentage: float
    savings_amount: float


class PromotionCreate(PromotionBase):
    dynamic_pricing_history_id: int


class PromotionUpdate(BaseModel):
    """Schema for admin to update promotion content before going live"""
    headline: Optional[str] = None
    tagline: Optional[str] = None
    promotion_text: Optional[str] = None


class RegenerateContentRequest(BaseModel):
    """Schema for regenerating content with optional custom prompts"""
    custom_text_prompt: Optional[str] = None  # Custom instructions for text generation
    custom_image_prompt: Optional[str] = None  # Custom instructions for image generation
    regenerate_image: bool = False  # Whether to also regenerate the image


class GenerateImageRequest(BaseModel):
    """Schema for generating promotional image"""
    custom_prompt: Optional[str] = None  # Custom prompt for image generation


# Default prompts that admin can view/modify
DEFAULT_TEXT_PROMPT = """You are an expert e-commerce marketing specialist and copywriter. Your task is to create compelling, conversion-optimized promotional content for products with dynamic pricing (AI-optimized discounts).

When given product and pricing information, you must generate:
1. A catchy HEADLINE (max 50 chars) - Use emojis, create urgency, highlight the discount
2. A persuasive TAGLINE (max 100 chars) - Focus on value proposition and savings
3. A PROMOTIONAL_TEXT (max 200 chars) - Detailed but concise marketing copy

Guidelines:
- Create urgency without being pushy
- Highlight the savings amount and percentage
- Use power words: "Exclusive", "Limited", "Smart Savings", "Best Value"
- Include relevant emojis to make it visually appealing
- Make it feel like a personalized, AI-curated deal
- Focus on the value the customer is getting

Response Format (JSON only, no markdown):
{
    "headline": "🔥 Your catchy headline here",
    "tagline": "Your persuasive tagline focusing on value",
    "promotional_text": "Your detailed marketing copy here"
}"""

DEFAULT_IMAGE_PROMPT = """Create a professional e-commerce promotional banner image:
- Modern, clean design with vibrant gradient colors
- Show a prominent discount/sale badge
- Include "SALE" or "SPECIAL OFFER" text overlay
- Professional retail aesthetic suitable for homepage carousel
- 16:9 landscape orientation, eye-catching hero banner style
- Do NOT include any placeholder text"""


class PromotionResponse(PromotionBase):
    id: int
    dynamic_pricing_history_id: int
    promotion_image_url: Optional[str] = None
    promotion_text: Optional[str] = None
    headline: Optional[str] = None
    tagline: Optional[str] = None
    status: str  # Changed from PromotionStatus to str for flexibility
    is_active: bool
    created_at: datetime
    expires_at: Optional[datetime] = None
    # Add prompt fields so admin can see what was used
    text_prompt_used: Optional[str] = None
    image_prompt_used: Optional[str] = None
    
    class Config:
        from_attributes = True


class PromotionDetailResponse(BaseModel):
    success: bool
    data: PromotionResponse
    message: Optional[str] = None


class PromotionListResponse(BaseModel):
    success: bool
    data: List[PromotionResponse]
    total: int


class PromotionCarouselItem(BaseModel):
    """Simplified promotion data for carousel display"""
    id: int
    product_id: int
    product_title: str
    product_thumbnail: str
    product_brand: str
    category_name: str
    original_price: float
    dynamic_price: float
    discount_percentage: float
    savings_amount: float
    promotion_image_url: Optional[str] = None
    headline: str
    tagline: str
    
    class Config:
        from_attributes = True


class CarouselResponse(BaseModel):
    success: bool
    promotions: List[PromotionCarouselItem]
    total: int


class GenerateImageRequest(BaseModel):
    promotion_id: int


class GenerateImageResponse(BaseModel):
    success: bool
    promotion_id: int
    image_url: Optional[str] = None
    message: str
    prompt_used: Optional[str] = None


class DefaultPromptsResponse(BaseModel):
    """Response containing default prompts for admin reference"""
    text_prompt: str
    image_prompt: str
