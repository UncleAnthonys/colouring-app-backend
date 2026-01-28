import os
import base64
import google.generativeai as genai
from fastapi import HTTPException
import time

GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")

async def extract_character_gemini(image_data: bytes, character_name: str):
    """Extract character with strict accuracy to original drawing"""
    
    if not GOOGLE_API_KEY:
        raise HTTPException(status_code=500, detail="Google API key not configured")
    
    genai.configure(api_key=GOOGLE_API_KEY)
    
    try:
        start_time = time.time()
        image_b64 = base64.b64encode(image_data).decode('utf-8')
        
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        analysis_prompt = """CRITICAL: Analyze this child's drawing with EXACT ACCURACY. Do not normalize or "fix" anything.

**STRICT ACCURACY RULES:**
1. **COUNT EXACTLY** - If there are 6 buttons, say exactly 6. If 8 spikes, say exactly 8. Never approximate.
2. **PRESERVE UNUSUAL PROPORTIONS** - If legs are extremely long, head is tiny, or torso is huge, that's the CHARACTER'S DISTINCTIVE FEATURE
3. **NEVER ADD ELEMENTS** - Only describe what's actually drawn. Don't add details that aren't there.
4. **LOCATION PRECISION** - If buttons run only up the middle, don't say "scattered throughout"
5. **PROPORTIONAL RELATIONSHIPS** - Measure head vs torso vs legs as ratios (e.g., "legs are 3x longer than torso")

**ANALYSIS FRAMEWORK:**

1. **PROPORTIONAL ANALYSIS**: 
   - Measure head size relative to body
   - Measure torso length relative to legs  
   - Measure arm length relative to body
   - Note ANY unusual proportions as key features

2. **EXACT ELEMENT COUNTING**:
   - Count buttons, dots, spikes, fingers, etc. exactly
   - Note precise placement (middle line, scattered, edges, etc.)
   - Record exact sequences and patterns

3. **DISTINCTIVE FEATURES**:
   - Identify what makes this character unique
   - Note unusual proportions, colors, or elements
   - These become story elements for adventures

4. **FLOW DIRECTION**:
   - Hair: Does it flow up, down, or sideways? How far?
   - Clothing: Recognize dresses, shirts, pants vs body segments
   - Elements: What direction do strokes go?

**REMEMBER**: The child's artistic choices (weird proportions, unusual features) are INTENTIONAL character design, not mistakes to fix."""

        response = model.generate_content([analysis_prompt, {"mime_type": "image/jpeg", "data": image_b64}])
        
        reveal_description = response.text
        extraction_time = time.time() - start_time
        
        return {
            "character": {
                "name": character_name,
                "description": reveal_description[:500] + "..." if len(reveal_description) > 500 else reveal_description,
                "key_feature": f"Distinctive features and proportions from {character_name}'s drawing"
            },
            "reveal_description": reveal_description,
            "extraction_time": extraction_time,
            "model_used": "gemini-2.5-flash-strict-accuracy"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Strict accuracy extraction failed: {str(e)}")

