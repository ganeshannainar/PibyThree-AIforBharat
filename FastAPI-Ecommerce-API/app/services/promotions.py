import os
import uuid
import base64
import asyncio
import httpx
from datetime import datetime, timedelta
from typing import Optional, List, Set
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.models import DynamicPromotion, Product, DynamicPricingHistory, Category, Order, OrderItem, Cart, CartItem
from app.schemas.promotions import PromotionCreate, PromotionCarouselItem
from app.utils.responses import ResponseHandler
from app.core.security import get_token_payload
from app.core.config import settings
from app.core.logging_config import (
    promotions_logger as logger,
    gemini_logger,
    log_flow_start,
    log_flow_end,
    log_step
)
import boto3
import json
from botocore.config import Config
from app.core.llm import llm

# Google Generative AI
# from google import genai
# from google.genai import types


def get_user_id_from_token(token: str) -> int:
    """Extract user ID from token string"""
    payload = get_token_payload(token)
    return payload.get('id')


# Path to save generated images
PROMOTIONS_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'uploads', 'promotions')
os.makedirs(PROMOTIONS_DIR, exist_ok=True)


# System prompt for Gemini to generate promotional content
PROMOTION_SYSTEM_PROMPT = """You are an expert e-commerce marketing specialist and copywriter. Your task is to create compelling, conversion-optimized promotional content for products with dynamic pricing.

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
}

Remember: These are dynamic, AI-optimized prices - make the customer feel they're getting a smart, personalized deal!"""


# Pollinations models to try in order
# POLLINATIONS_MODELS = ["flux", "turbo", "flux-realism", "flux-anime"]

# Hugging Face public image models (no key needed for free tier inference)
# These are text-to-image models on the HF Inference API
# HF_MODELS = [
#     "black-forest-labs/FLUX.1-schnell",
#     "stabilityai/stable-diffusion-xl-base-1.0",
#     "runwayml/stable-diffusion-v1-5",
# ]


class GeminiPromoGenerator:
    """
    AI Promotion Generator using AWS Bedrock

    Text Generation:
        Claude 4.5 Sonnet

    Image Generation:
        amazon titan image generation
    """

    def __init__(self):

        self.region = os.environ.get("AWS_REGION", "us-east-1")

        self.bedrock = boto3.client(
            service_name="bedrock-runtime",
            region_name=self.region,
            config=Config(
                read_timeout=300,
                retries={"max_attempts": 3}
            )
        )

        gemini_logger.info("AWS Bedrock initialized successfully")

    # ─────────────────────────────────────────────
    # TEXT GENERATION — Claude Sonnet
    # ─────────────────────────────────────────────

    def generate_promotional_content(
        self,
        product_info: dict,
        custom_prompt: Optional[str] = None
    ) -> dict:

        gemini_logger.info(
            f"📝 BEDROCK TEXT: Generating for {product_info.get('title')}"
        )

        try:

            system_prompt = custom_prompt or PROMOTION_SYSTEM_PROMPT

            prompt = f"""{system_prompt}

Product Information:
- Product Name: {product_info['title']}
- Brand: {product_info['brand']}
- Category: {product_info['category']}
- Description: {product_info.get('description','')[:200]}

Pricing:
Original Price: ${product_info['original_price']:.2f}
Dynamic Price: ${product_info['dynamic_price']:.2f}
Discount: {product_info['discount_percentage']:.1f}%
Savings: ${product_info['savings_amount']:.2f}

Return JSON only.
"""

            body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 500,
                "temperature": 0.7,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            }

            response = self.bedrock.invoke_model(
                modelId="global.anthropic.claude-sonnet-4-5-20250929-v1:0",
                body=json.dumps(body)
            )

            result = json.loads(response["body"].read())

            text = result["content"][0]["text"]

            # Remove markdown if Claude returns it
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]

            data = json.loads(text)

            headline = data.get("headline")
            tagline = data.get("tagline")
            promotional_text = data.get("promotional_text")

            if not headline or not tagline:
                return self._generate_fallback_content(product_info)

            return {
                "headline": headline,
                "tagline": tagline,
                "promotional_text": promotional_text
            }

        except Exception as e:

            gemini_logger.error(f"Bedrock Claude text generation failed: {e}")

            return self._generate_fallback_content(product_info)

    # ─────────────────────────────────────────────
    # IMAGE GENERATION — titan image generation
    # ─────────────────────────────────────────────

    async def generate_promotional_image(
        self,
        product_info: dict,
        custom_prompt: Optional[str] = None
    ) -> Optional[str]:

        try:
            prompt = custom_prompt or f"""
            high quality ecommerce promotional banner,
            product photography of {product_info['title']},
            brand {product_info['brand']},
            category {product_info['category']},
            {product_info['discount_percentage']} percent discount badge,
            modern ecommerce hero banner,
            clean studio lighting,
            bright gradient background,
            professional marketing banner,
            ultra realistic
            """

            # Clean prompt
            prompt = " ".join(prompt.split())

            gemini_logger.info(
                f"🖼️ BEDROCK: Invoking Titan image generator with prompt: {prompt[:120]}"
            )

            body = {
                "taskType": "TEXT_IMAGE",
                "textToImageParams": {
                    "text": prompt
                },
                "imageGenerationConfig": {
                    "numberOfImages": 1,
                    "width": 1152,
                    "height": 768,
                    "cfgScale": 8.0,
                    "seed": 4   2
                }
            }

            response = self.bedrock.invoke_model(
                modelId="amazon.titan-image-generator-v2:0",
                contentType="application/json",
                accept="application/json",
                body=json.dumps(body)
            )

            result = json.loads(response["body"].read())

            if "images" not in result or not result["images"]:
                gemini_logger.error(f"❌ No images returned from Titan: {result}")
                return None

            image_base64 = result["images"][0]

            image_bytes = base64.b64decode(image_base64)

            filename = f"{uuid.uuid4()}.png"
            filepath = os.path.join(PROMOTIONS_DIR, filename)

            with open(filepath, "wb") as f:
                f.write(image_bytes)

            gemini_logger.info(f"✅ BEDROCK IMAGE GENERATED: {filename}")

            return f"/static/uploads/promotions/{filename}"

        except Exception as e:

            gemini_logger.error(
                f"❌ Bedrock image generation failed: {e}",
                exc_info=True
            )

            return None
    # ─────────────────────────────────────────────
    # FALLBACK TEXT
    # ─────────────────────────────────────────────

    def _generate_fallback_content(self, product_info: dict) -> dict:

        discount = product_info.get("discount_percentage", 0)
        savings = product_info.get("savings_amount", 0)

        return {
            "headline": f"🔥 {int(discount)}% OFF Limited Deal",
            "tagline": f"Save ${savings:.0f} on {product_info['title']} today!",
            "promotional_text": f"Exclusive AI-priced deal on {product_info['title']}."
        }

# ─────────────────────────────────────────────────────────────────────────────
# PROMOTIONS SERVICE
# ─────────────────────────────────────────────────────────────────────────────

class PromotionsService:

    @staticmethod
    def create_promotion_from_pricing(
        db: Session, history: DynamicPricingHistory, product: Product
    ) -> DynamicPromotion:
        """
        Create a new promotion when dynamic pricing is approved.
        Uses Google Gemini to generate compelling promotional content.
        """
        log_flow_start(logger, "PROMOTION_CREATION", product=product.title)

        category = db.query(Category).filter(Category.id == product.category_id).first()
        category_name = category.name if category else "General"
        log_step(logger, 1, "Looking up category", category=category_name)

        original_price = history.original_price
        dynamic_price = history.predicted_price
        discount_percentage = abs(history.discount_from_original)
        savings_amount = abs(original_price - dynamic_price)

        log_step(logger, 2, "Calculating pricing details",
                 original=f"${original_price:.2f}",
                 dynamic=f"${dynamic_price:.2f}",
                 discount=f"{discount_percentage:.1f}%",
                 savings=f"${savings_amount:.2f}")

        product_info = {
            "title": product.title,
            "brand": product.brand,
            "category": category_name,
            "description": product.description,
            "original_price": original_price,
            "dynamic_price": dynamic_price,
            "discount_percentage": discount_percentage,
            "savings_amount": savings_amount,
            "stock": product.stock,
            "brand_tier": history.brand_tier if hasattr(history, 'brand_tier') else "Standard"
        }

        log_step(logger, 3, "Calling Gemini AI", action="generate promotional content")

        generator = GeminiPromoGenerator()
        content = generator.generate_promotional_content(product_info)

        log_step(logger, 4, "Gemini response received",
                 headline=content['headline'][:40],
                 tagline=content['tagline'][:40])

        promotion = DynamicPromotion(
            dynamic_pricing_history_id=history.id,
            product_id=product.id,
            product_title=product.title,
            product_description=product.description[:500] if product.description else "",
            product_thumbnail=product.thumbnail,
            product_brand=product.brand,
            category_name=category_name,
            original_price=original_price,
            dynamic_price=dynamic_price,
            discount_percentage=round(discount_percentage, 2),
            savings_amount=round(savings_amount, 2),
            headline=content["headline"],
            tagline=content["tagline"],
            promotion_text=content.get("promotional_text", ""),
            status="draft",
            is_active=False,
            expires_at=datetime.utcnow() + timedelta(days=7)
        )

        log_step(logger, 5, "Saving promotion to database (DRAFT status)")

        db.add(promotion)
        db.commit()
        db.refresh(promotion)

        log_flow_end(logger, "PROMOTION_CREATION", True,
                     promotion_id=promotion.id, product=product.title, status="draft")

        return promotion

    @staticmethod
    async def generate_promotion_image(
        db: Session, promotion_id: int, custom_prompt: Optional[str] = None
    ) -> dict:
        """
        Generate AI promotional image.
        Chain: Gemini → Pollinations (multi-model) → HuggingFace → product thumbnail
        """
        logger.info(f"🖼️ SERVICE: Generating image for promotion ID: {promotion_id}")

        promotion = db.query(DynamicPromotion).filter(
            DynamicPromotion.id == promotion_id
        ).first()
        if not promotion:
            logger.warning(f"🖼️ SERVICE: Promotion ID {promotion_id} not found")
            return {
                "success": False,
                "message": "Promotion not found",
                "promotion_id": promotion_id,
            }

        product_info = {
            "title": promotion.product_title,
            "brand": promotion.product_brand,
            "category": promotion.category_name,
            "discount_percentage": promotion.discount_percentage,
            "original_price": promotion.original_price,
            "dynamic_price": promotion.dynamic_price,
            "savings_amount": promotion.savings_amount,
        }

        if custom_prompt:
            final_prompt = (
                custom_prompt.format(
                    title=product_info["title"],
                    brand=product_info["brand"],
                    category=product_info["category"],
                    discount=product_info["discount_percentage"],
                    original_price=product_info["original_price"],
                    dynamic_price=product_info["dynamic_price"],
                    savings=product_info["savings_amount"],
                )
                if "{" in custom_prompt
                else custom_prompt
            )
            logger.info("🖼️ SERVICE: Using CUSTOM image prompt")
        else:
            final_prompt = None
            logger.info("🖼️ SERVICE: Using DEFAULT image prompt")

        generator = GeminiPromoGenerator()
        image_url = await generator.generate_promotional_image(
            product_info, custom_prompt=final_prompt
        )

        prompt_used = final_prompt or f"Default prompt for {product_info['title']}"

        if image_url:
            promotion.promotion_image_url = image_url
            promotion.image_prompt_used = prompt_used
            db.commit()
            db.refresh(promotion)

            logger.info(f"✅ SERVICE: Image generated and saved: {image_url}")
            return {
                "success": True,
                "promotion_id": promotion.id,
                "image_url": image_url,
                "message": "Promotion image generated successfully",
                "prompt_used": prompt_used,
            }

        # Final fallback: product thumbnail
        logger.warning(
            "🖼️ SERVICE: All AI generation failed — using product thumbnail as fallback"
        )
        promotion.promotion_image_url = promotion.product_thumbnail
        promotion.image_prompt_used = "FALLBACK: Using product thumbnail"
        db.commit()

        return {
            "success": True,
            "promotion_id": promotion.id,
            "image_url": promotion.product_thumbnail,
            "message": "Using product thumbnail (all AI image generation methods failed)",
            "prompt_used": "FALLBACK: Product thumbnail",
        }

    @staticmethod
    async def regenerate_promotion_content(
        db: Session,
        promotion_id: int,
        custom_text_prompt: Optional[str] = None,
        custom_image_prompt: Optional[str] = None,
        regenerate_image: bool = False,
    ) -> dict:
        """
        Regenerate promotional content (headline, tagline, text) using Gemini.
        Optionally regenerate the image as well.
        """
        logger.info(f"🔄 SERVICE: Regenerating content for promotion ID: {promotion_id}")

        promotion = db.query(DynamicPromotion).filter(
            DynamicPromotion.id == promotion_id
        ).first()
        if not promotion:
            logger.warning(f"🔄 SERVICE: Promotion ID {promotion_id} not found")
            return {"success": False, "message": "Promotion not found"}

        product_info = {
            "title": promotion.product_title,
            "brand": promotion.product_brand,
            "category": promotion.category_name,
            "description": promotion.product_description,
            "discount_percentage": promotion.discount_percentage,
            "original_price": promotion.original_price,
            "dynamic_price": promotion.dynamic_price,
            "savings_amount": promotion.savings_amount,
        }

        generator = GeminiPromoGenerator()
        content = generator.generate_promotional_content(
            product_info, custom_prompt=custom_text_prompt
        )

        promotion.headline = content["headline"]
        promotion.tagline = content["tagline"]
        promotion.promotion_text = content.get("promotional_text", "")
        promotion.text_prompt_used = custom_text_prompt or "DEFAULT PROMPT"

        image_result = None
        if regenerate_image:
            logger.info("🔄 SERVICE: Also regenerating image...")
            image_url = await generator.generate_promotional_image(
                product_info, custom_prompt=custom_image_prompt
            )
            if image_url:
                promotion.promotion_image_url = image_url
                promotion.image_prompt_used = custom_image_prompt or "DEFAULT PROMPT"
                image_result = image_url
            else:
                logger.warning("🔄 SERVICE: Image regeneration failed — keeping existing image")

        db.commit()
        db.refresh(promotion)

        logger.info("✅ SERVICE: Content regenerated successfully")

        return {
            "success": True,
            "promotion_id": promotion.id,
            "headline": promotion.headline,
            "tagline": promotion.tagline,
            "promotional_text": promotion.promotion_text,
            "image_url": image_result,
            "text_prompt_used": promotion.text_prompt_used,
            "image_prompt_used": promotion.image_prompt_used if regenerate_image else None,
            "message": "Promotional content regenerated successfully",
        }

    @staticmethod
    def get_active_promotions(
        db: Session, limit: int = 10
    ) -> List[PromotionCarouselItem]:
        """Get LIVE promotions for carousel display"""
        logger.info("📱 CAROUSEL: Fetching LIVE promotions for homepage")

        promotions = (
            db.query(DynamicPromotion)
            .filter(
                and_(
                    DynamicPromotion.is_active == True,
                    DynamicPromotion.status.in_(["live", "active"]),
                )
            )
            .order_by(DynamicPromotion.discount_percentage.desc())
            .limit(limit)
            .all()
        )

        logger.info(f"📱 CAROUSEL: Found {len(promotions)} live promotions")
        for p in promotions:
            logger.debug(
                f"   └─ {p.product_title}: {p.discount_percentage:.1f}% off "
                f"(${p.dynamic_price:.2f})"
            )

        return [
            PromotionCarouselItem(
                id=p.id,
                product_id=p.product_id,
                product_title=p.product_title,
                product_thumbnail=p.product_thumbnail,
                product_brand=p.product_brand,
                category_name=p.category_name,
                original_price=p.original_price,
                dynamic_price=p.dynamic_price,
                discount_percentage=p.discount_percentage,
                savings_amount=p.savings_amount,
                promotion_image_url=p.promotion_image_url,
                headline=p.headline or f"🔥 {p.discount_percentage:.0f}% OFF!",
                tagline=p.tagline or f"Save ${p.savings_amount:.0f} on {p.product_title}",
            )
            for p in promotions
        ]

    @staticmethod
    def get_all_promotions(
        db: Session, skip: int = 0, limit: int = 20, status_filter: str = None
    ) -> dict:
        """Get all promotions with pagination (for admin)"""
        query = db.query(DynamicPromotion)

        if status_filter:
            if status_filter == "live":
                query = query.filter(
                    DynamicPromotion.status.in_(["live", "active"])
                )
            else:
                query = query.filter(DynamicPromotion.status == status_filter)

        total = query.count()
        promotions = (
            query.order_by(DynamicPromotion.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

        return {"success": True, "data": promotions, "total": total}

    @staticmethod
    def get_promotion_by_id(db: Session, promotion_id: int) -> dict:
        """Get a single promotion by ID"""
        promotion = db.query(DynamicPromotion).filter(
            DynamicPromotion.id == promotion_id
        ).first()
        if not promotion:
            return {"success": False, "message": "Promotion not found"}
        return {"success": True, "data": promotion}

    @staticmethod
    def update_promotion(
        db: Session,
        promotion_id: int,
        headline: str = None,
        tagline: str = None,
        promotion_text: str = None,
    ) -> dict:
        """Update promotion content (admin editing before going live)"""
        logger.info(f"✏️ UPDATE: Updating promotion ID: {promotion_id}")

        promotion = db.query(DynamicPromotion).filter(
            DynamicPromotion.id == promotion_id
        ).first()
        if not promotion:
            logger.warning(f"✏️ UPDATE: Promotion ID {promotion_id} not found")
            return {"success": False, "message": "Promotion not found"}

        if headline is not None:
            promotion.headline = headline
        if tagline is not None:
            promotion.tagline = tagline
        if promotion_text is not None:
            promotion.promotion_text = promotion_text

        db.commit()
        db.refresh(promotion)

        logger.info("✏️ UPDATE: Promotion updated successfully")
        return {"success": True, "message": "Promotion updated", "data": promotion}

    @staticmethod
    def approve_promotion(db: Session, promotion_id: int) -> dict:
        """Approve a draft promotion - makes it LIVE"""
        logger.info(f"🚀 APPROVE: Making promotion ID {promotion_id} LIVE")

        promotion = db.query(DynamicPromotion).filter(
            DynamicPromotion.id == promotion_id
        ).first()
        if not promotion:
            logger.warning(f"🚀 APPROVE: Promotion ID {promotion_id} not found")
            return {"success": False, "message": "Promotion not found"}

        if promotion.status == "live":
            logger.warning("🚀 APPROVE: Promotion is already live")
            return {"success": False, "message": "Promotion is already live"}

        existing_live = (
            db.query(DynamicPromotion)
            .filter(
                DynamicPromotion.product_id == promotion.product_id,
                DynamicPromotion.status == "live",
                DynamicPromotion.id != promotion_id,
            )
            .all()
        )

        for existing in existing_live:
            existing.status = "expired"
            existing.is_active = False
            logger.info(
                f"🚀 APPROVE: Expired existing live promotion ID {existing.id} "
                f"for product {promotion.product_id}"
            )

        promotion.status = "live"
        promotion.is_active = True
        promotion.expires_at = datetime.utcnow() + timedelta(days=7)
        db.commit()
        db.refresh(promotion)

        logger.info(f"🚀 APPROVE: Promotion '{promotion.headline}' is now LIVE!")
        return {"success": True, "message": "Promotion is now live!", "data": promotion}

    @staticmethod
    def delete_promotion(db: Session, promotion_id: int) -> dict:
        """Delete a promotion"""
        logger.info(f"🗑️ DELETE: Deleting promotion ID: {promotion_id}")

        promotion = db.query(DynamicPromotion).filter(
            DynamicPromotion.id == promotion_id
        ).first()
        if not promotion:
            logger.warning(f"🗑️ DELETE: Promotion ID {promotion_id} not found")
            return {"success": False, "message": "Promotion not found"}

        db.delete(promotion)
        db.commit()

        logger.info(f"🗑️ DELETE: Promotion ID {promotion_id} deleted")
        return {"success": True, "message": "Promotion deleted successfully"}

    @staticmethod
    def deactivate_promotion(db: Session, promotion_id: int) -> dict:
        """Deactivate a promotion"""
        logger.info(f"🔴 DEACTIVATE: Deactivating promotion ID: {promotion_id}")

        promotion = db.query(DynamicPromotion).filter(
            DynamicPromotion.id == promotion_id
        ).first()
        if not promotion:
            logger.warning(f"🔴 DEACTIVATE: Promotion ID {promotion_id} not found")
            return {"success": False, "message": "Promotion not found"}

        promotion.is_active = False
        promotion.status = "expired"
        db.commit()

        logger.info(
            f"🔴 DEACTIVATE: Promotion deactivated for product: {promotion.product_title}"
        )
        return {"success": True, "message": "Promotion deactivated"}

    @staticmethod
    def reactivate_promotion(db: Session, promotion_id: int) -> dict:
        """Reactivate an expired promotion - sets it back to LIVE"""
        logger.info(f"🟢 REACTIVATE: Reactivating promotion ID: {promotion_id}")

        promotion = db.query(DynamicPromotion).filter(
            DynamicPromotion.id == promotion_id
        ).first()
        if not promotion:
            logger.warning(f"🟢 REACTIVATE: Promotion ID {promotion_id} not found")
            return {"success": False, "message": "Promotion not found"}

        promotion.is_active = True
        promotion.status = "live"
        promotion.expires_at = datetime.utcnow() + timedelta(days=7)
        db.commit()

        logger.info(
            f"🟢 REACTIVATE: Promotion reactivated for product: {promotion.product_title}"
        )
        return {"success": True, "message": "Promotion reactivated and is now live"}

    @staticmethod
    def expire_old_promotions(db: Session) -> int:
        """Expire promotions that have passed their expiry date"""
        now = datetime.utcnow()
        expired = (
            db.query(DynamicPromotion)
            .filter(
                and_(
                    DynamicPromotion.is_active == True,
                    DynamicPromotion.expires_at != None,
                    DynamicPromotion.expires_at < now,
                )
            )
            .all()
        )

        count = 0
        for promotion in expired:
            promotion.is_active = False
            promotion.status = "expired"
            count += 1

        if count > 0:
            db.commit()

        return count

    @staticmethod
    def get_user_preferred_categories(db: Session, user_id: int) -> Set[str]:
        """
        Get categories a user is interested in based on order and cart history.
        Returns a set of category names.
        """
        logger.info(
            f"🎯 PERSONALIZATION: Getting preferred categories for user ID: {user_id}"
        )

        preferred_categories: Set[str] = set()

        order_categories = (
            db.query(Category.name)
            .join(Product, Category.id == Product.category_id)
            .join(OrderItem, Product.id == OrderItem.product_id)
            .join(Order, OrderItem.order_id == Order.id)
            .filter(Order.user_id == user_id)
            .distinct()
            .all()
        )

        for (cat_name,) in order_categories:
            preferred_categories.add(cat_name)
            logger.debug(f"   └─ From orders: {cat_name}")

        cart_categories = (
            db.query(Category.name)
            .join(Product, Category.id == Product.category_id)
            .join(CartItem, Product.id == CartItem.product_id)
            .join(Cart, CartItem.cart_id == Cart.id)
            .filter(Cart.user_id == user_id)
            .distinct()
            .all()
        )

        for (cat_name,) in cart_categories:
            preferred_categories.add(cat_name)
            logger.debug(f"   └─ From cart: {cat_name}")

        logger.info(
            f"🎯 PERSONALIZATION: User {user_id} prefers "
            f"{len(preferred_categories)} categories: {preferred_categories}"
        )

        return preferred_categories

    @staticmethod
    def get_personalized_promotions(
        db: Session,
        user_id: Optional[int] = None,
        limit: int = 10,
    ) -> List[PromotionCarouselItem]:
        """
        Get personalized LIVE promotions based on user order/cart history.
        Falls back to all live promotions for anonymous users or no history.
        """
        logger.info(f"🎠 PERSONALIZED CAROUSEL: Fetching for user_id={user_id}")

        all_live_promotions = (
            db.query(DynamicPromotion)
            .filter(
                and_(
                    DynamicPromotion.is_active == True,
                    DynamicPromotion.status.in_(["live", "active"]),
                )
            )
            .order_by(DynamicPromotion.discount_percentage.desc())
            .all()
        )

        logger.info(
            f"🎠 PERSONALIZED CAROUSEL: Total live promotions available: "
            f"{len(all_live_promotions)}"
        )

        if user_id is None:
            logger.info("🎠 PERSONALIZED CAROUSEL: Anonymous user - showing all promotions")
            promotions = all_live_promotions[:limit]
        else:
            preferred_categories = PromotionsService.get_user_preferred_categories(
                db, user_id
            )

            if not preferred_categories:
                logger.info(
                    f"🎠 PERSONALIZED CAROUSEL: User {user_id} has no history "
                    f"- showing all promotions"
                )
                promotions = all_live_promotions[:limit]
            else:
                personalized = [
                    p
                    for p in all_live_promotions
                    if p.category_name in preferred_categories
                ]

                logger.info(
                    f"🎠 PERSONALIZED CAROUSEL: Found {len(personalized)} "
                    f"matching promotions for user {user_id}"
                )

                if personalized:
                    promotions = personalized[:limit]
                    logger.info(
                        f"🎠 PERSONALIZED CAROUSEL: Returning {len(promotions)} "
                        f"personalized promotions"
                    )
                else:
                    logger.info(
                        "🎠 PERSONALIZED CAROUSEL: No category matches "
                        "- falling back to all promotions"
                    )
                    promotions = all_live_promotions[:limit]

        for p in promotions:
            logger.debug(
                f"   └─ {p.product_title} ({p.category_name}): "
                f"{p.discount_percentage:.1f}% off"
            )

        return [
            PromotionCarouselItem(
                id=p.id,
                product_id=p.product_id,
                product_title=p.product_title,
                product_thumbnail=p.product_thumbnail,
                product_brand=p.product_brand,
                category_name=p.category_name,
                original_price=p.original_price,
                dynamic_price=p.dynamic_price,
                discount_percentage=p.discount_percentage,
                savings_amount=p.savings_amount,
                promotion_image_url=p.promotion_image_url,
                headline=p.headline or f"🔥 {p.discount_percentage:.0f}% OFF!",
                tagline=p.tagline or f"Save ${p.savings_amount:.0f} on {p.product_title}",
            )
            for p in promotions
        ]