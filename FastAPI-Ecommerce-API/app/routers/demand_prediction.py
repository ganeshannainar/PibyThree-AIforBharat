from fastapi import APIRouter, Depends, Query, status, Header
from app.db.database import get_db
from app.services.demand_prediction import DemandPredictionService
from sqlalchemy.orm import Session
from app.schemas.demand_prediction import (
    DemandPredictionRequest,
    BulkDemandPredictionRequest,
    DemandPredictionResponse,
    BulkDemandPredictionResponse,
    DemandPredictionHistoryListResponse,
    ProductsDemandListResponse,
    TrendingProductsResponse,
)
from app.core.security import check_admin_role
from typing import Optional
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Demand Prediction"], prefix="/demand-prediction")


# Get all products with demand info (for admin dashboard)
@router.get(
    "/products",
    status_code=status.HTTP_200_OK,
    response_model=ProductsDemandListResponse,
    dependencies=[Depends(check_admin_role)]
)
def get_products_for_demand(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    demand_level: Optional[str] = Query(None, description="Filter by demand level: low, medium, high, very_high"),
    authorization: str = Header(...),
):
    logger.info(f"📋 ROUTER: GET /demand-prediction/products - page={page}, limit={limit}, demand_level={demand_level}")
    token = authorization.replace("Bearer ", "")
    return DemandPredictionService.get_products_for_demand(token, db, page, limit, demand_level)


# Predict demand for a single product
@router.post(
    "/predict",
    status_code=status.HTTP_200_OK,
    response_model=DemandPredictionResponse,
    dependencies=[Depends(check_admin_role)]
)
def predict_demand(
    request: DemandPredictionRequest,
    db: Session = Depends(get_db),
    authorization: str = Header(...),
):
    logger.info(f"🔮 ROUTER: POST /demand-prediction/predict - Product ID: {request.product_id}")
    token = authorization.replace("Bearer ", "")
    return DemandPredictionService.predict_demand(token, db, request)


# Predict demand for multiple products
@router.post(
    "/predict-bulk",
    status_code=status.HTTP_200_OK,
    response_model=BulkDemandPredictionResponse,
    dependencies=[Depends(check_admin_role)]
)
def predict_bulk_demand(
    request: BulkDemandPredictionRequest,
    db: Session = Depends(get_db),
    authorization: str = Header(...),
):
    logger.info(f"🔮 ROUTER: POST /demand-prediction/predict-bulk")
    token = authorization.replace("Bearer ", "")
    return DemandPredictionService.predict_bulk_demand(token, db, request)


# Acknowledge a pending prediction
@router.post(
    "/acknowledge/{history_id}",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(check_admin_role)]
)
def acknowledge_prediction(
    history_id: int,
    db: Session = Depends(get_db),
    authorization: str = Header(...),
):
    logger.info(f"✅ ROUTER: POST /demand-prediction/acknowledge/{history_id}")
    token = authorization.replace("Bearer ", "")
    return DemandPredictionService.acknowledge_prediction(token, db, history_id)


# Get trending products for carousel (public, but enriched if logged in)
@router.get(
    "/trending",
    status_code=status.HTTP_200_OK,
    response_model=TrendingProductsResponse,
)
def get_trending_products(
    db: Session = Depends(get_db),
    limit: int = Query(10, ge=1, le=20, description="Number of trending products"),
    authorization: Optional[str] = Header(default=None),
):
    logger.info(f"📈 ROUTER: GET /demand-prediction/trending - limit={limit}")
    token = authorization.replace("Bearer ", "") if authorization else None
    return DemandPredictionService.get_trending_products(token, db, limit)


# Get all prediction history
@router.get(
    "/history",
    status_code=status.HTTP_200_OK,
    response_model=DemandPredictionHistoryListResponse,
    dependencies=[Depends(check_admin_role)]
)
def get_all_history(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    status_filter: Optional[str] = Query(None, description="Filter by status: pending, acknowledged"),
    demand_level: Optional[str] = Query(None, description="Filter by demand level: low, medium, high, very_high"),
    authorization: str = Header(...),
):
    token = authorization.replace("Bearer ", "")
    return DemandPredictionService.get_all_history(token, db, page, limit, status_filter, demand_level)


# Get prediction history for a specific product
@router.get(
    "/history/{product_id}",
    status_code=status.HTTP_200_OK,
    response_model=DemandPredictionHistoryListResponse,
    dependencies=[Depends(check_admin_role)]
)
def get_product_history(
    product_id: int,
    db: Session = Depends(get_db),
    authorization: str = Header(...),
):
    token = authorization.replace("Bearer ", "")
    return DemandPredictionService.get_product_history(token, db, product_id)


# Get demand statistics for dashboard
@router.get(
    "/stats",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(check_admin_role)]
)
def get_demand_stats(
    db: Session = Depends(get_db),
    authorization: str = Header(...),
):
    logger.info(f"📊 ROUTER: GET /demand-prediction/stats")
    token = authorization.replace("Bearer ", "")
    return DemandPredictionService.get_demand_stats(token, db)


# Delete a demand prediction history record
@router.delete(
    "/history/{history_id}",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(check_admin_role)]
)
def delete_prediction(
    history_id: int,
    db: Session = Depends(get_db),
    authorization: str = Header(...),
):
    logger.info(f"🗑️ ROUTER: DELETE /demand-prediction/history/{history_id}")
    token = authorization.replace("Bearer ", "")
    return DemandPredictionService.delete_prediction(token, db, history_id)
