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

STEP 2 - BUILD STORIES WHERE THE UNUSUAL FEATURE IS ESSENTIAL:
The character's weirdest feature should be WHY they save the day!

*** CREATIVE FEATURE USAGE - AVOID THE OBVIOUS! ***
For EVERY feature, think beyond the most obvious use. Gemini tends to repeat the same ideas - FIGHT THIS!

MOUTHS/TEETH: Do NOT default to singing/humming/making sounds. Think bigger:
- Big mouth = can blow enormous bubbles to float friends across a river
- Big mouth = can gulp up flood water to save a village
- Big mouth = can whisper secrets into the deepest caves to wake sleeping creatures
- Teeth = can chew through tangled vines trapping a friend
- Teeth = can carve beautiful patterns into ice/wood
- BANNED for mouths: singing to make quiet places loud, humming magical tunes, making special sounds

EYES: Do NOT default to "seeing special/hidden/magical things". Think bigger:
- Many eyes = can cry enough tears to fill a dry well and save a garden
- Many eyes = can wink in patterns to send secret messages across a battlefield
- Many eyes = can each look at a different friend during a crisis so nobody feels alone
- BANNED for eyes: seeing hidden magic, spotting invisible things, finding sparkly stuff

ARMS: Do NOT default to "juggling" or "hugging everyone". Think bigger:
- Many arms = can build a dam in seconds to stop a flood
- Many arms = can hold up a collapsing roof while friends escape
- Many arms = can paint a mural so fast it comes to life
- Many arms = can knit a net big enough to catch a falling star

LEGS: Do NOT default to "running fast". Think bigger:
- Many legs = can stomp a rhythm that makes seeds grow instantly
- Many legs = can form a bridge for tiny creatures to cross
- Many legs = each leg dances differently, confusing a scary predator

THE STORY SHOULD BE IMPOSSIBLE WITHOUT THIS FEATURE!
If a character has 10 eyes, the story should REQUIRE seeing 10 things at once.
If a character has 8 arms, the story should REQUIRE doing 8 things at once.

{age_guide}

CRITICAL: The stories MUST be appropriate for the age group above. Follow the sentence length, vocabulary, and complexity guidelines exactly.

For each theme, provide:
1. Theme name that fits this character personality and type (NEVER include specific body part numbers like "Eight-Armed" or "Six-Legged" in theme names)
2. Theme description (1 sentence, age-appropriate - NO specific body part numbers)
3. Theme blurb (1 exciting sentence to help kids choose - NO specific body part numbers)
4. 5 episodes, each with:
   - Episode number (1-10)
   - Title (short, age-appropriate)
   - Scene description (MUST include: {character_name}'s pose/action, specific setting details, any other characters present, at least 3-4 background objects to colour. Vary compositions: mix close-ups, wide shots, action scenes, and quiet moments across the 5 episodes)
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
- "Finding a special gem/jewel/crystal/stone/sparkle"
- Any quest where the character just "finds" or "collects" magical items
- Stories where the character's only action is LOOKING at things (seeing beauty, noticing sparkles)
- Stories with no real problem to solve - just wandering from place to place
These are OVERUSED. Be MORE CREATIVE than this!
*** WHAT MAKES A GREAT CHILDREN'S STORY ***

1. EMOTIONAL CORE - Every story needs a FEELING at its heart:
   - Loneliness → finding connection
   - Fear → discovering courage  
   - Feeling different → finding where you belong
   - Sadness → rediscovering joy
   - Confusion → gaining understanding

2. CHARACTER GROWTH - The character must CHANGE by the end:
   - They learn something about themselves
   - They overcome an internal struggle
   - They see the world differently

3. MEANINGFUL USE OF SPECIAL FEATURE:
   - The character's unique trait should solve an EMOTIONAL problem, not just physical
   - NOT: "Used strong arms to win a lifting contest"
   - YES: "Used strong arms to hold a bridge together while scared villagers crossed to safety"

ASK YOURSELF WHEN CREATING EACH THEME:
- What emotional need does this character fulfill for others?
- What fear might this character help someone overcome?
- What unlikely friendship could form?
- What broken relationship could they mend?
- What forgotten place could they bring back to life through PURPOSE (not magic)?

OVERUSED PATTERNS - use these SPARINGLY (max 1 per 3 themes):
- Contests, competitions, talent shows, races, tournaments
- "Restore the lost [color/magic/sparkle]"
- "Find the special [crystal/gem/jewel/stone/sparkle stone]"
- "Prove yourself to the doubters"
- Treasure hunts or quests to "find" a magical object
- Character just looks at things and notices they're special/magical
- Going to a series of locations and doing the same action at each one

*** MANDATORY STORY STRUCTURE ***

A. SUPPORTING CHARACTERS ARE REQUIRED:
- The story MUST include at least 2-3 named supporting characters with personalities
- At least one should appear by episode 2 and recur throughout the story
- Supporting characters should have their OWN feelings, problems, or funny quirks
- Examples: a nervous little bird, a grumpy old tortoise, a silly baby dragon, a bossy squirrel
- Do NOT have the main character alone for more than 2 consecutive episodes

B. THERE MUST BE A PROBLEM/ANTAGONIST:
- Something or someone must be causing trouble or be in need of help
- This problem should be established by episode 2 and not fully resolved until episode 9-10
- The problem should feel URGENT - someone is counting on the main character
- NOT acceptable: "character wanders around looking at pretty things"
- GOOD examples: a friend is trapped, a village is flooding, someone lost something precious to them, two friends had a fight

C. THERE MUST BE A SETBACK (episode 3-4):
- The character must TRY something and FAIL or face an unexpected complication
- This creates tension and makes the resolution feel earned
- Example: "They tried to use the special feature but it didn't work this time!"

D. DIALOGUE IS REQUIRED:
- At least 3 of the 5 episodes must include spoken dialogue in the story_text
- Use speech marks and give characters distinct voices
- 5-year-olds LOVE dialogue - characters talking, arguing, gasping, cheering

E. TEXT LENGTH - KEEP IT TIGHT:
- Each episode should have 2-3 sentences MAX for the story text
- The FINAL episode should be SHORT and punchy, not a long summary paragraph
- Let the ILLUSTRATION tell the story - don't over-explain in text
- NEVER cram 5+ sentences into one episode's text

F. THE ENDING MUST CONNECT TO THE BEGINNING:
- Episode 5 should reference or resolve something from episode 1
- The character who needed help in ep 1 should be the one celebrating in ep 5
- BAD ending: "And everything was wonderful forever!"
- GOOD ending: References the specific problem and how it was solved

GENERATE SOMETHING WE'VE NEVER SEEN BEFORE.
Imagine 1000 children have used this app - what story would NONE of them have received yet?
Be wildly creative. Surprise us. Make it unforgettable.

*** ANTI-REPETITION CHECK ***
Before finalising your story, ask yourself:
- Am I using the character's feature in the MOST OBVIOUS way? If yes, think of 3 alternatives and pick the weirdest one.
- Is my antagonist just "a grumpy thing blocking something"? Give them a REASON to be causing trouble.
- Does my story follow the pattern "quiet/broken place → character uses feature → place is fixed"? If yes, SCRAP IT and try a completely different structure.
- Is there physical comedy? A 5-year-old should LAUGH at least once.
- Would a child say "that was SO COOL" about at least one moment? If not, make it cooler.
- Each theme must have a clear beginning, middle, and end across 5 episodes
- *** CRITICAL - NARRATIVE FLOW AND LOCATION VARIETY ***:
  The story MUST visit AT LEAST 3-4 DIFFERENT LOCATIONS across 5 episodes. Do NOT stay in one place!
  A good story is a JOURNEY - the character should MOVE through the world.
  
  SETTING VARIETY - DO NOT DEFAULT TO NATURE/FORESTS/MEADOWS/VALLEYS:
  Stories set entirely in forests, meadows, valleys, or generic outdoor nature are BANNED.
  At least 2 of the 5 episodes must be in UNEXPECTED or EXCITING locations like:
  cities, rooftops, factories, underwater, space, restaurants, schools, hospitals, airports,
  castles, ships, trains, circuses, museums, stadiums, markets, construction sites, ice rinks,
  volcanoes, cloud kingdoms, giant's house, inside a clock, inside a whale, a cheese moon.
  Make the SETTING part of the fun - kids should want to colour the WORLD, not just the character.

  LOCATION PACING: Spend 1-2 episodes max in one location, then MOVE somewhere new.
  Example flows (use VARIED and UNEXPECTED settings - NOT always nature/forests!):
  - Underwater submarine (ep 1) → sunken pirate ship (ep 2) → whale's belly (ep 3) → coral reef village (ep 4) → beach celebration (ep 5)
  - Busy pizza restaurant kitchen (ep 1) → delivery through a thunderstorm (ep 2) → rooftop of a skyscraper (ep 3) → underground train station (ep 4) → surprise party (ep 5)
  - Space station (ep 1) → alien market on a moon (ep 2) → asteroid field (ep 3) → planet made of ice cream (ep 4) → home planet celebration (ep 5)
  - Monster school classroom (ep 1) → haunted gymnasium (ep 2) → school bus breaking down in a swamp (ep 3) → candy factory (ep 4) → school talent show (ep 5)
  
  When changing locations, include a BRIEF transition in the story_text:
  - "Following the sound, they found..." / "The map led them to..." / "On the way home, they spotted..."
  - BAD: Episode 3 in a library, Episode 4 suddenly on a bridge with NO explanation
  - GOOD: Episode 3 in a library, Episode 4: "A strange map fell out of the book, pointing to the old clock tower..."
- Always use "{character_name}" (not "the character") in story text - ALWAYS capitalise the name correctly
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
      "theme_id": "lonely_lighthouse",
      "theme_name": "The Lonely Lighthouse",
      "theme_description": "Example Monster befriends an old lighthouse keeper who has forgotten how to laugh, and helps the village remember why the lighthouse matters.",
      "theme_blurb": "Can Example Monster help a grumpy lighthouse keeper find joy again before the lighthouse closes forever?",
      "episodes": [
        {{
          "episode_num": 1,
          "title": "The Flickering Light",
          "scene_description": "Example Monster stands on a windy cliff path, looking up at an old lighthouse with a dim, flickering light. An elderly keeper watches sadly from the doorway. Seagulls circle overhead, waves crash on rocks below.",
          "story_text": "Everyone said the old lighthouse should be torn down. But Example Monster noticed something - the keeper looked so lonely up there. 'Hello!' called Example Monster. The keeper just frowned.",
          "emotion": "curious"
        }},
        {{
          "episode_num": 2,
          "title": "Dusty Memories",
          "scene_description": "CLOSE-UP: Example Monster and the grumpy keeper sit at a small table inside the dusty lighthouse. Old photos and maps cover the walls. A nervous little crab peeks from behind a teapot.",
          "story_text": "The keeper hadn't had a visitor in years. 'Nobody cares about lighthouses anymore,' he grumbled. But then a tiny crab scuttled across the table. 'That's Captain Pinch,' the keeper smiled for the first time. 'He's the only one who stayed.'",
          "emotion": "sad"
        }},
        {{
          "episode_num": 3,
          "title": "A Light in the Storm",
          "scene_description": "Example Monster and the keeper climb the spiral staircase inside the lighthouse. Rain lashes the windows. A tiny fishing boat is visible far out at sea, tilting in huge waves. Captain Pinch clings to Example Monster's shoulder.",
          "story_text": "A rumble of thunder shook the lighthouse! Example Monster spotted a tiny boat struggling in the waves. 'We have to help!' cried Example Monster. But the old lamp wouldn't light - it was completely broken!",
          "emotion": "scared"
        }},
        {{
          "episode_num": 4,
          "title": "A Monster-Sized Idea",
          "scene_description": "WIDE SHOT: Example Monster stands at the very top of the lighthouse, using their special feature to create a bright signal. The keeper watches in amazement. The fishing boat below starts turning toward the light. Captain Pinch waves a tiny flag.",
          "story_text": "The lamp was broken, but Example Monster had an idea! Using their special feature, they made the brightest light the cliff had ever seen. 'Over here!' shouted the keeper, waving his arms. The little boat began to turn.",
          "emotion": "determined"
        }},
        {{
          "episode_num": 5,
          "title": "Home Safe",
          "scene_description": "Example Monster, the keeper, Captain Pinch, and the rescued fisher (a grateful otter in a raincoat) all sit together in the warm lighthouse kitchen. The keeper is laughing. Through the window, the lighthouse beam shines brightly across the sea.",
          "story_text": "The fisher was safe! 'Thank you,' she whispered, still shaking. The keeper put the kettle on and laughed - a real, big belly laugh. 'Maybe this old lighthouse isn't finished yet,' he said, looking at Example Monster. And from that night on, the light never went out again.",
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
