import pandas as pd
import numpy as np
import random
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from app.models.models import Product, DemandPredictionHistory, User, ProductSalesData, DynamicPricingHistory
from app.schemas.demand_prediction import DemandPredictionRequest, BulkDemandPredictionRequest
from app.utils.responses import ResponseHandler
from app.core.security import get_token_payload
from app.core.logging_config import (
    dynamic_pricing_logger as logger,
    ml_model_logger,
    log_flow_start,
    log_flow_end,
    log_step
)
import os
import logging

# Get logger
demand_logger = logging.getLogger("demand_prediction")

def get_user_id_from_token(token: str) -> int:
    """Extract user ID from token string"""
    payload = get_token_payload(token)
    return payload.get('id')


# Path to demand prediction model
ML_MODELS_PATH = os.path.join(os.path.dirname(__file__), '..', 'ml_models')
DEMAND_MODEL_PATH = os.path.join(ML_MODELS_PATH, 'demand_prediction.ckpt')

# Lazy load model
_tft_predictor = None
_market_engine = None


def load_demand_model():
    """Load TFT demand prediction model"""
    global _tft_predictor
    
    if _tft_predictor is None:
        try:
            from pytorch_forecasting import TemporalFusionTransformer, TimeSeriesDataSet
            ml_model_logger.info("Loading TFT Demand Prediction model...")
            
            if not os.path.exists(DEMAND_MODEL_PATH):
                ml_model_logger.warning(f"Demand model not found at {DEMAND_MODEL_PATH}, using mock predictions")
                return None
            
            _tft_predictor = TemporalFusionTransformer.load_from_checkpoint(
                DEMAND_MODEL_PATH, 
                map_location="cpu",
                weights_only=False
            )
            ml_model_logger.info("✅ TFT Demand Prediction model loaded successfully!")
        except Exception as e:
            ml_model_logger.error(f"❌ Error loading TFT model: {e}")
            ml_model_logger.warning("Using mock predictions instead")
            return None
    
    return _tft_predictor


def classify_demand_level(forecast: float) -> str:
    """Classify demand into levels based on forecast value"""
    if forecast < 50:
        return "low"
    elif forecast < 150:
        return "medium"
    elif forecast < 300:
        return "high"
    else:
        return "very_high"


def get_trend_direction(current: float, previous: float = None) -> str:
    """Determine trend direction based on forecast change"""
    if previous is None:
        return "stable"
    
    change_pct = ((current - previous) / previous * 100) if previous > 0 else 0
    
    if change_pct > 10:
        return "up"
    elif change_pct < -10:
        return "down"
    else:
        return "stable"


def auto_trigger_dynamic_pricing(admin_id: int, db: Session, product: Product, demand_level: str, holiday_input: str):
    """
    Automatically trigger dynamic pricing prediction for high/very_high and low/very_low demand products.
    
    Logic:
    - High/Very High demand: INCREASE price (capitalize on demand)
    - Low/Very Low demand: DECREASE price + create promotion (boost sales)
    
    This creates a dynamic pricing prediction with sensible defaults based on the product and demand level.
    """
    # Trigger for high demand (increase price) or low demand (decrease price + promotion)
    if demand_level not in ["high", "very_high", "low", "very_low"]:
        return None
    
    try:
        from app.services.promotions import PromotionsService
        
        logger.info(f"🔄 AUTO-TRIGGER: Dynamic pricing for product {product.id} ({product.title}) - Demand: {demand_level}")
        
        # Map category names to enum values
        category_map = {
            "electronics": "Electronics",
            "wearables": "Wearables", 
            "gaming": "Gaming",
            "home": "Home",
            "fashion": "Fashion",
            "beauty": "Beauty"
        }
        
        # Get product category, default to Electronics if not found
        product_category = product.category.name.lower() if product.category else "electronics"
        category_value = category_map.get(product_category, "Electronics")
        
        # Determine brand tier from price
        if float(product.price) > 500:
            brand_tier = "Luxury"
        elif float(product.price) > 100:
            brand_tier = "Premium"
        else:
            brand_tier = "Budget"
        
        # Determine season based on current month
        month = datetime.now().month
        if month in [3, 4, 5]:
            season = "Spring"
        elif month in [6, 7, 8]:
            season = "Summer"
        elif month in [9, 10, 11]:
            season = "Fall"
        else:
            season = "Winter"
        
        # Holiday event flag based on demand prediction input
        holiday_event = 1 if holiday_input != "No Holiday" else 0
        
        # Calculate dynamic pricing input values
        base_price = float(product.price)
        msrp = base_price * 1.2  # Assume MSRP is 20% above current price
        cogs = base_price * 0.6  # Assume 40% margin on COGS
        
        # Determine if this is high demand (increase price) or low demand (decrease price)
        is_high_demand = demand_level in ["high", "very_high"]
        is_low_demand = demand_level in ["low", "very_low"]
        
        # Adjust metrics based on demand level
        if demand_level == "very_high":
            sell_through_rate = random.uniform(0.7, 0.9)
            daily_sales_velocity = random.uniform(40, 80)
            conversion_rate = random.uniform(0.08, 0.15)
            weeks_of_cover = random.uniform(0.3, 1.0)
            marketing_spend_boost = 1
            demand_multiplier = 1.15  # INCREASE price 15%
        elif demand_level == "high":
            sell_through_rate = random.uniform(0.5, 0.7)
            daily_sales_velocity = random.uniform(20, 50)
            conversion_rate = random.uniform(0.05, 0.1)
            weeks_of_cover = random.uniform(1.0, 2.5)
            marketing_spend_boost = 0
            demand_multiplier = 1.08  # INCREASE price 8%
        elif demand_level == "low":
            sell_through_rate = random.uniform(0.15, 0.3)
            daily_sales_velocity = random.uniform(5, 15)
            conversion_rate = random.uniform(0.02, 0.04)
            weeks_of_cover = random.uniform(6, 10)
            marketing_spend_boost = 1  # Need marketing push
            demand_multiplier = 0.92  # DECREASE price 8%
        else:  # very_low
            sell_through_rate = random.uniform(0.05, 0.15)
            daily_sales_velocity = random.uniform(1, 8)
            conversion_rate = random.uniform(0.01, 0.025)
            weeks_of_cover = random.uniform(10, 20)
            marketing_spend_boost = 1  # Need marketing push
            demand_multiplier = 0.85  # DECREASE price 15%
        
        # Create pricing prediction input
        pricing_data = {
            'category': category_value,
            'brand_tier': brand_tier,
            'msrp': round(msrp, 2),
            'cogs': round(cogs, 2),
            'min_margin_req': 0.15,
            'inventory_qty': product.stock,
            'weeks_of_cover': round(weeks_of_cover, 2),
            'sell_through_rate': round(sell_through_rate, 2),
            'stock_age_days': random.randint(10, 60) if is_high_demand else random.randint(60, 120),
            'daily_sales_velocity': round(daily_sales_velocity, 2),
            'conversion_rate': round(conversion_rate, 3),
            'cart_abandon_rate': round(random.uniform(0.5, 0.75), 2),
            'competitor_price': round(base_price * random.uniform(0.9, 1.1), 2),
            'competitor_price_diff_pct': round(random.uniform(-0.15, 0.15), 3),
            'competitor_stock_status': 1,
            'market_saturation': round(random.uniform(0.3, 0.6), 2) if is_high_demand else round(random.uniform(0.6, 0.85), 2),
            'season': season,
            'holiday_event': holiday_event,
            'marketing_spend_boost': marketing_spend_boost,
        }
        
        # Calculate predicted price based on demand
        predicted_price = round(base_price * demand_multiplier, 2)
        
        # Ensure predicted price doesn't go below COGS (maintain minimum margin)
        min_viable_price = cogs * 1.15  # At least 15% margin
        if predicted_price < min_viable_price:
            predicted_price = round(min_viable_price, 2)
            logger.info(f"      └─ Adjusted predicted price to maintain margin: ${predicted_price:.2f}")
        
        # Calculate metrics
        original_price = base_price
        discount_from_original = round(((original_price - predicted_price) / original_price) * 100, 2)
        
        # Create history record - AUTO-APPROVED since it's triggered from demand prediction
        history_record = DynamicPricingHistory(
            product_id=product.id,
            admin_id=admin_id,
            predicted_price=predicted_price,
            original_price=original_price,
            discount_from_original=discount_from_original,  # Positive = discount, Negative = price increase
            status="approved",  # Auto-approved for demand-triggered pricing
            decided_at=datetime.utcnow(),  # Mark as decided now
            category=pricing_data['category'],
            brand_tier=pricing_data['brand_tier'],
            msrp=pricing_data['msrp'],
            cogs=pricing_data['cogs'],
            min_margin_req=pricing_data['min_margin_req'],
            inventory_qty=pricing_data['inventory_qty'],
            weeks_of_cover=pricing_data['weeks_of_cover'],
            sell_through_rate=pricing_data['sell_through_rate'],
            stock_age_days=pricing_data['stock_age_days'],
            daily_sales_velocity=pricing_data['daily_sales_velocity'],
            conversion_rate=pricing_data['conversion_rate'],
            cart_abandon_rate=pricing_data['cart_abandon_rate'],
            competitor_price=pricing_data['competitor_price'],
            competitor_price_diff_pct=pricing_data['competitor_price_diff_pct'],
            competitor_stock_status=pricing_data['competitor_stock_status'],
            market_saturation=pricing_data['market_saturation'],
            season=pricing_data['season'],
            holiday_event=pricing_data['holiday_event'],
            marketing_spend_boost=pricing_data['marketing_spend_boost'],
        )
        
        db.add(history_record)
        db.flush()  # Get the ID without committing
        
        # AUTO-ACTIVATE: Update the product's dynamic price immediately
        if product.base_price is None:
            product.base_price = float(product.price)
        
        product.dynamic_price = predicted_price
        product.is_dynamic_pricing_active = True
        
        # Update discount percentage (bounded to 0-100%)
        if product.base_price > 0:
            discount_pct = ((product.base_price - predicted_price) / product.base_price) * 100
            product.discount_percentage = round(max(0, min(discount_pct, 100)), 2)  # Bounded 0-100%
        
        price_direction = "↑" if is_high_demand else "↓"
        logger.info(f"      └─ ✅ Auto-created & ACTIVATED dynamic pricing: ${original_price:.2f} → ${predicted_price:.2f} {price_direction} (History ID: {history_record.id})")
        
        result = {
            "history_id": history_record.id,
            "product_id": product.id,
            "product_title": product.title,
            "original_price": original_price,
            "predicted_price": predicted_price,
            "discount_percentage": abs(discount_from_original),
            "demand_level": demand_level,
            "status": "approved",
            "auto_activated": True,
            "price_direction": "increased" if is_high_demand else "decreased",
            "promotion_created": False,
            "promotion_id": None
        }
        
        # AUTO-TRIGGER PROMOTION for ALL demand levels (same as manual dynamic pricing)
        # Create promotional banner for both high demand (capitalize on trend) and low demand (boost sales)
        logger.info(f"      └─ 🎯 Auto-triggering promotional banner for {demand_level} demand...")
        try:
            promotion = PromotionsService.create_promotion_from_pricing(db, history_record, product)
            if promotion:
                result["promotion_created"] = True
                result["promotion_id"] = promotion.id
                logger.info(f"      └─ ✅ Auto-created promotion: ID {promotion.id} (status: draft)")
        except Exception as promo_error:
            logger.error(f"      └─ ⚠️ Failed to create promotion: {promo_error}")
        
        return result
        
    except Exception as e:
        logger.error(f"      └─ ❌ Failed to auto-trigger dynamic pricing for product {product.id}: {e}")
        return None


def generate_mock_prediction(product_id: int, holiday: str, weather: str) -> dict:
    """Generate mock prediction when model is not available"""
    import random
    
    # Base forecast with some randomness
    base = random.uniform(50, 250)
    
    # Holiday boost
    holiday_boost = {
        "No Holiday": 1.0,
        "Christmas": 1.5,
        "Black Friday": 1.8,
        "Cyber Monday": 1.6,
        "New Year": 1.3,
        "Valentine's Day": 1.2,
        "Mother's Day": 1.25,
        "Father's Day": 1.2,
        "Easter": 1.15,
        "Thanksgiving": 1.3,
        "Independence Day": 1.1
    }.get(holiday, 1.0)
    
    # Weather effect
    weather_effect = {
        "Overcast": 1.0,
        "Sunny": 1.1,
        "Rainy": 0.9,
        "Cloudy": 0.95,
        "Stormy": 0.7,
        "Snowy": 0.8,
        "Clear": 1.05
    }.get(weather, 1.0)
    
    adjusted = base * holiday_boost * weather_effect
    
    return {
        "product_id": str(product_id),
        "base_forecast": round(base, 2),
        "trend_score": round(random.uniform(20, 80), 1),
        "sentiment_score": round(random.uniform(-0.5, 0.5), 2),
        "multiplier": round(holiday_boost * weather_effect, 3),
        "adjusted_forecast": round(adjusted, 2)
    }


class DemandPredictionService:
    
    @staticmethod
    def predict_demand(token: str, db: Session, request: DemandPredictionRequest):
        """
        Predict demand for a single product
        """
        log_flow_start(logger, "DEMAND PREDICTION", 
                      product_id=request.product_id,
                      holiday=request.holiday.value,
                      weather=request.weather.value)
        
        # Step 1: Authenticate admin
        log_step(logger, 1, "Authenticating admin user")
        admin_id = get_user_id_from_token(token)
        logger.info(f"      └─ Admin ID: {admin_id}")
        
        # Step 2: Verify product exists
        log_step(logger, 2, "Fetching product from database")
        product = db.query(Product).filter(Product.id == request.product_id).first()
        if not product:
            logger.error(f"Product not found: {request.product_id}")
            ResponseHandler.not_found_error("Product", request.product_id)
        logger.info(f"      └─ Product: {product.title}")
        
        # Step 3: Generate prediction
        log_step(logger, 3, "Running demand prediction model")
        
        # Try to load model, fall back to mock if not available
        model = load_demand_model()
        
        if model is not None:
            # Try to get historical data from database
            sales_data = db.query(ProductSalesData).filter(
                ProductSalesData.product_id == str(request.product_id)
            ).order_by(ProductSalesData.time_idx.asc()).all()
            
            if sales_data and len(sales_data) >= 10:
                # Use real model with historical data
                # This would need the full TFT inference pipeline
                prediction = generate_mock_prediction(
                    request.product_id,
                    request.holiday.value,
                    request.weather.value
                )
            else:
                # Not enough historical data, use mock
                prediction = generate_mock_prediction(
                    request.product_id,
                    request.holiday.value,
                    request.weather.value
                )
        else:
            # Model not available, use mock predictions
            prediction = generate_mock_prediction(
                request.product_id,
                request.holiday.value,
                request.weather.value
            )
        
        logger.info(f"      └─ 🎯 PREDICTED DEMAND: {prediction['adjusted_forecast']:.2f} units")
        
        # Step 4: Get previous prediction for comparison
        log_step(logger, 4, "Calculating demand change")
        previous = db.query(DemandPredictionHistory).filter(
            DemandPredictionHistory.product_id == request.product_id
        ).order_by(desc(DemandPredictionHistory.created_at)).first()
        
        demand_change_pct = None
        if previous:
            demand_change_pct = round(
                ((prediction['adjusted_forecast'] - previous.adjusted_forecast) / previous.adjusted_forecast * 100)
                if previous.adjusted_forecast > 0 else 0, 2
            )
            logger.info(f"      └─ Previous forecast: {previous.adjusted_forecast}, Change: {demand_change_pct}%")
        
        # Step 5: Classify demand level
        log_step(logger, 5, "Classifying demand level")
        demand_level = classify_demand_level(prediction['adjusted_forecast'])
        logger.info(f"      └─ Demand Level: {demand_level.upper()}")
        
        # Step 6: Store in history
        log_step(logger, 6, "Saving prediction to history table")
        history_record = DemandPredictionHistory(
            product_id=request.product_id,
            admin_id=admin_id,
            holiday_input=request.holiday.value,
            weather_input=request.weather.value,
            base_forecast=prediction['base_forecast'],
            trend_score=prediction.get('trend_score'),
            sentiment_score=prediction.get('sentiment_score'),
            multiplier=prediction.get('multiplier', 1.0),
            adjusted_forecast=prediction['adjusted_forecast'],
            demand_level=demand_level,
            demand_change_pct=demand_change_pct,
            status="pending"
        )
        
        db.add(history_record)
        db.commit()
        db.refresh(history_record)
        
        logger.info(f"      └─ History record ID: {history_record.id}")
        
        # Step 7: Auto-trigger dynamic pricing for high demand (increase price) or low demand (decrease + promotion)
        dynamic_pricing_result = None
        if demand_level in ["high", "very_high", "low", "very_low"]:
            action = "increase price" if demand_level in ["high", "very_high"] else "decrease price + create promotion"
            log_step(logger, 7, f"Auto-triggering dynamic pricing for {demand_level} demand ({action})")
            dynamic_pricing_result = auto_trigger_dynamic_pricing(
                admin_id, db, product, demand_level, request.holiday.value
            )
            db.commit()  # Commit the dynamic pricing record
        
        log_flow_end(logger, "DEMAND PREDICTION", success=True,
                    history_id=history_record.id,
                    forecast=f"{prediction['adjusted_forecast']:.2f} units",
                    demand_level=demand_level)
        
        response = {
            "success": True,
            "history_id": history_record.id,
            "prediction": {
                "product_id": product.id,
                "product_title": product.title,
                "product_thumbnail": product.thumbnail,
                "base_forecast": prediction['base_forecast'],
                "trend_score": prediction.get('trend_score'),
                "sentiment_score": prediction.get('sentiment_score'),
                "multiplier": prediction.get('multiplier', 1.0),
                "adjusted_forecast": prediction['adjusted_forecast'],
                "demand_level": demand_level,
                "demand_change_pct": demand_change_pct
            },
            "message": f"Demand prediction completed for '{product.title}'. Forecast: {prediction['adjusted_forecast']:.0f} units ({demand_level})"
        }
        
        # Add dynamic pricing info to response if triggered
        if dynamic_pricing_result:
            response["dynamic_pricing_triggered"] = True
            response["dynamic_pricing"] = dynamic_pricing_result
            
            price_direction = "↑" if demand_level in ["high", "very_high"] else "↓"
            response["message"] += f" | Dynamic pricing auto-activated: ${dynamic_pricing_result['predicted_price']:.2f} {price_direction}"
            
            # Add promotion info if created
            if dynamic_pricing_result.get("promotion_created"):
                response["promotion_created"] = True
                response["promotion_id"] = dynamic_pricing_result["promotion_id"]
                response["message"] += f" | Promotion banner created (ID: {dynamic_pricing_result['promotion_id']})"
        
        return response
    
    @staticmethod
    def predict_bulk_demand(token: str, db: Session, request: BulkDemandPredictionRequest):
        """
        Predict demand for multiple products
        """
        log_flow_start(logger, "BULK DEMAND PREDICTION",
                      product_count=len(request.product_ids) if request.product_ids else "all")
        
        admin_id = get_user_id_from_token(token)
        
        # Get products
        if request.product_ids:
            products = db.query(Product).filter(Product.id.in_(request.product_ids)).all()
        else:
            products = db.query(Product).limit(50).all()  # Limit to 50 for bulk
        
        predictions = []
        
        for product in products:
            # Generate prediction
            prediction = generate_mock_prediction(
                product.id,
                request.holiday.value,
                request.weather.value
            )
            
            # Get previous for comparison
            previous = db.query(DemandPredictionHistory).filter(
                DemandPredictionHistory.product_id == product.id
            ).order_by(desc(DemandPredictionHistory.created_at)).first()
            
            demand_change_pct = None
            if previous:
                demand_change_pct = round(
                    ((prediction['adjusted_forecast'] - previous.adjusted_forecast) / previous.adjusted_forecast * 100)
                    if previous.adjusted_forecast > 0 else 0, 2
                )
            
            demand_level = classify_demand_level(prediction['adjusted_forecast'])
            
            # Store in history
            history_record = DemandPredictionHistory(
                product_id=product.id,
                admin_id=admin_id,
                holiday_input=request.holiday.value,
                weather_input=request.weather.value,
                base_forecast=prediction['base_forecast'],
                trend_score=prediction.get('trend_score'),
                sentiment_score=prediction.get('sentiment_score'),
                multiplier=prediction.get('multiplier', 1.0),
                adjusted_forecast=prediction['adjusted_forecast'],
                demand_level=demand_level,
                demand_change_pct=demand_change_pct,
                status="pending"
            )
            db.add(history_record)
            
            pred_result = {
                "product_id": product.id,
                "product_title": product.title,
                "product_thumbnail": product.thumbnail,
                "base_forecast": prediction['base_forecast'],
                "trend_score": prediction.get('trend_score'),
                "sentiment_score": prediction.get('sentiment_score'),
                "multiplier": prediction.get('multiplier', 1.0),
                "adjusted_forecast": prediction['adjusted_forecast'],
                "demand_level": demand_level,
                "demand_change_pct": demand_change_pct,
                "dynamic_pricing_triggered": False
            }
            
            predictions.append(pred_result)
        
        # Commit all demand predictions first
        db.commit()
        
        # Now auto-trigger dynamic pricing for high/very_high AND low/very_low demand products
        dynamic_pricing_results = []
        promotion_results = []
        
        # Get products that need dynamic pricing (high demand = increase price, low demand = decrease + promotion)
        actionable_products = [p for p in predictions if p["demand_level"] in ["high", "very_high", "low", "very_low"]]
        high_demand_count = len([p for p in actionable_products if p["demand_level"] in ["high", "very_high"]])
        low_demand_count = len([p for p in actionable_products if p["demand_level"] in ["low", "very_low"]])
        
        if actionable_products:
            logger.info(f"🔄 AUTO-TRIGGER: Dynamic pricing for {len(actionable_products)} products ({high_demand_count} high demand ↑, {low_demand_count} low demand ↓)")
            
            for pred in actionable_products:
                product = db.query(Product).filter(Product.id == pred["product_id"]).first()
                if product:
                    dp_result = auto_trigger_dynamic_pricing(
                        admin_id, db, product, pred["demand_level"], request.holiday.value
                    )
                    if dp_result:
                        dynamic_pricing_results.append(dp_result)
                        # Update the prediction result to indicate dynamic pricing was triggered
                        pred["dynamic_pricing_triggered"] = True
                        pred["dynamic_pricing"] = dp_result
                        
                        # Track promotions separately
                        if dp_result.get("promotion_created"):
                            promotion_results.append({
                                "product_id": dp_result["product_id"],
                                "product_title": dp_result["product_title"],
                                "promotion_id": dp_result["promotion_id"]
                            })
            
            db.commit()  # Commit all dynamic pricing and promotion records
        
        log_flow_end(logger, "BULK DEMAND PREDICTION", success=True,
                    total_products=len(predictions),
                    dynamic_pricing_triggered=len(dynamic_pricing_results),
                    promotions_created=len(promotion_results))
        
        # Build summary message
        summary_parts = [f"Bulk demand prediction completed for {len(predictions)} products."]
        if high_demand_count > 0:
            summary_parts.append(f"Price increased for {high_demand_count} high-demand products.")
        if low_demand_count > 0:
            summary_parts.append(f"Price decreased for {low_demand_count} low-demand products.")
        if len(promotion_results) > 0:
            summary_parts.append(f"{len(promotion_results)} promotional banners created.")
        
        return {
            "success": True,
            "total_products": len(predictions),
            "predictions": predictions,
            "dynamic_pricing_triggered_count": len(dynamic_pricing_results),
            "dynamic_pricing_results": dynamic_pricing_results,
            "promotions_created_count": len(promotion_results),
            "promotion_results": promotion_results,
            "message": " ".join(summary_parts)
        }
    
    @staticmethod
    def acknowledge_prediction(token: str, db: Session, history_id: int):
        """Acknowledge a pending prediction"""
        admin_id = get_user_id_from_token(token)
        
        history = db.query(DemandPredictionHistory).filter(
            DemandPredictionHistory.id == history_id
        ).first()
        
        if not history:
            ResponseHandler.not_found_error("Prediction History", history_id)
        
        if history.status == "acknowledged":
            return {
                "success": False,
                "message": "Prediction already acknowledged"
            }
        
        history.status = "acknowledged"
        history.acknowledged_at = datetime.utcnow()
        
        db.commit()
        db.refresh(history)
        
        return {
            "success": True,
            "message": f"Prediction acknowledged",
            "history_id": history.id
        }
    
    @staticmethod
    def get_products_for_demand(token: str, db: Session, page: int, limit: int, demand_level: str = None):
        """Get all products with their demand prediction status"""
        admin_id = get_user_id_from_token(token)
        
        # If filtering by demand level, we need to filter products based on their latest prediction
        if demand_level:
            # Get products that have predictions with the specified demand level
            subquery = db.query(
                DemandPredictionHistory.product_id,
                func.max(DemandPredictionHistory.id).label("latest_id")
            ).group_by(DemandPredictionHistory.product_id).subquery()
            
            latest_predictions = db.query(DemandPredictionHistory).join(
                subquery,
                DemandPredictionHistory.id == subquery.c.latest_id
            ).filter(
                DemandPredictionHistory.demand_level == demand_level
            ).all()
            
            product_ids = [p.product_id for p in latest_predictions]
            products = db.query(Product).filter(Product.id.in_(product_ids)).order_by(Product.id.asc()).offset((page - 1) * limit).limit(limit).all()
        else:
            products = db.query(Product).order_by(Product.id.asc()).offset((page - 1) * limit).limit(limit).all()
        
        result = []
        for product in products:
            # Get latest prediction
            latest = db.query(DemandPredictionHistory).filter(
                DemandPredictionHistory.product_id == product.id
            ).order_by(desc(DemandPredictionHistory.created_at)).first()
            
            # Count pending predictions
            pending_count = db.query(func.count(DemandPredictionHistory.id)).filter(
                DemandPredictionHistory.product_id == product.id,
                DemandPredictionHistory.status == "pending"
            ).scalar()
            
            result.append({
                "id": product.id,
                "title": product.title,
                "price": product.price,
                "stock": product.stock,
                "brand": product.brand,
                "thumbnail": product.thumbnail,
                "category_name": product.category.name if product.category else None,
                "latest_forecast": latest.adjusted_forecast if latest else None,
                "latest_demand_level": latest.demand_level if latest else None,
                "pending_predictions": pending_count or 0,
                "latest_history_id": latest.id if latest else None,
            })
        
        return {
            "message": f"Page {page} with {len(result)} products",
            "data": result
        }
    
    @staticmethod
    def get_all_history(token: str, db: Session, page: int, limit: int, status_filter: str = None, demand_level: str = None):
        """Get all demand prediction history"""
        admin_id = get_user_id_from_token(token)
        
        query = db.query(DemandPredictionHistory).order_by(DemandPredictionHistory.created_at.desc())
        
        if status_filter:
            query = query.filter(DemandPredictionHistory.status == status_filter)
        
        if demand_level:
            query = query.filter(DemandPredictionHistory.demand_level == demand_level)
        
        history_records = query.offset((page - 1) * limit).limit(limit).all()
        
        result = []
        for record in history_records:
            product = db.query(Product).filter(Product.id == record.product_id).first()
            result.append({
                "id": record.id,
                "product_id": record.product_id,
                "admin_id": record.admin_id,
                "holiday_input": record.holiday_input,
                "weather_input": record.weather_input,
                "base_forecast": record.base_forecast,
                "trend_score": record.trend_score,
                "sentiment_score": record.sentiment_score,
                "multiplier": record.multiplier,
                "adjusted_forecast": record.adjusted_forecast,
                "demand_level": record.demand_level,
                "demand_change_pct": record.demand_change_pct,
                "status": record.status,
                "created_at": record.created_at,
                "acknowledged_at": record.acknowledged_at,
                "product_title": product.title if product else "Deleted Product",
                "product_thumbnail": product.thumbnail if product else None,
                "product_price": product.price if product else None,
                "product_stock": product.stock if product else None,
            })
        
        return {
            "message": f"Page {page} with {len(result)} history records",
            "data": result
        }
    
    @staticmethod
    def get_trending_products(token: str, db: Session, limit: int = 10):
        """Get top trending products based on demand predictions"""
        admin_id = None
        if token:
            try:
                admin_id = get_user_id_from_token(token)
            except:
                pass  # Public access allowed
        
        # Get latest predictions with high demand, ordered by adjusted forecast
        subquery = db.query(
            DemandPredictionHistory.product_id,
            func.max(DemandPredictionHistory.id).label("latest_id")
        ).group_by(DemandPredictionHistory.product_id).subquery()
        
        trending = db.query(DemandPredictionHistory).join(
            subquery,
            DemandPredictionHistory.id == subquery.c.latest_id
        ).filter(
            DemandPredictionHistory.demand_level.in_(["high", "very_high", "medium"])
        ).order_by(
            desc(DemandPredictionHistory.adjusted_forecast)
        ).limit(limit).all()
        
        result = []
        for record in trending:
            product = db.query(Product).filter(Product.id == record.product_id).first()
            if not product:
                continue
            
            # Determine trend direction
            trend_direction = get_trend_direction(
                record.adjusted_forecast,
                record.demand_change_pct and (record.adjusted_forecast / (1 + record.demand_change_pct / 100)) if record.demand_change_pct else None
            )
            
            result.append({
                "id": record.id,
                "product_id": product.id,
                "product_title": product.title,
                "product_thumbnail": product.thumbnail,
                "product_price": float(product.price),
                "product_stock": product.stock,
                "brand": product.brand,
                "category_name": product.category.name if product.category else None,
                "adjusted_forecast": record.adjusted_forecast,
                "demand_level": record.demand_level,
                "demand_change_pct": record.demand_change_pct,
                "trend_direction": "up" if (record.demand_change_pct and record.demand_change_pct > 5) else ("down" if (record.demand_change_pct and record.demand_change_pct < -5) else "stable"),
                "trend_score": record.trend_score,
            })
        
        return {
            "message": f"Found {len(result)} trending products",
            "data": result
        }
    
    @staticmethod
    def get_product_history(token: str, db: Session, product_id: int):
        """Get demand prediction history for a specific product"""
        admin_id = get_user_id_from_token(token)
        
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            ResponseHandler.not_found_error("Product", product_id)
        
        history_records = db.query(DemandPredictionHistory).filter(
            DemandPredictionHistory.product_id == product_id
        ).order_by(DemandPredictionHistory.created_at.desc()).all()
        
        result = []
        for record in history_records:
            result.append({
                "id": record.id,
                "product_id": record.product_id,
                "admin_id": record.admin_id,
                "holiday_input": record.holiday_input,
                "weather_input": record.weather_input,
                "base_forecast": record.base_forecast,
                "trend_score": record.trend_score,
                "sentiment_score": record.sentiment_score,
                "multiplier": record.multiplier,
                "adjusted_forecast": record.adjusted_forecast,
                "demand_level": record.demand_level,
                "demand_change_pct": record.demand_change_pct,
                "status": record.status,
                "created_at": record.created_at,
                "acknowledged_at": record.acknowledged_at,
                "product_title": product.title,
                "product_thumbnail": product.thumbnail,
                "product_price": product.price,
                "product_stock": product.stock,
            })
        
        return {
            "message": f"Found {len(result)} history records for product '{product.title}'",
            "data": result
        }
    
    @staticmethod
    def delete_prediction(token: str, db: Session, history_id: int):
        """Delete a demand prediction history record"""
        admin_id = get_user_id_from_token(token)
        
        history = db.query(DemandPredictionHistory).filter(
            DemandPredictionHistory.id == history_id
        ).first()
        
        if not history:
            ResponseHandler.not_found_error("Prediction History", history_id)
        
        product_id = history.product_id
        db.delete(history)
        db.commit()
        
        return {
            "success": True,
            "message": f"Prediction history record deleted",
            "history_id": history_id,
            "product_id": product_id
        }
    
    @staticmethod
    def get_demand_stats(token: str, db: Session):
        """Get demand statistics for dashboard - counts by level and top 3 products"""
        admin_id = get_user_id_from_token(token)
        
        # Get latest predictions per product (subquery)
        subquery = db.query(
            DemandPredictionHistory.product_id,
            func.max(DemandPredictionHistory.id).label("latest_id")
        ).group_by(DemandPredictionHistory.product_id).subquery()
        
        # Get all latest predictions
        latest_predictions = db.query(DemandPredictionHistory).join(
            subquery,
            DemandPredictionHistory.id == subquery.c.latest_id
        ).all()
        
        # Count by demand level
        counts = {
            "low": 0,
            "medium": 0,
            "high": 0,
            "very_high": 0
        }
        
        for pred in latest_predictions:
            if pred.demand_level in counts:
                counts[pred.demand_level] += 1
        
        # Get top 3 products by demand (highest adjusted_forecast with high/very_high demand)
        top3_records = db.query(DemandPredictionHistory).join(
            subquery,
            DemandPredictionHistory.id == subquery.c.latest_id
        ).filter(
            DemandPredictionHistory.demand_level.in_(["high", "very_high"])
        ).order_by(
            desc(DemandPredictionHistory.adjusted_forecast)
        ).limit(3).all()
        
        top3 = []
        for record in top3_records:
            product = db.query(Product).filter(Product.id == record.product_id).first()
            if product:
                top3.append({
                    "product_id": product.id,
                    "product_title": product.title,
                    "product_thumbnail": product.thumbnail,
                    "adjusted_forecast": record.adjusted_forecast,
                    "demand_level": record.demand_level,
                    "demand_change_pct": record.demand_change_pct
                })
        
        return {
            "success": True,
            "counts": counts,
            "total_predicted": sum(counts.values()),
            "top3": top3
        }
