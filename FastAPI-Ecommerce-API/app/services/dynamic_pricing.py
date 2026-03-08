import pandas as pd
import pickle
import os
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.models import Product, DynamicPricingHistory, User, DynamicPromotion
from app.schemas.dynamic_pricing import DynamicPricingPredictRequest
from app.utils.responses import ResponseHandler
from app.core.security import get_token_payload
from app.core.logging_config import (
    dynamic_pricing_logger as logger,
    ml_model_logger,
    log_flow_start,
    log_flow_end,
    log_step
)


def get_user_id_from_token(token: str) -> int:
    """Extract user ID from token string"""
    payload = get_token_payload(token)
    return payload.get('id')

# Get the path to ML models
ML_MODELS_PATH = os.path.join(os.path.dirname(__file__), '..', 'ml_models')

# Load ML artifacts at module level for efficiency
_model = None
_scaler = None
_expected_columns = None
_num_cols_idxs = None

def load_ml_artifacts():
    """Load ML model and preprocessing artifacts"""
    global _model, _scaler, _expected_columns, _num_cols_idxs
    
    if _model is None:
        ml_model_logger.info("Loading ML artifacts for the first time...")
        try:
            with open(os.path.join(ML_MODELS_PATH, 'best_model_xgboost.pkl'), 'rb') as f:
                _model = pickle.load(f)
            ml_model_logger.info("  ✓ Loaded XGBoost model")
            
            with open(os.path.join(ML_MODELS_PATH, 'scaler.pkl'), 'rb') as f:
                _scaler = pickle.load(f)
            ml_model_logger.info("  ✓ Loaded scaler")
            
            with open(os.path.join(ML_MODELS_PATH, 'expected_columns.pkl'), 'rb') as f:
                _expected_columns = pickle.load(f)
            ml_model_logger.info(f"  ✓ Loaded expected columns ({len(_expected_columns)} features)")
            
            with open(os.path.join(ML_MODELS_PATH, 'num_cols_idxs.pkl'), 'rb') as f:
                _num_cols_idxs = pickle.load(f)
            ml_model_logger.info(f"  ✓ Loaded numeric column indices")
                
            ml_model_logger.info("✅ All ML artifacts loaded successfully!")
        except Exception as e:
            ml_model_logger.error(f"❌ Error loading ML artifacts: {e}")
            raise e
    else:
        ml_model_logger.debug("ML artifacts already loaded, using cached version")
    
    return _model, _scaler, _expected_columns, _num_cols_idxs


# Categorical columns to encode (must match training)
CAT_COLS = ['category', 'brand_tier', 'competitor_stock_status', 'season']


class DynamicPricingService:
    
    @staticmethod
    def predict_price(token: str, db: Session, request: DynamicPricingPredictRequest):
        """
        Predict optimal price using ML model and store in history
        """
        log_flow_start(logger, "DYNAMIC PRICE PREDICTION", 
                      product_id=request.product_id,
                      category=request.category.value,
                      msrp=f"${request.msrp}")
        
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
        logger.info(f"      └─ Current Price: ${product.price}")
        
        # Step 3: Load ML artifacts
        log_step(logger, 3, "Loading ML model and artifacts")
        model, scaler, expected_columns, num_cols_idxs = load_ml_artifacts()
        
        # Step 4: Prepare input data
        log_step(logger, 4, "Preparing input features for ML model")
        input_data = {
            'category': request.category.value,
            'brand_tier': request.brand_tier.value,
            'msrp': request.msrp,
            'cogs': request.cogs,
            'min_margin_req': request.min_margin_req,
            'inventory_qty': request.inventory_qty,
            'weeks_of_cover': request.weeks_of_cover,
            'sell_through_rate': request.sell_through_rate,
            'stock_age_days': request.stock_age_days,
            'daily_sales_velocity': request.daily_sales_velocity,
            'conversion_rate': request.conversion_rate,
            'cart_abandon_rate': request.cart_abandon_rate,
            'competitor_price': request.competitor_price,
            'competitor_price_diff_pct': request.competitor_price_diff_pct,
            'competitor_stock_status': request.competitor_stock_status,
            'market_saturation': request.market_saturation,
            'season': request.season.value,
            'holiday_event': request.holiday_event,
            'marketing_spend_boost': request.marketing_spend_boost,
        }
        
        input_df = pd.DataFrame([input_data])
        logger.debug(f"      └─ Input features: {len(input_data)} columns")
        
        # Step 5: One-hot encode categorical variables
        log_step(logger, 5, "One-hot encoding categorical variables")
        input_encoded = pd.get_dummies(input_df, columns=CAT_COLS, drop_first=True)
        logger.debug(f"      └─ Encoded columns: {len(input_encoded.columns)}")
        
        # Align columns with training set
        for col in expected_columns:
            if col not in input_encoded.columns:
                input_encoded[col] = 0
        input_encoded = input_encoded[expected_columns]
        
        # Step 6: Scale numeric columns
        log_step(logger, 6, "Scaling numeric features")
        input_encoded.iloc[:, num_cols_idxs] = scaler.transform(input_encoded.iloc[:, num_cols_idxs])
        
        # Step 7: Run ML prediction
        log_step(logger, 7, "Running XGBoost prediction")
        pred = model.predict(input_encoded)
        raw_predicted_price = float(pred[0])
        logger.info(f"      └─ 🎯 RAW PREDICTED PRICE: ${raw_predicted_price:.2f}")
        
        # Validate and bound predicted price (must be positive and reasonable)
        original_price = float(product.price)
        min_price = max(request.cogs * 1.05, 0.01)  # At least 5% margin over COGS or $0.01
        max_price = original_price * 2  # Don't exceed 2x original price
        predicted_price = max(min_price, min(raw_predicted_price, max_price))
        
        if raw_predicted_price != predicted_price:
            logger.warning(f"      └─ ⚠️ Price adjusted from ${raw_predicted_price:.2f} to ${predicted_price:.2f} (bounds: ${min_price:.2f} - ${max_price:.2f})")
        logger.info(f"      └─ 🎯 FINAL PREDICTED PRICE: ${predicted_price:.2f}")
        
        # Step 8: Calculate pricing analysis
        log_step(logger, 8, "Calculating pricing metrics")
        margin = predicted_price - request.cogs
        margin_pct = (margin / predicted_price) * 100 if predicted_price > 0 else 0
        discount_from_msrp = ((request.msrp - predicted_price) / request.msrp) * 100 if request.msrp > 0 else 0
        discount_from_original = ((original_price - predicted_price) / original_price) * 100 if original_price > 0 else 0
        # Bound discount to 0-100%
        discount_from_original = max(0, min(discount_from_original, 100))
        savings_amount = max(0, original_price - predicted_price)
        
        logger.info(f"      └─ Original Price: ${original_price:.2f}")
        logger.info(f"      └─ Predicted Price: ${predicted_price:.2f}")
        logger.info(f"      └─ Savings: ${savings_amount:.2f} ({abs(discount_from_original):.1f}%)")
        logger.info(f"      └─ Margin: ${margin:.2f} ({margin_pct:.1f}%)")
        
        # Step 9: Store in history
        log_step(logger, 9, "Saving prediction to history table")
        history_record = DynamicPricingHistory(
            product_id=request.product_id,
            admin_id=admin_id,
            predicted_price=round(predicted_price, 2),
            original_price=original_price,
            discount_from_original=round(discount_from_original, 2),
            status="pending",
            category=request.category.value,
            brand_tier=request.brand_tier.value,
            msrp=request.msrp,
            cogs=request.cogs,
            min_margin_req=request.min_margin_req,
            inventory_qty=request.inventory_qty,
            weeks_of_cover=request.weeks_of_cover,
            sell_through_rate=request.sell_through_rate,
            stock_age_days=request.stock_age_days,
            daily_sales_velocity=request.daily_sales_velocity,
            conversion_rate=request.conversion_rate,
            cart_abandon_rate=request.cart_abandon_rate,
            competitor_price=request.competitor_price,
            competitor_price_diff_pct=request.competitor_price_diff_pct,
            competitor_stock_status=request.competitor_stock_status,
            market_saturation=request.market_saturation,
            season=request.season.value,
            holiday_event=request.holiday_event,
            marketing_spend_boost=request.marketing_spend_boost,
        )
        
        db.add(history_record)
        db.commit()
        db.refresh(history_record)
        
        logger.info(f"      └─ History record ID: {history_record.id}")
        logger.info(f"      └─ Status: PENDING (awaiting admin approval)")
        
        log_flow_end(logger, "DYNAMIC PRICE PREDICTION", success=True,
                    history_id=history_record.id,
                    predicted_price=f"${predicted_price:.2f}",
                    savings=f"${savings_amount:.2f}")
        
        return {
            "success": True,
            "history_id": history_record.id,
            "product_id": product.id,
            "product_title": product.title,
            "original_price": original_price,
            "predicted_price": round(predicted_price, 2),
            "discount_percentage": round(abs(discount_from_original), 2),
            "savings_amount": round(savings_amount, 2),
            "pricing_analysis": {
                "margin": round(margin, 2),
                "margin_percentage": round(margin_pct, 2),
                "discount_from_msrp_pct": round(discount_from_msrp, 2),
                "meets_min_margin": margin_pct >= (request.min_margin_req * 100),
            },
            "status": "pending",
            "message": f"Price prediction completed. Predicted: ${round(predicted_price, 2)} (Save ${round(savings_amount, 2)})"
        }
    
    @staticmethod
    def approve_prediction(token: str, db: Session, history_id: int):
        """
        Approve a pending prediction and update product price
        """
        log_flow_start(logger, "APPROVE DYNAMIC PRICING", history_id=history_id)
        
        # Step 1: Authenticate admin
        log_step(logger, 1, "Authenticating admin user")
        admin_id = get_user_id_from_token(token)
        logger.info(f"      └─ Admin ID: {admin_id}")
        
        # Step 2: Get history record
        log_step(logger, 2, "Fetching prediction history")
        
        # Step 2: Get history record
        log_step(logger, 2, "Fetching prediction history")
        history = db.query(DynamicPricingHistory).filter(
            DynamicPricingHistory.id == history_id
        ).first()
        
        if not history:
            logger.error(f"History record not found: {history_id}")
            ResponseHandler.not_found_error("Pricing History", history_id)
        
        logger.info(f"      └─ Predicted Price: ${history.predicted_price}")
        logger.info(f"      └─ Original Price: ${history.original_price}")
        logger.info(f"      └─ Current Status: {history.status}")
        
        if history.status != "pending":
            logger.warning(f"Cannot approve: prediction is already {history.status}")
            return {
                "success": False,
                "message": f"Cannot approve: prediction is already {history.status}"
            }
        
        # Step 3: Get product
        log_step(logger, 3, "Fetching product details")
        product = db.query(Product).filter(Product.id == history.product_id).first()
        if not product:
            logger.error(f"Product not found: {history.product_id}")
            ResponseHandler.not_found_error("Product", history.product_id)
        logger.info(f"      └─ Product: {product.title}")
        
        # Step 4: Update history status
        log_step(logger, 4, "Updating prediction status to APPROVED")
        history.status = "approved"
        history.decided_at = datetime.utcnow()
        logger.info(f"      └─ Status changed: pending → approved")
        
        # Step 5: Update product with dynamic pricing
        log_step(logger, 5, "Applying dynamic price to product")
        if product.base_price is None:
            product.base_price = float(product.price)
            logger.info(f"      └─ Saved base price: ${product.base_price}")
        
        old_dynamic_price = product.dynamic_price
        product.dynamic_price = history.predicted_price
        product.is_dynamic_pricing_active = True
        logger.info(f"      └─ Dynamic price: ${old_dynamic_price} → ${product.dynamic_price}")
        logger.info(f"      └─ Dynamic pricing: ACTIVATED")
        
        # Calculate new discount_percentage based on dynamic price
        if product.base_price > 0:
            new_discount = ((product.base_price - history.predicted_price) / product.base_price) * 100
            # Bound discount to 0-100%
            product.discount_percentage = round(max(0, min(new_discount, 100)), 2)
            logger.info(f"      └─ Discount: {product.discount_percentage}%")
        
        db.commit()
        db.refresh(product)
        db.refresh(history)
        
        # Step 6: Create dynamic promotion
        log_step(logger, 6, "Creating promotional banner")
        logger.info("      └─ Triggering promotion creation with Gemini AI...")
        from app.services.promotions import PromotionsService
        promotion = PromotionsService.create_promotion_from_pricing(db, history, product)
        logger.info(f"      └─ Promotion ID: {promotion.id if promotion else 'None'}")
        
        log_flow_end(logger, "APPROVE DYNAMIC PRICING", success=True,
                    product=product.title,
                    new_price=f"${history.predicted_price}",
                    promotion_id=promotion.id if promotion else None)
        
        return {
            "success": True,
            "message": f"Dynamic pricing approved! Product '{product.title}' now has dynamic price ${history.predicted_price}",
            "product_id": product.id,
            "product_title": product.title,
            "new_dynamic_price": history.predicted_price,
            "base_price": product.base_price,
            "discount_percentage": product.discount_percentage,
            "promotion_id": promotion.id if promotion else None
        }
    
    @staticmethod
    def reject_prediction(token: str, db: Session, history_id: int):
        """
        Reject a pending prediction
        """
        log_flow_start(logger, "REJECT DYNAMIC PRICING", history_id=history_id)
        
        admin_id = get_user_id_from_token(token)
        logger.info(f"  Admin ID: {admin_id}")
        
        # Get history record
        history = db.query(DynamicPricingHistory).filter(
            DynamicPricingHistory.id == history_id
        ).first()
        
        if not history:
            logger.error(f"History record not found: {history_id}")
            ResponseHandler.not_found_error("Pricing History", history_id)
        
        logger.info(f"  Predicted Price: ${history.predicted_price}")
        logger.info(f"  Current Status: {history.status}")
        
        if history.status != "pending":
            logger.warning(f"Cannot reject: prediction is already {history.status}")
            return {
                "success": False,
                "message": f"Cannot reject: prediction is already {history.status}"
            }
        
        # Update history status
        history.status = "rejected"
        history.decided_at = datetime.utcnow()
        
        db.commit()
        db.refresh(history)
        
        log_flow_end(logger, "REJECT DYNAMIC PRICING", success=True,
                    status="rejected")
        
        return {
            "success": True,
            "message": f"Prediction rejected. Product price remains unchanged.",
            "history_id": history.id
        }
        history.decided_at = datetime.utcnow()
        
        db.commit()
        db.refresh(history)
        
        return {
            "success": True,
            "message": f"Prediction rejected. Product price remains unchanged.",
            "history_id": history.id
        }
    
    @staticmethod
    def deactivate_dynamic_pricing(token: str, db: Session, product_id: int):
        """
        Deactivate dynamic pricing for a product, reverting to base price
        """
        admin_id = get_user_id_from_token(token)
        
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            ResponseHandler.not_found_error("Product", product_id)
        
        if not product.is_dynamic_pricing_active:
            return {
                "success": False,
                "message": "Dynamic pricing is not active for this product"
            }
        
        # Deactivate
        product.is_dynamic_pricing_active = False
        product.discount_percentage = 0  # Reset discount
        
        db.commit()
        db.refresh(product)
        
        return {
            "success": True,
            "message": f"Dynamic pricing deactivated for '{product.title}'",
            "product_id": product.id,
            "product_title": product.title
        }
    
    @staticmethod
    def get_all_history(token: str, db: Session, page: int, limit: int, status_filter: str = None):
        """
        Get all dynamic pricing history with optional status filter
        """
        admin_id = get_user_id_from_token(token)
        
        query = db.query(DynamicPricingHistory).order_by(DynamicPricingHistory.created_at.desc())
        
        if status_filter:
            query = query.filter(DynamicPricingHistory.status == status_filter)
        
        history_records = query.offset((page - 1) * limit).limit(limit).all()
        
        # Enrich with product info
        result = []
        for record in history_records:
            product = db.query(Product).filter(Product.id == record.product_id).first()
            record_dict = {
                "id": record.id,
                "product_id": record.product_id,
                "admin_id": record.admin_id,
                "predicted_price": record.predicted_price,
                "original_price": record.original_price,
                "discount_from_original": record.discount_from_original,
                "status": record.status,
                "category": record.category,
                "brand_tier": record.brand_tier,
                "msrp": record.msrp,
                "cogs": record.cogs,
                "min_margin_req": record.min_margin_req,
                "inventory_qty": record.inventory_qty,
                "weeks_of_cover": record.weeks_of_cover,
                "sell_through_rate": record.sell_through_rate,
                "stock_age_days": record.stock_age_days,
                "daily_sales_velocity": record.daily_sales_velocity,
                "conversion_rate": record.conversion_rate,
                "cart_abandon_rate": record.cart_abandon_rate,
                "competitor_price": record.competitor_price,
                "competitor_price_diff_pct": record.competitor_price_diff_pct,
                "competitor_stock_status": record.competitor_stock_status,
                "market_saturation": record.market_saturation,
                "season": record.season,
                "holiday_event": record.holiday_event,
                "marketing_spend_boost": record.marketing_spend_boost,
                "created_at": record.created_at,
                "decided_at": record.decided_at,
                "product_title": product.title if product else "Deleted Product",
                "product_thumbnail": product.thumbnail if product else None,
            }
            result.append(record_dict)
        
        return {
            "message": f"Page {page} with {len(result)} history records",
            "data": result
        }
    
    @staticmethod
    def get_product_history(token: str, db: Session, product_id: int):
        """
        Get dynamic pricing history for a specific product
        """
        admin_id = get_user_id_from_token(token)
        
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            ResponseHandler.not_found_error("Product", product_id)
        
        history_records = db.query(DynamicPricingHistory).filter(
            DynamicPricingHistory.product_id == product_id
        ).order_by(DynamicPricingHistory.created_at.desc()).all()
        
        result = []
        for record in history_records:
            record_dict = {
                "id": record.id,
                "product_id": record.product_id,
                "admin_id": record.admin_id,
                "predicted_price": record.predicted_price,
                "original_price": record.original_price,
                "discount_from_original": record.discount_from_original,
                "status": record.status,
                "category": record.category,
                "brand_tier": record.brand_tier,
                "msrp": record.msrp,
                "cogs": record.cogs,
                "min_margin_req": record.min_margin_req,
                "inventory_qty": record.inventory_qty,
                "weeks_of_cover": record.weeks_of_cover,
                "sell_through_rate": record.sell_through_rate,
                "stock_age_days": record.stock_age_days,
                "daily_sales_velocity": record.daily_sales_velocity,
                "conversion_rate": record.conversion_rate,
                "cart_abandon_rate": record.cart_abandon_rate,
                "competitor_price": record.competitor_price,
                "competitor_price_diff_pct": record.competitor_price_diff_pct,
                "competitor_stock_status": record.competitor_stock_status,
                "market_saturation": record.market_saturation,
                "season": record.season,
                "holiday_event": record.holiday_event,
                "marketing_spend_boost": record.marketing_spend_boost,
                "created_at": record.created_at,
                "decided_at": record.decided_at,
                "product_title": product.title,
                "product_thumbnail": product.thumbnail,
            }
            result.append(record_dict)
        
        return {
            "message": f"Found {len(result)} history records for product '{product.title}'",
            "data": result
        }
    
    @staticmethod
    def get_products_for_pricing(token: str, db: Session, page: int, limit: int):
        """
        Get all products with their dynamic pricing status for admin view
        """
        admin_id = get_user_id_from_token(token)
        
        products = db.query(Product).order_by(Product.id.asc()).offset((page - 1) * limit).limit(limit).all()
        
        result = []
        for product in products:
            # Count pending predictions for this product
            pending_count = db.query(func.count(DynamicPricingHistory.id)).filter(
                DynamicPricingHistory.product_id == product.id,
                DynamicPricingHistory.status == "pending"
            ).scalar()
            
            result.append({
                "id": product.id,
                "title": product.title,
                "price": product.price,
                "base_price": product.base_price,
                "dynamic_price": product.dynamic_price,
                "is_dynamic_pricing_active": product.is_dynamic_pricing_active,
                "discount_percentage": product.discount_percentage,
                "stock": product.stock,
                "brand": product.brand,
                "thumbnail": product.thumbnail,
                "category_name": product.category.name if product.category else None,
                "pending_predictions": pending_count or 0,
            })
        
        return {
            "message": f"Page {page} with {len(result)} products",
            "data": result
        }
    
    @staticmethod
    def flush_history(token: str, db: Session, status_filter: str = None):
        """
        Flush (delete) all dynamic pricing history records.
        Optionally filter by status.
        """
        admin_id = get_user_id_from_token(token)
        logger.info(f"🗑️ FLUSH HISTORY: Admin {admin_id} flushing history, filter={status_filter}")
        
        query = db.query(DynamicPricingHistory)
        if status_filter:
            query = query.filter(DynamicPricingHistory.status == status_filter)
        
        count = query.count()
        query.delete(synchronize_session=False)
        db.commit()
        
        logger.info(f"🗑️ FLUSH HISTORY: Deleted {count} records")
        
        return {
            "success": True,
            "message": f"Flushed {count} history records",
            "deleted_count": count
        }
    
    @staticmethod
    def get_top_changes(token: str, db: Session, limit: int = 3):
        """
        Get the top N most significant dynamic price changes (approved only).
        Ordered by absolute discount percentage.
        """
        admin_id = get_user_id_from_token(token)
        
        # Get approved records with the highest absolute discount
        history_records = db.query(DynamicPricingHistory).filter(
            DynamicPricingHistory.status == "approved"
        ).order_by(
            func.abs(DynamicPricingHistory.discount_from_original).desc()
        ).limit(limit).all()
        
        result = []
        for record in history_records:
            product = db.query(Product).filter(Product.id == record.product_id).first()
            result.append({
                "id": record.id,
                "product_id": record.product_id,
                "product_title": product.title if product else "Deleted Product",
                "product_thumbnail": product.thumbnail if product else None,
                "original_price": record.original_price,
                "predicted_price": record.predicted_price,
                "discount_from_original": record.discount_from_original,
                "created_at": record.created_at,
                "is_active": product.is_dynamic_pricing_active if product else False
            })
        
        return {
            "success": True,
            "data": result
        }
    
    @staticmethod
    def update_prediction_status(token: str, db: Session, history_id: int, new_status: str):
        """
        Update the status of a prediction record.
        Allows re-approving rejected predictions or deactivating approved ones.
        """
        admin_id = get_user_id_from_token(token)
        logger.info(f"📝 UPDATE STATUS: Admin {admin_id} updating history {history_id} to {new_status}")
        
        history = db.query(DynamicPricingHistory).filter(
            DynamicPricingHistory.id == history_id
        ).first()
        
        if not history:
            logger.error(f"History record not found: {history_id}")
            ResponseHandler.not_found_error("Pricing History", history_id)
        
        old_status = history.status
        product = db.query(Product).filter(Product.id == history.product_id).first()
        
        if new_status == "approved" and old_status != "approved":
            # Approve/re-approve the prediction
            history.status = "approved"
            history.decided_at = datetime.utcnow()
            
            if product:
                if product.base_price is None:
                    product.base_price = float(product.price)
                product.dynamic_price = history.predicted_price
                product.is_dynamic_pricing_active = True
                if product.base_price > 0:
                    new_discount = ((product.base_price - history.predicted_price) / product.base_price) * 100
                    # Bound discount to 0-100%
                    product.discount_percentage = round(max(0, min(new_discount, 100)), 2)
            
            db.commit()
            return {
                "success": True,
                "message": f"Prediction re-approved and applied to product",
                "history_id": history.id,
                "new_status": "approved"
            }
        
        elif new_status == "rejected":
            # Reject (or re-reject) the prediction
            history.status = "rejected"
            history.decided_at = datetime.utcnow()
            db.commit()
            return {
                "success": True,
                "message": f"Prediction rejected",
                "history_id": history.id,
                "new_status": "rejected"
            }
        
        elif new_status == "pending":
            # Reset to pending (undo decision)
            history.status = "pending"
            history.decided_at = None
            db.commit()
            return {
                "success": True,
                "message": f"Prediction reset to pending",
                "history_id": history.id,
                "new_status": "pending"
            }
        
        elif new_status == "deactivated" and old_status == "approved":
            # Deactivate this specific approved pricing
            history.status = "rejected"  # Mark as rejected since it's no longer active
            history.decided_at = datetime.utcnow()
            
            if product and product.is_dynamic_pricing_active:
                # Check if there's another approved prediction to fall back to
                other_approved = db.query(DynamicPricingHistory).filter(
                    DynamicPricingHistory.product_id == history.product_id,
                    DynamicPricingHistory.status == "approved",
                    DynamicPricingHistory.id != history_id
                ).order_by(DynamicPricingHistory.decided_at.desc()).first()
                
                if other_approved:
                    product.dynamic_price = other_approved.predicted_price
                else:
                    product.is_dynamic_pricing_active = False
                    product.discount_percentage = 0
            
            db.commit()
            return {
                "success": True,
                "message": f"Dynamic pricing deactivated for this prediction",
                "history_id": history.id,
                "new_status": "rejected"
            }
        
        return {
            "success": False,
            "message": f"Invalid status transition from {old_status} to {new_status}"
        }
    
    @staticmethod
    def get_stats(token: str, db: Session):
        """
        Get dynamic pricing statistics for the dashboard.
        """
        admin_id = get_user_id_from_token(token)
        
        # Count by status
        pending_count = db.query(func.count(DynamicPricingHistory.id)).filter(
            DynamicPricingHistory.status == "pending"
        ).scalar() or 0
        
        approved_count = db.query(func.count(DynamicPricingHistory.id)).filter(
            DynamicPricingHistory.status == "approved"
        ).scalar() or 0
        
        rejected_count = db.query(func.count(DynamicPricingHistory.id)).filter(
            DynamicPricingHistory.status == "rejected"
        ).scalar() or 0
        
        # Count active dynamic pricing products
        active_products = db.query(func.count(Product.id)).filter(
            Product.is_dynamic_pricing_active == True
        ).scalar() or 0
        
        return {
            "success": True,
            "counts": {
                "pending": pending_count,
                "approved": approved_count,
                "rejected": rejected_count,
                "active_products": active_products
            }
        }

