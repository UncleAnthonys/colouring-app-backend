"""
Adventure Gemini - Simplified Universal Character Reveal
Focus on: PROPORTIONS, COLORS, PIXAR FACE - in that priority order
"""

import os
import base64
import google.generativeai as genai
from fastapi import HTTPException


async def generate_adventure_reveal_gemini(character_data: dict) -> str:
    """Generate Monsters Inc / Pixar style reveal - proven to give best proportions and style"""
    
    api_key = os.environ.get('GOOGLE_API_KEY') or os.environ.get('GEMINI_API_KEY')
    if not api_key:
        raise HTTPException(status_code=500, detail='Google API key not configured')
    
    genai.configure(api_key=api_key)
    
    try:
        model = genai.GenerativeModel('gemini-2.5-flash-image')
        
        description = character_data.get("description", "")
        character_name = character_data.get("name", "Character")
        
        prompt = f'''Create a MONSTERS INC / PIXAR MOVIE style 3D character named "{character_name}" based on this child's drawing analysis:

{description}

===== STYLE =====
This should look like a character straight out of MONSTERS INC or INSIDE OUT - that specific Pixar aesthetic where ALL characters (even humans, princesses, animals) have that stylized, appealing movie look.

===== THE 3 MOST IMPORTANT RULES (FOLLOW EXACTLY) =====

**RULE 1 - PROPORTIONS ARE SACRED:**
Read the percentages in the analysis above. The child's proportions are INTENTIONAL:
- If body is 65-70% of total height → body must be MUCH LARGER than head
- If legs are 70% of height → make them EXTREMELY LONG (like the stick figure cyclops)
- If it's a tall thin character → keep it TALL and THIN
- If head is huge → keep it HUGE
- Do NOT normalize to standard cartoon proportions - the unusual proportions make it SPECIAL

**RULE 2 - EXACT COLORS (NO SUBSTITUTIONS):**
- Show ALL color sections in exact order
- ORANGE means ORANGE (not red)
- PURPLE means PURPLE (not blue)  
- If it has rainbow stripes → show ALL the rainbow stripes
- Never merge or skip color sections

**RULE 3 - MONSTERS INC AESTHETIC:**
Think Mike Wazowski, Sulley, Boo, the characters from Inside Out:
- Big expressive eyes with that Pixar sparkle and multiple light reflections
- Smooth, appealing 3D surfaces
- That specific Monsters Inc "feel" - fun, appealing, movie-quality
- Expression showing EMOTION (joy, excitement)
- The face should make you FEEL something

===== REQUIREMENTS =====
- Celebration background with confetti and sparkles
- Portrait orientation - show FULL figure
- NO TEXT anywhere on image
- Only include features that are in the original drawing (no random additions)
- Smooth Pixar-quality surfaces (not knitted, not felt, not woolen)

Generate the character now.'''
        
        response = model.generate_content([prompt])
        
        if response.parts:
            for part in response.parts:
                if hasattr(part, 'inline_data') and part.inline_data:
                    return base64.b64encode(part.inline_data.data).decode('utf-8')
        
        raise HTTPException(status_code=500, detail='No image generated')
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Reveal generation failed: {str(e)}')


async def generate_adventure_episode_gemini(character_data: dict, scene_prompt: str, age_rules: str, reveal_image_b64: str = None, story_text: str = None) -> str:
    """
    Generate black & white coloring page using the REVEAL IMAGE as reference.
    
    This ensures the coloring page character matches the reveal exactly.
    Gemini SEES the reveal image and converts it to line art in the scene.
    """
    
    api_key = os.environ.get('GOOGLE_API_KEY') or os.environ.get('GEMINI_API_KEY')
    if not api_key:
        raise HTTPException(status_code=500, detail='Google API key not configured')
    
    genai.configure(api_key=api_key)
    
    try:
        model = genai.GenerativeModel('gemini-2.5-flash-image')
        
        character_name = character_data.get("name", "Character")
        
        # Build prompt - this exact wording worked perfectly in testing
        full_prompt = f'''Create a COLORING PAGE for children.

I am showing you a reference character image. You must CONVERT this character into BLACK LINE ART and place them in the story scene.

⚠️ CRITICAL: THIS IS A COLORING PAGE - ZERO COLOR ALLOWED ⚠️
- The output must be 100% BLACK LINES on WHITE BACKGROUND
- NO color AT ALL - not green, not blue, not purple, not orange, not any color
- NOT EVEN A HINT of color anywhere
- Children will add the colors themselves with crayons
- If you add ANY color, the coloring page is ruined

CHARACTER: {character_name}
Match the reference image exactly - same proportions, same features, same distinctive elements.

STORY SCENE:
{scene_prompt}

AGE-APPROPRIATE COMPLEXITY:
{age_rules}

COLORING PAGE REQUIREMENTS:
- BLACK LINES ONLY on PURE WHITE BACKGROUND
- NO color anywhere - not on character, not on scene, not anywhere
- NO shading, NO grey gradients
- Bold clear lines for children to color
- Leave bottom 20% blank for story text
- All shapes enclosed so children can color them in

OUTPUT: 100% BLACK AND WHITE coloring page. Pure black lines on pure white background. ABSOLUTELY NO COLOR.'''
        
        # If we have a reveal image, include it as reference
        if reveal_image_b64:
            response = model.generate_content([
                full_prompt,
                {"mime_type": "image/png", "data": reveal_image_b64}
            ])
        else:
            response = model.generate_content([full_prompt])
        
        if response.parts:
            for part in response.parts:
                if hasattr(part, 'inline_data') and part.inline_data:
                    return base64.b64encode(part.inline_data.data).decode('utf-8')
        
        raise HTTPException(status_code=500, detail='No image generated')
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Episode generation failed: {str(e)}')
