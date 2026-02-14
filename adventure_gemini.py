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
        
        # Extract image from response (with retry)
        for attempt in range(3):
            if attempt > 0:
                import asyncio
                print(f"[REVEAL] Retry attempt {attempt + 1}/3...")
                response = client.models.generate_content(
                    model='gemini-2.5-flash-image',
                    contents=contents,
                    config=types.GenerateContentConfig(
                        response_modalities=['IMAGE', 'TEXT'],
                        image_config=types.ImageConfig(
                            aspect_ratio='3:4',
                        )
                    )
                )
            
            if (response.candidates 
                and response.candidates[0].content 
                and response.candidates[0].content.parts):
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'inline_data') and part.inline_data:
                        return base64.b64encode(part.inline_data.data).decode('utf-8')
            
            print(f"[REVEAL] Attempt {attempt + 1} returned no image")
        
        raise HTTPException(status_code=500, detail='No image generated after 3 attempts')
        
    except ImportError as e:
        raise HTTPException(status_code=500, detail=f'google-genai package not installed: {str(e)}')
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Reveal generation failed: {str(e)}')


async def generate_adventure_episode_gemini(character_data: dict, scene_prompt: str, age_rules: str, reveal_image_b64: str = None, story_text: str = None, character_emotion: str = None, source_type: str = "drawing", previous_page_b64: str = None) -> str:
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
        
        # Build continuity guidance if previous page provided
        continuity_guidance = ""
        if previous_page_b64:
            continuity_guidance = f"""
*** PREVIOUS PAGE REFERENCE ***
The previous storybook page is attached for LIGHT reference only.
- Use it to keep the CHARACTER looking consistent (same body shape, features)
- Do NOT copy the scene layout, composition, or background from it
- Generate this page FRESH based on the scene description below
- Each page should look like a COMPLETELY DIFFERENT illustration
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

{continuity_guidance}

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
        
        # Build content with reveal image and optional previous page
        contents = [full_prompt]
        
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
            
            contents.append(types.Part.from_bytes(
                data=gray_bytes,
                mime_type="image/png"
            ))
        
        if previous_page_b64:
            # Add previous page for continuity reference
            prev_bytes = base64.b64decode(previous_page_b64)
            contents.append(types.Part.from_bytes(
                data=prev_bytes,
                mime_type="image/png"
            ))
        
        # If no images, just use prompt string
        if len(contents) == 1:
            contents = full_prompt
        
        # Generate with portrait aspect ratio - STANDARD pricing tier
        # 3:4 at standard resolution = ~864x1152 = 995,328 pixels (under 1MP)
        # This avoids 2K/4K pricing tiers
        response = client.models.generate_content(
            model='gemini-2.5-flash-image',
            contents=contents,
            config=types.GenerateContentConfig(
                response_modalities=['IMAGE', 'TEXT'],
                temperature=0.4,  # Moderate temp: enough variance for different compositions, not so high it drifts
                image_config=types.ImageConfig(
                    aspect_ratio='3:4'  # Portrait for A4-style, standard resolution
                )
            )
        )
        
        # Extract image from response (with retry)
        for attempt in range(3):
            if attempt > 0:
                import asyncio
                print(f"[REVEAL] Retry attempt {attempt + 1}/3...")
                response = client.models.generate_content(
                    model='gemini-2.5-flash-image',
                    contents=contents,
                    config=types.GenerateContentConfig(
                        response_modalities=['IMAGE', 'TEXT'],
                        image_config=types.ImageConfig(
                            aspect_ratio='3:4',
                        )
                    )
                )
            
            if (response.candidates 
                and response.candidates[0].content 
                and response.candidates[0].content.parts):
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'inline_data') and part.inline_data:
                        return base64.b64encode(part.inline_data.data).decode('utf-8')
            
            print(f"[REVEAL] Attempt {attempt + 1} returned no image")
        
        raise HTTPException(status_code=500, detail='No image generated after 3 attempts')
        
    except ImportError as e:
        raise HTTPException(status_code=500, detail=f'google-genai package not installed: {str(e)}')
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Episode generation failed: {str(e)}')


async def generate_personalized_stories(character_name: str, character_description: str, age_level: str = "age_6") -> dict:
    """
    Generate 3 personalized story themes based on character type and child age.
    
    Each theme has 5 episodes that tell a complete story featuring the character.
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
- Familiar BUT exciting settings: a wobbly treehouse, a toy shop after dark, a kitchen where food comes alive, a bath-time ocean adventure, a blanket fort kingdom, a busy airport, a zoo at night
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
- Fun words: "super-duper", "teeny-tiny", "ginormous", "splashy-splashy", "rumbly-tumbly"
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
- Funny comparisons: "as bouncy as a kangaroo on a trampoline!"
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

STEP 2 - PICK AND ADAPT A SCENARIO

Below is a pool of 180 story scenarios. For each of your 3 themes:
1. Pick a scenario that the character's unique feature would be PERFECT for
2. ADAPT it — don't copy it word-for-word. Change details, combine ideas, make it your own
3. The character's feature should be essential to the story but in a SURPRISING way

The scenario is the STARTING POINT. The character's feature determines HOW they deal with it.
Example: "A popcorn machine at the cinema won't stop" + a character with a big mouth = the character tries to eat all the popcorn but can't keep up, gets buried in it, then discovers they can use their mouth to blow the popcorn into a giant popcorn sculpture that wins a prize instead.

Each theme MUST use a DIFFERENT unique feature as the main plot device.
NEVER include specific body part numbers in theme names.

*** SCENARIO POOL ***

FOOD CHAOS:
1. A popcorn machine at the cinema won't stop and popcorn is flooding the whole building
2. A birthday cake has come alive and is running through the town leaving icing footprints everywhere
3. Someone put magic beans in the school dinner and now vegetables are growing through the roof
4. The world's longest spaghetti noodle has tangled around the entire city like a giant web
5. A chocolate fountain at the fair has gone turbo and is spraying chocolate over everything
6. A bubble gum machine exploded and giant sticky bubbles are trapping people inside
7. The ice cream van's freezer broke and a tidal wave of melting ice cream is sliding downhill toward the school
8. A baker's bread dough won't stop rising and is pushing the roof off the bakery
9. Someone mixed up the recipes — the pet shop is full of cake and the bakery is full of hamsters
10. A soup volcano erupted in the school canteen and tomato soup is flowing down the corridors
11. The sweet shop's pick-and-mix machine is firing sweets like cannonballs across the high street
12. A jam factory pipe burst and a river of strawberry jam is heading for the swimming pool

TRANSPORT GONE WRONG:
13. A double decker bus has started flying and the passengers don't know how to land it
14. A train has lost its driver and passengers must stop it before the end of the line
15. The world's biggest shopping trolley is rolling downhill toward the lake with no brakes
16. A hot air balloon got tangled in the town clock tower and passengers are stuck
17. A submarine's steering is broken and it's heading for an underwater volcano
18. The school bus accidentally drove into a car wash and can't find the way out
19. A spaceship's sat-nav is broken and keeps landing in wrong places — a farm, a wedding, a swimming pool
20. The roller coaster won't stop and riders have been going round for hours
21. A pirate ship appeared in the park boating lake and nobody knows where it came from
22. The new robot taxi is picking people up and dropping them at completely wrong places

ANIMAL MAYHEM:
23. All zoo animals swapped enclosures — penguin in the lion cage, lion in the aquarium
24. A magician's rabbit won't go back in the hat and is multiplying — 300 rabbits in the shopping centre
25. A parrot learned everyone's secrets and is shouting them at the school assembly
26. The dentist's goldfish grew to the size of a car overnight
27. Squirrels moved into the school computer room and are hoarding all the keyboards
28. The class hamster escaped and is now running the school from the headteacher's chair
29. A whale fell asleep across the harbour and no boats can get in or out
30. A cat stole the Mayor's golden chain and is sitting on top of the church spire
31. All dogs in town started walking backwards at the same time — nobody knows why
32. An octopus at the aquarium keeps stealing visitors' phones and taking selfies

WEATHER WEIRDNESS:
33. It's raining something different on every street — custard, bouncy balls, socks
34. A giant snowball rolling through town getting bigger, collecting everything in its path
35. Wind blew everyone's laundry and mixed it up — the Mayor is wearing a nappy
36. A rainbow fell out of the sky and is blocking the motorway
37. Clouds came down to ground level and nobody can see — chaos everywhere
38. A leaf tornado trapped all the playground equipment inside it
39. The sun went behind a cloud and forgot to come back — expedition to find it
40. A thunderstorm is only happening inside the library and nobody knows why

BUILDING DISASTERS:
41. New playground built upside down — swings underground, sandpit on the roof
42. A skyscraper is slowly tilting and everyone inside is sliding to one side
43. Bouncy castle inflated too much — now the size of a real castle, floating above town
44. School maze built too well — all the teachers are lost inside
45. A crane picked up the swimming pool with people still in it
46. The new bridge is made of chocolate and it's a hot day
47. A treehouse growing by itself, adding rooms faster than anyone can explore
48. Clock tower gears jammed — some people in fast-forward, others in slow motion

CELEBRATION DISASTERS:
49. All the festival fireworks went off at once inside the storage shed
50. Magician's show went wrong — half the audience invisible, half upside down
51. School nativity donkey is actually real and eating the set
52. Wedding cake delivered to fire station — they used it for training
53. Giant Christmas tree fell over blocking every road in town
54. Carnival floats moving on their own with no drivers
55. A pinata won't break, started moving, and is now chasing the children

SCIENCE GONE WRONG:
56. Shrinking ray hit the teacher — class now has a pencil-sized teacher
57. Growing potion spilled on the goldfish — it's now the size of the school hall
58. Time machine sent packed lunches to the dinosaur age — T-Rex eating someone's sandwich
59. Science fair volcano actually erupted — school surrounded by bubbling goo
60. Invisibility experiment — the whole school building disappeared but everyone's still inside
61. Duplicating machine made 50 copies of the headteacher giving different instructions
62. Gravity experiment went wrong — everything in the gym floating, including PE teacher
63. Science fair robot decided it wants to be a student and won't leave class

TOY/GAME CHAOS:
64. Toy shop toys came alive at midnight for a party — shop opens in one hour
65. Board game became real-sized — dice the size of cars, whole town playing
66. Teddy bear wish came true — tiny teddy is now 10 feet tall, still wants cuddles
67. Arcade machines playing themselves, high scores going crazy
68. Jigsaw puzzle assembling itself into a portal — things coming through from the picture
69. LEGO built itself into a castle overnight — a LEGO knight guards the door
70. Remote control cars escaped the toy shop and are racing through town

JOBS GONE WRONG:
71. Firefighter's hose spraying silly string instead of water during a real emergency
72. Postman's letters flying out and delivering themselves to wrong houses
73. Dentist's chair started flying around the surgery with patient still in it
74. Hairdresser's magic shampoo makes hair grow super fast — out the door in minutes
75. Painter used magic paint — everything painted is coming alive
76. Librarian's robot organising books by colour not title and refuses to stop

SPACE:
77. Alien spaceship crashed into school roof — needs fixing before home time or alien's mum will worry
78. Aliens visiting Earth think vinegar is perfume and chips are building blocks
79. Space station gravity keeps flipping — astronauts bouncing between ceiling and floor
80. Giant space snowball heading to Earth — unexpected snow day incoming

UNDERWATER:
81. Ocean plug came loose — all water draining out, fish NOT happy
82. Underwater post office lost deliveries — shark got a seahorse's birthday card
83. Sunken treasure chest opened — gold coins floating up causing beach chaos
84. Coral reef talent show — three grumpy crab judges giving everyone zero

ADVENTURE & EXPLORATION:
85. A mysterious door appeared at the back of the school gym that wasn't there yesterday
86. A treasure map blew in through the classroom window showing a route nobody recognises
87. The museum's oldest painting has a tiny staircase in the corner nobody noticed before
88. A message in a bottle with coordinates pointing underneath the town fountain
89. An old lift has a button for a floor that doesn't exist — Floor 13 and a half
90. New kid at school says they're from a country nobody can find on any map
91. Tunnels underneath the town being mapped for the first time — something's making noises down there
92. Lighthouse keeper missing — left behind strange inventions and half-finished notes
93. Hot air balloon landed in the playground with nobody in it — just a note saying HELP
94. A door in the big oak tree that only appears when it rains
95. Old boat washed up covered in barnacles with a logbook in an unknown language
96. Town hall attic locked for 100 years — today they found the key

FRIENDSHIP & KINDNESS:
97. New kid at school doesn't speak the same language and looks lonely at lunch
98. Two best friends both want the same part in the school play — it's tearing them apart
99. Grumpy neighbour who shouts at everyone secretly been feeding all the stray cats
100. Smallest kid always picked last for teams but has an amazing hidden talent
101. A kid's imaginary friend is sad because the kid is growing up and doesn't play pretend anymore
102. School bully caught crying behind the bins — having a really hard time at home
103. Two rival bakers must work together when a power cut hits both shops
104. Shy kid finds a lost dog and has to knock on strangers' doors to find the owner
105. Elderly neighbour can't get to the shops anymore and nobody noticed except the character
106. Class goldfish is poorly — whole class works together on the best fish hospital ever
107. Kid who just moved to new town pretending everything's fine but secretly misses old friends
108. Grandparent forgetting things more and more — grandchild finds creative ways to help them remember
109. Loneliest tree in the park has no birds — every other tree does — someone investigates why
110. Child finds names carved on a park bench from decades ago and tries to find the people

BEING DIFFERENT & BELONGING:
111. Only kid who can't swim has to go to the pool party everyone else is excited about
112. A creature that looks completely different from everyone turns up at the market — nobody will talk to them
113. Kid who uses a wheelchair discovers a part of the playground only they can reach
114. Weirdest house on the street about to be knocked down but it's actually the most special one
115. Kid told they're "too loud" everywhere until they find a place where loud is exactly what's needed
116. One fish swimming opposite to all others discovers something amazing the rest missed
117. Kid who draws outside the lines enters a competition where that's the whole point
118. Wonky homemade cake enters a competition full of perfect professional cakes
119. Bird that can't fly lives among birds that can — until winter when flying isn't what's needed
120. Scruffiest dog at the rescue centre keeps getting overlooked while cute puppies get chosen

FUNNY & ABSURD:
121. Birthday wish made everything opposite — up is down, cats bark, teachers are students
122. Copy machine left on overnight — 1000 newsletters flying through town
123. Town statue came alive but can only move when nobody's looking
124. Hiccup going around town — each person hiccups something different: bubbles, confetti, glitter
125. Kid's homework excuse came true — "a dinosaur ate my homework" and now there's a dinosaur
126. Everything the character says comes true literally — "I could eat a horse" and a horse appears on a plate
127. School camera takes photos of what people are THINKING not what they look like
128. Restaurant critic coming today but the chef lost their sense of taste — need a secret taster
129. Town crier got hiccups — all announcements coming out garbled and wrong
130. Picture day camera adds silly hats and moustaches to everyone and won't stop
131. Kid's shadow detached and is doing its own thing — going to classes, eating with other kids
132. Voice-activated town systems mishearing everything — "lights on" turns on sprinklers
133. Smart board learned to talk and won't stop giving opinions during lessons
134. Fancy dinner party where everything goes wrong — cold soup, collapsing chairs, exploding dessert

OVERCOMING FEARS:
135. Kid terrified of the dark has to cross the school field at night to get something important
136. Child scared of water — their best friend's puppy just fell in the pond
137. Kid who hates thunder is at a sleepover when the biggest storm hits
138. Child afraid of heights — only way to rescue the stuck kite is to climb
139. Shy kid has exactly the information everyone needs but must say it in front of the whole school
140. Kid scared of dogs has to walk past one daily — one day the dog needs help
141. Kid who hates getting messy — the only fix involves getting VERY messy
142. Child who hates loud noises must cross the noisiest place in town for an important delivery

HELPING & COMMUNITY:
143. Town's only bridge broken — everyone stuck on one side, character must connect them
144. Oldest lady's garden destroyed by storm — it was the one thing that made her happy
145. Homeless kitten hiding under the school, too scared to come out, getting cold tonight
146. Local park becoming a car park unless someone proves it's special enough to keep
147. School dinner lady secretly using her own money so no kid goes hungry
148. Power out on coldest night — neighbours don't even know each other
149. Elderly toymaker's hands shake too much to make toys but Christmas is coming
150. Town's ice cream van broke down on the hottest day — ice cream melting fast

IMAGINATION & PLAY:
151. Cardboard box becomes a real spaceship when nobody's looking — must get back before bedtime
152. Drawings in a sketchbook climbing off the pages when the kid sleeps
153. Blanket fort became an actual kingdom with tiny citizens who need help
154. Bath time rubber ducks turned into real ducks — bath is now an ocean
155. Kid's imaginary world leaking into reality — imaginary dragon is in the kitchen
156. Toy dinosaur came alive in the museum — get it back to the exhibit before the guard notices
157. Chalk playground drawings become real when it rains — someone drew a lion
158. Bedtime story telling itself differently — characters going off-script
159. Snow globe on the shelf snowing for real — tiny town inside needs help with their blizzard
160. Kid's LEGO city comes alive at night — they shrink down but something's wrong in LEGO town

COMPETITION & GAMES:
161. Sports day chaos — egg and spoon egg is an ostrich egg, sack race sacks have holes
162. School bake-off where the oven keeps changing temperature on its own
163. Dance competition where the floor tiles light up randomly and you must follow them
164. Paper boat race on the river but this year there are real tiny rapids
165. Hide and seek championship where hiding spots keep moving — wardrobe walks to new room
166. Spelling bee where correctly spelled words come alive and walk around the stage
167. School science fair — every project activates at once, hall becomes total chaos
168. Sandcastle competition but the tide is coming in fast
169. Kite competition on the windiest day ever — kites pulling owners into the sky
170. School team playing against robots that keep glitching in funny ways

GENTLE & COSY:
171. Kid finds a tiny injured bird and nurses it back to health, not knowing if it will fly again
172. First snow of winter — whole town building the most spectacular snowman ever
173. Rainy afternoon baking with grandparent who shares stories from when they were young
174. Kid growing a sunflower for competition but starts caring more about the flower than winning
175. Moving day — saying goodbye to old room, old street, old climbing tree
176. Kid saving up pocket money for weeks to buy something special for someone they love
177. Last day of summer holidays — friends plan the perfect final adventure before school starts
178. Box of old letters in the attic tells the story of how grandparents met
179. Night before starting new school — kid can't sleep, imagining everything that might happen
180. Child stays up late to see the stars for the first time, wrapped in a blanket with their parent

*** HOW TO USE THESE SCENARIOS ***

1. Read the character's features from STEP 1
2. Scan ALL 180 scenarios — pick the 3 where the character's feature would be MOST fun, surprising, or useful
3. Each theme must use a DIFFERENT feature
4. ADAPT the scenario — change names, settings, details. The scenario is a starting point not a script
5. The character's feature should help in a SURPRISING way, not the obvious way

{age_guide}

CRITICAL: Follow the age guidelines above exactly for sentence length, vocabulary, and complexity.

*** FORMAT ***

For each theme provide:
1. Theme name (fun, age-appropriate)
2. Theme description (1 sentence)
3. Theme blurb (ONE short punchy sentence, MAX 15 words. Describe the chaos/situation only. NEVER mention the character's body parts in the blurb)
4. 5 episodes with: episode number (1-5), title, scene_description, story_text, emotion

Scene descriptions MUST include: character's pose/action, specific setting details, other characters present, 3-4 background objects to colour. Mix close-ups, wide shots, and action scenes across the 5 episodes.

Story text: Follow the age guidelines for length. Final episode should be short and punchy.

Emotion must be one of: nervous, excited, scared, determined, happy, curious, sad, proud, worried, surprised

*** 5 NON-NEGOTIABLE RULES ***

1. CHARACTERS: At least 2 named supporting characters with funny personalities who appear throughout, not just once.
2. SETBACK ON EPISODE 3: Character tries and FAILS or makes things worse. Makes the win feel earned.
3. DIALOGUE: At least 3 of 5 episodes need characters talking in speech marks.
4. ENDING: Episode 5 resolves the specific problem from episode 1. No generic happy endings.
5. NEVER copy a scenario word-for-word. Adapt it, remix it, make it feel fresh and unique to this character.

Return ONLY valid JSON. Here is a COMPLETE EXAMPLE of the exact format required:

{{
  "character_name": "Example Monster",
  "age_level": "age_5",
  "themes": [
    {{
      "theme_id": "runaway_robot_chef",
      "theme_name": "The Runaway Robot Chef",
      "theme_description": "When a pizza restaurant's robot chef goes haywire, Example Monster must chase it through the city before it buries the Mayor's birthday party in cheese.",
      "theme_blurb": "A robot chef has gone BONKERS and is covering the whole city in pizza! Can Example Monster stop the cheesy chaos before the Mayor's party is ruined?",
      "episodes": [
        {{
          "episode_num": 1,
          "title": "Too Much Cheese!",
          "scene_description": "Inside a busy pizza restaurant kitchen. A robot chef with spinning arms sprays melted cheese everywhere. The restaurant owner (a tiny hamster in a chef hat) stands on a stool looking panicked. Pizza dough flies through the air. Pots and pans scattered on the floor.",
          "story_text": "Chef Whizz the robot had gone completely bonkers! Melted cheese was flying EVERYWHERE. 'Help!' squeaked Mr. Pepperoni the hamster. 'He won't stop cooking!'",
          "emotion": "surprised"
        }},
        {{
          "episode_num": 2,
          "title": "The Great Cheese Chase",
          "scene_description": "WIDE SHOT: Example Monster chases the runaway robot down a city street. The robot leaves a trail of tomato sauce. A postman duck slips on sauce. A grumpy cat on a balcony gets splattered with cheese. Buildings and shop fronts line the street.",
          "story_text": "Chef Whizz zoomed out and down the street! 'After him!' yelled Mr. Pepperoni, riding on Example Monster's head. The robot was heading straight for the Mayor's big birthday party!",
          "emotion": "excited"
        }},
        {{
          "episode_num": 3,
          "title": "Slippery Trouble",
          "scene_description": "CLOSE-UP: Example Monster has slipped on a huge puddle of tomato sauce in the town square. Chef Whizz escapes in the background. Mr. Pepperoni has landed in a fountain. Mozzarella stretches across the square like silly string.",
          "story_text": "Example Monster tried to grab Chef Whizz but — SPLAT! Slipped right on the sauce. Mr. Pepperoni landed in the fountain. 'He's getting away!' spluttered the soggy little hamster.",
          "emotion": "worried"
        }},
        {{
          "episode_num": 4,
          "title": "The Big Catch",
          "scene_description": "ACTION SHOT: Example Monster uses their special feature creatively to catch Chef Whizz outside the town hall. The Mayor (a tall flamingo in a party hat) peeks from the doorway. Streamers and balloons everywhere. Mr. Pepperoni cheers from Example Monster's shoulder.",
          "story_text": "Example Monster had a super-duper idea! Using their special feature, they caught Chef Whizz just in time. 'Whizz just wanted to make the biggest pizza ever,' beeped the little robot sadly.",
          "emotion": "determined"
        }},
        {{
          "episode_num": 5,
          "title": "The Biggest Pizza Party",
          "scene_description": "The town square party. Everyone eating a GIANT pizza that Chef Whizz made properly. Example Monster, Mr. Pepperoni, the Mayor flamingo, and Chef Whizz all together. Bunting, balloons, and fairy lights everywhere.",
          "story_text": "'What if Whizz makes the birthday pizza?' said Example Monster. The robot beeped happily and made the most ginormous, perfect pizza EVER. 'Best party ever!' laughed the Mayor.",
          "emotion": "happy"
        }}
      ]
    }}
  ]
}}

NOW generate for {character_name} using this EXACT format. The "emotion" field MUST be one of: nervous, excited, scared, determined, happy, curious, sad, proud, worried, surprised

Generate 3 complete themes with all 5 episodes each. Return ONLY the JSON, no other text.'''
        
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
