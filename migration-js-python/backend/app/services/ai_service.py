import google.generativeai as genai
from fastapi import UploadFile
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime
import json
import base64
import logging
from PIL import Image
import pillow_heif
import io

from app.core.config import settings

logger = logging.getLogger(__name__)

# Configure Google Gemini
if settings.has_gemini_config:
    genai.configure(api_key=settings.GEMINI_API_KEY)

# Register HEIF opener with Pillow
pillow_heif.register_heif_opener()

class ExtractedTransactionData(BaseModel):
    amount: float
    description: str
    merchant: Optional[str] = None
    category: Optional[str] = None
    date: Optional[datetime] = None
    confidence: float
    raw_data: str


class AIProvider:
    @staticmethod
    def get_active_provider() -> str:
        return settings.active_ai_provider
    
    @staticmethod
    async def extract_receipt_data(file: UploadFile) -> ExtractedTransactionData:
        provider = AIProvider.get_active_provider()
        
        if provider == "gemini":
            return await extract_with_gemini(file)
        # elif provider == "azure":
        #     return await extract_with_azure(file)
        else:
            logger.warning("No AI provider configured, using fallback")
            return ExtractedTransactionData(
                amount=0.0,
                description="Manual entry required - no AI provider configured",
                confidence=0.0,
                raw_data="No AI provider available"
            )

async def extract_transaction_data(file: UploadFile) -> ExtractedTransactionData:
    """Main entry point for transaction data extraction"""
    return await AIProvider.extract_receipt_data(file)

async def extract_with_gemini(file: UploadFile) -> ExtractedTransactionData:
    """Extract transaction data using Google Gemini"""
    try:
        # Read file contents
        contents = await file.read()
        
        # Convert HEIF/HEIC to JPEG if needed
        if file.content_type in ['image/heif', 'image/heic'] or file.filename.lower().endswith(('.heif', '.heic')):
            try:
                # Open HEIF image with Pillow
                image = Image.open(io.BytesIO(contents))
                
                # Convert to RGB if necessary
                if image.mode != 'RGB':
                    image = image.convert('RGB')
                
                # Save as JPEG
                jpeg_buffer = io.BytesIO()
                image.save(jpeg_buffer, format='JPEG', quality=85)
                contents = jpeg_buffer.getvalue()
                
                # Update content type for Gemini
                content_type = 'image/jpeg'
                
            except Exception as e:
                logger.warning(f"HEIF conversion failed: {e}, trying original format")
                content_type = file.content_type
        else:
            content_type = file.content_type
        
        # Encode image
        image_data = base64.b64encode(contents).decode()
        
        # Initialize Gemini model - use newer model
        model = genai.GenerativeModel("gemini-1.5-flash")  # Updated model name
        
        prompt = """
        Analyze this receipt image and extract the following information:
        - Total amount (number only, without currency symbol, in Romanian Lei/RON)
        - Merchant/business name
        - Date of transaction (if visible)
        - Brief description of items purchased (keep original language from receipt)
        - Suggested spending category (e.g., "Food", "Transportation", "Shopping", etc.)
        
        Return the information in the following JSON format:
        {
            "amount": 0.00,
            "merchant": "Business Name",
            "date": "DD/MM/YYYY",
            "description": "Brief description in original language",
            "category": "Category Name",
            "confidence": 0.95
        }
        
        CRITICAL: 
        - For the date field, extract the EXACT transaction date from the receipt. Use DD/MM/YYYY format. Do NOT use today's date - only the date printed on the receipt.
        - Keep the description in the original language (Romanian) - do NOT translate to English.
        - Preserve original item names and text as they appear on the receipt.
        
        If any information is unclear or missing, set confidence lower and use null for missing fields.
        Note: Convert any currency amounts to Romanian Lei (RON) if different currency is detected.
        """
        
        # Create image part for Gemini
        image_part = {
            "mime_type": content_type,
            "data": image_data
        }
        
        # Generate response
        response = model.generate_content([prompt, image_part])
        result_text = response.text
        logger.info(f"RAW GEMINI RESPONSE: {result_text}")
        print(f"RAW GEMINI RESPONSE: {result_text}")
        
        return parse_ai_response(result_text, "gemini")
        
    except Exception as e:
        logger.error(f"Gemini extraction failed: {e}")
        return create_fallback_response(f"Gemini error: {str(e)}")

def parse_ai_response(result_text: str, provider: str) -> ExtractedTransactionData:
    """Parse AI response text into structured data"""
    try:
        # Try to parse JSON response
        try:
            parsed_data = json.loads(result_text)
        except json.JSONDecodeError:
            # Extract JSON from code blocks
            import re
            json_match = re.search(r'```json\n(.*?)\n```', result_text, re.DOTALL)
            if json_match:
                parsed_data = json.loads(json_match.group(1))
            else:
                raise ValueError("Could not parse AI response as JSON")
        
        # Convert date string to datetime if provided
        transaction_date = None
        if parsed_data.get("date") and parsed_data["date"] not in ["null", None, ""]:
            date_str = str(parsed_data["date"]).strip()
            print(f"AI returned date: '{date_str}'")
            
            # Try parsing with multiple formats
            date_formats = [
                "%d/%m/%Y",    # DD/MM/YYYY (European)
                "%d.%m.%Y",    # DD.MM.YYYY
                "%d-%m-%Y",    # DD-MM-YYYY
                "%Y-%m-%d",    # YYYY-MM-DD
                "%m/%d/%Y",    # MM/DD/YYYY (US)
                "%d/%m/%y",    # DD/MM/YY
                "%d.%m.%y",    # DD.MM.YY
            ]
            
            for fmt in date_formats:
                try:
                    transaction_date = datetime.strptime(date_str, fmt)
                    print(f"Successfully parsed date '{date_str}' with format '{fmt}' -> {transaction_date}")
                    break
                except ValueError:
                    continue
            
            if not transaction_date:
                print(f"Failed to parse date '{date_str}' with any format")
        else:
            print(f"No valid date from AI: {parsed_data.get('date')}")
        
        result = ExtractedTransactionData(
            amount=float(parsed_data.get("amount", 0)),
            description=parsed_data.get("description", "Receipt scan"),
            merchant=parsed_data.get("merchant"),
            category=parsed_data.get("category"),
            date=transaction_date,
            confidence=float(parsed_data.get("confidence", 0.8)),
            raw_data=f"{provider} response: {result_text}"
        )
        print(f"Final ExtractedTransactionData date: {result.date}")
        if result.date:
            print(f"Date will be stored as: {result.date.isoformat()}")
        else:
            print("No date extracted - will use current time")
        return result
        
    except Exception as e:
        logger.error(f"Failed to parse {provider} response: {e}")
        return create_fallback_response(f"{provider} parsing error: {str(e)}")

def create_fallback_response(error_msg: str) -> ExtractedTransactionData:
    """Create fallback response when AI processing fails"""
    return ExtractedTransactionData(
        amount=0.0,
        description="Receipt scan - manual review needed",
        merchant=None,
        category=None,
        date=None,
        confidence=0.1,
        raw_data=error_msg
    )

def determine_category(merchant: Optional[str], content: str) -> Optional[str]:
    """Determine spending category based on merchant and content"""
    if not merchant and not content:
        return None
    
    text = (merchant or "").lower() + " " + content.lower()
    
    category_keywords = {
        "Food & Dining": ["restaurant", "cafe", "coffee", "pizza", "burger", "food", "dining", "starbucks", "mcdonald", "kfc", "pizza hut"],
        "Groceries": ["grocery", "supermarket", "market", "carrefour", "kaufland", "lidl", "auchan", "mega image", "profi"],
        "Transportation": ["gas", "fuel", "uber", "lyft", "taxi", "metro", "transit", "parking", "petrom", "omv", "rompetrol"],
        "Shopping": ["store", "mall", "amazon", "emag", "fashion days", "clothing", "apparel", "zara", "h&m"],
        "Healthcare": ["pharmacy", "hospital", "clinic", "medical", "doctor", "catena", "dona", "help net"],
        "Entertainment": ["movie", "theater", "netflix", "spotify", "game", "entertainment", "cinema"]
    }
    
    for category, keywords in category_keywords.items():
        if any(keyword in text for keyword in keywords):
            return category
    
    return "Other"
