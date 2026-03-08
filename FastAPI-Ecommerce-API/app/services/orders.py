from sqlalchemy.orm import Session
from app.models.models import Order, OrderItem, Cart, CartItem
from app.core.security import get_current_user
from fastapi import HTTPException, status
from app.utils.responses import ResponseHandler


class OrderService:
    
    @staticmethod
    def get_all_orders(token, db: Session, page: int, limit: int):
        """Get all orders for the current user"""
        user_id = get_current_user(token)
        
        offset = (page - 1) * limit
        orders = db.query(Order).filter(
            Order.user_id == user_id
        ).order_by(Order.created_at.desc()).offset(offset).limit(limit).all()
        
        return ResponseHandler.success("Orders retrieved successfully", orders)
    
    @staticmethod
    def get_order(token, db: Session, order_id: int):
        """Get a specific order by ID"""
        user_id = get_current_user(token)
        
        order = db.query(Order).filter(
            Order.id == order_id,
            Order.user_id == user_id
        ).first()
        
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )
        
        return ResponseHandler.success("Order retrieved successfully", order)
    
    @staticmethod
    def create_order(token, db: Session):
        """Create an order from the user's cart"""
        user_id = get_current_user(token)
        
        # Get the user's latest cart
        cart = db.query(Cart).filter(Cart.user_id == user_id).order_by(Cart.id.desc()).first()
        
        print(f"DEBUG: create_order user_id={user_id}")
        print(f"DEBUG: found cart={cart}")
        if cart:
            print(f"DEBUG: cart items count={len(cart.cart_items)}")

        if not cart or not cart.cart_items:
            # Debugging info in error message since logs are not visible
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cart failure. UserID: {user_id}. Cart Found: {cart.id if cart else 'None'}. Items: {len(cart.cart_items) if cart and cart.cart_items else 0}"
            )
        
        # Calculate total from cart items (don't rely on cart.total_amount)
        total_amount = sum(item.subtotal for item in cart.cart_items)
        
        # Create order
        new_order = Order(
            user_id=user_id,
            total_amount=total_amount,
            status="confirmed"
        )
        db.add(new_order)
        db.flush()  # Get the order ID
        
        # Create order items from cart items
        for cart_item in cart.cart_items:
            product = cart_item.product
            # Use dynamic price if active, otherwise use regular price
            if product.is_dynamic_pricing_active and product.dynamic_price:
                effective_price = product.dynamic_price
                discount_pct = 0  # Dynamic pricing already accounts for adjustments
                discount_amt = 0
            else:
                effective_price = product.price
                discount_pct = product.discount_percentage or 0
                discount_amt = effective_price * (discount_pct / 100)
            
            order_item = OrderItem(
                order_id=new_order.id,
                product_id=cart_item.product_id,
                product_title=product.title,
                product_price=effective_price,
                discount_percentage=discount_pct,
                discount_amount=discount_amt,
                quantity=cart_item.quantity,
                subtotal=cart_item.subtotal
            )
            db.add(order_item)
            
            # Reduce product stock
            cart_item.product.stock -= cart_item.quantity
        
        # Delete cart items and cart
        db.query(CartItem).filter(CartItem.cart_id == cart.id).delete()
        db.query(Cart).filter(Cart.id == cart.id).delete()
        
        db.commit()
        db.refresh(new_order)
        
        return ResponseHandler.success("Order placed successfully", new_order)
    
    @staticmethod
    def cancel_order(token, db: Session, order_id: int):
        """Cancel an order (only if status is pending or confirmed)"""
        user_id = get_current_user(token)
        
        order = db.query(Order).filter(
            Order.id == order_id,
            Order.user_id == user_id
        ).first()
        
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )
        
        if order.status not in ["pending", "confirmed"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot cancel order with status: " + order.status
            )
        
        # Restore product stock
        for item in order.order_items:
            if item.product:
                item.product.stock += item.quantity
        
        order.status = "cancelled"
        db.commit()
        db.refresh(order)
        
        return ResponseHandler.success("Order cancelled successfully", order)
