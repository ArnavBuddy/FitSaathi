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

async def analyze_clothing_placement(image_bytes: bytes) -> dict:
    """Analyze a user's photo to determine where to place clothing for virtual try-on."""
    if not settings.GOOGLE_API_KEY:
        return {"error": "config_missing", "message": "GOOGLE_API_KEY is not set. Please add it to your .env file."}
    
    genai.configure(api_key=settings.GOOGLE_API_KEY)
    model = genai.GenerativeModel('gemini-2.0-flash')

    system_instruction = """
    You are an expert in virtual clothing try-on. You analyze user photos to determine 
    the exact position, size, and rotation for overlaying a piece of clothing. 
    Be precise and return valid JSON only.
    """

    user_prompt = """
    Analyze this photo of a person. Determine the best placement for overlaying a piece 
    of clothing (like a shirt, top, or dress). Return ONLY a valid JSON object with these fields:
    {
      "placement": {
        "top_percent": <number 0-100, how far from the top to place the clothing>,
        "left_percent": <number 0-100, how far from the left to place the clothing>,
        "width_percent": <number 1-100, width of the clothing relative to the image>,
        "rotation_degrees": <number -30 to 30, how much to rotate the clothing>
      },
      "clothing_type": "<one of: top, dress, outerwear, lower>",
      "confidence_score": <number 0.0 to 1.0>,
      "notes": "<one sentence about the placement>"
    }
    """

    try:
        response = model.generate_content([
            {"text": system_instruction},
            {"mime_type": "image/jpeg", "data": image_bytes},
            {"text": user_prompt}
        ])
        
        # Clean response text
        text = response.text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

        analysis = json.loads(text)
        
        # Add default values if needed
        if "placement" not in analysis:
            analysis["placement"] = {
                "top_percent": 15,
                "left_percent": 50,
                "width_percent": 60,
                "rotation_degrees": 0
            }
            
        return analysis
    except Exception as e:
        logger.error(f"Error analyzing clothing placement: {str(e)}")
        # Return default placement if analysis fails
        return {
            "placement": {
                "top_percent": 15,
                "left_percent": 50,
                "width_percent": 60,
                "rotation_degrees": 0
            },
            "clothing_type": "top",
            "confidence_score": 0.3,
            "notes": "Using default placement. Could not analyze photo precisely."
        }
