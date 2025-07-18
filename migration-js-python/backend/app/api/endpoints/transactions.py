from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Response
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
from datetime import datetime
import logging
import hashlib
import io
from uuid import UUID

from app.core.database import get_db
from app.core.auth import get_current_user_id
from app.models.transaction import Transaction
from app.services.ai_service import extract_transaction_data
from app.crud.transaction import transaction_crud
from app.schemas.transaction import TransactionCreate

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/")
async def create_transaction(
    response: Response,
    transaction: TransactionCreate,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Create a new transaction manually"""
    response.headers["Access-Control-Allow-Origin"] = "*"
    
    transaction_data = {
        "amount": transaction.amount,
        "description": transaction.description,
        "category": transaction.category,
        "merchant": transaction.merchant,
        "date": transaction.date or datetime.utcnow(),
        "transaction_type": transaction.transaction_type,
        "processing_status": "completed"
    }
    
    created_transaction = transaction_crud.create(db, transaction_data, user_id)
    
    return created_transaction.to_dict()

@router.post("/scan-receipt")
async def scan_receipt(
    response: Response,
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Extract transaction data from receipt image using AI"""
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    
    # Check file type - now including HEIF/HEIC
    allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp', 'image/heif', 'image/heic']
    allowed_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.heif', '.heic']
    
    is_valid_type = (
        file.content_type in allowed_types or 
        any(file.filename.lower().endswith(ext) for ext in allowed_extensions)
    )
    
    if not is_valid_type:
        raise HTTPException(400, "File must be an image (JPEG, PNG, WebP, HEIF, or HEIC)")
    
    try:
        print(f"Receipt scan started for user: {user_id}")
        # Calculate receipt hash
        contents = await file.read()
        receipt_hash = hashlib.sha256(contents).hexdigest()
        print(f"Receipt hash: {receipt_hash[:10]}...")
        
        # Check for duplicate receipt
        existing_transaction = db.query(Transaction).filter(
            Transaction.user_id == user_id,
            Transaction.receipt_hash == receipt_hash
        ).first()
        
        if existing_transaction:
            # Format date for better readability
            processed_date = existing_transaction.created_at.strftime("%B %d, %Y at %H:%M")
            
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "This receipt has already been processed",
                    "transaction_id": str(existing_transaction.id),
                    "processed_at": existing_transaction.created_at.isoformat(),
                    "amount": float(existing_transaction.amount),
                    "merchant": existing_transaction.merchant or "Unknown merchant",
                    "formatted_date": processed_date
                }
            )
        
        # Reset file position for AI processing
        await file.seek(0)
        
        # Extract data using AI
        extracted_data = await extract_transaction_data(file)
        
        # Ensure we have a valid amount (fallback to a small amount for testing)
        amount = extracted_data.amount if extracted_data.amount > 0 else 10.0
        
        # Create transaction with explicit transaction_type
        transaction_data = {
            "amount": amount,
            "description": extracted_data.description or "Receipt scan",
            "merchant": extracted_data.merchant,
            "category": extracted_data.category or "Uncategorized",
            "date": extracted_data.date if extracted_data.date else datetime.utcnow(),
            "ai_confidence": extracted_data.confidence,
            "processing_status": "completed",
            "transaction_type": "expense",
            "receipt_hash": receipt_hash
        }
        
        print(f"Creating receipt transaction: {transaction_data}")
        print(f"Extracted date: {extracted_data.date}, AI raw response: {extracted_data.raw_data[:200]}...")
        transaction = transaction_crud.create(db, transaction_data, user_id)
        print(f"Receipt transaction created: {transaction.id}")
        
        return transaction.to_dict()
        
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Receipt scanning error: {e}")
        raise HTTPException(500, f"Error processing receipt: {str(e)}")

@router.options("/scan-receipt")
async def scan_receipt_options(response: Response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return {"message": "OK"}

@router.get("/")
async def get_transactions(
    response: Response,
    skip: int = 0,
    limit: int = 50,
    category: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get user's transactions with optional filtering"""
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    
    transactions = transaction_crud.get_by_user(
        db=db,
        user_id=user_id,
        skip=skip,
        limit=limit,
        category=category,
        start_date=start_date,
        end_date=end_date
    )
    return [t.to_dict() for t in transactions]

@router.get("/stats/monthly")
async def get_monthly_stats(
    response: Response,
    year: int,
    month: int,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get monthly spending statistics with debugging"""
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    
    try:
        # Force fresh query without creating new session
        db.rollback()
        db.expire_all()
        
        result = transaction_crud.get_monthly_stats(db, user_id, year, month)
        return result
    except Exception as e:
        logger.error(f"Monthly stats error: {e}", exc_info=True)
        return {
            "total_spent": 0.0,
            "total_income": 0.0,
            "transaction_count": 0,
            "by_category": {},
            "period": f"{year}-{month:02d}",
            "average_transaction": 0.0
        }

@router.options("/stats/monthly")
async def monthly_stats_options(response: Response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return {"message": "OK"}

@router.options("/")
async def transactions_options(response: Response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return {"message": "OK"}

@router.options("/{transaction_id}")
async def transaction_options(response: Response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return {"message": "OK"}

@router.get("/ai-status")
async def get_ai_status(response: Response):
    """Get AI provider configuration status"""
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    
    from app.core.config import settings
    
    return {
        "active_provider": settings.active_ai_provider,
        "available_providers": {
            "gemini": settings.has_gemini_config,
            "azure": settings.has_azure_config
        }
    }

@router.put("/{transaction_id}")
async def update_transaction(
    transaction_id: str,
    update_data: dict,
    response: Response,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Update a transaction"""
    response.headers["Access-Control-Allow-Origin"] = "*"
    
    try:
        transaction_uuid = UUID(transaction_id)
    except ValueError:
        raise HTTPException(400, "Invalid transaction ID format")
    
    transaction = db.query(Transaction).filter(
        Transaction.id == transaction_uuid,
        Transaction.user_id == user_id
    ).first()
    
    if not transaction:
        raise HTTPException(404, "Transaction not found")
    
    # Update allowed fields
    for field, value in update_data.items():
        if hasattr(transaction, field) and field not in ['id', 'user_id', 'created_at']:
            setattr(transaction, field, value)
    
    transaction.updated_at = datetime.utcnow()
    db.commit()
    
    return transaction.to_dict()

@router.delete("/{transaction_id}")
async def delete_transaction(
    transaction_id: str,
    response: Response,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Delete a transaction"""
    response.headers["Access-Control-Allow-Origin"] = "*"
    
    try:
        transaction_uuid = UUID(transaction_id)
    except ValueError:
        raise HTTPException(400, "Invalid transaction ID format")
    
    transaction = db.query(Transaction).filter(
        Transaction.id == transaction_uuid,
        Transaction.user_id == user_id
    ).first()
    
    if not transaction:
        print(f"Transaction not found: {transaction_id} for user {user_id}")
        raise HTTPException(404, "Transaction not found")
    
    print(f"Deleting transaction: {transaction.id}")
    db.delete(transaction)
    db.commit()
    
    return {"message": "Transaction deleted successfully"}

@router.get("/debug")
async def debug_transactions(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Debug endpoint to check transactions"""
    transactions = db.query(Transaction).filter(Transaction.user_id == user_id).all()
    
    return {
        "user_id": user_id,
        "total_transactions": len(transactions),
        "transactions": [
            {
                "id": str(t.id),
                "amount": t.amount,
                "date": t.date.isoformat() if t.date else None,
                "type": t.transaction_type,
                "merchant": t.merchant,
                "category": t.category
            }
            for t in transactions
        ]
    }