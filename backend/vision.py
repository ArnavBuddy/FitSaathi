import google.generativeai as genai
from .config import settings
import json
import logging

logger = logging.getLogger(__name__)

async def analyze_body_photo(image_bytes: bytes) -> dict:
    if not settings.GOOGLE_API_KEY:
        return {"error": "config_missing", "message": "GOOGLE_API_KEY is not set. Please add it to your .env file."}
    
    genai.configure(api_key=settings.GOOGLE_API_KEY)
    model = genai.GenerativeModel('gemini-2.0-flash')

    system_instruction = """
    You are a professional body measurement analyst. You analyze 
    full-body photographs to extract body proportions for clothing 
    recommendations. Be precise, non-judgmental, and clinical. 
    Always return valid JSON only.
    """

    user_prompt = """
    Analyze this full-body photograph and extract the following. 
    Return ONLY a valid JSON object with no explanation, no markdown. 

    { 
      "body_type": "<one of: pear|hourglass|athletic|inverted_triangle|rectangle|plus>", 
      "height_category": "<one of: petite|regular|tall>", 
      "shoulder_width": "<one of: narrow|medium|broad>", 
      "waist_definition": "<one of: defined|moderate|straight>", 
      "hip_ratio": "<one of: narrow|balanced|wide>", 
      "torso_length": "<one of: short|average|long>", 
      "leg_length": "<one of: short|average|long>", 
      "estimated_measurements": { 
        "shoulder_cm_range": [min, max], 
        "chest_cm_range": [min, max], 
        "waist_cm_range": [min, max], 
        "hip_cm_range": [min, max], 
        "inseam_cm_range": [min, max] 
      }, 
      "recommended_fits": ["<fit types that suit this body>"], 
      "avoid_fits": ["<fit types to avoid>"], 
      "flattering_styles": ["<style approaches that enhance proportions>"], 
      "confidence_score": <float 0.0 to 1.0>, 
      "analysis_notes": "<one sentence summary>" 
    }
    """

    try:
        response = model.generate_content([
            {"text": system_instruction},
            {"mime_type": "image/jpeg", "data": image_bytes},
            {"text": user_prompt}
        ])
        
        # Clean response text from markdown code blocks if present
        text = response.text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

        analysis = json.loads(text)
        
        # Basic validation if it's actually a body photo analysis
        if "body_type" not in analysis:
             return {"error": "not_full_body", "message": "The image does not appear to be a full-body photo or could not be analyzed."}
             
        return analysis
    except Exception as e:
        logger.error(f"Error analyzing body photo: {str(e)}")
        return {"error": "analysis_failed", "message": f"Failed to analyze image: {str(e)}"}
