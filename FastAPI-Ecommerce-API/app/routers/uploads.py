from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import FileResponse
from app.core.security import check_admin_role
import os
import uuid
import shutil
from pathlib import Path

router = APIRouter(tags=["Uploads"], prefix="/uploads")

# Configure upload directory
UPLOAD_DIR = Path(__file__).parent.parent.parent / "uploads" / "products"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Allowed file extensions
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB


def validate_file(file: UploadFile):
    """Validate uploaded file"""
    # Check file extension
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    return ext


@router.post("/image", dependencies=[Depends(check_admin_role)])
async def upload_image(file: UploadFile = File(...)):
    """
    Upload a product image.
    Returns the URL path to access the uploaded image.
    """
    # Validate file
    ext = validate_file(file)
    
    # Generate unique filename
    unique_filename = f"{uuid.uuid4()}{ext}"
    file_path = UPLOAD_DIR / unique_filename
    
    # Save file
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
    finally:
        file.file.close()
    
    # Return the URL path (using /static/uploads for static file serving)
    return {
        "success": True,
        "filename": unique_filename,
        "url": f"/static/uploads/products/{unique_filename}"
    }


@router.post("/images", dependencies=[Depends(check_admin_role)])
async def upload_multiple_images(files: list[UploadFile] = File(...)):
    """
    Upload multiple product images.
    Returns list of URL paths for the uploaded images.
    """
    uploaded = []
    
    for file in files:
        # Validate file
        ext = validate_file(file)
        
        # Generate unique filename
        unique_filename = f"{uuid.uuid4()}{ext}"
        file_path = UPLOAD_DIR / unique_filename
        
        # Save file
        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            uploaded.append({
                "filename": unique_filename,
                "url": f"/static/uploads/products/{unique_filename}"
            })
        except Exception as e:
            # Continue with other files if one fails
            pass
        finally:
            file.file.close()
    
    return {
        "success": True,
        "uploaded": uploaded,
        "count": len(uploaded)
    }


@router.get("/products/{filename}")
async def get_product_image(filename: str):
    """Serve uploaded product images"""
    file_path = UPLOAD_DIR / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Image not found")
    
    return FileResponse(file_path)
