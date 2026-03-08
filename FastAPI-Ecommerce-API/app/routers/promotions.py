from fastapi import APIRouter, Depends, HTTPException, Body, Header
from fastapi.security.http import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional
import logging

from app.db.database import get_db
from app.core.security import auth_scheme, get_token_payload
from app.services.promotions import PromotionsService
from app.schemas.promotions import (
    CarouselResponse, 
    PromotionListResponse,
    PromotionDetailResponse,
    PromotionUpdate,
    GenerateImageRequest,
    GenerateImageResponse,
    RegenerateContentRequest,
    DefaultPromptsResponse,
    DEFAULT_TEXT_PROMPT,
    DEFAULT_IMAGE_PROMPT
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/promotions", tags=["Promotions"])


def get_current_user(token: HTTPAuthorizationCredentials = Depends(auth_scheme)):
    """Get current user from token"""
    payload = get_token_payload(token.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    return payload


def require_admin(token: HTTPAuthorizationCredentials = Depends(auth_scheme)):
    """Require admin role"""
    payload = get_token_payload(token.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    return payload


def get_optional_user(authorization: Optional[str] = None):
    """
    Get current user from Authorization header if provided.
    Returns None if no token or invalid token.
    Used for endpoints that work for both anonymous and logged-in users.
    """
    if not authorization:
        return None
    
    # Handle "Bearer <token>" format
    if authorization.startswith("Bearer "):
        token = authorization[7:]
    else:
        token = authorization
    
    try:
        payload = get_token_payload(token)
        return payload
    except:
        return None


# Public endpoint - get LIVE promotions for homepage carousel (personalized if logged in)
@router.get("/carousel", response_model=CarouselResponse)
def get_carousel_promotions(
    limit: int = 5,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    Get LIVE promotions for the homepage carousel.
    
    This endpoint supports personalization:
    - If user is logged in (token provided): Returns promotions filtered by user's
      purchase history and cart items (categories they're interested in)
    - If anonymous or no matching categories: Returns all live promotions
    
    Pass the Authorization header with Bearer token to get personalized results.
    """
    # Try to get user from token if provided
    user = get_optional_user(authorization)
    user_id = user['id'] if user else None
    
    if user_id:
        logger.info(f"🎠 ROUTER: GET /promotions/carousel - PERSONALIZED for user ID: {user_id}")
    else:
        logger.info("🎠 ROUTER: GET /promotions/carousel - Anonymous user (showing all)")
    
    # First, expire any old promotions
    expired_count = PromotionsService.expire_old_promotions(db)
    if expired_count > 0:
        logger.info(f"🎠 ROUTER: Expired {expired_count} old promotions")
    
    # Get personalized or all promotions based on user
    promotions = PromotionsService.get_personalized_promotions(db, user_id=user_id, limit=limit)
    
    logger.info(f"🎠 ROUTER: Returning {len(promotions)} promotions for carousel")
    
    return CarouselResponse(
        success=True,
        promotions=promotions,
        total=len(promotions)
    )


# ==================== ADMIN ENDPOINTS ====================

@router.get("/all", response_model=PromotionListResponse)
def get_all_promotions(
    skip: int = 0,
    limit: int = 20,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    user: dict = Depends(require_admin)
):
    """Get all promotions with optional status filter (admin only)"""
    logger.info(f"📋 ROUTER: GET /promotions/all - status={status}")
    result = PromotionsService.get_all_promotions(db, skip=skip, limit=limit, status_filter=status)
    return result


@router.get("/{promotion_id}", response_model=PromotionDetailResponse)
def get_promotion(
    promotion_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(require_admin)
):
    """Get a single promotion by ID (admin only)"""
    logger.info(f"📋 ROUTER: GET /promotions/{promotion_id}")
    result = PromotionsService.get_promotion_by_id(db, promotion_id)
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result["message"])
    return result


@router.put("/{promotion_id}")
def update_promotion(
    promotion_id: int,
    update_data: PromotionUpdate,
    db: Session = Depends(get_db),
    user: dict = Depends(require_admin)
):
    """
    Update promotion content (admin only).
    Use this to edit AI-generated content before approving.
    """
    logger.info(f"✏️ ROUTER: PUT /promotions/{promotion_id} - Updating content")
    result = PromotionsService.update_promotion(
        db, 
        promotion_id, 
        headline=update_data.headline,
        tagline=update_data.tagline,
        promotion_text=update_data.promotion_text
    )
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result["message"])
    return result


@router.post("/{promotion_id}/approve")
def approve_promotion(
    promotion_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(require_admin)
):
    """
    Approve a draft promotion and make it LIVE (admin only).
    This makes the promotion visible on the homepage carousel.
    """
    logger.info(f"🚀 ROUTER: POST /promotions/{promotion_id}/approve - Making LIVE")
    result = PromotionsService.approve_promotion(db, promotion_id)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.post("/{promotion_id}/regenerate")
async def regenerate_promotion_content(
    promotion_id: int,
    custom_text_prompt: Optional[str] = Body(None),
    custom_image_prompt: Optional[str] = Body(None),
    regenerate_image: bool = Body(False),
    db: Session = Depends(get_db),
    user: dict = Depends(require_admin)
):
    """
    Regenerate promotional content (headline, tagline, text) using Gemini (admin only).
    Optionally provide custom prompts for more control over the generation.
    """
    logger.info(f"🔄 ROUTER: POST /promotions/{promotion_id}/regenerate")
    logger.info(f"   Custom text prompt: {'YES' if custom_text_prompt else 'NO (using default)'}")
    logger.info(f"   Custom image prompt: {'YES' if custom_image_prompt else 'NO (using default)'}")
    logger.info(f"   Regenerate image: {regenerate_image}")
    
    result = await PromotionsService.regenerate_promotion_content(
        db, 
        promotion_id, 
        custom_text_prompt=custom_text_prompt,
        custom_image_prompt=custom_image_prompt,
        regenerate_image=regenerate_image
    )
    return result


@router.post("/generate-image/{promotion_id}", response_model=GenerateImageResponse)
async def generate_promotion_image(
    promotion_id: int,
    custom_prompt: Optional[str] = Body(None, embed=True),
    db: Session = Depends(get_db),
    user: dict = Depends(require_admin)
):
    """
    Generate AI promotional image for a promotion (admin only).
    Uses Gemini 2.0 Flash for image generation.
    Optionally provide a custom prompt.
    """
    logger.info(f"🖼️ ROUTER: POST /promotions/generate-image/{promotion_id}")
    logger.info(f"   Custom prompt: {'YES' if custom_prompt else 'NO (using default)'}")
    
    result = await PromotionsService.generate_promotion_image(db, promotion_id, custom_prompt=custom_prompt)
    return GenerateImageResponse(**result)


@router.get("/admin/default-prompts", response_model=DefaultPromptsResponse)
def get_default_prompts(
    user: dict = Depends(require_admin)
):
    """
    Get the default prompts used for content and image generation (admin only).
    Admins can use these as a starting point for custom prompts.
    """
    logger.info("📋 ROUTER: GET /promotions/admin/default-prompts")
    return DefaultPromptsResponse(
        text_prompt=DEFAULT_TEXT_PROMPT,
        image_prompt=DEFAULT_IMAGE_PROMPT
    )


@router.post("/{promotion_id}/deactivate")
def deactivate_promotion(
    promotion_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(require_admin)
):
    """Deactivate a live promotion (admin only)"""
    logger.info(f"🔴 ROUTER: POST /promotions/{promotion_id}/deactivate")
    return PromotionsService.deactivate_promotion(db, promotion_id)


@router.post("/{promotion_id}/reactivate")
def reactivate_promotion(
    promotion_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(require_admin)
):
    """Reactivate an expired promotion (admin only)"""
    logger.info(f"🟢 ROUTER: POST /promotions/{promotion_id}/reactivate")
    return PromotionsService.reactivate_promotion(db, promotion_id)


@router.delete("/{promotion_id}")
def delete_promotion(
    promotion_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(require_admin)
):
    """Delete a promotion (admin only)"""
    logger.info(f"🗑️ ROUTER: DELETE /promotions/{promotion_id}")
    return PromotionsService.delete_promotion(db, promotion_id)


@router.post("/expire-old")
def expire_old_promotions(
    db: Session = Depends(get_db),
    user: dict = Depends(require_admin)
):
    """Manually trigger expiration of old promotions (admin only)"""
    count = PromotionsService.expire_old_promotions(db)
    return {"success": True, "expired_count": count}
