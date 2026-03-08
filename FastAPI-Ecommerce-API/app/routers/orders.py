from fastapi import APIRouter, Depends, Query, status
from app.db.database import get_db
from app.services.orders import OrderService
from sqlalchemy.orm import Session
from app.schemas.orders import OrderOut, OrdersOut
from fastapi.security import HTTPBearer
from fastapi.security.http import HTTPAuthorizationCredentials

router = APIRouter(tags=["Orders"], prefix="/orders")
auth_scheme = HTTPBearer()


# Get All Orders for current user
@router.get("/", status_code=status.HTTP_200_OK, response_model=OrdersOut)
def get_all_orders(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    token: HTTPAuthorizationCredentials = Depends(auth_scheme)
):
    return OrderService.get_all_orders(token, db, page, limit)


# Get Order By ID
@router.get("/{order_id}", status_code=status.HTTP_200_OK, response_model=OrderOut)
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    token: HTTPAuthorizationCredentials = Depends(auth_scheme)
):
    return OrderService.get_order(token, db, order_id)


# Create Order (Place Order from Cart)
@router.post("/", status_code=status.HTTP_201_CREATED, response_model=OrderOut)
def create_order(
    db: Session = Depends(get_db),
    token: HTTPAuthorizationCredentials = Depends(auth_scheme)
):
    return OrderService.create_order(token, db)


# Cancel Order
@router.put("/{order_id}/cancel", status_code=status.HTTP_200_OK, response_model=OrderOut)
def cancel_order(
    order_id: int,
    db: Session = Depends(get_db),
    token: HTTPAuthorizationCredentials = Depends(auth_scheme)
):
    return OrderService.cancel_order(token, db, order_id)
