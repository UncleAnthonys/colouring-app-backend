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


async def generate_personalized_stories(character_name: str, character_description: str, age_level: str = "age_6") -> dict:
    """
    Generate 3 personalized story themes based on character type and child's age.
    
    Each theme has 10 episodes that tell a complete story featuring the character.
    Stories are tailored to:
    - Character type (monster = monster themes, princess = fairy tale themes, etc.)
    - Child's age (simpler stories for younger kids, more complex for older)
    """
    
    api_key = os.environ.get('GOOGLE_API_KEY') or os.environ.get('GEMINI_API_KEY')
    if not api_key:
        raise HTTPException(status_code=500, detail='Google API key not configured')
    
    genai.configure(api_key=api_key)
    
    # Age-specific story guidelines
    age_guidelines = {
        "age_3": """
AGE GROUP: 2-3 YEARS OLD (TODDLER)
- VERY simple sentences (5-8 words max)
- Basic emotions only: happy, sad, scared, excited
- Familiar settings: home, garden, playground, farm
- Simple actions: walking, running, eating, sleeping, hugging
- No complex plots - just simple discoveries and moments
- Repetition is good ("Rainbow walked. Rainbow saw a flower. Rainbow smiled.")
- No villains or scary elements
- Story text: 1-2 very short sentences per episode
- Scene descriptions: Simple, few elements (character + 2-3 objects max)
""",
        "age_4": """
AGE GROUP: 4 YEARS OLD
- Simple sentences (8-12 words)
- Basic story progression: beginning, simple problem, happy ending
- Familiar settings with light magic: enchanted garden, friendly forest
- Simple emotions and basic friendships
- Gentle challenges that are easily overcome
- Story text: 2 short sentences per episode
- Scene descriptions: Character + simple setting + 1 friend or object
""",
        "age_5": """
AGE GROUP: 5 YEARS OLD
- Medium sentences, slightly more vocabulary
- Clear 3-part stories: setup, small adventure, resolution
- Can include mild suspense (will they find the lost item?)
- Friendship themes, helping others, being brave
- Settings can be more fantastical: castles, undersea, clouds
- Story text: 2-3 sentences per episode
- Scene descriptions: More detail, can include background characters
""",
        "age_6": """
AGE GROUP: 6 YEARS OLD
- Fuller sentences with descriptive words
- Multi-episode story arcs that connect
- Can include mild challenges and problem-solving
- Themes: friendship, creativity, discovery, helping community
- Magical elements and fantasy settings welcome
- Story text: 2-3 engaging sentences per episode
- Scene descriptions: Rich detail with multiple elements
""",
        "age_7": """
AGE GROUP: 7 YEARS OLD
- Complex sentences with good vocabulary
- Connected story arcs with cause and effect
- Characters can face challenges and grow
- Themes: teamwork, perseverance, creativity, adventure
- Can include mild mystery or quest elements
- Story text: 3 sentences with more detail
- Scene descriptions: Complex scenes with action and emotion
""",
        "age_8": """
AGE GROUP: 8 YEARS OLD
- Rich vocabulary and varied sentence structure
- Complex plots with subplots
- Character development across episodes
- Themes: responsibility, friendship challenges, discovery
- Can include mysteries, quests, competitions
- Story text: 3-4 descriptive sentences
- Scene descriptions: Dynamic scenes with multiple characters and action
""",
        "age_9": """
AGE GROUP: 9 YEARS OLD
- Advanced vocabulary and complex narrative
- Sophisticated story arcs with twists
- Deep character development and relationships
- Themes: identity, belonging, overcoming obstacles, leadership
- Can include multi-layered adventures
- Story text: 3-4 rich, engaging sentences
- Scene descriptions: Detailed, cinematic scenes
""",
        "age_10": """
AGE GROUP: 10+ YEARS OLD
- Mature vocabulary and nuanced storytelling
- Complex interconnected plots
- Character growth and meaningful challenges
- Themes: self-discovery, complex friendships, making hard choices
- Can include epic quests, mysteries, world-building
- Story text: 4+ sentences with depth
- Scene descriptions: Highly detailed, dramatic compositions
"""
    }
    
    # Get age guidelines or default to age_6
    age_guide = age_guidelines.get(age_level, age_guidelines["age_6"])
    
    # Extract just the age number for display
    age_display = age_level.replace("age_", "")
    if age_display == "3":
        age_display = "2-3"
    elif age_display == "10":
        age_display = "10+"
    
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        prompt = f'''You are creating personalized story adventures for a children's coloring book app.

Based on this character named "{character_name}", generate 3 DIFFERENT story themes. Each theme should have 10 episodes that tell a complete story.

CHARACTER ANALYSIS:
{character_description}

{age_guide}

CRITICAL: The stories MUST be appropriate for the age group above. Follow the sentence length, vocabulary, and complexity guidelines exactly.

For each theme, provide:
1. Theme name that fits this character's personality and type
2. Theme description (1 sentence, age-appropriate)
3. 10 episodes, each with:
   - Episode number (1-10)
   - Title (short, age-appropriate)
   - Scene description (detailed for drawing - what to draw including {character_name}, setting, other characters, action, objects)
   - Story text (MUST follow the age guidelines above for length and complexity)

IMPORTANT RULES:
- {character_name} is ALWAYS the hero of the story
- Match themes to character type:
  - Monster characters → monster school, spooky adventures, making friends despite being different
  - Princess/girl characters → fashion, art, friendship, magical adventures
  - Robot characters → invention, space, technology adventures
  - Animal characters → nature, forest, animal friends adventures
  - Superhero characters → saving the day, helping others
- Each theme must have a clear beginning, middle, and end across 10 episodes
- Always use "{character_name}" (not "the character") in story text
- Scene descriptions must be detailed enough to draw as coloring pages
- FOLLOW THE AGE GUIDELINES - this is for a {age_display} year old child!

Return ONLY valid JSON in this exact format (no markdown, no extra text):
{{
  "character_name": "{character_name}",
  "age_level": "{age_level}",
  "themes": [
    {{
      "theme_id": "theme_name_lowercase_underscore",
      "theme_name": "Theme Display Name",
      "theme_description": "One sentence description of the adventure.",
      "episodes": [
        {{
          "episode_num": 1,
          "title": "Episode Title",
          "scene_description": "Detailed description of scene with {character_name} doing something specific in a specific setting with specific objects and possibly other characters.",
          "story_text": "Age-appropriate story text following the guidelines above."
        }}
      ]
    }}
  ]
}}

Generate 3 complete themes with all 10 episodes each. Return ONLY the JSON, no other text.'''
        
        response = model.generate_content([prompt])
        
        # Parse the JSON response
        text = response.text.strip()
        
        # Remove markdown code blocks if present
        if text.startswith('```json'):
            text = text[7:]
        if text.startswith('```'):
            text = text[3:]
        if text.endswith('```'):
            text = text[:-3]
        text = text.strip()
        
        # Find JSON boundaries
        start = text.find('{')
        end = text.rfind('}') + 1
        
        if start >= 0 and end > start:
            import json
            json_str = text[start:end]
            data = json.loads(json_str)
            return data
        
        raise HTTPException(status_code=500, detail='Failed to parse story response as JSON')
        
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f'JSON parse error: {str(e)}')
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Story generation failed: {str(e)}')
