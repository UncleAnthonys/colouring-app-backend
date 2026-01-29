"""
Adventure Gemini - Simplified Universal Character Reveal
Focus on: PROPORTIONS, COLORS, PIXAR FACE - in that priority order
"""

import os
import base64
import google.generativeai as genai
import json
from fastapi import HTTPException


def create_a4_page_with_text(image_b64: str, story_text: str, title: str = None) -> str:
    """
    Take a square coloring image and create an A4 page with story text below.
    
    Layout:
    - Top 85%: Large coloring illustration (fills the width)
    - Bottom 15%: Compact title + story text
    
    Returns: Base64 encoded A4 PNG image
    """
    from PIL import Image, ImageDraw, ImageFont
    import io
    import textwrap
    
    # A4 at 150 DPI = 1240 x 1754 pixels
    A4_WIDTH = 1240
    A4_HEIGHT = 1754
    
    # Decode the coloring image
    img_data = base64.b64decode(image_b64)
    coloring_img = Image.open(io.BytesIO(img_data))
    
    # Create A4 canvas (white)
    a4_page = Image.new('RGB', (A4_WIDTH, A4_HEIGHT), 'white')
    
    # Make coloring image as big as possible - 85% of page height
    # Leave only 15% for text at bottom
    max_coloring_height = int(A4_HEIGHT * 0.82)
    max_coloring_width = A4_WIDTH - 60  # Small margin each side
    
    # Scale to fit while maintaining aspect ratio
    img_ratio = coloring_img.width / coloring_img.height
    
    if img_ratio > (max_coloring_width / max_coloring_height):
        # Image is wider - fit to width
        new_width = max_coloring_width
        new_height = int(new_width / img_ratio)
    else:
        # Image is taller - fit to height
        new_height = max_coloring_height
        new_width = int(new_height * img_ratio)
    
    # Resize coloring image
    coloring_img = coloring_img.resize((new_width, new_height), Image.LANCZOS)
    
    # Center horizontally, place at top with small margin
    x_offset = (A4_WIDTH - new_width) // 2
    y_offset = 30  # Small top margin
    
    a4_page.paste(coloring_img, (x_offset, y_offset))
    
    # Draw a thin border around the coloring image
    draw = ImageDraw.Draw(a4_page)
    draw.rectangle(
        [x_offset - 2, y_offset - 2, x_offset + new_width + 2, y_offset + new_height + 2],
        outline='black',
        width=2
    )
    
    # Text area starts below the image - compact layout
    text_area_top = y_offset + new_height + 20
    
    # Try to load fonts - moderate sizes for compact area
    try:
        title_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 38)
        story_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 26)
    except:
        try:
            title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 38)
            story_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 26)
        except:
            title_font = ImageFont.load_default()
            story_font = ImageFont.load_default()
    
    current_y = text_area_top
    
    # Draw title if provided
    if title:
        title_bbox = draw.textbbox((0, 0), title, font=title_font)
        title_width = title_bbox[2] - title_bbox[0]
        title_x = (A4_WIDTH - title_width) // 2
        draw.text((title_x, current_y), title, fill='black', font=title_font)
        current_y += 50
    
    # Wrap and draw story text - single line if short enough
    wrapped_text = textwrap.fill(story_text, width=65)
    
    for line in wrapped_text.split('\n'):
        line_bbox = draw.textbbox((0, 0), line, font=story_font)
        line_width = line_bbox[2] - line_bbox[0]
        line_x = (A4_WIDTH - line_width) // 2
        draw.text((line_x, current_y), line, fill='black', font=story_font)
        current_y += 35
    
    # Convert to base64
    buffer = io.BytesIO()
    a4_page.save(buffer, format='PNG', dpi=(150, 150))
    buffer.seek(0)
    
    return base64.b64encode(buffer.read()).decode('utf-8')


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
    
    Uses 3:4 portrait aspect ratio for A4-style pages.
    """
    
    api_key = os.environ.get('GOOGLE_API_KEY') or os.environ.get('GEMINI_API_KEY')
    if not api_key:
        raise HTTPException(status_code=500, detail='Google API key not configured')
    
    try:
        from google import genai
        from google.genai import types
        
        client = genai.Client(api_key=api_key)
        
        character_name = character_data.get("name", "Character")
        
        # Build prompt
        full_prompt = f'''Create a COLORING PAGE for children.

⚠️ CRITICAL: THIS IS A COLORING PAGE - ZERO COLOR ALLOWED ⚠️
- The output must be 100% BLACK LINES on WHITE BACKGROUND
- NO color AT ALL - not green, not blue, not purple, not orange, not any color
- Children will add the colors themselves with crayons

CHARACTER: {character_name}
Match the reference image exactly - same proportions, same features, same distinctive elements.

STORY SCENE:
{scene_prompt}

AGE-APPROPRIATE COMPLEXITY:
{age_rules}

COLORING PAGE REQUIREMENTS:
- BLACK LINES ONLY on PURE WHITE BACKGROUND
- NO color anywhere
- NO shading, NO grey gradients  
- Bold clear lines for children to color
- All shapes enclosed so children can color them in
- Fill the entire image with the illustration

OUTPUT: Black and white coloring page. NO COLOR.'''
        
        # Build content with reveal image if provided
        if reveal_image_b64:
            contents = [
                full_prompt,
                types.Part.from_bytes(
                    data=base64.b64decode(reveal_image_b64),
                    mime_type="image/png"
                )
            ]
        else:
            contents = full_prompt
        
        # Generate with portrait aspect ratio
        response = client.models.generate_content(
            model='gemini-2.5-flash-image',
            contents=contents,
            config=types.GenerateContentConfig(
                response_modalities=['IMAGE', 'TEXT'],
                image_config=types.ImageConfig(
                    aspect_ratio='3:4'  # Portrait for A4-style
                )
            )
        )
        
        # Extract image from response
        for part in response.candidates[0].content.parts:
            if hasattr(part, 'inline_data') and part.inline_data:
                return base64.b64encode(part.inline_data.data).decode('utf-8')
        
        raise HTTPException(status_code=500, detail='No image generated')
        
    except ImportError as e:
        raise HTTPException(status_code=500, detail=f'google-genai package not installed: {str(e)}')
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
