from sqlalchemy import Boolean, Column, Integer, String, ForeignKey, Float, ARRAY, Enum, Text, JSON, DateTime
from sqlalchemy.sql.expression import text
from sqlalchemy.sql.sqltypes import TIMESTAMP
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta
from app.db.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, nullable=False, unique=True, autoincrement=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    is_active = Column(Boolean, server_default="True", nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("NOW()"), nullable=False)

    # New column for role
    role = Column(Enum("admin", "user", name="user_roles"), nullable=False, server_default="user")

    # Relationship with carts
    carts = relationship("Cart", back_populates="user")
    
    # Relationship with orders
    orders = relationship("Order", back_populates="user")


class Cart(Base):
    __tablename__ = "carts"

    id = Column(Integer, primary_key=True, nullable=False, unique=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("NOW()"), nullable=False)
    total_amount = Column(Float, nullable=False)

    # Relationship with user
    user = relationship("User", back_populates="carts")

    # Relationship with cart items
    cart_items = relationship("CartItem", back_populates="cart")


class CartItem(Base):
    __tablename__ = "cart_items"

    id = Column(Integer, primary_key=True, nullable=False, unique=True, autoincrement=True)
    cart_id = Column(Integer, ForeignKey("carts.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    quantity = Column(Integer, nullable=False)
    subtotal = Column(Float, nullable=False)

    # Relationship with cart and product
    cart = relationship("Cart", back_populates="cart_items")
    product = relationship("Product", back_populates="cart_items")


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, nullable=False, unique=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)

    # Relationship with products
    products = relationship("Product", back_populates="category")


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, nullable=False, unique=True, autoincrement=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=False)
    price = Column(Integer, nullable=False)  # Current effective price
    base_price = Column(Float, nullable=True)  # Original MSRP price
    dynamic_price = Column(Float, nullable=True)  # ML predicted price
    is_dynamic_pricing_active = Column(Boolean, server_default="False", nullable=False)
    discount_percentage = Column(Float, nullable=False)
    rating = Column(Float, nullable=False)
    stock = Column(Integer, nullable=False)
    brand = Column(String, nullable=False)
    thumbnail = Column(String, nullable=False)
    images = Column(ARRAY(String), nullable=False)
    is_published = Column(Boolean, server_default="True", nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("NOW()"), nullable=False)

    # Relationship with category
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="CASCADE"), nullable=False)
    category = relationship("Category", back_populates="products")

    # Relationship with cart items
    cart_items = relationship("CartItem", back_populates="product", cascade="all, delete-orphan")
    
    # Relationship with order items
    order_items = relationship("OrderItem", back_populates="product")
    
    # Relationship with dynamic pricing history - cascade delete when product is deleted
    dynamic_pricing_history = relationship("DynamicPricingHistory", back_populates="product", cascade="all, delete-orphan")
    
    # Relationship with dynamic promotions - cascade delete when product is deleted
    promotions = relationship("DynamicPromotion", back_populates="product", cascade="all, delete-orphan")
    
    # Relationship with demand predictions - cascade delete when product is deleted
    demand_predictions = relationship("DemandPredictionHistory", back_populates="product", cascade="all, delete-orphan")


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, nullable=False, unique=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    total_amount = Column(Float, nullable=False)
    status = Column(Enum("pending", "confirmed", "shipped", "delivered", "cancelled", name="order_status"), 
                   nullable=False, server_default="confirmed")
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("NOW()"), nullable=False)

    # Relationship with user
    user = relationship("User", back_populates="orders")
    
    # Relationship with order items
    order_items = relationship("OrderItem", back_populates="order")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, nullable=False, unique=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="SET NULL"), nullable=True)
    product_title = Column(String, nullable=False)
    product_price = Column(Float, nullable=False)
    discount_percentage = Column(Float, nullable=False, server_default="0")
    discount_amount = Column(Float, nullable=False, server_default="0")
    quantity = Column(Integer, nullable=False)
    subtotal = Column(Float, nullable=False)

    # Relationship with order and product
    order = relationship("Order", back_populates="order_items")
    product = relationship("Product", back_populates="order_items")


class DynamicPricingHistory(Base):
    """Stores ML prediction history for audit and retraining purposes"""
    __tablename__ = "dynamic_pricing_history"

    id = Column(Integer, primary_key=True, nullable=False, unique=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    admin_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # Prediction results
    predicted_price = Column(Float, nullable=False)
    original_price = Column(Float, nullable=False)  # Price at time of prediction
    discount_from_original = Column(Float, nullable=False)  # Percentage discount
    
    # Status: pending, approved, rejected
    status = Column(Enum("pending", "approved", "rejected", name="pricing_status"), 
                   nullable=False, server_default="pending")
    
    # ML Model Input Features (stored for audit/retraining)
    category = Column(String, nullable=False)
    brand_tier = Column(String, nullable=False)
    msrp = Column(Float, nullable=False)
    cogs = Column(Float, nullable=False)
    min_margin_req = Column(Float, nullable=False)
    inventory_qty = Column(Integer, nullable=False)
    weeks_of_cover = Column(Float, nullable=False)
    sell_through_rate = Column(Float, nullable=False)
    stock_age_days = Column(Integer, nullable=False)
    daily_sales_velocity = Column(Float, nullable=False)
    conversion_rate = Column(Float, nullable=False)
    cart_abandon_rate = Column(Float, nullable=False)
    competitor_price = Column(Float, nullable=False)
    competitor_price_diff_pct = Column(Float, nullable=False)
    competitor_stock_status = Column(Integer, nullable=False)  # 0 or 1
    market_saturation = Column(Float, nullable=False)
    season = Column(String, nullable=False)
    holiday_event = Column(Integer, nullable=False)  # 0 or 1
    marketing_spend_boost = Column(Integer, nullable=False)  # 0 or 1
    
    # Timestamps
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("NOW()"), nullable=False)
    decided_at = Column(TIMESTAMP(timezone=True), nullable=True)  # When approved/rejected
    
    # Relationships
    product = relationship("Product", back_populates="dynamic_pricing_history")
    admin = relationship("User")


class DynamicPromotion(Base):
    """Stores promotional banners for products with active dynamic pricing"""
    __tablename__ = "dynamic_promotions"

    id = Column(Integer, primary_key=True, nullable=False, unique=True, autoincrement=True)
    
    # Link to dynamic pricing history
    dynamic_pricing_history_id = Column(Integer, ForeignKey("dynamic_pricing_history.id", ondelete="CASCADE"), nullable=False)
    
    # Product info snapshot (denormalized for quick access)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    product_title = Column(String, nullable=False)
    product_description = Column(Text, nullable=False)
    product_thumbnail = Column(String, nullable=False)
    product_brand = Column(String, nullable=False)
    category_name = Column(String, nullable=False)
    
    # Pricing info
    original_price = Column(Float, nullable=False)
    dynamic_price = Column(Float, nullable=False)
    discount_percentage = Column(Float, nullable=False)
    savings_amount = Column(Float, nullable=False)
    
    # Generated promotion content
    promotion_image_url = Column(String, nullable=True)  # AI-generated image URL
    promotion_text = Column(Text, nullable=True)  # Full promotional text
    headline = Column(String, nullable=True)  # Short headline for banner
    tagline = Column(String, nullable=True)  # Catchy tagline
    
    # Store prompts used for regeneration/audit
    text_prompt_used = Column(Text, nullable=True)  # The prompt used to generate text
    image_prompt_used = Column(Text, nullable=True)  # The prompt used to generate image
    
    # Status and timing
    status = Column(String, nullable=False, server_default="draft")  # draft, live, expired
    is_active = Column(Boolean, server_default="False", nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("NOW()"), nullable=False)
    expires_at = Column(TIMESTAMP(timezone=True), nullable=True)  # Optional expiration
    
    # Relationships
    product = relationship("Product", back_populates="promotions")
    pricing_history = relationship("DynamicPricingHistory")


class ProductSalesData(Base):
    """Historical sales data for demand prediction model"""
    __tablename__ = "product_sales_data"

    id = Column(Integer, primary_key=True, nullable=False, unique=True, autoincrement=True)
    product_id = Column(String, nullable=False)  # String to match TFT model format
    time_idx = Column(Integer, nullable=False)  # Time index for sequence
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    week = Column(Integer, nullable=False)
    Holiday = Column(String, nullable=False, default="No Holiday")
    weather = Column(String, nullable=False, default="Overcast")
    total_sales = Column(Float, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("NOW()"), nullable=False)


class DemandPredictionHistory(Base):
    """Stores demand prediction history for each product"""
    __tablename__ = "demand_prediction_history"

    id = Column(Integer, primary_key=True, nullable=False, unique=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    admin_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # Prediction inputs
    holiday_input = Column(String, nullable=False, default="No Holiday")
    weather_input = Column(String, nullable=False, default="Overcast")
    
    # Prediction results
    base_forecast = Column(Float, nullable=False)
    trend_score = Column(Float, nullable=True)
    sentiment_score = Column(Float, nullable=True)
    multiplier = Column(Float, nullable=True, default=1.0)
    adjusted_forecast = Column(Float, nullable=False)
    
    # Demand classification
    demand_level = Column(String, nullable=False)  # low, medium, high, very_high
    demand_change_pct = Column(Float, nullable=True)  # Change from previous prediction
    
    # Status: pending, acknowledged
    status = Column(String, nullable=False, server_default="pending")
    
    # Timestamps
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("NOW()"), nullable=False)
    acknowledged_at = Column(TIMESTAMP(timezone=True), nullable=True)
    
    # Relationships
    product = relationship("Product", back_populates="demand_predictions")
    admin = relationship("User")
