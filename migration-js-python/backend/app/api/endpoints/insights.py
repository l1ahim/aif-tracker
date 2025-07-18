from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc
from typing import List, Dict, Any
from datetime import datetime, timedelta

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.transaction import Transaction, BudgetCategory
from app.services.ai_service import generate_spending_insights, analyze_spending_patterns
from app.crud.transaction import transaction_crud

router = APIRouter()

@router.get("/dashboard-summary")
async def get_dashboard_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive dashboard summary with AI insights"""
    now = datetime.utcnow()
    
    # Current month stats
    monthly_stats = transaction_crud.get_monthly_stats(db, current_user.id, now.year, now.month)
    
    # Spending trend (last 30 days)
    spending_trend = transaction_crud.get_spending_trend(db, current_user.id, 30)
    
    # Top merchants
    top_merchants = transaction_crud.get_top_merchants(db, current_user.id, 5)
    
    # Recent transactions
    recent_transactions = transaction_crud.get_by_user(db, current_user.id, 0, 5)
    
    # Budget alerts
    budget_alerts = await get_budget_alerts_data(current_user, db)
    
    # AI tip of the day
    ai_tip = await generate_daily_tip(current_user, db)
    
    return {
        "monthly_stats": monthly_stats,
        "spending_trend": spending_trend,
        "top_merchants": top_merchants,
        "recent_transactions": [t.to_dict() for t in recent_transactions],
        "budget_alerts": budget_alerts,
        "ai_tip": ai_tip,
        "summary_generated_at": now.isoformat()
    }

@router.get("/spending-patterns")
async def get_spending_patterns(
    days: int = 90,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Analyze detailed spending patterns and habits"""
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Get transactions for analysis
    transactions = db.query(Transaction).filter(
        and_(
            Transaction.user_id == current_user.id,
            Transaction.date >= start_date,
            Transaction.transaction_type == "expense"
        )
    ).all()
    
    # Analyze patterns
    patterns = analyze_spending_patterns(transactions)
    
    # Day of week analysis
    day_of_week_spending = {}
    for transaction in transactions:
        day = transaction.date.strftime("%A")
        if day not in day_of_week_spending:
            day_of_week_spending[day] = 0
        day_of_week_spending[day] += transaction.amount
    
    # Time of day analysis (if we have hour data)
    hour_spending = {}
    for transaction in transactions:
        hour = transaction.date.hour
        if hour not in hour_spending:
            hour_spending[hour] = 0
        hour_spending[hour] += transaction.amount
    
    return {
        "patterns": patterns,
        "day_of_week_analysis": day_of_week_spending,
        "hour_analysis": hour_spending,
        "total_transactions": len(transactions),
        "period_days": days
    }

@router.get("/savings-opportunities")
async def get_savings_opportunities(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """AI-powered savings opportunity analysis"""
    # Get last 3 months of data
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=90)
    
    transactions = db.query(Transaction).filter(
        and_(
            Transaction.user_id == current_user.id,
            Transaction.date >= start_date,
            Transaction.transaction_type == "expense"
        )
    ).all()
    
    opportunities = []
    
    # Subscription analysis
    subscriptions = [t for t in transactions if t.is_recurring]
    if subscriptions:
        subscription_total = sum(s.amount for s in subscriptions)
        opportunities.append({
            "type": "subscription_review",
            "title": "Review Your Subscriptions",
            "description": f"You have {len(subscriptions)} recurring payments totaling ${subscription_total:.2f}/month",
            "potential_savings": subscription_total * 0.2,  # Estimate 20% savings
            "action": "Review and cancel unused subscriptions"
        })
    
    # Category-based opportunities
    category_spending = {}
    for transaction in transactions:
        category = transaction.category or "Uncategorized"
        if category not in category_spending:
            category_spending[category] = []
        category_spending[category].append(transaction.amount)
    
    # Find categories with high variance (potential for optimization)
    for category, amounts in category_spending.items():
        if len(amounts) >= 5:  # Need sufficient data
            avg_amount = sum(amounts) / len(amounts)
            max_amount = max(amounts)
            if max_amount > avg_amount * 1.5:  # High variance
                opportunities.append({
                    "type": "spending_optimization",
                    "title": f"Optimize {category} Spending",
                    "description": f"Your {category} spending varies significantly. Average: ${avg_amount:.2f}, Max: ${max_amount:.2f}",
                    "potential_savings": (max_amount - avg_amount) * len(amounts) / 12,  # Monthly estimate
                    "action": f"Set a budget limit for {category} category"
                })
    
    return {
        "opportunities": opportunities,
        "total_potential_savings": sum(opp.get("potential_savings", 0) for opp in opportunities)
    }

@router.get("/merchant-insights")
async def get_merchant_insights(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Detailed merchant spending analysis"""
    # Get last 6 months of data
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=180)
    
    merchant_data = db.query(
        Transaction.merchant,
        func.sum(Transaction.amount).label('total'),
        func.count(Transaction.id).label('count'),
        func.avg(Transaction.amount).label('average'),
        func.min(Transaction.date).label('first_visit'),
        func.max(Transaction.date).label('last_visit')
    ).filter(
        and_(
            Transaction.user_id == current_user.id,
            Transaction.merchant.isnot(None),
            Transaction.date >= start_date,
            Transaction.transaction_type == "expense"
        )
    ).group_by(Transaction.merchant).order_by(desc('total')).limit(20).all()
    
    insights = []
    for merchant in merchant_data:
        days_between = (merchant.last_visit - merchant.first_visit).days
        frequency = merchant.count / max(days_between / 30, 1)  # visits per month
        
        insights.append({
            "merchant": merchant.merchant,
            "total_spent": float(merchant.total),
            "visit_count": merchant.count,
            "average_spend": float(merchant.average),
            "frequency_per_month": round(frequency, 1),
            "first_visit": merchant.first_visit.isoformat(),
            "last_visit": merchant.last_visit.isoformat(),
            "loyalty_score": min(frequency * merchant.count / 10, 10)  # Simple loyalty metric
        })
    
    return {
        "merchant_insights": insights,
        "analysis_period_days": 180
    }

async def get_budget_alerts_data(user: User, db: Session):
    """Helper function to get budget alert data"""
    categories = db.query(BudgetCategory).filter(
        BudgetCategory.user_id == user.id,
        BudgetCategory.is_active == True
    ).all()
    
    alerts = []
    for category in categories:
        current_spending = category.get_current_spending(db)
        
        if category.budget_limit:
            percentage = (current_spending / category.budget_limit) * 100
            
            if percentage >= 100:
                alerts.append({
                    "type": "over_budget",
                    "category": category.name,
                    "current": current_spending,
                    "limit": category.budget_limit,
                    "percentage": percentage
                })
            elif percentage >= (category.alert_threshold * 100):
                alerts.append({
                    "type": "approaching_limit",
                    "category": category.name,
                    "current": current_spending,
                    "limit": category.budget_limit,
                    "percentage": percentage
                })
    
    return alerts

async def generate_daily_tip(user: User, db: Session):
    """Generate daily AI tip based on user's spending"""
    tips = [
        "💡 Track your daily coffee spending - small amounts add up quickly!",
        "🎯 Set a weekly dining out budget to maintain better control.",
        "📊 Review your subscriptions monthly to avoid unwanted charges.",
        "💰 Use the 24-hour rule for non-essential purchases over $50.",
        "📱 Enable budget alerts to stay on track with your financial goals."
    ]
    
    # In a real implementation, this would be AI-generated based on user data
    import random
    return random.choice(tips)
