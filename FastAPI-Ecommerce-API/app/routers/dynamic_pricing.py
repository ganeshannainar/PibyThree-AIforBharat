from fastapi import APIRouter, Depends, Query, status, Header
from app.db.database import get_db
from app.services.dynamic_pricing import DynamicPricingService
from sqlalchemy.orm import Session
from app.schemas.dynamic_pricing import (
    DynamicPricingPredictRequest,
    DynamicPricingPredictResponse,
    DynamicPricingHistoryListResponse,
    ProductsDynamicPricingListResponse,
)
from app.core.security import check_admin_role
from typing import Optional
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Dynamic Pricing"], prefix="/dynamic-pricing")


# Get all products with dynamic pricing info (for admin dashboard)
@router.get(
    "/products",
    status_code=status.HTTP_200_OK,
    response_model=ProductsDynamicPricingListResponse,
    dependencies=[Depends(check_admin_role)]
)
def get_products_for_pricing(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    authorization: str = Header(...),
):
    logger.info(f"📋 ROUTER: GET /dynamic-pricing/products - page={page}, limit={limit}")
    token = authorization.replace("Bearer ", "")
    return DynamicPricingService.get_products_for_pricing(token, db, page, limit)


# Predict dynamic price for a product
@router.post(
    "/predict",
    status_code=status.HTTP_200_OK,
    response_model=DynamicPricingPredictResponse,
    dependencies=[Depends(check_admin_role)]
)
def predict_price(
    request: DynamicPricingPredictRequest,
    db: Session = Depends(get_db),
    authorization: str = Header(...),
):
    logger.info(f"🔮 ROUTER: POST /dynamic-pricing/predict - Product ID: {request.product_id}")
    token = authorization.replace("Bearer ", "")
    return DynamicPricingService.predict_price(token, db, request)


# Approve a pending prediction
@router.post(
    "/approve/{history_id}",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(check_admin_role)]
)
def approve_prediction(
    history_id: int,
    db: Session = Depends(get_db),
    authorization: str = Header(...),
):
    logger.info(f"✅ ROUTER: POST /dynamic-pricing/approve/{history_id} - Approving prediction")
    token = authorization.replace("Bearer ", "")
    return DynamicPricingService.approve_prediction(token, db, history_id)


# Reject a pending prediction
@router.post(
    "/reject/{history_id}",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(check_admin_role)]
)
def reject_prediction(
    history_id: int,
    db: Session = Depends(get_db),
    authorization: str = Header(...),
):
    logger.info(f"❌ ROUTER: POST /dynamic-pricing/reject/{history_id} - Rejecting prediction")
    token = authorization.replace("Bearer ", "")
    return DynamicPricingService.reject_prediction(token, db, history_id)


# Deactivate dynamic pricing for a product
@router.post(
    "/deactivate/{product_id}",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(check_admin_role)]
)
def deactivate_dynamic_pricing(
    product_id: int,
    db: Session = Depends(get_db),
    authorization: str = Header(...),
):
    token = authorization.replace("Bearer ", "")
    return DynamicPricingService.deactivate_dynamic_pricing(token, db, product_id)


# Get all pricing history
@router.get(
    "/history",
    status_code=status.HTTP_200_OK,
    response_model=DynamicPricingHistoryListResponse,
    dependencies=[Depends(check_admin_role)]
)
def get_all_history(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    status_filter: Optional[str] = Query(None, description="Filter by status: pending, approved, rejected"),
    authorization: str = Header(...),
):
    token = authorization.replace("Bearer ", "")
    return DynamicPricingService.get_all_history(token, db, page, limit, status_filter)


# Get pricing history for a specific product
@router.get(
    "/history/{product_id}",
    status_code=status.HTTP_200_OK,
    response_model=DynamicPricingHistoryListResponse,
    dependencies=[Depends(check_admin_role)]
)
def get_product_history(
    product_id: int,
    db: Session = Depends(get_db),
    authorization: str = Header(...),
):
    token = authorization.replace("Bearer ", "")
    return DynamicPricingService.get_product_history(token, db, product_id)


# Flush all pricing history
@router.delete(
    "/history/flush",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(check_admin_role)]
)
def flush_history(
    db: Session = Depends(get_db),
    status_filter: Optional[str] = Query(None, description="Filter by status: pending, approved, rejected"),
    authorization: str = Header(...),
):
    logger.info(f"🗑️ ROUTER: DELETE /dynamic-pricing/history/flush - status_filter={status_filter}")
    token = authorization.replace("Bearer ", "")
    return DynamicPricingService.flush_history(token, db, status_filter)


# Get top price changes for dashboard
@router.get(
    "/top-changes",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(check_admin_role)]
)
def get_top_changes(
    db: Session = Depends(get_db),
    limit: int = Query(3, ge=1, le=10, description="Number of top changes to return"),
    authorization: str = Header(...),
):
    logger.info(f"📊 ROUTER: GET /dynamic-pricing/top-changes - limit={limit}")
    token = authorization.replace("Bearer ", "")
    return DynamicPricingService.get_top_changes(token, db, limit)


# Update prediction status (approve, reject, or reset)
@router.put(
    "/history/{history_id}/status",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(check_admin_role)]
)
def update_prediction_status(
    history_id: int,
    new_status: str = Query(..., description="New status: approved, rejected, pending, or deactivated"),
    db: Session = Depends(get_db),
    authorization: str = Header(...),
):
    logger.info(f"📝 ROUTER: PUT /dynamic-pricing/history/{history_id}/status - new_status={new_status}")
    token = authorization.replace("Bearer ", "")
    return DynamicPricingService.update_prediction_status(token, db, history_id, new_status)


# Get dynamic pricing stats
@router.get(
    "/stats",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(check_admin_role)]
)
def get_stats(
    db: Session = Depends(get_db),
    authorization: str = Header(...),
):
    logger.info("📊 ROUTER: GET /dynamic-pricing/stats")
    token = authorization.replace("Bearer ", "")
    return DynamicPricingService.get_stats(token, db)

