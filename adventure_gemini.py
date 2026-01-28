import os
import base64
import google.generativeai as genai
from fastapi import HTTPException

async def generate_adventure_reveal_gemini(character_data: dict) -> str:
    """Generate Disney/Pixar reveal using extracted character details universally"""
    api_key = os.environ.get('GOOGLE_API_KEY') or os.environ.get('GEMINI_API_KEY')
    if not api_key:
        raise HTTPException(status_code=500, detail='Google API key not configured')
    
    genai.configure(api_key=api_key)
    
    try:
        model = genai.GenerativeModel('gemini-2.5-flash-image')
        
        description = character_data.get("description", "")
        
        prompt = f'''THIS IS A CHILD'S DRAWING. THE PROPORTIONS ARE INTENTIONAL AND CORRECT. DO NOT NORMALIZE THEM.

CHARACTER ANALYSIS FROM CHILD'S DRAWING:
{description}

ABSOLUTE CRITICAL RULES - FOLLOW EXACTLY:

1. PROPORTIONS ARE THE CHARACTER'S IDENTITY - DO NOT CHANGE THEM:
   - If analysis says head is 25% of height and body is 52%, the body MUST be MORE THAN TWICE as tall as the head
   - If analysis says arms are 15% of height, keep them SHORT and stubby
   - If analysis says no legs visible and dress is 52% of height, make the dress EXTREMELY LONG
   - These are NOT mistakes - this is what makes this character unique
   - The unusual proportions ARE CORRECT - they are from a child's imagination

2. COLOR SECTIONS IN EXACT ORDER (CRITICAL):
   - If analysis lists Red, Yellow, Green, Blue, Orange sections, show ALL 5 in EXACT order
   - Each section must be clearly visible and distinct
   - Do NOT merge or skip any color sections

3. EXACT FEATURE COUNTS:
   - Count buttons, crown points, etc exactly as described
   - If 6 buttons, show exactly 6 buttons
   - If 3 red dots on crown, show exactly 3 red dots

4. DISNEY/PIXAR QUALITY:
   - Professional 3D rendering with depth
   - Expressive face with emotion and personality
   - Realistic textures for hair, fabric, skin
   - Proper lighting and shadows
   - NOT a toy - a living character

5. CELEBRATION BACKGROUND:
   - Magical scene with confetti, sparkles, rainbows
   - Portrait orientation
   - NO TEXT

REMEMBER: This is a CHILD'S DRAWING brought to life. The "weird" proportions are what make it special. DO NOT make it look like a normal person or character. Keep the exact proportions from the analysis.'''
        
        response = model.generate_content([prompt])
        
        if response.parts:
            for part in response.parts:
                if hasattr(part, 'inline_data') and part.inline_data:
                    return base64.b64encode(part.inline_data.data).decode('utf-8')
        
        raise HTTPException(status_code=500, detail='No image generated')
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Reveal generation failed: {str(e)}')

async def generate_adventure_episode_gemini(character_data: dict, scene_prompt: str, age_rules: str) -> str:
    """Generate black & white coloring page"""
    api_key = os.environ.get('GOOGLE_API_KEY') or os.environ.get('GEMINI_API_KEY')
    if not api_key:
        raise HTTPException(status_code=500, detail='Google API key not configured')
    
    genai.configure(api_key=api_key)
    
    try:
        model = genai.GenerativeModel('gemini-2.5-flash-image')
        
        structure_desc = f"""Character with distinctive features from original drawing"""
        
        full_prompt = f'''Create A4 portrait coloring page:

CHARACTER: {character_data["name"]} - {structure_desc}
SCENE: {scene_prompt}

FORMAT: A4 portrait - leave bottom 30% for story text
CRITICAL: BLACK LINES ONLY on WHITE BACKGROUND - NO COLOR FILLS
OUTPUT: Pure black line art suitable for children to color'''
        
        response = model.generate_content([full_prompt])
        
        if response.parts:
            for part in response.parts:
                if hasattr(part, 'inline_data') and part.inline_data:
                    return base64.b64encode(part.inline_data.data).decode('utf-8')
        
        raise HTTPException(status_code=500, detail='No image generated')
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Episode generation failed: {str(e)}')
