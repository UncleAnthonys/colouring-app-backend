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




def create_front_cover(image_b64: str, theme_name: str, character_name: str) -> str:
    """
    Create a front cover for the story book.
    
    Layout:
    - Top: "A [Character Name] Adventure" 
    - Middle: Large coloring illustration
    - Bottom: Theme/Story title
    
    Returns: Base64 encoded A4 PNG image
    """
    from PIL import Image, ImageDraw, ImageFont
    import io
    import textwrap
    
    # A4 at 150 DPI
    A4_WIDTH = 1240
    A4_HEIGHT = 1754
    
    # Decode the coloring image
    img_data = base64.b64decode(image_b64)
    coloring_img = Image.open(io.BytesIO(img_data))
    
    # Create A4 canvas (white)
    a4_page = Image.new('RGB', (A4_WIDTH, A4_HEIGHT), 'white')
    draw = ImageDraw.Draw(a4_page)
    
    # Load fonts
    try:
        title_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 52)
        subtitle_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 36)
    except:
        try:
            title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 52)
            subtitle_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 36)
        except:
            title_font = ImageFont.load_default()
            subtitle_font = ImageFont.load_default()
    
    # Top text: "A Coloring Story Book"
    top_text = "A Coloring Story Book"
    top_bbox = draw.textbbox((0, 0), top_text, font=subtitle_font)
    top_width = top_bbox[2] - top_bbox[0]
    draw.text(((A4_WIDTH - top_width) // 2, 50), top_text, fill='black', font=subtitle_font)
    
    # Scale and center the coloring image
    max_img_height = int(A4_HEIGHT * 0.65)
    max_img_width = A4_WIDTH - 100
    
    img_ratio = coloring_img.width / coloring_img.height
    if img_ratio > (max_img_width / max_img_height):
        new_width = max_img_width
        new_height = int(new_width / img_ratio)
    else:
        new_height = max_img_height
        new_width = int(new_height * img_ratio)
    
    coloring_img = coloring_img.resize((new_width, new_height), Image.LANCZOS)
    
    # Center image vertically in middle section
    x_offset = (A4_WIDTH - new_width) // 2
    y_offset = 120  # Below top text
    
    a4_page.paste(coloring_img, (x_offset, y_offset))
    
    # Draw border around image
    draw.rectangle(
        [x_offset - 3, y_offset - 3, x_offset + new_width + 3, y_offset + new_height + 3],
        outline='black',
        width=3
    )
    
    # Bottom: Full book title combining character and theme
    title_y = y_offset + new_height + 40
    
    # Create full title: "Character Name and Theme Name"
    # Clean up theme name if it already has "The" at start
    clean_theme = theme_name
    if not theme_name.lower().startswith("the "):
        clean_theme = "the " + theme_name
    
    full_title = f"{character_name} and {clean_theme}"
    
    # Wrap title if too long
    wrapped_title = textwrap.fill(full_title, width=35)
    for line in wrapped_title.split('\n'):
        line_bbox = draw.textbbox((0, 0), line, font=title_font)
        line_width = line_bbox[2] - line_bbox[0]
        draw.text(((A4_WIDTH - line_width) // 2, title_y), line, fill='black', font=title_font)
        title_y += 60
    
    # Convert to base64
    buffer = io.BytesIO()
    a4_page.save(buffer, format='PNG', dpi=(150, 150))
    buffer.seek(0)
    return base64.b64encode(buffer.getvalue()).decode('utf-8')


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
        source_type = character_data.get("source_type", "drawing")
        
        if source_type == "photo":
            prompt = f'''I am showing you a REAL PHOTOGRAPH of a subject. Transform this EXACT subject into a Disney/Pixar 3D movie character.

CHARACTER NAME: {character_name}

===== CRITICAL: MATCH THE PHOTO SUBJECT =====
Look at the photo I am showing you. Your output MUST be a Pixar 3D version of THIS EXACT subject:
- If it is a STUFFED TOY / PLUSH → Bring it to LIFE like Toy Story (Lotso, Woody)
- If it is a REAL ANIMAL / PET → Anthropomorphize like Zootopia, Bolt, Puss in Boots
- If it is a CHILD / PERSON → Pixar-stylize like Inside Out, Coco, Brave
- If it is an OBJECT → Personify like Cars, Forky
- MATCH what you SEE in the photo!

===== CHARACTER ANALYSIS =====
{description}

===== STYLE: PIXAR/DISNEY 3D =====
Transform the photo subject into a character that looks like it belongs in:
- Toy Story (for toys/plush - bring them to LIFE)
- Zootopia (for animals - anthropomorphize with personality)
- Inside Out / Coco (for humans - stylize with Pixar charm)
- Cars / Forky (for objects - personify)

===== THE 3 MOST IMPORTANT RULES =====

**RULE 1 - MATCH THE PHOTO SUBJECT:**
- Photo shows a STUFFED MONKEY → Output is a Pixar 3D MONKEY CHARACTER (alive, expressive, same proportions)
- Photo shows a DOG → Output is a Pixar 3D DOG (like Bolt or Dug from Up)
- Photo shows a CHILD → Output is a Pixar 3D CHILD (like Riley from Inside Out)
- Keep ALL identifying features: colors, proportions, markings, texture

**RULE 2 - EXACT FEATURES FROM PHOTO:**
- Fur/hair color and pattern from the photo
- Body proportions from the photo (long arms stay long, big head stays big)
- Eye color and face shape from the photo
- Any distinctive markings, patterns, or accessories
- ALL details visible in the photo

**RULE 3 - PIXAR QUALITY:**
- Big expressive Disney/Pixar eyes (even if subject has small bead eyes - enlarge and add life!)
- Smooth appealing 3D surfaces with appropriate texture
- Emotion and personality in the face - JOYFUL and ALIVE
- Professional movie-quality rendering

===== REQUIREMENTS =====
- Celebration background with confetti and sparkles
- Portrait orientation - show FULL figure
- ABSOLUTELY NO WATERMARKS, NO SIGNATURES, NO TEXT, NO LOGOS anywhere in the image
- ABSOLUTELY NO WATERMARKS, NO SIGNATURES, NO TEXT, NO LOGOS anywhere in the image
- This is original art - do not copy or include any watermarks from any source
- NO TEXT anywhere on image
- Character looks JOYFUL and ALIVE
- Character should be STANDING/POSED (even if photo shows subject sitting/lying)

IMPORTANT: Look at the photo! Transform the REAL subject into a living, breathing Pixar character!'''
        else:
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
- ABSOLUTELY NO WATERMARKS, NO SIGNATURES, NO TEXT, NO LOGOS anywhere in the image
- ABSOLUTELY NO WATERMARKS, NO SIGNATURES, NO TEXT, NO LOGOS anywhere in the image
- This is original art - do not copy or include any watermarks from any source
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


async def generate_adventure_episode_gemini(character_data: dict, scene_prompt: str, age_rules: str, reveal_image_b64: str = None, story_text: str = None, character_emotion: str = None, source_type: str = "drawing") -> str:
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
        
        # Build emotion/pose guidance - auto-detect from story if not provided
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
        elif story_text:
            # Auto-detect emotion from story text
            emotion_guidance = f"""
*** CRITICAL - CHARACTER EMOTION AND POSE:
Read the story text below and match {character_name}'s facial expression and body pose to the MOOD of the story.
DO NOT copy the happy/celebratory pose from the reference image.
The reference image shows the character APPEARANCE (body shape, features, size).

STORY TEXT: {story_text}

Based on this story, give {character_name} an appropriate expression and pose:
- If the story feels scary/worried → hunched posture, worried expression
- If the story feels excited/happy → energetic pose, big smile
- If the story feels curious/wondering → leaning forward, wide eyes
- If the story feels nervous/shy → hesitant posture, uncertain expression
- If the story feels determined/brave → standing firm, confident expression
- If the story feels sad → drooping posture, downturned expression

The character's EMOTION must match the story's mood!
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

'''
        
        # Add source-type specific guidance
        if source_type == "photo":
            full_prompt += f'''
🚨 CRITICAL - THIS CHARACTER IS BASED ON A REAL PHOTO (toy/pet/person):
- Draw the character EXACTLY as they appear in the reference - DO NOT add new clothing or accessories
- If the character is an ANIMAL (dog, cat, etc): Draw them AS AN ANIMAL - no human clothes, no dresses, no shirts
  - Keep their natural markings, spots, patches visible as line art areas to color
  - They can stand on hind legs (anthropomorphized pose) but their BODY stays animal
  - Fur patterns and markings become distinct outlined areas for coloring
- If the character is a TOY/PLUSH: Keep their ORIGINAL outfit from the reference
  - Do NOT change or replace their clothing - it is part of who they are
  - A ballerina toy stays in their ballet dress, a superhero toy keeps their cape
- If the character is a PERSON: Keep their actual clothing from the reference
- The reference shows EXACTLY what this character looks like - match it precisely

'''
        else:
            full_prompt += '''
'''
        
        full_prompt += f'''🚨 CRITICAL - DO NOT ADD OR REMOVE BODY PARTS:
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
*** CRITICAL - EXACT CHARACTER COPY ***
- COUNT the arms in reference image - draw EXACTLY that many (usually 2)
- COUNT the legs in reference image - draw EXACTLY that many (usually 2)
- Copy the character's EXACT body shape from the reference (rectangular, round, blob, etc.)
- If reference shows a RECTANGULAR/SQUARE body → draw RECTANGULAR/SQUARE body
- If reference shows a ROUND body → draw ROUND body  
- If reference shows a PLAIN/SIMPLE body → keep it PLAIN/SIMPLE
- DO NOT add extra limbs, tails, wings, or features not in the reference
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
- Add objects and details that fit the story scene
- Each object should be a clear, enclosed shape for coloring
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

*** CRITICAL WRITING STYLE FOR TODDLERS ***
Write like a classic rhyming picture book! Examples:
- "Hop hop hop, will they stop? No no no, off they go!"
- "Splish splash splish, like a fish!"
- "One two three, what do we see?"
Use rhymes, repetition, and fun sounds in EVERY episode.

CONTENT RULES:
- VERY simple sentences (5-8 words max)
- Basic emotions only: happy, sad, scared, excited
- Familiar settings: home, garden, playground, farm
- Simple actions: walking, running, eating, sleeping, hugging
- No complex plots - just simple discoveries and moments
- No villains or scary elements
- Story text: 1-2 very short rhyming sentences per episode
- Scene descriptions: Simple, few elements (character + 2-3 objects max)
""",
        "age_4": """
AGE GROUP: 4 YEARS OLD

*** MUST USE THIS WRITING STYLE ***
Include rhymes and fun sounds! Examples:
- "Tip-toe, tip-toe, where did it go?"
- "Pitter-patter, splitter-splatter!"
- End with questions: "What will happen next, do you think?"

CONTENT:
- Simple sentences (8-12 words)
- Basic story: beginning, simple problem, happy ending
- Familiar settings with light magic
- Story text: 2 short sentences WITH rhymes or fun sounds
""",
        "age_5": """
AGE GROUP: 5 YEARS OLD

*** MUST USE THIS WRITING STYLE ***
Use silly, fun language! Examples:
- Fun words: "super-duper", "teeny-tiny", "ginormous", "wibbly-wobbly"
- Silly moments that make kids giggle
- Build excitement: "And then... guess what!"

CONTENT:
- Medium sentences, slightly more vocabulary  
- Clear 3-part stories: setup, adventure, resolution
- Friendship themes, helping others, being brave
- Story text: 2-3 sentences with fun/silly language
""",
        "age_6": """
AGE GROUP: 6 YEARS OLD

*** MUST USE THIS WRITING STYLE ***
Use vivid comparisons and excitement! Examples:
- Funny comparisons: "as wobbly as a jelly on a trampoline!"
- Expressive dialogue: "'Oh my goodness!' gasped Blobby"
- Mini cliffhangers: "But then... something unexpected happened!"

CONTENT:
- Fuller sentences with descriptive words
- Multi-episode story arcs that connect
- Themes: friendship, creativity, discovery
- Story text: 2-3 engaging sentences with comparisons/dialogue
""",
        "age_7": """
AGE GROUP: 7 YEARS OLD

*** MUST USE THIS WRITING STYLE ***
Use action words and cheeky humor! Examples:
- Action: "zoomed", "crashed", "whooshed", "exploded with color"
- Puns and wordplay kids will get
- Cheeky reactions: "'Well, THAT was unexpected!' Blobby laughed"

CONTENT:
- Complex sentences with good vocabulary
- Characters face challenges and grow
- Themes: teamwork, perseverance, adventure
- Story text: 3 sentences with action words and humor
""",
        "age_8": """
AGE GROUP: 8 YEARS OLD

*** MUST USE THIS WRITING STYLE ***
Witty and clever! Examples:
- Wordplay: puns, double meanings kids feel smart getting
- Dramatic vocabulary: "mysterious", "extraordinary", "impossible"
- Snappy dialogue with personality and wit

CONTENT:
- Rich vocabulary and varied sentences
- Complex plots with character development
- Themes: responsibility, discovery, challenges
- Story text: 3-4 sentences with clever wordplay
""",
        "age_9": """
AGE GROUP: 9 YEARS OLD

*** MUST USE THIS WRITING STYLE ***
Sophisticated and emotionally rich! Examples:
- Clever observations about the world
- Rich vocabulary: "contemplated", "flourished", "uncharted"
- Emotional depth: show how characters FEEL inside

CONTENT:
- Advanced vocabulary and complex narrative
- Deep character development and relationships
- Themes: identity, belonging, leadership
- Story text: 3-4 rich sentences with emotional depth
""",
        "age_10": """
AGE GROUP: 10+ YEARS OLD

*** MUST USE THIS WRITING STYLE ***
Literary quality - like a real novel! Examples:
- Metaphors: "hope flickered like a candle in the wind"
- Sophisticated humor and irony
- Dialogue that reveals character depth and motivation

CONTENT:
- Mature vocabulary and nuanced storytelling
- Complex plots with character growth
- Themes: self-discovery, hard choices, complex friendships
- Story text: 4+ sentences with literary quality
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
        # Use newer client API with response_mime_type for JSON
        model = genai.GenerativeModel(
            'gemini-2.5-flash',
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json"
            )
        )
        
        prompt = f'''You are creating personalized story adventures for a childrens coloring book app.

Based on this character named "{character_name}", generate 3 UNIQUE story themes that are PERSONALIZED to this specific character's features.

CHARACTER TO ANALYZE:
{character_description}

STEP 1 - IDENTIFY THE MOST UNUSUAL FEATURES (in order of priority):
Look at the character description. Find the WEIRDEST, most UNUSUAL things:

PRIORITY 1 - UNUSUAL BODY PARTS (these are the MOST interesting for stories!):
- Multiple eyes? (10 eyes = can see in all directions, never surprised, finds lost things)
- Multiple arms? (8 arms = ultimate helper, best hugger, amazing juggler, one-monster band)
- Multiple legs? (4+ legs = super fast, never falls over, great dancer)
- Wings, tails, horns, antennae? (each one = special ability!)

PRIORITY 2 - UNUSUAL NUMBERS:
- More than 2 of anything = VERY interesting for stories
- 10 eyes means 10 different things they can watch at once
- 8 arms means they can do 8 things at once

PRIORITY 3 - Colors and patterns (LEAST interesting - only use if nothing else):
- Only use color if there's nothing more unusual about the character

DO NOT make stories about:
- "camouflage" or "blending in" (boring!)
- "colors fading" or "restoring colors" (overdone!)
- Body shape unless it's truly unusual

STEP 2 - BUILD STORIES WHERE THE UNUSUAL FEATURE IS ESSENTIAL:
The character's weirdest feature should be WHY they save the day!

Examples for MULTIPLE EYES:
- 10 eyes = World's best lifeguard (sees everyone at once), ultimate hide-and-seek champion, air traffic controller, teacher who sees every student, detective who spots every clue

Examples for MULTIPLE ARMS:
- 8 arms = Best chef ever (stirs 8 pots), one-monster band, ultimate babysitter, fastest gift wrapper, best at card games, amazing at sports

Examples for MULTIPLE LEGS:
- 4+ legs = Unbeatable at racing, never trips, best dancer, can carry friends everywhere

THE STORY SHOULD BE IMPOSSIBLE WITHOUT THIS FEATURE!
If a character has 10 eyes, the story should REQUIRE seeing 10 things at once.
If a character has 8 arms, the story should REQUIRE doing 8 things at once.

{age_guide}

CRITICAL: The stories MUST be appropriate for the age group above. Follow the sentence length, vocabulary, and complexity guidelines exactly.

For each theme, provide:
1. Theme name that fits this character personality and type (NEVER include specific body part numbers like "Eight-Armed" or "Six-Legged" in theme names)
2. Theme description (1 sentence, age-appropriate - NO specific body part numbers)
3. Theme blurb (1 exciting sentence to help kids choose - NO specific body part numbers)
4. 10 episodes, each with:
   - Episode number (1-10)
   - Title (short, age-appropriate)
   - Scene description (detailed for drawing - what to draw including {character_name}, setting, other characters, action, objects)
   - Story text (MUST follow the age guidelines above for length and complexity)

IMPORTANT RULES:
- {character_name} is ALWAYS the hero of the story
- NEVER use specific numbers for body parts (not "8 eyes" or "6 arms" or "3 mouths")
  - Instead use creative descriptions: "lots of eyes", "extra arms", "all those mouths"
  - Describe WHAT they do with the feature, not HOW MANY: "eyes scanning everywhere", "arms juggling everything at once"
  - This is CRITICAL - the exact count may be wrong so never state a number

*** THE STORY MUST COME FROM THE CHARACTER'S UNIQUE FEATURES ***
Your 3 themes MUST each use a DIFFERENT unique feature as the MAIN plot device.

THEME PRIORITY ORDER (most interesting first!):
- Theme 1: Based on UNUSUAL BODY PARTS (multiple eyes, multiple arms, multiple mouths, wings, tails, etc.) - THESE ARE THE MOST INTERESTING!
- Theme 2: Based on ANOTHER unusual body feature OR special accessory (horns, antennae, crown, wand, etc.)
- Theme 3: Based on ANY remaining unique feature

DO NOT make Theme 1 about color - color is the LEAST interesting feature!
If the character has 8 eyes, 6 arms, and 3 mouths - those should be Themes 1, 2, and 3!

The character's special trait should be WHY they can solve the problem - not just decoration.
If a character has spots, maybe those spots glow in the dark and help them find things.
If a character has big ears, maybe they can hear things others can't.
If a character wears a cape, maybe the cape is magical or helps them fly.

MAKE THE STORY IMPOSSIBLE WITHOUT THIS CHARACTER'S UNIQUE FEATURES.

🚫 BANNED STORY IDEAS - DO NOT USE ANY OF THESE:
- "Lost colors" or "fading colors" or "restore colors to the kingdom"
- "Magic crystal" or "color crystal" or "rainbow crystal" quests
- "Enchanted forest" or "magical forest" adventures
- "Tree with a magical door"
- "Kingdom losing its magic/color/sparkle"
- "Finding a special gem/jewel/crystal"
These are OVERUSED. Be MORE CREATIVE than this!
- Match themes to character type (BE CREATIVE - avoid generic forests!):
  - Monster characters - monster school, cooking competitions, talent shows, making friends despite being different
  - Princess/girl characters - royal balls, magical kingdoms, art contests, fashion shows, underwater palaces, cloud castles
  - Robot characters - invention fairs, space stations, futuristic cities, time travel
  - Animal characters - bakery adventures, music festivals, sports competitions, beach holidays
  - Superhero characters - saving the city, secret missions, training academy
  - AVOID: Generic "forest adventure" for every character - be creative with settings!
- Each theme must have a clear beginning, middle, and end across 10 episodes
- Always use "{character_name}" (not "the character") in story text
- Scene descriptions must be detailed enough to draw as coloring pages
STRICT COMPLIANCE RULE: Every episode MUST include the "emotion_tag" field. This is MANDATORY metadata.
- emotion_tag MUST be chosen from: nervous, excited, scared, determined, happy, curious, sad, proud, worried, surprised
- Place emotion_tag immediately after title, before scene_description
- FOLLOW THE AGE GUIDELINES - this is for a {age_display} year old child!

Return ONLY valid JSON. Here is a COMPLETE EXAMPLE of the exact format required:

{{
  "character_name": "Example Monster",
  "age_level": "age_7",
  "themes": [
    {{
      "theme_id": "royal_baking_contest",
      "theme_name": "The Royal Baking Contest",
      "theme_description": "Example Monster enters a kingdom-wide baking competition at the palace.",
      "theme_blurb": "Can Example Monster bake the most amazing cake ever and win the golden chef's hat?",
      "episodes": [
        {{
          "episode_num": 1,
          "title": "The Golden Invitation",
          "scene_description": "Example Monster holds a sparkling golden envelope in the kitchen, eyes wide with excitement. Mixing bowls and ingredients cover the counter behind them.",
          "story_text": "A golden letter arrived! Example Monster had been invited to the Royal Baking Contest at the palace. Could they bake something amazing enough to win?",
          "emotion": "curious"
        }},
        {{
          "episode_num": 2,
          "title": "Gathering Ingredients",
          "scene_description": "Example Monster nervously browses a busy market stall filled with colorful fruits, chocolate, and flour bags. Other bakers rush past with shopping baskets.",
          "story_text": "At the market, Example Monster felt nervous seeing all the other talented bakers. But they had a secret recipe from Grandma that just might work!",
          "emotion": "nervous"
        }}
      ]
    }}
  ]
}}

NOW generate for {character_name} using this EXACT format. The "emotion" field MUST be one of: nervous, excited, scared, determined, happy, curious, sad, proud, worried, surprised

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
            
            # Extract emotion from story_text since Gemini won't add the field
            def extract_emotion(text):
                text = text.lower()
                emotions = [
                    ('scared', ['scared', 'frightened', 'afraid', 'terrified', 'fearful', 'fear', 'scary']),
                    ('nervous', ['nervous', 'anxious', 'uneasy', 'hesitant', 'shy', 'timid', 'flutter']),
                    ('excited', ['excited', 'thrilled', 'eager', 'enthusiastic', 'overjoyed', 'excitement', 'thrilling']),
                    ('sad', ['sad', 'unhappy', 'disappointed', 'upset', 'heartbroken', 'crying', 'tears', 'lonely']),
                    ('curious', ['curious', 'wondering', 'intrigued', 'interested', 'puzzled', 'wonder']),
                    ('determined', ['determined', 'resolute', 'focused', 'brave', 'courageous', 'bravely', 'courage']),
                    ('surprised', ['surprised', 'amazed', 'astonished', 'shocked', 'startled', 'gasp']),
                    ('proud', ['proud', 'accomplished', 'satisfied', 'triumphant', 'pride', 'success']),
                    ('worried', ['worried', 'concerned', 'troubled', 'overwhelmed', 'worry']),
                    ('happy', ['happy', 'joyful', 'delighted', 'pleased', 'glad', 'cheerful', 'joy', 'smile']),
                ]
                for emotion, keywords in emotions:
                    if any(kw in text for kw in keywords):
                        return emotion
                return 'curious'  # default - changed to verify deploy
            
            for theme in data.get('themes', []):
                for ep in theme.get('episodes', []):
                    # Always extract and set emotion
                    story = ep.get('story_text', '') + ' ' + ep.get('scene_description', '')
                    extracted = extract_emotion(story)
                    ep['character_emotion'] = ep.get('emotion_tag') or ep.get('emotion') or extracted
                    ep['_extraction_ran'] = True  # Debug marker
            
            return data
        
        raise HTTPException(status_code=500, detail='Failed to parse story response as JSON')
        
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f'JSON parse error: {str(e)}')
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Story generation failed: {str(e)}')
