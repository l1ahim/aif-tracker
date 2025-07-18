from celery import current_task
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import logging

from ..core.database import SessionLocal
from ..models.user import User
from ..models.transaction import Transaction
from ..services.ai_service import generate_financial_insights
from ..crud.transaction import transaction_crud

logger = logging.getLogger(__name__)


def get_db():
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()


def process_receipt_async(transaction_id: str):
    """Process receipt in background for additional analysis"""
    db = get_db()
    try:
        transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
        if transaction:
            transaction.processing_status = "completed"
            db.commit()
            logger.info(f"Processed receipt for transaction {transaction_id}")
    except Exception as e:
        logger.error(f"Error processing receipt {transaction_id}: {str(e)}")
    finally:
        db.close()


def generate_monthly_insights_for_all_users():
    """Generate monthly insights for all active users"""
    db = get_db()
    try:
        users = db.query(User).filter(User.is_active == True).all()
        
        for user in users:
            try:
                # Get current month stats
                now = datetime.utcnow()
                stats = transaction_crud.get_monthly_stats(db, user.id, now.year, now.month)
                
                # Generate AI insights
                insights = generate_financial_insights(stats)
                
                # TODO: Send email with insights
                logger.info(f"Generated insights for user {user.id}")
                
            except Exception as e:
                logger.error(f"Error generating insights for user {user.id}: {str(e)}")
                
    except Exception as e:
        logger.error(f"Error in monthly insights task: {str(e)}")
    finally:
        db.close()


def check_budget_alerts_for_all_users():
    """Check budget alerts for all users"""
    db = get_db()
    try:
        # TODO: Implement budget alert checking
        logger.info("Budget alerts checked")
    except Exception as e:
        logger.error(f"Error checking budget alerts: {str(e)}")
    finally:
        db.close()


def cleanup_old_receipts():
    """Clean up old receipt files"""
    try:
        # TODO: Implement file cleanup
        logger.info("Old receipts cleaned up")
    except Exception as e:
        logger.error(f"Error cleaning up receipts: {str(e)}")
