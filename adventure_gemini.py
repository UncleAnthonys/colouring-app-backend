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
        
        # Parse the extracted description to create universal reveal prompt
        description = character_data.get("description", "")
        
        prompt = f'''Create a high-quality Disney/Pixar 3D character reveal:

CHARACTER: Based on this detailed analysis: {description}

CRITICAL INSTRUCTIONS:
1. HIGH-QUALITY Disney/Pixar 3D animation style - smooth, polished, professional
2. Use ONLY the character details from the analysis - preserve ALL distinctive features, proportions, and elements exactly as described
3. If hair is described as extending downward/flowing, make it LONG and flowing
4. If proportions are unusual (very tall, long limbs, etc.), PRESERVE these as key character features
5. CELEBRATION BACKGROUND: Magical scene with confetti, sparkles, colorful particles, rainbows
6. NO TEXT - just the character and celebration background
7. IGNORE any background elements from original drawing - character only

Translate the extracted character analysis into a beautiful 3D reveal while preserving every unique feature.'''
        
        response = model.generate_content([prompt])
        
        if response.parts:
            for part in response.parts:
                if hasattr(part, 'inline_data') and part.inline_data:
                    return base64.b64encode(part.inline_data.data).decode('utf-8')
        
        raise HTTPException(status_code=500, detail='No image generated')
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Reveal generation failed: {str(e)}')

async def generate_adventure_episode_gemini(character_data: dict, scene_prompt: str, age_rules: str) -> str:
    """Generate black & white coloring page using structure-only description"""
    api_key = os.environ.get('GOOGLE_API_KEY') or os.environ.get('GEMINI_API_KEY')
    if not api_key:
        raise HTTPException(status_code=500, detail='Google API key not configured')
    
    genai.configure(api_key=api_key)
    
    try:
        model = genai.GenerativeModel('gemini-2.5-flash-image')
        
        # Convert to structure-only for coloring pages
        structure_desc = f"""Character with distinctive features from original drawing:
- Preserve unique proportions and key visual elements
- Maintain character's special characteristics
- Age-appropriate for {age_rules}"""
        
        full_prompt = f'''Create A4 portrait coloring page:

CHARACTER: {character_data["name"]} - {structure_desc}
SCENE: {scene_prompt}

FORMAT: A4 portrait (tall, not square) - leave bottom 30% for story text
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
