from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session
import google.generativeai as genai
import json

from app.core.database import get_db
from app.core.auth import get_current_user_id
from app.core.config import settings

router = APIRouter()


@router.post("/generate-insight")
async def generate_spending_insight(
    data: dict,
    response: Response,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Generate AI-powered spending insights"""
    response.headers["Access-Control-Allow-Origin"] = "*"
    
    if not settings.has_gemini_config:
        return {"message": "💡 Keep tracking your expenses for better insights!"}
    
    try:
        monthly_stats = data.get('monthly_stats', {})
        recent_transactions = data.get('recent_transactions', [])
        
        # Prepare data for AI
        spending_data = {
            "total_spent": monthly_stats.get('total_spent', 0),
            "transaction_count": monthly_stats.get('transaction_count', 0),
            "average_transaction": monthly_stats.get('average_transaction', 0),
            "categories": monthly_stats.get('by_category', {}),
            "recent_transactions": [
                {
                    "amount": t.get('amount', 0),
                    "merchant": t.get('merchant', 'Unknown'),
                    "category": t.get('category', 'Other')
                }
                for t in recent_transactions[:3]
            ]
        }
        
        prompt = f"""
        Analyze this spending data and provide ONE personalized financial insight in Romanian:
        
        Monthly spending: {spending_data['total_spent']} lei
        Number of transactions: {spending_data['transaction_count']}
        Average transaction: {spending_data['average_transaction']} lei
        
        Categories: {json.dumps(spending_data['categories'], indent=2)}
        
        Recent transactions: {json.dumps(spending_data['recent_transactions'], indent=2)}
        
        Provide a single, actionable insight in Romanian (max 100 characters) with an emoji. 
        Focus on spending patterns, savings opportunities, or budgeting tips.
        Examples:
        - "🎯 60% din cheltuieli merg pe mâncare - încearcă să gătești mai mult acasă"
        - "💰 Tranzacțiile tale mici se adună - urmărește cheltuielile zilnice"
        - "📊 Cheltuiești constant - excelent pentru urmărirea bugetului!"
        
        Return only the insight message, nothing else.
        """
        
        model = genai.GenerativeModel("gemini-1.5-flash")
        result = model.generate_content(prompt)
        
        insight = result.text.strip()
        if len(insight) > 150:
            insight = insight[:147] + "..."
            
        return {"message": insight}
        
    except Exception as e:
        print(f"AI insight generation failed: {e}")
        return {"message": "💡 Continuă să urmărești cheltuielile pentru insights mai bune!"}


@router.options("/generate-insight")
async def ai_insight_options(response: Response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return {"message": "OK"}