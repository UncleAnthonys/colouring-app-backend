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


async def generate_adventure_reveal_gemini(character_data: dict, original_drawing_b64: str = None) -> str:
    """Generate Monsters Inc / Pixar style reveal - uses ORIGINAL DRAWING as visual reference
    
    Uses google.genai SDK with explicit size constraints to stay in standard pricing tier.
    Output: ~1024x1024 or 3:4 portrait (~864x1152) - both under 1 megapixel.
    """
    
    api_key = os.environ.get('GOOGLE_API_KEY') or os.environ.get('GEMINI_API_KEY')
    if not api_key:
        raise HTTPException(status_code=500, detail='Google API key not configured')
    
    try:
        # Use new SDK for consistent size control
        from google import genai
        from google.genai import types
        
        client = genai.Client(api_key=api_key)
        
        description = character_data.get("description", "")
        character_name = character_data.get("name", "Character")
        
        prompt = f'''I am showing you a CHILDS DRAWING. Transform this EXACT character into a Disney/Pixar 3D movie character.

CHARACTER NAME: {character_name}

===== CRITICAL: MATCH THE DRAWING =====
Look at the drawing I am showing you. Your output MUST be a 3D version of THIS EXACT CHARACTER:
- If it is a GIRL with hair, dress, etc - Create a 3D GIRL (like Boo from Monsters Inc, Riley from Inside Out)
- If it is a ONE-EYED MONSTER - Create a 3D monster (like Mike Wazowski)
- If it is a ROBOT - Create a 3D robot
- MATCH what you SEE in the drawing!

===== CHARACTER ANALYSIS =====
{description}

===== STYLE: PIXAR/DISNEY 3D =====
Transform the childs drawing into a character that looks like it belongs in:
- Monsters Inc (for monsters)
- Inside Out (for humanoid characters)  
- Toy Story (for toys/objects)
- Frozen/Tangled (for princesses/girls)

===== THE 3 MOST IMPORTANT RULES =====

**RULE 1 - MATCH THE DRAWING TYPE:**
- Drawing shows a HUMAN/GIRL - Output is a 3D HUMAN/GIRL (NOT a blob, NOT a monster)
- Drawing shows a MONSTER - Output is a 3D MONSTER
- Drawing shows clothing (jacket, skirt, dress) - Include that EXACT clothing
- Drawing shows hair (brown curls, blonde, etc) - Include that EXACT hair

**RULE 2 - EXACT FEATURES FROM DRAWING:**
- Hair color and style from the drawing
- Clothing from the drawing (black jacket, rainbow skirt, etc)
- Skin tone interpretation (if orange crayon = warm skin tone)
- Eye color from the drawing
- ALL details visible in the drawing

**RULE 3 - PIXAR QUALITY:**
- Big expressive Disney/Pixar eyes
- Smooth appealing 3D surfaces
- Emotion and personality in the face
- Professional movie-quality rendering

===== REQUIREMENTS =====
- Celebration background with confetti and sparkles
- Portrait orientation - show FULL figure
- NO TEXT anywhere on image
- Character looks JOYFUL and ALIVE

IMPORTANT: Look at the drawing! If it is a girl with brown hair and a rainbow skirt, create a 3D GIRL - not a rainbow blob!'''
        
        # Build content with original drawing if provided
        if original_drawing_b64:
            contents = [
                prompt,
                types.Part.from_bytes(
                    data=base64.b64decode(original_drawing_b64),
                    mime_type="image/jpeg"
                )
            ]
        else:
            contents = prompt
        
        # Generate with STANDARD size (under 1 megapixel to avoid 2K/4K pricing)
        # 3:4 portrait at standard resolution = ~864x1152 = 995,328 pixels
        response = client.models.generate_content(
            model='gemini-2.5-flash-image',
            contents=contents,
            config=types.GenerateContentConfig(
                response_modalities=['IMAGE', 'TEXT'],
                image_config=types.ImageConfig(
                    aspect_ratio='3:4',  # Portrait orientation
                    # Standard resolution - no 2K/4K upscaling
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
        raise HTTPException(status_code=500, detail=f'Reveal generation failed: {str(e)}')


async def generate_adventure_episode_gemini(character_data: dict, scene_prompt: str, age_rules: str, reveal_image_b64: str = None, story_text: str = None, character_emotion: str = None) -> str:
    """
    Generate black & white coloring page using the REVEAL IMAGE as reference.
    
    Uses 3:4 portrait aspect ratio for A4-style pages.
    character_emotion overrides the default reveal pose with scene-appropriate emotion.
    """
    
    api_key = os.environ.get('GOOGLE_API_KEY') or os.environ.get('GEMINI_API_KEY')
    if not api_key:
        raise HTTPException(status_code=500, detail='Google API key not configured')
    
    try:
        from google import genai
        from google.genai import types
        
        client = genai.Client(api_key=api_key)
        
        character_name = character_data.get("name", "Character")
        
        # Build emotion/pose guidance
        emotion_guidance = ""
        if character_emotion:
            emotion_guidance = f"""
*** CRITICAL - CHARACTER EMOTION AND POSE:
{character_name} should look {character_emotion} in this scene.
DO NOT copy the happy/celebratory pose from the reference image.
The reference image shows the character APPEARANCE (body shape, features, size).
But the EMOTION and POSE must match this scene: {character_emotion}
- If scared: hunched, worried expression, maybe hiding partially
- If curious: leaning forward, wide eye, reaching out
- If sad: drooping posture, downturned expression
- If determined: standing firm, focused expression
- If nervous: hesitant posture, uncertain expression
"""
        
        # Build prompt
        full_prompt = f'''[STRICT CONTROLS]: Monochrome black and white 1-bit line art only.
[VISUAL DOMAIN]: Technical Vector Graphic / Die-cut sticker template.
[COLOR CONSTRAINTS]: Strictly binary 1-bit color palette. Output must contain #000000 (Black) and #FFFFFF (White) ONLY. Any other color or shade of grey is a failure.

[STYLE]: Clean, bold, uniform-weight black outlines. Pure white empty interiors. Thick, heavy marker outlines. Bold 5pt vector strokes.

[MANDATORY EXCLUSIONS]: No gradients. No volume. No depth. No shadows. No grayscale. No shading. No color leaks. No 3D volume. Paper-white fills only.

[REFERENCE USE]: Use the attached image ONLY for the character's shape and silhouette. Completely ignore all color, value, and shading data from the reference. DO NOT use the colors or lighting from the reference.

Create a professional kids' COLORING BOOK PAGE.

*** CRITICAL: MONOCHROME OUTPUT ONLY ***
This MUST be a pure BLACK and WHITE image.
- BLACK lines (#000000) 
- WHITE background and fill areas (#FFFFFF)
- ABSOLUTELY NOTHING ELSE

CHARACTER: {character_name}
Use the reference image for SHAPE AND FORM ONLY - completely ignore all colors:
- Body shape, proportions, and size
- Distinctive features (number of eyes, horns, fur texture, etc.)
- Clothing style and accessories (but NOT their colors)

🚨 CRITICAL - DO NOT ADD OR REMOVE BODY PARTS:
- Count the arms in the reference - draw EXACTLY that many arms (usually 2)
- Count the legs in the reference - draw EXACTLY that many legs (usually 2)
- DO NOT add extra arms, tails, horns, wings, or appendages that aren't in the reference
- DO NOT add stripes or patterns to the body that aren't in the reference
- The character has a SPECIFIC anatomy - copy it EXACTLY

⚠️ CHARACTER BODY RULES:
- Keep STRUCTURAL LINES from reference (dress segments, buttons, hair sections)
- These define colorable areas - KEEP THEM
- But DO NOT ADD decorative patterns, swirls, or stripes to the character's body
- NO spirals, NO mandala patterns, NO decorative flourishes ON the character
- Character's body sections should be PLAIN WHITE inside, ready to color
- BACKGROUND can have intricate details, but CHARACTER stays structurally simple

{emotion_guidance}

STORY SCENE:
{scene_prompt}

AGE-APPROPRIATE COMPLEXITY:
{age_rules}

╔══════════════════════════════════════════════════════════════════════════════╗
║  ABSOLUTE REQUIREMENT: 100% MONOCHROME - BLACK INK ON WHITE PAPER            ║
╚══════════════════════════════════════════════════════════════════════════════╝

**THE REFERENCE IMAGE HAS COLORS - YOU MUST IGNORE THEM COMPLETELY**
The reference shows a colorful character. DO NOT reproduce those colors.
Convert everything to BLACK OUTLINES on WHITE:
- Pink dress section → WHITE area with BLACK outline
- Blue dress section → WHITE area with BLACK outline  
- Green dress section → WHITE area with BLACK outline
- Yellow hair → WHITE area with BLACK outline strokes
- Blue nose → WHITE area with BLACK outline (NOT blue!)
- ALL colors → WHITE areas with BLACK outlines

⚠️ ABSOLUTELY NO COLOR OR GREY ANYWHERE:
- No blue tints on nose, legs, or any body part
- No grey shading in trees, sky, or background
- No gradient fills anywhere
- Every single area must be PURE WHITE (#FFFFFF) inside
- The ONLY non-white pixels are the BLACK lines (#000000)

🎯 CRITICAL - PRESERVE CHARACTER'S EXACT SHAPE:
- Copy the character's EXACT body shape from the reference (rectangular, round, blob, etc.)
- If reference shows a RECTANGULAR/SQUARE body → draw RECTANGULAR/SQUARE body
- If reference shows a ROUND body → draw ROUND body  
- If reference shows a PLAIN/SIMPLE body → keep it PLAIN/SIMPLE
- The character must look IDENTICAL to the reference - same simplicity level
- Match the reference EXACTLY - no additions, no modifications
- Only convert COLORS to white - keep all SHAPES identical

**MONOCHROME MEANS:**
- Only 2 values: BLACK (#000000) and WHITE (#FFFFFF)
- No RGB colors at all - not even pale/light versions
- No pink, no blue, no green, no yellow, no red, no orange
- No grey, no cream, no beige, no any tint
- Like a photocopied line drawing

**EVERY AREA IS WHITE:**
- Character's dress = WHITE (all sections)
- Character's hair = WHITE  
- Character's skin = WHITE
- All clothing = WHITE
- All background = WHITE
- Children will add colors with their crayons

**INCLUDE MANY COLORABLE OBJECTS:**
- Butterflies, birds, squirrels, rabbits
- Flowers, mushrooms, leaves
- Fairies, sparkles as enclosed shapes
- Fill the scene with things to color

*** OUTPUT SPECIFICATION ***
Format: Pure black line art on white background
Colors allowed: BLACK and WHITE only
Shading: NONE
Gradients: NONE
Tints: NONE

This is a COLORING BOOK PAGE - children color it themselves.

FINAL CHECK - CRITICAL RULES:
1. Every pixel must be pure black (#000000) OR pure white (#FFFFFF) - nothing else
2. NO colors from reference - no blue, no orange, no any color
3. NO SOLID BLACK FILLS - clothing, hair, skin must be WHITE with black OUTLINES only
4. Black is ONLY for outlines/lines, NEVER for filling areas
5. All enclosed areas must be empty white space for children to color in'''
        
        # Build content with reveal image if provided
        if reveal_image_b64:
            # Convert reveal to grayscale to prevent color leaking
            from PIL import Image
            import io as pil_io
            reveal_bytes = base64.b64decode(reveal_image_b64)
            img = Image.open(pil_io.BytesIO(reveal_bytes))
            gray = img.convert('L').convert('RGB')  # Grayscale but keep RGB format
            buffer = pil_io.BytesIO()
            gray.save(buffer, format='PNG')
            gray_bytes = buffer.getvalue()
            
            contents = [
                full_prompt,
                types.Part.from_bytes(
                    data=gray_bytes,
                    mime_type="image/png"
                )
            ]
        else:
            contents = full_prompt
        
        # Generate with portrait aspect ratio - STANDARD pricing tier
        # 3:4 at standard resolution = ~864x1152 = 995,328 pixels (under 1MP)
        # This avoids 2K/4K pricing tiers
        response = client.models.generate_content(
            model='gemini-2.5-flash-image',
            contents=contents,
            config=types.GenerateContentConfig(
                response_modalities=['IMAGE', 'TEXT'],
                temperature=0,  # Lower temp for more deterministic, less creative drifting
                seed=42,  # Fixed seed for consistency (different from reveal)
                image_config=types.ImageConfig(
                    aspect_ratio='3:4'  # Portrait for A4-style, standard resolution
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
    Generate 3 personalized story themes based on character type and child age.
    
    Each theme has 10 episodes that tell a complete story featuring the character.
    Stories are tailored to:
    - Character type (monster = monster themes, princess = fairy tale themes, etc.)
    - Child age (simpler stories for younger kids, more complex for older)
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
        
        prompt = f'''You are creating personalized story adventures for a childrens coloring book app.

Based on this character named "{character_name}", generate 3 DIFFERENT story themes. Each theme should have 10 episodes that tell a complete story.

CHARACTER ANALYSIS:
{character_description}

{age_guide}

CRITICAL: The stories MUST be appropriate for the age group above. Follow the sentence length, vocabulary, and complexity guidelines exactly.

For each theme, provide:
1. Theme name that fits this character personality and type
2. Theme description (1 sentence, age-appropriate)
3. 10 episodes, each with:
   - Episode number (1-10)
   - Title (short, age-appropriate)
   - Scene description (detailed for drawing - what to draw including {character_name}, setting, other characters, action, objects)
   - Story text (MUST follow the age guidelines above for length and complexity)

IMPORTANT RULES:
- {character_name} is ALWAYS the hero of the story
- Match themes to character type:
  - Monster characters - monster school, spooky adventures, making friends despite being different
  - Princess/girl characters - fashion, art, friendship, magical adventures
  - Robot characters - invention, space, technology adventures
  - Animal characters - nature, forest, animal friends adventures
  - Superhero characters - saving the day, helping others
- Each theme must have a clear beginning, middle, and end across 10 episodes
- Always use "{character_name}" (not "the character") in story text
- Scene descriptions must be detailed enough to draw as coloring pages
- EVERY episode MUST have a "character_emotion" field (happy, sad, excited, nervous, scared, curious, proud, worried, surprised, determined)
- FOLLOW THE AGE GUIDELINES - this is for a {age_display} year old child!

⚠️ CRITICAL: Every episode MUST include ALL 5 fields: episode_num, title, scene_description, story_text, AND character_emotion. Missing fields will cause errors!

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
          "character_emotion": "happy",
          "scene_description": "Detailed description of scene...",
          "story_text": "Age-appropriate story text..."
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
