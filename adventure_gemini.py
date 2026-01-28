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
        
        prompt = f'''Create a Disney/Pixar quality 3D character from this child's drawing.

CHARACTER ANALYSIS:
{description}

STYLE & QUALITY (MOST IMPORTANT):
- Professional Pixar/Disney animation quality like Toy Story, Monsters Inc, Inside Out
- Smooth polished plastic/skin surfaces - NOT felt, fabric, or toy-like texture
- Expressive face with depth, personality, and emotion
- Proper lighting, shadows, and realistic 3D rendering
- Living breathing character, not a toy or puppet

KEY CHARACTER FEATURES (MUST INCLUDE):
- Follow exact proportions from analysis (if body is 60%, head is 35%, keep those ratios)
- Include ALL distinctive features mentioned (spikes, bolts, teeth, buttons, crown, etc)
- Show ALL color sections in exact order listed
- Count everything exactly (if 8 spikes, show 8; if 12 teeth, show 12)

BACKGROUND:
- Celebration scene with confetti, sparkles, rainbows
- Portrait orientation, NO TEXT

Bring this child's unique vision to life with Pixar-level professional quality.'''
        
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
