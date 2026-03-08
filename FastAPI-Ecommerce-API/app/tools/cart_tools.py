"""
Cart Tools - Handles adding, removing, and placing orders.
Converted to LangChain @tool format for use with React agents.
"""
import logging
import json
from typing import Dict, Any
from langchain_core.tools import tool
from sqlalchemy.orm import Session
from app.models.models import Cart, CartItem, Order, OrderItem, Product

logger = logging.getLogger(__name__)

# Store context for tool access (set by agent before invoking)
_db_session: Session = None
_user_id: int = None
_fetched_items: list = []


def set_cart_context(db: Session, user_id: int, fetched_items: list = None):
    """Set the context for cart tools access."""
    global _db_session, _user_id, _fetched_items
    _db_session = db
    _user_id = user_id
    _fetched_items = fetched_items or []


def get_cart_context():
    """Get the current cart context."""
    global _db_session, _user_id, _fetched_items
    return _db_session, _user_id, _fetched_items


@tool
def add_to_cart(product_id: int = None, quantity: int = 1) -> str:
    """
    Adds a product to the user's shopping cart.
    Use this when the user wants to add an item to their cart.
    
    Args:
        product_id: The ID of the product to add. If not provided, uses the first item from currently displayed products.
        quantity: Number of units to add (default: 1)
    
    Returns:
        JSON string with success status and message.
    """
    db, user_id, fetched_items = get_cart_context()
    
    if not db or not user_id:
        return json.dumps({"success": False, "message": "Please log in to add items to cart."})
    
    # If no product_id, try to use first fetched item
    pid = product_id
    if not pid and fetched_items:
        pid = fetched_items[0].get("id")
    
    if not pid:
        return json.dumps({"success": False, "message": "Please specify which product to add to cart."})
    
    logger.info(f"Adding product {pid} to cart for user {user_id}")
    try:
        product = db.query(Product).filter(Product.id == pid).first()
        if not product:
            return json.dumps({"success": False, "message": f"Product with ID {pid} not found."})
        
        if product.stock < quantity:
            return json.dumps({"success": False, "message": f"Only {product.stock} units of '{product.title}' available."})
        
        # Get or create cart
        cart = db.query(Cart).filter(Cart.user_id == user_id).order_by(Cart.id.desc()).first()
        if not cart:
            cart = Cart(user_id=user_id, total_amount=0)
            db.add(cart)
            db.flush()
        
        # Calculate price (dynamic or regular)
        if product.is_dynamic_pricing_active and product.dynamic_price:
            effective_price = product.dynamic_price
        else:
            effective_price = product.price * (1 - (product.discount_percentage or 0) / 100)
        
        subtotal = quantity * effective_price
        
        # Check if item exists
        cart_item = db.query(CartItem).filter(CartItem.cart_id == cart.id, CartItem.product_id == pid).first()
        if cart_item:
            cart_item.quantity += quantity
            cart_item.subtotal += subtotal
        else:
            cart_item = CartItem(cart_id=cart.id, product_id=pid, quantity=quantity, subtotal=subtotal)
            db.add(cart_item)
        
        cart.total_amount += subtotal
        db.commit()
        
        return json.dumps({
            "success": True, 
            "message": f"Added {quantity} of '{product.title}' to cart.",
            "cart_total": float(cart.total_amount),
            "action": "cart_updated",
            "type": "add"
        })
    except Exception as e:
        logger.error(f"Error in add_to_cart: {e}")
        db.rollback()
        return json.dumps({"success": False, "message": str(e)})


@tool
def remove_from_cart(product_name: str) -> str:
    """
    Removes a product from the user's shopping cart based on product name.
    Use this when the user wants to remove an item from their cart.
    
    Args:
        product_name: Name or partial name of the product to remove.
    
    Returns:
        JSON string with success status and message.
    """
    db, user_id, _ = get_cart_context()
    
    if not db or not user_id:
        return json.dumps({"success": False, "message": "Please log in to modify your cart."})
    
    try:
        cart = db.query(Cart).filter(Cart.user_id == user_id).order_by(Cart.id.desc()).first()
        if not cart or not cart.cart_items:
            return json.dumps({"success": False, "message": "Your cart is empty."})
        
        # Find the item
        target_item = None
        for item in cart.cart_items:
            if product_name.lower() in item.product.title.lower():
                target_item = item
                break
        
        if not target_item:
            return json.dumps({"success": False, "message": f"'{product_name}' not found in your cart."})
        
        product_title = target_item.product.title
        cart.total_amount -= target_item.subtotal
        db.delete(target_item)
        db.commit()
        
        return json.dumps({
            "success": True, 
            "message": f"Removed '{product_title}' from your cart.",
            "cart_total": float(cart.total_amount),
            "action": "cart_updated",
            "type": "remove"
        })
    except Exception as e:
        logger.error(f"Error in remove_from_cart: {e}")
        db.rollback()
        return json.dumps({"success": False, "message": str(e)})


@tool
def place_order() -> str:
    """
    Places an order from the current shopping cart contents.
    Use this when the user wants to checkout or place their order.
    
    Returns:
        JSON string with order confirmation or error message.
    """
    db, user_id, _ = get_cart_context()
    
    if not db or not user_id:
        return json.dumps({"success": False, "message": "Please log in to place an order."})
    
    try:
        cart = db.query(Cart).filter(Cart.user_id == user_id).order_by(Cart.id.desc()).first()
        if not cart or not cart.cart_items:
            return json.dumps({"success": False, "message": "Your cart is empty."})
        
        total_amount = sum(item.subtotal for item in cart.cart_items)
        
        new_order = Order(user_id=user_id, total_amount=total_amount, status="confirmed")
        db.add(new_order)
        db.flush()
        
        for cart_item in cart.cart_items:
            product = cart_item.product
            product.stock -= cart_item.quantity
            
            order_item = OrderItem(
                order_id=new_order.id,
                product_id=cart_item.product_id,
                product_title=product.title,
                product_price=cart_item.subtotal / cart_item.quantity,
                quantity=cart_item.quantity,
                subtotal=cart_item.subtotal
            )
            db.add(order_item)
        
        # Clear cart
        db.query(CartItem).filter(CartItem.cart_id == cart.id).delete()
        db.query(Cart).filter(Cart.id == cart.id).delete()
        
        db.commit()
        return json.dumps({
            "success": True, 
            "message": f"Order #{new_order.id} placed successfully!",
            "order_id": new_order.id,
            "total": float(total_amount),
            "action": "cart_updated",
            "type": "place_order"
        })
    except Exception as e:
        logger.error(f"Error in place_order: {e}")
        db.rollback()
        return json.dumps({"success": False, "message": str(e)})


@tool
def view_cart() -> str:
    """
    Views the current contents of the user's shopping cart.
    Use this when the user asks what's in their cart.
    
    Returns:
        JSON string with cart contents or message if empty.
    """
    db, user_id, _ = get_cart_context()
    
    if not db or not user_id:
        return json.dumps({"success": False, "message": "Please log in to view your cart."})
    
    try:
        cart = db.query(Cart).filter(Cart.user_id == user_id).order_by(Cart.id.desc()).first()
        if not cart or not cart.cart_items:
            return json.dumps({"success": True, "message": "Your cart is currently empty.", "items": []})
        
        items = [{
            "id": i.product_id,
            "title": i.product.title,
            "quantity": i.quantity,
            "price": float(i.product.price),
            "subtotal": float(i.subtotal)
        } for i in cart.cart_items]
        
        return json.dumps({
            "success": True,
            "items": items,
            "total": float(cart.total_amount),
            "message": f"Your cart has {len(items)} items totaling ${cart.total_amount:.2f}"
        })
    except Exception as e:
        logger.error(f"Error in view_cart: {e}")
        return json.dumps({"success": False, "message": str(e)})


@tool
def view_orders() -> str:
    """
    Views the user's order history.
    Use this when the user asks about their past orders or order status.
    
    Returns:
        JSON string with order history.
    """
    db, user_id, _ = get_cart_context()
    
    if not db or not user_id:
        return json.dumps({"success": False, "message": "Please log in to view your orders."})
    
    try:
        orders = db.query(Order).filter(Order.user_id == user_id).order_by(Order.created_at.desc()).limit(5).all()
        if not orders:
            return json.dumps({"success": True, "message": "You haven't placed any orders yet.", "orders": []})
        
        order_list = [{
            "id": o.id,
            "status": o.status,
            "total": float(o.total_amount)
        } for o in orders]
        
        latest = orders[0]
        return json.dumps({
            "success": True,
            "orders": order_list,
            "message": f"You have {len(orders)} recent orders. Your latest order #{latest.id} is {latest.status}."
        })
    except Exception as e:
        logger.error(f"Error in view_orders: {e}")
        return json.dumps({"success": False, "message": str(e)})


# Legacy functions for backwards compatibility
def add_to_cart_tool(db: Session, user_id: int, product_id: int, quantity: int = 1) -> Dict[str, Any]:
    """Legacy function - use add_to_cart tool instead."""
    set_cart_context(db, user_id)
    result = json.loads(add_to_cart.invoke({"product_id": product_id, "quantity": quantity}))
    return result


def remove_from_cart_tool(db: Session, user_id: int, product_name_query: str) -> Dict[str, Any]:
    """Legacy function - use remove_from_cart tool instead."""
    set_cart_context(db, user_id)
    result = json.loads(remove_from_cart.invoke({"product_name": product_name_query}))
    return result


def place_order_tool(db: Session, user_id: int) -> Dict[str, Any]:
    """Legacy function - use place_order tool instead."""
    set_cart_context(db, user_id)
    result = json.loads(place_order.invoke({}))
    return result
