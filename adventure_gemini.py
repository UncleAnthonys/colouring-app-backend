"""
Adventure Gemini - Simplified Universal Character Reveal
Focus on: PROPORTIONS, COLORS, PIXAR FACE - in that priority order
"""

import os
import base64
import google.generativeai as genai
import json
import random
import anthropic

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
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
    
    # No title on episode pages — just story text (like a real storybook)
    
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
            prompt = f'''I am showing you a REAL PHOTOGRAPH. Transform this subject into an ANIMATED CARTOON CHARACTER for a children's storybook.

CHARACTER NAME: {character_name}

===== WHAT TO DO =====
Look at the photo. Create a CARTOON VERSION of this subject — like a character from a Pixar/Disney/Dreamworks animated movie. 
The result must be CLEARLY A CARTOON, not a realistic rendering of the photo.

- If it is a CHILD / PERSON → Turn them into a cartoon character like Riley from Inside Out, Miguel from Coco, or Rapunzel. BIG expressive cartoon eyes (2-3x the size of real eyes), smooth rounded features, exaggerated expressions, simplified but charming. They should look like they BELONG in an animated movie, not like a photo with a filter.
- If it is a STUFFED TOY / PLUSH → Bring it to LIFE like Toy Story characters (Lotso, Woody, Buzz). Give it real animated personality and movement.
- If it is a REAL ANIMAL / PET → Anthropomorphize like Zootopia, Bolt, Puss in Boots. Big expressive cartoon eyes, personality in the face.
- If it is an OBJECT → Personify like Cars, Forky.

===== CHARACTER ANALYSIS =====
{description}

===== CARTOON STYLIZATION (THE MOST IMPORTANT PART) =====

🚨 THE OUTPUT MUST LOOK LIKE AN ANIMATED MOVIE CHARACTER, NOT A PHOTO 🚨

For HUMAN subjects, apply these cartoon transformations:
- Eyes: Make them bigger with glossy irises, visible highlights/catchlights — classic Disney/Pixar style
- Features: Smooth and rounded, simplified skin — no realistic pores/freckles/blemishes
- Expression: Joyful and animated — huge smile, bright eyes, bursting with personality
- Hair: SAME colour, SAME style, SAME length — but rendered in smooth cartoon style with volume
- Overall: The character should look like they were rendered by Pixar, not photographed

What to KEEP from the photo (the child MUST recognise themselves):
- Face shape and overall look — this must clearly be THEM
- Hair colour, style, and length EXACTLY as in the photo
- Clothing: SAME outfit, SAME colours, SAME patterns (stripes stay stripes, polka dots stay polka dots) — but rendered in smooth cartoon/Pixar style. The clothes must look like CARTOON CLOTHES on a Pixar character, not real fabric pasted onto a cartoon. A striped sweater becomes a smooth Pixar-rendered striped sweater. A floral dress becomes a clean cartoon floral dress. The patterns and colours are IDENTICAL but the rendering style is animated movie.
- Accessories (glasses, hat, bow, hairband, etc.) — keep them all, cartoon-rendered
- Skin tone (represented in the cartoon palette)
- General proportions — if the child is small/tall/slim, keep that

What to CHANGE from the photo:
- The rendering style becomes 3D animated movie (NOT photorealistic)
- Eyes become larger and more expressive (Pixar style)
- Skin becomes smooth cartoon skin
- Expression becomes more animated and joyful
- Overall look is polished and stylized like a movie character

===== REQUIREMENTS =====
- Celebration background with confetti and sparkles
- Portrait orientation - show FULL figure
- Character should be STANDING/POSED in a confident, joyful pose
- Character looks JOYFUL and ALIVE — like the hero of their own movie
- ABSOLUTELY NO WATERMARKS, NO SIGNATURES, NO TEXT, NO LOGOS anywhere in the image
- NO TEXT anywhere on image

IMPORTANT: The output should make a child say "WOW that's me as a CARTOON!" — not "that's just my photo with a weird filter." Go BIG on the cartoon stylization!'''
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


async def generate_adventure_episode_gemini(character_data: dict, scene_prompt: str, age_rules: str, reveal_image_b64: str = None, story_text: str = None, character_emotion: str = None, source_type: str = "drawing", previous_page_b64: str = None, second_character_image_b64: str = None, second_character_name: str = None, second_character_description: str = None) -> str:
    """
    Generate black & white coloring page using the REVEAL IMAGE as reference.
    
    Uses 3:4 portrait aspect ratio for A4-style pages.
    character_emotion overrides the default reveal pose with scene-appropriate emotion.
    Optionally accepts a second character (friend/pet) reference image.
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
*** CRITICAL - CHARACTER EMOTION AND POSE — THIS IS THE #1 THING THAT MAKES EACH PAGE DIFFERENT:
{character_name} MUST look {character_emotion} in this scene.

🚨 DO NOT draw the same happy open-mouth face on every page!
🚨 DO NOT copy the pose from the reference image!
The reference shows APPEARANCE ONLY (body shape, features). The EMOTION and POSE must change EVERY page.

EMOTION: {character_emotion}
Draw {character_name} with THIS expression and body language:
- happy/proud: Big smile, arms up or hands on hips, confident stance
- excited: Jumping or bouncing, arms wide, huge grin, movement lines
- scared: Hunched small, hands up defensively, wide frightened eyes, mouth in O shape
- worried/nervous: Biting lip or covering mouth, hunched shoulders, eyebrows up
- sad: Slumped posture, droopy eyes looking down, mouth turned down, maybe sitting on ground
- surprised: Hands on cheeks, mouth wide open, eyebrows way up, leaning back
- determined: Leaning forward, fists clenched, focused narrow eyes, strong stance
- curious: Head tilted, one eyebrow up, leaning toward something, hand on chin
- embarrassed: Hands covering face partially, looking sideways, shrinking down
- panicked: Running pose, arms flailing, sweat drops, wide eyes

The POSE tells the story as much as the scene does. A sad character SITS DOWN. A scared character HIDES. A proud character STANDS TALL.
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
*** PREVIOUS PAGE — USE FOR ANTI-REPETITION + SUPPORTING CHARACTER CONSISTENCY ***
A previous storybook page is attached. Use it for TWO purposes:

🚨 PURPOSE 1 — COMPOSITION MUST BE COMPLETELY DIFFERENT:
- DIFFERENT camera angle / framing than the previous page
- Characters in DIFFERENT positions (if they were center, put them left/right/foreground)
- DIFFERENT background arrangement — do NOT reproduce the same skyline, buildings, or layout
- If the previous page showed characters standing on the ground, THIS page must show them doing something else (sitting, climbing, riding, falling, running, crouching)
- If the previous page was a medium shot, THIS page must be a different shot type

🎭 PURPOSE 2 — SUPPORTING CHARACTERS MUST LOOK THE SAME:
- Look at the previous page image. Any SUPPORTING CHARACTERS (not the main character or second character — those use reference images) that appear again MUST look identical to the previous page
- Same species, same size, same body shape, same accessories (hat, bow tie, apron, glasses, etc.)
- Read the scene_description for character names and their bracketed descriptions — match them to the characters visible in the previous page
- Example: if a fat penguin with a chef hat appeared on the previous page, draw that SAME fat penguin with chef hat — not a thin penguin with no hat
- The main character and second character use their REFERENCE IMAGES for appearance — but supporting characters only exist in previous pages, so you MUST copy their look from there

📐 WHAT ELSE TO KEEP CONSISTENT:
- General story setting (if still at a fairground, it's still a fairground — but shown from a completely different angle and area)
- Time of day / weather

🚨 IF THE OVERALL COMPOSITION LOOKS SIMILAR TO THE PREVIOUS PAGE, YOU HAVE FAILED.
The whole point of a storybook is that EVERY page gives the child something NEW to look at and color.
"""
        
        # Build prompt
        full_prompt = f'''
╔══════════════════════════════════════════════════════════════╗
║  #1 PRIORITY — THIS IS WHAT YOU MUST DRAW                   ║
╚══════════════════════════════════════════════════════════════╝

SCENE TO ILLUSTRATE:
{scene_prompt}

STORY TEXT FOR THIS PAGE:
{story_text if story_text else "No story text provided."}

🚨 DRAW THE ACTION, NOT A PORTRAIT 🚨
- Read the scene description and story text above. Identify the KEY ACTION happening.
- Draw the characters DOING that action — NOT standing still, NOT posed for a photo.
- If the story says a character "climbed aboard the rollercoaster" → draw them IN the rollercoaster cart, gripping the bar, moving along the track
- If the story says a character "tumbled down" → draw them mid-fall, arms flailing, ground rushing up
- If the story says a character "ran through the market" → draw them mid-stride, legs apart, stalls blurring past
- Characters must be IN the situation, not standing nearby observing it
- The SETTING must change to match the scene description — if it says "inside the rollercoaster cart" then the background is track, sky, motion — NOT a ground-level fairground view
- EVERY page must look like a DIFFERENT FRAME from a movie, not the same frame with a different subtitle

╔══════════════════════════════════════════════════════════════╗
║  COMPOSITION — MANDATORY VARIETY                             ║
╚══════════════════════════════════════════════════════════════╝

If the scene_description specifies a CAMERA ANGLE or LOCATION, you MUST follow it exactly:
- "WIDE SHOT" → characters are small (20-30% of frame), environment dominates
- "CLOSE-UP" → character's face/upper body fills 60%+ of the frame, minimal background
- "OVERHEAD VIEW" → looking straight down on the scene
- "LOW ANGLE" → looking up at characters from below, they appear large/powerful
- "MEDIUM SHOT" → characters at 40-50% of frame, balanced with environment
- "NEW LOCATION" → the background must be COMPLETELY different from all previous pages

DO NOT default to the same medium-distance, straight-on, standing-in-the-middle composition every time. Each page is a NEW cinematic shot.

🚫 ABSOLUTELY NO TEXT IN THE IMAGE — THIS IS NON-NEGOTIABLE 🚫
- Do NOT write ANY words, letters, sentences, story text, dialogue, captions, or speech bubbles in the image
- Do NOT write the story text in the image — story text is added separately in post-processing
- Do NOT add character names, titles, labels, signs with readable text, or any other text
- The ONLY things in this image are ILLUSTRATIONS — black lines on white paper, nothing else
- If you add ANY text to the image, the page is RUINED and must be regenerated
- Text on signs/shopfronts in the background is OK ONLY if it is illegible scribble lines, NOT real words

[FORMAT]: Monochrome black and white 1-bit line art. Clean coloring book page.
[STYLE]: Clean, bold, uniform-weight black outlines. Pure white empty interiors. Thick, heavy marker outlines. Bold 5pt vector strokes.
[COLOR]: Strictly BLACK (#000000) and WHITE (#FFFFFF) ONLY. No gradients, no grey, no shading, no color.

[REFERENCE USE]: Use the attached reference image(s) ONLY for the character's shape and silhouette. Completely ignore all color, value, and shading data. DO NOT use the colors or lighting from the reference. DO NOT copy the POSE or COMPOSITION from the reference — only copy the character's APPEARANCE (body shape, features, clothing style).

CHARACTER: {character_name}
Use the reference image for SHAPE AND FORM ONLY — completely ignore all colors:
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
        
        # Add second character guidance if provided
        if second_character_name and second_character_image_b64:
            sc_desc = second_character_description or "a companion character"
            full_prompt += f'''
*** SECOND CHARACTER: {second_character_name} ***
A second reference image is attached for {second_character_name} ({sc_desc}).
Use this second reference image for {second_character_name}'s SHAPE AND FORM ONLY — ignore all colors.

🔴 CRITICAL - MATCH THE SECOND CHARACTER'S REFERENCE EXACTLY:
- Study the second reference image CAREFULLY before drawing
- {second_character_name}'s BREED/SPECIES must match: if the reference shows a spaniel with long floppy ears, draw a spaniel with long floppy ears — NOT a generic dog
- {second_character_name}'s SIZE relative to {character_name} must be realistic (a real dog comes up to a child's waist/hip, not tiny)
- {second_character_name}'s DISTINCTIVE FEATURES must be preserved: ear shape, ear length, fur texture, body proportions, face shape
- If the reference shows spots/patches → draw outlined patch areas for coloring
- If the reference shows long wavy fur → draw wavy fur outlines
- {second_character_name} should be IMMEDIATELY RECOGNIZABLE as the same character from the reference on every page

RULES FOR TWO CHARACTERS:
- BOTH {character_name} AND {second_character_name} MUST appear in the scene
- Use the FIRST reference image for {character_name}'s appearance
- Use the SECOND reference image for {second_character_name}'s appearance
- Each character must be clearly recognizable from their respective reference
- Both characters should be prominent in the scene — not one tiny in the background
- VARY their positions: don't put them in the same arrangement every page. Sometimes side by side, sometimes one in foreground and one behind, sometimes on opposite sides of the scene
- If {second_character_name} is an animal: Draw them AS AN ANIMAL — no human clothes, keep their natural markings as line art areas to color, floppy ears stay floppy, spots stay spots
- If {second_character_name} is a person: Keep their clothing and features from the reference
- Both characters should be INTERACTING in the scene (looking at each other, working together, reacting to events)
- {second_character_name} should show EMOTION too — tail wagging, ears perked, crouching scared, jumping excitedly

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
- No grey on pavements, roads, walls, ground, or ANY surface
- No grey "mood lighting" or "atmosphere" — even sad/scary scenes are pure white paper
- No grey puddle reflections or water shading — puddles are white with ripple LINES
- Every single area must be PURE WHITE (#FFFFFF) inside with only black outlines
- The ONLY non-white pixels are the BLACK lines (#000000)
- If you are tempted to add grey to convey mood, darkness, or shadow — DO NOT. Use thicker lines, cross-hatching, or context objects instead. The paper stays WHITE.

🚨 CLOTHING AND HAIR — THE BIGGEST PROBLEM AREA 🚨
Gemini: you keep filling clothing with GREY and DARK FILLS. STOP. Every single test output has grey trousers, grey stripes, or solid black jackets. This RUINS the coloring page.

SPECIFIC RULES FOR CLOTHING:
- STRIPED clothing (sweaters, shirts, socks): ALL stripes are WHITE. Show stripes with BLACK OUTLINE LINES only. Do NOT fill alternating stripes with grey — the child will color in different stripe colors themselves. A striped sweater = white sweater with horizontal black lines creating stripe sections.
- DARK clothing (black jackets, dark dresses, dark trousers): Draw as WHITE with black outlines. A "black jacket" in the story = WHITE jacket shape with black outline and maybe lapel/button details. NEVER fill it solid black or dark grey.
- TROUSERS/PANTS: Always WHITE inside with black outlines. Never grey. Never shaded.
- HAIR: Always WHITE inside with black outline strokes showing texture. Never solid black fill, even for black hair. Dark hair = white area with more texture lines, NOT black fill.
- SHOES: WHITE with black outlines. Not grey, not black fill.
- The child colors in ALL clothing — you provide the outlines, they provide the colors.
- If you make ANY clothing item grey or black-filled, that area CANNOT be colored in and the page is RUINED.

TEST YOURSELF: After generating, check EVERY piece of clothing on EVERY character. Is any clothing area filled with grey or black instead of white? If yes, you have failed.

🎯 CRITICAL - PRESERVE CHARACTER'S EXACT SHAPE:
- COUNT the arms in reference image - draw EXACTLY that many (usually 2)
- COUNT the legs in reference image - draw EXACTLY that many (usually 2)
- Copy the character's EXACT body shape from the reference
- DO NOT add extra limbs, tails, wings, or features not in the reference
- Match the reference EXACTLY - no additions, no modifications
- Only convert COLORS to white - keep all SHAPES identical

**MONOCHROME MEANS:**
- Only 2 values: BLACK (#000000) and WHITE (#FFFFFF)
- No RGB colors at all - not even pale/light versions
- No pink, no blue, no green, no yellow, no red, no orange
- No grey, no cream, no beige, no any tint
- Like a photocopied line drawing

**EVERY AREA IS WHITE — NO EXCEPTIONS:**
- Character's dress = WHITE (all sections, all layers)
- Character's hair = WHITE (even dark/black hair = white with texture lines)
- Character's skin = WHITE
- Striped sweater = WHITE with stripe LINES (not grey-filled stripes)
- Dark jacket/coat = WHITE with outline details (not black-filled)
- Trousers/pants = WHITE (never grey, never shaded)
- Shoes and boots = WHITE with outlines
- All background = WHITE
- Children will add ALL colors with their crayons — you provide ZERO color, ZERO grey, ZERO black fills

**INCLUDE MANY COLORABLE OBJECTS:**
- Add objects and details that fit the story scene
- Each object should be a clear, enclosed shape for coloring
- Fill the scene with things to color

FINAL CHECK - CRITICAL RULES:
1. Every pixel must be pure black (#000000) OR pure white (#FFFFFF) - nothing else
2. NO colors from reference - no blue, no orange, no any color
3. NO SOLID BLACK FILLS - clothing, hair, skin must be WHITE with black OUTLINES only
4. Black is ONLY for outlines/lines, NEVER for filling areas
5. All enclosed areas must be empty white space for children to color in
6. NO LARGE BLACK AREAS — roads, floors, tracks, sky, backgrounds, and large surfaces must be WHITE with texture lines, not solid black. Small strategic black fills are OK ONLY for tiny details like a shadow under a shoe, a small cave opening, or a silhouette in the distance — but NEVER fill a road, track, floor, wall, or any area larger than a fist with solid black. Parents print these pages and large black areas waste ink and leave nothing for kids to colour.
7. GREY IS NOT ALLOWED — not for trousers, not for stripes, not for mood, not for anything. If you see grey in your output, regenerate. Grey = failure.
8. SCAN EVERY CHARACTER'S CLOTHING — if any item is filled grey or black instead of white, fix it immediately

🚨 DARK SCENES — UNDERGROUND, CAVES, SEWERS, NIGHT, SPACE:
Even if the story takes place somewhere DARK (underground tunnel, sewer, cave, night time, space, deep sea), the page must STILL be pure black lines on pure white paper. There is NO exception.
- Tunnel walls = WHITE with brick/stone texture LINES
- Cave interior = WHITE with rock texture LINES
- Sewer pipes = WHITE with rivet/joint LINES
- Night sky = WHITE with star outlines and moon outline
- Deep sea = WHITE with bubble outlines and seaweed outlines
- Convey the SETTING through objects and texture lines, NEVER through grey shading or dark fills
- A child colouring this page will ADD the darkness themselves with dark crayons if they want to
- If you shade the walls grey, there is nothing left to colour — you have RUINED the page

ABSOLUTELY NO WATERMARKS, NO SIGNATURES, NO TEXT, NO LOGOS anywhere in the image. NO STORY TEXT, NO DIALOGUE, NO SPEECH BUBBLES, NO CAPTIONS. This is an ILLUSTRATION ONLY — text is added in post-processing.'''
        
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
            
            if second_character_image_b64:
                # Label the first image so Gemini knows which is which
                contents.append(types.Part.from_text(text=f"[REFERENCE IMAGE 1 - {character_name}]"))
            
            contents.append(types.Part.from_bytes(
                data=gray_bytes,
                mime_type="image/png"
            ))
        
        # Add second character image if provided
        if second_character_image_b64:
            from PIL import Image
            import io as pil_io
            sc_bytes = base64.b64decode(second_character_image_b64)
            sc_img = Image.open(pil_io.BytesIO(sc_bytes))
            sc_gray = sc_img.convert('L').convert('RGB')
            sc_buffer = pil_io.BytesIO()
            sc_gray.save(sc_buffer, format='PNG')
            sc_gray_bytes = sc_buffer.getvalue()
            
            sc_name = second_character_name or "Second Character"
            contents.append(types.Part.from_text(text=f"[REFERENCE IMAGE 2 - {sc_name}]"))
            contents.append(types.Part.from_bytes(
                data=sc_gray_bytes,
                mime_type="image/png"
            ))
        
        if previous_page_b64:
            # Add previous page for continuity reference
            prev_bytes = base64.b64decode(previous_page_b64)
            contents.append(types.Part.from_text(text="[PREVIOUS PAGE - for continuity reference]"))
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
                temperature=0.7,  # Higher temp for compositional variety across pages
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


async def generate_personalized_stories(character_name: str, character_description: str, age_level: str = "age_6", writing_style: str = None, life_lesson: str = None, second_character_name: str = None, second_character_description: str = None) -> dict:
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

*** WRITING STYLE ***
- Rhyming and rhythmic text is ESSENTIAL - every episode should have a rhyme or repeated phrase
- Sound effects on every page: "SPLISH!", "BANG!", "WHOOOOSH!", "POP POP POP!"
- Very short sentences (5-8 words max)
- Repetition with variation is the #1 tool - same phrase structure, different word each time
- Fun made-up words: "splishy-sploshy", "rumbly-tumbly", "snore-a-saurus"
- Basic emotions only: happy, sad, scared, excited, surprised
- Direct address to the reader: "Uh oh!", "Oh no!", "Can YOU see it?"

*** BEFORE YOU WRITE ANYTHING - DEFINE THE STORY DRIVER ***
Every great toddler story has ONE clear answer to: "What does the character WANT?"
The want must be something a 2-3 year old understands and cares about:
- Wanting to make a friend but being too scary/loud/big
- Wanting to help but accidentally making things worse
- Wanting to join in but not knowing how
- Wanting to give someone a present/surprise but everything goes wrong on the way
- Wanting to get home but obstacles keep appearing
- Being hungry and trying to find food

The character's special feature must be WHY they struggle (it causes the problem)
AND eventually WHY they succeed (they learn to use it differently).

*** WHAT SEPARATES A BAD STORY FROM A GOOD ONE ***

A BAD toddler story has:
- No clear WANT (character just wanders around)
- Feature causes RANDOM chaos with no purpose (loud = stuff breaks, strong = stuff smashes)
- Resolution is just "do the opposite" (loud -> quiet, fast -> slow)
- No emotional moment — nothing to make the kid feel anything
- No reason for the kid to care what happens next

A GOOD toddler story has:
- A SPECIFIC want the kid can relate to (help a friend, get somewhere, give a present, fix a mistake)
- Feature causes SPECIFIC funny problems that block the want (not random destruction)
- Each failed attempt is different and funnier than the last
- An emotional low point where the character feels sad/stuck (this is what makes the win feel good)
- A CREATIVE resolution where the feature is used in a SURPRISING new way (not the obvious use, not just "stop using it")
- The resolution connects emotionally to the want — not just "problem fixed" but "friendship strengthened" or "character accepted"

CRITICAL: DO NOT use the same story as the examples above. Pick from the SCENARIO POOL below and apply these principles to create something ORIGINAL.
The scenario pool has 180 creative starting points — USE THEM.

*** STORY STRUCTURE - USE ONE OF THESE 3 PROVEN PATTERNS ***

PATTERN A: "REPETITION WITH SURPRISE" (like Dear Zoo, Brown Bear Brown Bear)
- Episodes 1-3: Same pattern repeats with a different funny thing each time
- Episode 4: The pattern changes or breaks in a surprising way
- Episode 5: Satisfying conclusion that calls back to episode 1
Example: Character tries to find something. Ep1: finds wrong thing (too big!). Ep2: finds wrong thing (too small!). Ep3: finds wrong thing (too noisy!). Ep4: surprise - the thing finds THEM! Ep5: happy together.

PATTERN B: "ACCUMULATING CHAOS" (like The Very Hungry Caterpillar)
- Each episode adds ONE more silly thing to a growing pile of chaos
- By episode 3-4, everything is hilariously out of control
- Episode 5: one big action fixes everything (or makes it even funnier)
Example: Character accidentally makes one mess. Then a bigger mess. Then an ENORMOUS mess. Tries to clean up but makes it worse. Finally one silly accident fixes everything at once.

PATTERN C: "JOURNEY WITH OBSTACLES" (like We're Going on a Bear Hunt)
- Character goes somewhere, hits an obstacle, gets past it with a fun sound/action
- Each obstacle is different and fun to act out
- Final obstacle leads to a big surprise
- Then rush back home!
Example: Ep1: Can't get past the puddle (SPLASH!). Ep2: Can't get past the hill (WHEEE!). Ep3: Can't get past the sleeping dragon (SHHHHH tip-toe!). Ep4: Made it! But wait - surprise twist! Ep5: Rush home, funny ending.

*** WHAT MAKES TODDLER STORIES WORK ***
- A parent reading aloud should naturally do funny voices and actions
- At least ONE moment where the kid will LAUGH (physical comedy, something going splat, a funny noise)
- The character DOES things - never just looks or observes
- Predictable pattern that kids can "join in" with after one hearing
- A warm "everything's OK" ending
- The ending must MAKE SENSE: if the character made a mess, the mess leads to the solution. If they broke something, the broken thing becomes useful. The "mistake" should secretly BE the answer.

*** BANNED FOR AGE 3 ***
- Passive searching (look here, look there, found it, done)
- Character just observing or noticing things
- Abstract or conceptual themes
- Stories with no funny moment or surprise
- RANDOM SCENE JUMPS: every episode must connect to the previous one. If the character was in a park, explain HOW they got to the next place. A toddler story is simple but it still makes SENSE.

*** SCENE DESCRIPTIONS FOR AGE 3 ***
- Character should be LARGE in frame (40%+ of image)
- Maximum 2-3 background objects per scene
- Big chunky shapes, but still clearly narrative (viewer can tell what's happening in the story)
- Supporting characters big and simple with clear expressions
- Each scene looks VERY different from the last

*** TEXT LENGTH — STRICTLY ENFORCED ***
- 1-2 very short sentences per episode
- MAXIMUM 20 WORDS per episode. Count them. If it's over 20, cut it down.
- At least one sound effect or exclamation per episode
- Final episode: shortest of all (under 15 words)
- If you find yourself writing more than 2 sentences, you are writing TOO MUCH for a toddler
- Think: "Hop hop hop! Oh no — SPLAT! Sam fell in the mud." = PERFECT length
""",

        "age_4": """
AGE GROUP: 4 YEARS OLD

*** WRITING STYLE ***
- Rhyming is great but not required on every line
- Lots of sound effects: "KERPLUNK!", "tip-toe-tip-toe", "KABOOM!"
- Simple sentences (8-12 words) with occasional longer ones for drama
- A catchphrase or repeated question works great as a story thread
- Funny comparisons: "as tall as a house!", "louder than a thunderstorm!"
- Questions to the reader: "What do YOU think happened next?"
- Named emotions: scared, brave, proud, grumpy, excited, worried, silly

*** BEFORE YOU WRITE - DEFINE THE STORY DRIVER ***
Every story needs ONE clear answer to: "What does the character WANT, and what's stopping them?"
The want should be specific and urgent — not vague:
- BAD want: "Jerry wants to be helpful" (vague, no urgency)
- GOOD want: "Jerry wants to win the talent show but his big mouth keeps scaring the judges"
- BAD want: "Ted wants to explore" (no stakes, no obstacle)  
- GOOD want: "Ted needs to get the class hamster back in its cage before the teacher returns, but his big feet keep knocking things over"

The character's special feature must create a SPECIFIC, FUNNY obstacle to getting what they want.
The resolution must be CLEVER — not just "stop doing the bad thing" or "do the opposite."

*** STORY STRUCTURE - USE ONE OF THESE PATTERNS ***

PATTERN A: "THE CLEVER TRICK" (like The Gruffalo)
- Character faces a problem bigger than them
- Uses their special feature in a CLEVER way (not the obvious way)
- Moment of "oh no, it didn't work!"
- They try a smarter version and it works
- Everyone is impressed (or the trick is hilariously revealed)
Key: Character should be SMART, not just lucky.

PATTERN B: "THE GROWING TEAM" (like Room on the Broom)
- Character sets off on a mission alone
- Episodes 2-3: Meets helpers with funny personalities
- Episode 4: Individual efforts fail - they must work TOGETHER
- Episode 5: Team victory + celebration
Key: Each helper adds something funny AND useful.

PATTERN C: "THE BIG MISTAKE" (like Elmer, Oi Frog)
- Character does something causing an unexpected chain reaction
- Things get progressively sillier and more out of control
- The "mistake" turns out to be something good or useful
- Or the character learns they were great all along
Key: Comedy from things going wrong in UNEXPECTED ways.

*** WHAT MAKES AGE 4 STORIES GREAT ***
- A moment where the kid gasps or says "oh no!"
- A genuinely funny bit that makes the parent laugh too
- Supporting characters with ONE clear personality trait (the grumpy one, the scared one, the bossy one)
- The main character solving the problem THEMSELVES (no adult swooping in to fix it)
- Physical comedy AND verbal comedy together
- The solution must LOGICALLY follow from the problem — not a random new action

*** SCENE DESCRIPTIONS FOR AGE 4 ***
- Character prominent but not dominating (30-40% of image)
- 3-5 background objects per scene
- Moderate detail, some fun things to discover (a funny sign, a hidden creature)
- Supporting characters with clear distinctive looks
- Mix close-ups and wider shots across the 5 episodes

*** TEXT LENGTH ***
- 2-3 sentences per episode (25-40 words)
- Dialogue in at least 3 episodes
- Sound effects in at least 2 episodes
- Final episode: 2 short punchy sentences
""",

        "age_5": """
AGE GROUP: 5 YEARS OLD

*** WRITING STYLE ***
- Natural storytelling voice with personality
- Fun words: "super-duper", "teeny-tiny", "ginormous", "splashy-splashy", "rumbly-tumbly"
- Sound effects for impact: "CRASH!", "SPLORT!", "WHOMP!"
- Sentences 8-15 words, with occasional longer ones for dramatic moments
- Dialogue is essential - characters TALK to each other with personality
- Exclamations: "No way!", "That's impossible!", "Not AGAIN!"
- Character thoughts: "Tommy scratched his head. This was going to be tricky..."

*** BEFORE YOU WRITE - DEFINE THE STORY DRIVER ***
Answer these before writing a single word:
1. What does the character WANT? (Must be specific: "save the baby penguin" not "help others")
2. WHY do they want it? (Emotional reason: "because the penguin is crying and alone")
3. How does their special feature make it HARDER? (The feature causes a specific funny problem)
4. How does the feature eventually HELP in an UNEXPECTED way? (Not the obvious use)

BAD: Feature just does its obvious thing and saves the day.
GOOD: Feature causes problems all story, then the character finds a creative sideways use.

The OBVIOUS use of a feature is always BORING. The SURPRISING use is what makes great stories:
- BAD resolution: Feature does exactly what you'd expect (big mouth = shouts to save the day, many arms = grabs things)
- GOOD resolution: Feature is used SIDEWAYS — in a way nobody expected (big mouth becomes a boat, many arms become a bridge, big eyes become mirrors)
The weirder and more creative the use, the better the story. Pick from the SCENARIO POOL and find an unexpected angle.

*** STORY STRUCTURE ***

STRUCTURE A: "RESCUE/DELIVERY UNDER PRESSURE" (like Zog, Supertato)
- Episode 1: Clear urgent problem - someone needs help or something must be delivered NOW
- Episode 2: First attempt using the character's special feature
- Episode 3: SETBACK - the attempt fails or makes things worse. Moment of doubt.
- Episode 4: Creative solution - uses their feature DIFFERENTLY, or gets unexpected help
- Episode 5: Victory! Resolution connects back to episode 1 in a satisfying way
Key: The setback must feel real. The kid should worry it won't work out.

STRUCTURE B: "MYSTERY/DETECTIVE"
- Episode 1: Something weird is happening - clues are found
- Episode 2: Follow clues, meet a witness/helper with a funny personality
- Episode 3: Red herring! They blame the wrong person/thing (funny misunderstanding)
- Episode 4: Real answer discovered - surprising and funny
- Episode 5: Everything explained, problem solved, the "culprit" had a good/sweet reason
Key: The mystery answer should be funny or heartwarming, not scary.

STRUCTURE C: "ACCIDENTAL HERO" (like Dogger, Giraffes Can't Dance)
- Episode 1: Character feels they can't do something or doesn't fit in
- Episode 2: Forced into a situation where they HAVE to try
- Episode 3: Their attempt goes hilariously wrong
- Episode 4: But the "wrong" thing accidentally solves a bigger problem nobody noticed
- Episode 5: Character celebrated for being exactly who they are
Key: Message through ACTION not moralising. Show don't tell.

*** WHAT MAKES AGE 5 STORIES GREAT ***
- A setback that makes the kid say "uh oh, NOW what?!"
- Dialogue that sounds like real characters talking (not narration dressed as speech)
- At least one genuinely funny moment
- Supporting characters who actively HELP or HINDER - not just stand around watching
- An ending that makes the kid want to hear the story AGAIN
- The character's feature used in a way that surprises even the character
- The solution must come FROM the problem — the "disaster" secretly created the answer

*** SCENE DESCRIPTIONS FOR AGE 5 ***
- Rich detailed scenes with lots to colour
- 4-6 background objects plus supporting characters
- Mix compositions: wide establishing shots, close-up action, overhead views
- Characters showing clear emotions through body language
- Fun details that reward looking closely
- Each scene genuinely different in setting and feel

*** TEXT LENGTH ***
- 2-3 sentences per episode (30-50 words)
- Dialogue in at least 3 of 5 episodes
- At least one sound effect or onomatopoeia
- Final episode: short and punchy, don't summarise
""",

        "age_6": """
AGE GROUP: 6 YEARS OLD

*** WRITING STYLE ***
- Confident narrative voice with humour and personality
- Funny comparisons: "as bouncy as a kangaroo on a trampoline!"
- Dramatic pauses built into text: "And then... silence."
- Character voice should be distinct - the way THEY would say it
- Include thoughts AND dialogue: '"This is fine," thought Mo. It was NOT fine.'
- Longer sentences OK for tension (up to 20 words)
- Break the fourth wall occasionally: "Now, you might think this was a good idea. It was not."

*** BEFORE YOU WRITE - DEFINE THE STORY DRIVER ***
1. What does the character WANT? (Specific, urgent goal)
2. What are the STAKES? (What happens if they fail? Someone gets hurt/disappointed/left out)
3. How does the feature create an interesting DILEMMA? (It helps in one way but hurts in another)
4. What does the character LEARN? (Not a preachy lesson — an earned realisation through action)

The resolution must be CLEVER and EARNED — not just "try harder" or "believe in yourself."
The character should solve the problem in a way that reframes the whole story.

*** STORY STRUCTURE ***
Age 6 can handle real plot twists and emotional stakes:

- Episode 1: Establish the character's world AND the problem in the same beat. Hook immediately.
- Episode 2: First plan - starts well but a complication appears
- Episode 3: MAJOR SETBACK - plan fails badly. Character's limitation exposed. Lowest point.
- Episode 4: Realisation or unexpected help. New approach using what they LEARNED from failing.
- Episode 5: Climax and resolution - clever solution, ending connects to opening, final joke or emotional beat.

*** KEY PRINCIPLES ***
- The setback must be REAL - not just "oops, wrong place." Something genuinely goes wrong.
- Supporting characters have their own mini-motivations (not just cheerleaders)
- Dramatic irony where possible (reader knows something the character doesn't)
- The ending is EARNED - character MAKES things work out, things don't just happen to work
- Humour from character and situation, not just random wackiness

*** SCENE DESCRIPTIONS FOR AGE 6 ***
- Detailed rich scenes appropriate for the age
- 5-7 background objects/elements
- Dynamic compositions: action mid-movement, dramatic angles
- Environmental storytelling (background details that hint at the story)
- Varied settings that feel like a real world

*** TEXT LENGTH ***
- 3-4 sentences per episode (40-60 words)
- Mix of dialogue, action, and internal thought
- Final episode: wrap up efficiently, don't drag
""",

        "age_7": """
AGE GROUP: 7-8 YEARS OLD

*** WRITING STYLE ***
- Witty, fast-paced narrative with a strong authorial voice
- Humour through irony, exaggeration, and understatement
- Characters have distinct speech patterns and personalities
- Can include mild peril and genuine tension
- Internal monologue: "This was either the bravest or the stupidest thing Mo had ever done. Probably both."
- Wordplay and clever descriptions
- Sophisticated emotions: embarrassment, determination, reluctant admiration

*** BEFORE YOU WRITE - DEFINE THE STORY DRIVER ***
1. What does the character WANT? (Compelling, specific goal with real urgency)
2. What are the STAKES? (Real consequences — not just "things go wrong" but someone is counting on them)
3. What is the COST of the character's feature? (Every power has a downside that creates tension)
4. What is the TWIST? (Something the reader thinks they understand that gets reframed)

The best stories at this age have a moment where the reader's assumption is flipped.

*** STORY STRUCTURE ***
Full 5-act structure with genuine stakes:

- Episode 1: Hook immediately. Problem established with urgency and real consequences.
- Episode 2: Investigation/preparation. Build the world. Introduce allies and obstacles with personality.
- Episode 3: MAJOR FAILURE. Plan backfires spectacularly. Real consequences. Supporting characters affected too.
- Episode 4: Character adapts. Uses their feature in an unexpected creative way. Combines what they learned from failure.
- Episode 5: Climactic resolution with a twist. Ending reframes something from episode 1. Satisfying but not predictable.

*** KEY PRINCIPLES ***
- Real stakes: feelings get hurt, something important is at risk, time runs out
- Multiple characters with competing goals (not just good vs evil)
- The obstacle/villain should have an understandable motivation
- Humour and tension ALTERNATE - don't be one or the other, be both
- The character's special feature should have a COST or LIMITATION
- Subvert expectations at least once

*** SCENE DESCRIPTIONS ***
- Complex detailed scenes with many colourable areas
- Rich backgrounds with environmental storytelling
- Dynamic action compositions with movement
- Multiple characters interacting with clear body language
- Intricate details that reward careful colouring

*** TEXT LENGTH ***
- 3-4 sentences per episode (50-70 words)
- Heavy on dialogue and character interaction
- Can include mini-cliffhangers between episodes
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
        # Use Claude Haiku 4.5 for story generation (much better creative quality)
        claude_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        
        # Scenario pool - shuffled each time for variety
        _scenario_pool = [
        "A popcorn machine at the cinema won\'t stop and popcorn is flooding the whole building",
        "A birthday cake has come alive and is running through the town leaving icing footprints everywhere",
        "Someone put magic beans in the school dinner and now vegetables are growing through the roof",
        "The world\'s longest spaghetti noodle has tangled around the entire city like a giant web",
        "A chocolate fountain at the fair has gone turbo and is spraying chocolate over everything",
        "A bubble gum machine exploded and giant sticky bubbles are trapping people inside",
        "The ice cream van\'s freezer broke and a tidal wave of melting ice cream is sliding downhill toward the school",
        "A baker\'s bread dough won\'t stop rising and is pushing the roof off the bakery",
        "Someone mixed up the recipes — the pet shop is full of cake and the bakery is full of hamsters",
        "A soup volcano erupted in the school canteen and tomato soup is flowing down the corridors",
        "The sweet shop\'s pick-and-mix machine is firing sweets like cannonballs across the high street",
        "A jam factory pipe burst and a river of strawberry jam is heading for the swimming pool",
        "A double decker bus has started flying and the passengers don\'t know how to land it",
        "A train has lost its driver and passengers must stop it before the end of the line",
        "The world\'s biggest shopping trolley is rolling downhill toward the lake with no brakes",
        "A hot air balloon got tangled in the town clock tower and passengers are stuck",
        "A submarine\'s steering is broken and it\'s heading for an underwater volcano",
        "The school bus accidentally drove into a car wash and can\'t find the way out",
        "A spaceship\'s sat-nav is broken and keeps landing in wrong places — a farm, a wedding, a swimming pool",
        "The roller coaster won\'t stop and riders have been going round for hours",
        "A pirate ship appeared in the park boating lake and nobody knows where it came from",
        "The new robot taxi is picking people up and dropping them at completely wrong places",
        "All zoo animals swapped enclosures — penguin in the lion cage, lion in the aquarium",
        "A magician\'s rabbit won\'t go back in the hat and is multiplying — 300 rabbits in the shopping centre",
        "A parrot learned everyone\'s secrets and is shouting them at the school assembly",
        "The dentist\'s goldfish grew to the size of a car overnight",
        "Squirrels moved into the school computer room and are hoarding all the keyboards",
        "The class hamster escaped and is now running the school from the headteacher\'s chair",
        "A whale fell asleep across the harbour and no boats can get in or out",
        "A cat stole the Mayor\'s golden chain and is sitting on top of the church spire",
        "All dogs in town started walking backwards at the same time — nobody knows why",
        "An octopus at the aquarium keeps stealing visitors\' phones and taking selfies",
        "It\'s raining something different on every street — custard, bouncy balls, socks",
        "A giant snowball rolling through town getting bigger, collecting everything in its path",
        "Wind blew everyone\'s laundry and mixed it up — the Mayor is wearing a nappy",
        "A rainbow fell out of the sky and is blocking the motorway",
        "Clouds came down to ground level and nobody can see — chaos everywhere",
        "A leaf tornado trapped all the playground equipment inside it",
        "The sun went behind a cloud and forgot to come back — expedition to find it",
        "A thunderstorm is only happening inside the library and nobody knows why",
        "New playground built upside down — swings underground, sandpit on the roof",
        "A skyscraper is slowly tilting and everyone inside is sliding to one side",
        "Bouncy castle inflated too much — now the size of a real castle, floating above town",
        "School maze built too well — all the teachers are lost inside",
        "A crane picked up the swimming pool with people still in it",
        "The new bridge is made of chocolate and it\'s a hot day",
        "A treehouse growing by itself, adding rooms faster than anyone can explore",
        "Clock tower gears jammed — some people in fast-forward, others in slow motion",
        "All the festival fireworks went off at once inside the storage shed",
        "Magician\'s show went wrong — half the audience invisible, half upside down",
        "School nativity donkey is actually real and eating the set",
        "Wedding cake delivered to fire station — they used it for training",
        "Giant Christmas tree fell over blocking every road in town",
        "Carnival floats moving on their own with no drivers",
        "A pinata won\'t break, started moving, and is now chasing the children",
        "Shrinking ray hit the teacher — class now has a pencil-sized teacher",
        "Growing potion spilled on the goldfish — it\'s now the size of the school hall",
        "Time machine sent packed lunches to the dinosaur age — T-Rex eating someone\'s sandwich",
        "Science fair volcano actually erupted — school surrounded by bubbling goo",
        "Invisibility experiment — the whole school building disappeared but everyone\'s still inside",
        "Duplicating machine made 50 copies of the headteacher giving different instructions",
        "Gravity experiment went wrong — everything in the gym floating, including PE teacher",
        "Science fair robot decided it wants to be a student and won\'t leave class",
        "Toy shop toys came alive at midnight for a party — shop opens in one hour",
        "Board game became real-sized — dice the size of cars, whole town playing",
        "Teddy bear wish came true — tiny teddy is now 10 feet tall, still wants cuddles",
        "Arcade machines playing themselves, high scores going crazy",
        "Jigsaw puzzle assembling itself into a portal — things coming through from the picture",
        "LEGO built itself into a castle overnight — a LEGO knight guards the door",
        "Remote control cars escaped the toy shop and are racing through town",
        "Firefighter\'s hose spraying silly string instead of water during a real emergency",
        "Postman\'s letters flying out and delivering themselves to wrong houses",
        "Dentist\'s chair started flying around the surgery with patient still in it",
        "Hairdresser\'s magic shampoo makes hair grow super fast — out the door in minutes",
        "Painter used magic paint — everything painted is coming alive",
        "Librarian\'s robot organising books by colour not title and refuses to stop",
        "Alien spaceship crashed into school roof — needs fixing before home time or alien\'s mum will worry",
        "Aliens visiting Earth think vinegar is perfume and chips are building blocks",
        "Space station gravity keeps flipping — astronauts bouncing between ceiling and floor",
        "Giant space snowball heading to Earth — unexpected snow day incoming",
        "Ocean plug came loose — all water draining out, fish NOT happy",
        "Underwater post office lost deliveries — shark got a seahorse\'s birthday card",
        "Sunken treasure chest opened — gold coins floating up causing beach chaos",
        "Coral reef talent show — three grumpy crab judges giving everyone zero",
        "A mysterious door appeared at the back of the school gym that wasn\'t there yesterday",
        "A treasure map blew in through the classroom window showing a route nobody recognises",
        "The museum\'s oldest painting has a tiny staircase in the corner nobody noticed before",
        "A message in a bottle with coordinates pointing underneath the town fountain",
        "An old lift has a button for a floor that doesn\'t exist — Floor 13 and a half",
        "New kid at school says they\'re from a country nobody can find on any map",
        "Tunnels underneath the town being mapped for the first time — something\'s making noises down there",
        "Lighthouse keeper missing — left behind strange inventions and half-finished notes",
        "Hot air balloon landed in the playground with nobody in it — just a note saying HELP",
        "A door in the big oak tree that only appears when it rains",
        "Old boat washed up covered in barnacles with a logbook in an unknown language",
        "Town hall attic locked for 100 years — today they found the key",
        "New kid at school doesn\'t speak the same language and looks lonely at lunch",
        "Two best friends both want the same part in the school play — it\'s tearing them apart",
        "Grumpy neighbour who shouts at everyone secretly been feeding all the stray cats",
        "Smallest kid always picked last for teams but has an amazing hidden talent",
        "A kid\'s imaginary friend is sad because the kid is growing up and doesn\'t play pretend anymore",
        "School bully caught crying behind the bins — having a really hard time at home",
        "Two rival bakers must work together when a power cut hits both shops",
        "Shy kid finds a lost dog and has to knock on strangers\' doors to find the owner",
        "Elderly neighbour can\'t get to the shops anymore and nobody noticed except the character",
        "Class goldfish is poorly — whole class works together on the best fish hospital ever",
        "Kid who just moved to new town pretending everything\'s fine but secretly misses old friends",
        "Grandparent forgetting things more and more — grandchild finds creative ways to help them remember",
        "Loneliest tree in the park has no birds — every other tree does — someone investigates why",
        "Child finds names carved on a park bench from decades ago and tries to find the people",
        "Only kid who can\'t swim has to go to the pool party everyone else is excited about",
        "A creature that looks completely different from everyone turns up at the market — nobody will talk to them",
        "Kid who uses a wheelchair discovers a part of the playground only they can reach",
        "Weirdest house on the street about to be knocked down but it\'s actually the most special one",
        "Kid told they\'re \"too loud\" everywhere until they find a place where loud is exactly what\'s needed",
        "One fish swimming opposite to all others discovers something amazing the rest missed",
        "Kid who draws outside the lines enters a competition where that\'s the whole point",
        "Wonky homemade cake enters a competition full of perfect professional cakes",
        "Bird that can\'t fly lives among birds that can — until winter when flying isn\'t what\'s needed",
        "Scruffiest dog at the rescue centre keeps getting overlooked while cute puppies get chosen",
        "Birthday wish made everything opposite — up is down, cats bark, teachers are students",
        "Copy machine left on overnight — 1000 newsletters flying through town",
        "Town statue came alive but can only move when nobody\'s looking",
        "Hiccup going around town — each person hiccups something different: bubbles, confetti, glitter",
        "Kid\'s homework excuse came true — \"a dinosaur ate my homework\" and now there\'s a dinosaur",
        "Everything the character says comes true literally — \"I could eat a horse\" and a horse appears on a plate",
        "School camera takes photos of what people are THINKING not what they look like",
        "Restaurant critic coming today but the chef lost their sense of taste — need a secret taster",
        "Town crier got hiccups — all announcements coming out garbled and wrong",
        "Picture day camera adds silly hats and moustaches to everyone and won\'t stop",
        "Kid\'s shadow detached and is doing its own thing — going to classes, eating with other kids",
        "Voice-activated town systems mishearing everything — \"lights on\" turns on sprinklers",
        "Smart board learned to talk and won\'t stop giving opinions during lessons",
        "Fancy dinner party where everything goes wrong — cold soup, collapsing chairs, exploding dessert",
        "Kid terrified of the dark has to cross the school field at night to get something important",
        "Child scared of water — their best friend\'s puppy just fell in the pond",
        "Kid who hates thunder is at a sleepover when the biggest storm hits",
        "Child afraid of heights — only way to rescue the stuck kite is to climb",
        "Shy kid has exactly the information everyone needs but must say it in front of the whole school",
        "Kid scared of dogs has to walk past one daily — one day the dog needs help",
        "Kid who hates getting messy — the only fix involves getting VERY messy",
        "Child who hates loud noises must cross the noisiest place in town for an important delivery",
        "Town\'s only bridge broken — everyone stuck on one side, character must connect them",
        "Oldest lady\'s garden destroyed by storm — it was the one thing that made her happy",
        "Homeless kitten hiding under the school, too scared to come out, getting cold tonight",
        "Local park becoming a car park unless someone proves it\'s special enough to keep",
        "School dinner lady secretly using her own money so no kid goes hungry",
        "Power out on coldest night — neighbours don\'t even know each other",
        "Elderly toymaker\'s hands shake too much to make toys but Christmas is coming",
        "Town\'s ice cream van broke down on the hottest day — ice cream melting fast",
        "Cardboard box becomes a real spaceship when nobody\'s looking — must get back before bedtime",
        "Drawings in a sketchbook climbing off the pages when the kid sleeps",
        "Blanket fort became an actual kingdom with tiny citizens who need help",
        "Bath time rubber ducks turned into real ducks — bath is now an ocean",
        "Kid\'s imaginary world leaking into reality — imaginary dragon is in the kitchen",
        "Toy dinosaur came alive in the museum — get it back to the exhibit before the guard notices",
        "Chalk playground drawings become real when it rains — someone drew a lion",
        "Bedtime story telling itself differently — characters going off-script",
        "Snow globe on the shelf snowing for real — tiny town inside needs help with their blizzard",
        "Kid\'s LEGO city comes alive at night — they shrink down but something\'s wrong in LEGO town",
        "Sports day chaos — egg and spoon egg is an ostrich egg, sack race sacks have holes",
        "School bake-off where the oven keeps changing temperature on its own",
        "Dance competition where the floor tiles light up randomly and you must follow them",
        "Paper boat race on the river but this year there are real tiny rapids",
        "Hide and seek championship where hiding spots keep moving — wardrobe walks to new room",
        "Spelling bee where correctly spelled words come alive and walk around the stage",
        "School science fair — every project activates at once, hall becomes total chaos",
        "Sandcastle competition but the tide is coming in fast",
        "Kite competition on the windiest day ever — kites pulling owners into the sky",
        "School team playing against robots that keep glitching in funny ways",
        "Kid finds a tiny injured bird and nurses it back to health, not knowing if it will fly again",
        "First snow of winter — whole town building the most spectacular snowman ever",
        "Rainy afternoon baking with grandparent who shares stories from when they were young",
        "Kid growing a sunflower for competition but starts caring more about the flower than winning",
        "Moving day — saying goodbye to old room, old street, old climbing tree",
        "Kid saving up pocket money for weeks to buy something special for someone they love",
        "Last day of summer holidays — friends plan the perfect final adventure before school starts",
        "Box of old letters in the attic tells the story of how grandparents met",
        "Night before starting new school — kid can\'t sleep, imagining everything that might happen",
        "Child stays up late to see the stars for the first time, wrapped in a blanket with their parent",
        ]
        random.shuffle(_scenario_pool)
        _scenario_subset = _scenario_pool[:30]
        shuffled_scenarios = "\n".join(f"{i+1}. {s}" for i, s in enumerate(_scenario_subset))

        # Build optional style/theme override block
        style_theme_block = ""
        if writing_style:
            style_theme_block += f"""
*** WRITING STYLE OVERRIDE ***
The user has chosen a specific writing style: "{writing_style}"
Adapt ALL story text to match this style:
- If "Rhyming": Every episode's story_text should rhyme. Use couplets or AABB rhyme schemes. Make it flow like a poem.
- If "Funny": Maximize humor — puns, physical comedy, absurd situations, ironic narration. Make the parent laugh too.
- If "Adventurous": High stakes, cliffhangers between episodes, brave choices, exciting action verbs.
- If "Gentle": Soft, calming language. Quiet moments of wonder. Cozy settings. Warm resolutions.
- If "Silly": Over-the-top nonsense, made-up words, ridiculous situations, characters being goofy.
- For any other style: interpret it naturally and apply it consistently across all episodes.
This style should permeate the story_text, episode titles, and theme descriptions.
"""
        if life_lesson:
            style_theme_block += f"""
*** LIFE LESSON OVERRIDE ***
The user wants the story to teach or explore this life lesson: "{life_lesson}"
ALL 3 story pitches must weave this lesson naturally into the narrative:
- If "Friendship": The story should explore making friends, loyalty, helping each other, or what it means to be a good friend.
- If "Being brave": The character should face fears, show courage, or learn that being brave doesn't mean not being scared.
- If "It's OK to make mistakes": The character should mess up, feel bad, but discover that mistakes lead to learning or something good.
- If "Kindness": The story should show acts of kindness, empathy, or helping others without expecting anything back.
- If "Being yourself": The character should learn to embrace what makes them different or unique.
- If "Sharing": The story should explore sharing, generosity, or discovering that sharing makes things better.
- If "Perseverance": The character should keep trying when things get hard, showing that persistence pays off.
- For any other lesson: interpret it naturally and weave it throughout the story arc.
IMPORTANT: The lesson should emerge THROUGH THE STORY, not through lecturing or moralising. Show don't tell. The character EXPERIENCES the lesson through what happens to them.
"""

        # Build second character block for the prompt
        second_char_block = ""
        if second_character_name and second_character_description:
            second_char_block = f"""
*** SECOND CHARACTER (COMPANION/FRIEND/PET) ***
Name: {second_character_name}
Description: {second_character_description}

This is {character_name}'s companion who appears in EVERY scene. {second_character_name}'s features and personality should ALSO drive the story:
- Their features can cause problems (muddy paws track dirt everywhere, long tail knocks things over, curiosity leads them into trouble)
- Their features can also help solve problems (keen nose sniffs out clues, strong arms lift heavy things, tiny size fits through gaps)
- They should have their OWN personality and reactions — not just follow the main character silently
- At least ONE of the 3 themes should use {second_character_name}'s features as a key story element
- {second_character_name} and {character_name} should work as a TEAM — sometimes disagreeing, sometimes complementing each other
"""

        prompt = f'''You are creating personalized story adventures for a childrens coloring book app.
{style_theme_block}
Based on this character named "{character_name}"{f" and their companion {second_character_name}" if second_character_name else ""}, generate 3 UNIQUE story themes that are PERSONALIZED to the character's features.

CHARACTER TO ANALYZE:
{character_description}

{second_char_block}

STEP 1 - IDENTIFY THE MOST UNUSUAL FEATURES (in order of priority):
Look at the character description. Find the WEIRDEST, most UNUSUAL things:

⚠️ CRITICAL — HUMAN/PERSON CHARACTERS:
If the character is a REAL CHILD, PERSON, or HUMAN (not a monster, animal, toy, or drawing):
- NEVER use their PHYSICAL BODY as a story feature: skin colour, hair type/texture, body shape, weight, height, facial features, disability, or any physical characteristic they were born with
- Clothing and accessories ARE fine to use as features: a bow tie, cardigan, favourite hat, backpack, special shoes — these make great story elements
- Poses and habits are fine too: always has hands in pockets, never takes off their hat, carries a lucky charm
- If the description ONLY mentions physical body traits and no clothing/accessories, give the character a FUN PERSONALITY TRAIT instead: brave but clumsy, incredibly curious, talks to animals, amazing at building things, never gives up, always loses things
- The key rule: a child should never see a story that makes fun of or centres on how their body naturally looks

For NON-HUMAN characters (monsters, animals, toys, drawings): Use the feature analysis below as normal — multiple eyes, tentacles, unusual shapes etc. are all great story features.

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
Example: "A duplicating machine made 50 copies of the headteacher" + a character with many eyes = each eye can track a different copy, but they keep getting confused when copies swap clothes. Eventually they spot the real one because only the original has a coffee stain on their tie.

Each theme MUST use a DIFFERENT unique feature as the main plot device.

*** CRITICAL: EVERY THEME MUST HAVE A CLEAR "WANT" ***
Before writing each theme, define:
- WANT: What does the character specifically want? (NOT vague like "help others" or "explore" — SPECIFIC like "rescue the stuck kitten" or "find their lost friend" or "win the sandcastle competition")
- OBSTACLE: How does their special feature make this HARDER? (The feature should cause funny, specific problems)
- TWIST: How does the feature eventually help in an UNEXPECTED way? (Not the obvious use)

Stories without a clear WANT are boring. "Character walks around and their feature causes random chaos" is NOT a story.
"Character desperately wants X but their feature keeps causing Y" IS a story.
NEVER include specific body part numbers in theme names.

*** SCENARIO POOL ***

{shuffled_scenarios}

*** HOW TO USE THESE SCENARIOS ***

1. Read the character's features from STEP 1
2. Scan ALL 180 scenarios — DO NOT just pick from the top of the list! Read the ENTIRE list before choosing.
3. Pick the 3 where the character's feature would create the FUNNIEST, most SURPRISING story
4. Each theme must use a DIFFERENT feature
5. NEVER pick scenarios 1-20 unless they are genuinely the best fit — the top of the list is NOT better than the rest
6. ADAPT the scenario — change names, settings, details, put your own spin on it. The scenario is a starting point not a script
7. The character's feature should help in a SURPRISING way, not the obvious way
8. NEVER use the scenario's exact wording in the theme blurb — rewrite it completely

{age_guide}

CRITICAL: Follow the age guidelines above exactly for sentence length, vocabulary, and complexity.

*** FORMAT ***

For each theme provide:
1. Theme name (fun, age-appropriate)
2. Theme description (1 sentence)
3. Theme blurb (ONE short punchy sentence, MAX 15 words. Describe the chaos/situation only. NEVER mention the character's body parts in the blurb)
4. 5 episodes with: episode number (1-5), title, scene_description, story_text, emotion

Scene descriptions MUST focus on THE MAIN ACTION of the episode:
- ALWAYS START with the LOCATION: "In the kitchen...", "At the park climbing frame...", "Still at the fountain..."
- What is the character DOING? (not just standing — show the action mid-happening)
- What are the VISIBLE CONSEQUENCES? (ketchup on the floor, cake flying through air, toys scattered everywhere)
- What is the character's BODY LANGUAGE? (slumped and sad, jumping with excitement, running away in panic)
- Include specific setting details and 3-4 background objects to colour
- IMPORTANT: If the scene is in the SAME LOCATION as the previous episode, REPEAT the key setting objects (climbing frame, oven, fountain etc.) — don't assume the artist remembers them
- SUPPORTING CHARACTERS: Every time a supporting character appears in a scene description, include their species, size, and any accessories in brackets. Example: "Pip (small duck with bow tie)" or "Mrs. Whiskers (tall cat wearing apron)" NOT just "Pip". NO COLOURS — this is a colouring book. Describe by shape and features only. Use the EXACT SAME description each time so they look consistent across pages.
- Mix close-ups, wide shots, and action scenes across the 5 episodes
- The scene description is what gets drawn — if you don't describe it, it won't be in the image!

Story text: Follow the age guidelines for length. Final episode should be short and punchy.

Supporting characters: When you introduce a supporting character, define their appearance with a brief tag describing species, size, and accessories (NO COLOURS). E.g. "Pip (small duck with bow tie)". Then in EVERY scene_description where that character appears, include the SAME tag after their name. The artist has no memory between pages — if you just write "Pip" they will draw a different character each time.

Emotion must be one of: nervous, excited, scared, determined, happy, curious, sad, proud, worried, surprised, embarrassed, panicked

*** EMOTION RULES — CRITICAL ***
- You MUST use at LEAST 3 DIFFERENT emotions across the 5 episodes
- Episodes 1-3 should ESCALATE emotionally (e.g. curious → worried → sad)
- Episode 3 (the setback) MUST NOT be "happy" or "excited" — use sad, worried, scared, or panicked
- Episode 5 (resolution) should be happy, proud, or excited
- NEVER use "happy" for more than 2 episodes
- The emotion should match what the character FEELS in that moment of the story

*** 6 NON-NEGOTIABLE RULES ***

1. CHARACTERS: At least 2 named supporting characters with funny personalities who appear throughout, not just once.
2. SETBACK ON EPISODE 3: Character tries and FAILS or makes things worse. Makes the win feel earned.
3. DIALOGUE: At least 3 of 5 episodes need characters talking in speech marks.
4. ENDING: Episode 5 resolves the specific problem from episode 1. No generic happy endings.
5. NEVER copy a scenario word-for-word. Adapt it, remix it, make it feel fresh and unique to this character.
6. NUANCED RESOLUTION: The character's feature should NOT directly fix the problem alone. Instead, a SUPPORTING CHARACTER should suggest a new way to use the feature, OR the character should learn to use it differently after the setback. The solution should feel like a team effort or a moment of growth, not just "feature solves everything".

Return ONLY valid JSON. Generate 3 theme PITCHES (no full episodes yet). Here is the exact format:

{{
  "character_name": "Example Monster",
  "age_level": "age_5",
  "themes": [
    {{
      "theme_id": "the_great_gravity_mix_up",
      "theme_name": "The Great Gravity Mix-Up",
      "theme_description": "When the gym's gravity experiment goes wrong, everything starts floating and Example Monster must catch everyone before they drift out the windows.",
      "theme_blurb": "Everything in the gym is floating and the PE teacher is stuck on the ceiling!",
      "feature_used": "big eye",
      "want": "catch all the floating students before they drift out the windows",
      "obstacle": "the eye keeps getting distracted tracking too many floating objects at once",
      "twist": "uses the eye as a magnifying glass to focus sunlight and melt the anti-gravity device"
    }},
    {{
      "theme_id": "the_missing_socks_mystery",
      "theme_name": "The Missing Socks Mystery",
      "theme_description": "Every sock in town has vanished overnight and Example Monster must follow the trail of woolly clues to find the thief.",
      "theme_blurb": "Every single sock in town has disappeared overnight!",
      "feature_used": "long arms",
      "want": "find who stole all the socks before the big football match",
      "obstacle": "long arms keep accidentally knocking over clues and evidence",
      "twist": "uses arms to reach into the tiny mouse hole where the sock-hoarding mice live"
    }},
    {{
      "theme_id": "the_worlds_worst_haircut",
      "theme_name": "The World's Worst Haircut",
      "theme_description": "The new barber is a robot who has gone haywire, giving everyone ridiculous haircuts, and Example Monster must stop it.",
      "theme_blurb": "The robot barber has gone BONKERS and nobody's hair is safe!",
      "feature_used": "spiky head",
      "want": "stop the robot barber before it reaches the school photo",
      "obstacle": "the robot keeps trying to cut the character's spikes thinking they're messy hair",
      "twist": "the spikes jam the robot's scissors, causing it to short-circuit and reset"
    }}
  ]
}}

NOW generate 3 theme PITCHES for {character_name}. Each theme must use a DIFFERENT character feature. Include theme_id, theme_name, theme_description, theme_blurb, feature_used, want, obstacle, and twist. Do NOT generate full episodes — just the pitches. Return ONLY the JSON, no other text.'''
        
        claude_response = claude_client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        # Parse the JSON response
        text = claude_response.content[0].text.strip()
        
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


async def generate_story_for_theme(
    character_name: str,
    character_description: str,
    theme_name: str,
    theme_description: str,
    theme_blurb: str,
    feature_used: str,
    want: str,
    obstacle: str,
    twist: str,
    age_level: str = "age_6",
    writing_style: str = None,
    life_lesson: str = None,
    second_character_name: str = None,
    second_character_description: str = None
) -> dict:
    """Generate full 5-episode story for a single chosen theme."""
    
    anthropic_key = os.environ.get('ANTHROPIC_API_KEY')
    if not anthropic_key:
        raise HTTPException(status_code=500, detail='Anthropic API key not configured')
    
    import anthropic
    claude_client = anthropic.Anthropic(api_key=anthropic_key)
    
    # Get age-specific guidelines
    age_guidelines = {
        "age_3": """AGE 3: Max 20 words per episode. Very simple sentences. 2-3 word sound effects. Familiar settings (home, garden, park). Basic emotions only (happy, sad, scared). No complex plots.""",
        "age_4": """AGE 4: Max 30 words per episode. Simple sentences with one fun word per page. Sound effects like CRASH, SPLAT. Familiar settings with one magical element. Clear emotions.""",
        "age_5": """AGE 5: 30-50 words per episode. Natural storytelling voice. Fun words: "super-duper", "ginormous". Sound effects: "CRASH!", "SPLORT!". Dialogue in at least 3 of 5 episodes. At least one genuinely funny moment. Supporting characters who actively HELP or HINDER.""",
        "age_6": """AGE 6: 40-60 words per episode. Richer vocabulary. Subplots with supporting characters. Emotional complexity. Humor through situation and character. Dialogue-driven storytelling.""",
        "age_7": """AGE 7: 50-70 words per episode. More sophisticated plots. Character development. Themes of friendship, perseverance. Multiple supporting characters with distinct personalities.""",
        "age_8": """AGE 8: 60-80 words per episode. Complex narrative structure. Red herrings, plot twists. Deeper emotional arcs. Witty dialogue.""",
        "age_9": """AGE 9: 70-90 words per episode. Sophisticated storytelling. Multiple storylines. Nuanced characters. Themes of identity and belonging.""",
        "age_10": """AGE 10: 80-100 words per episode. Near-novel quality. Complex themes. Rich descriptions. Layered humor. Character growth across episodes.""",
    }
    
    age_guide = age_guidelines.get(age_level, age_guidelines["age_5"])
    
    # Build optional style/theme override block for full story
    style_theme_block = ""
    if writing_style:
        style_theme_block += f"""
*** WRITING STYLE: {writing_style} ***
The user chose "{writing_style}" style. Apply this to ALL story_text:
- Rhyming: Every episode rhymes (couplets/AABB). Make it flow like a poem.
- Funny: Maximize humor — puns, physical comedy, absurd situations, ironic narration.
- Adventurous: High stakes, cliffhangers, brave choices, exciting action verbs.
- Gentle: Soft, calming language. Quiet wonder. Cozy settings. Warm resolutions.
- Silly: Over-the-top nonsense, made-up words, ridiculous situations.
For any other style: interpret naturally and apply consistently.
"""
    if life_lesson:
        style_theme_block += f"""
*** LIFE LESSON: {life_lesson} ***
Weave this life lesson naturally into the story: "{life_lesson}".
The character should EXPERIENCE this lesson through what happens — not through lecturing.
The lesson should emerge from the story events, especially through the setback in episode 3 and the resolution in episodes 4-5.
"""

    # Build second character block
    second_char_story_block = ""
    if second_character_name and second_character_description:
        second_char_story_block = f"""
*** COMPANION CHARACTER: {second_character_name} ***
Description: {second_character_description}

{second_character_name} is {character_name}'s companion and appears in EVERY episode. They are NOT a supporting character — they are a CO-STAR.
- {second_character_name} should have their OWN reactions, dialogue, and personality throughout the story
- Their features should actively affect the plot: causing problems, providing solutions, creating funny moments
- They should interact with {character_name} as a real partner — sometimes helping, sometimes accidentally making things worse, sometimes having their own ideas
- In scene_description, ALWAYS include {second_character_name} with a brief description in brackets, e.g. "{second_character_name} ({second_character_description[:60]})"
- {second_character_name} should be DOING things in every scene — not just standing next to {character_name}
"""

    prompt = f'''You are writing a complete 5-episode story for a children's coloring book app.
{style_theme_block}
CHARACTER: {character_name}
CHARACTER DESCRIPTION: {character_description}

{second_char_story_block}

CHOSEN THEME: {theme_name}
THEME DESCRIPTION: {theme_description}
THEME BLURB: {theme_blurb}

STORY PLAN:
- Feature used: {feature_used}
- WANT: {want}
- OBSTACLE: {obstacle}
- TWIST: {twist}

⚠️ IF THE CHARACTER IS A REAL CHILD/PERSON (not a monster, animal, or toy):
NEVER base the story on their PHYSICAL BODY features (skin colour, hair type, body shape, facial features, height, weight, disability).
Clothing and accessories (bow tie, cardigan, hat, backpack) ARE fine as story features — keep using them.
If the "feature used" describes a physical body trait, treat it as a minor character quirk and focus the story on the scenario, the character's personality, and their interactions with supporting characters instead.

{age_guide}

*** STORY STRUCTURE ***
- Episode 1: Set up the problem. Introduce 2 named supporting characters with funny personalities (include species, size, accessories in brackets after each name). The companion character (if present) should react to the problem in their own way.
- Episode 2: First attempt using the character's feature. Things start going wrong. The companion character's features or personality may contribute to the chaos.
- Episode 3: SETBACK — attempt fails or makes things worse. Real moment of doubt. This episode MUST NOT be happy. The companion character provides emotional support or accidentally makes things worse.
- Episode 4: Creative solution — uses feature DIFFERENTLY based on the twist. The companion character OR a supporting character helps or suggests the new approach. The companion's own features might be key to the solution.
- Episode 5: Resolution that connects back to episode 1. Short and punchy ending. Do NOT summarise or moralise.

*** SCENE DESCRIPTIONS ***
- Start each with LOCATION: "In the kitchen...", "At the park..."
- Show the ACTION mid-happening, not characters standing around
- Include VISIBLE CONSEQUENCES (things scattered, flying, broken)
- Include character's BODY LANGUAGE
- 3-4 background objects to colour
- SUPPORTING CHARACTERS: Every time they appear, include species/size/accessories in brackets. Example: "Pip (small duck with bow tie)". NO COLOURS. Use SAME description each time.
- IMPORTANT: The brackets with character descriptions are for scene_description ONLY. In story_text, just use the character's NAME — never include the bracketed description tags in story_text. Example: scene_description says "Pip (small duck with bow tie) runs over" but story_text says "Pip ran over".
- If same location as previous episode, REPEAT key setting objects

*** CRITICAL: SCENE VARIETY RULES (NON-NEGOTIABLE) ***
Each of the 5 episodes MUST have a visually distinct composition. The scene_description is an ILLUSTRATION BRIEF — it tells the artist exactly what to draw. Be specific about:

MANDATORY CAMERA PATTERN:
- Episode 1: WIDE ESTABLISHING SHOT — show the full location. Characters are small (20-30% of frame). Lots of environment detail. This is the "setting the scene" shot.
- Episode 2: MEDIUM ACTION SHOT — characters bigger (40-50%), actively DOING something physical. A different part of the location from episode 1. Characters are IN MOTION.
- Episode 3: CLOSE-UP EMOTIONAL SHOT — character's face and upper body fill 60%+ of the frame. Minimal background. Focus on the SETBACK emotion. This should feel intimate and different from every other page.
- Episode 4: DYNAMIC ANGLE — overhead view looking DOWN, or low angle looking UP, or dramatic side angle. Characters in active motion. Different area of the setting.
- Episode 5: NEW LOCATION OR DRAMATICALLY DIFFERENT VIEW — move to a new place for resolution. If same location, show it from the OPPOSITE angle. This must feel fresh.

SCENE DESCRIPTION MUST SPECIFY THE CHARACTER'S PHYSICAL ACTION:
- BAD: "Tom is at the fairground feeling scared" (Gemini will draw Tom standing at the fairground)
- GOOD: "CLOSE-UP: Tom is crouching on the ground, knees pulled up, hands over his ears. Behind him the rollercoaster track curves overhead. His face shows fear — wide eyes, mouth open."
- BAD: "Tom tries to stop the rollercoaster" (vague)
- GOOD: "LOW ANGLE looking up: Tom is climbing onto the rollercoaster cart, one leg over the side, both hands gripping the safety bar. The track stretches upward ahead of him. Wind blows his hair back."

Every scene_description must include:
1. CAMERA ANGLE (from the mandatory pattern above)
2. CHARACTER'S EXACT PHYSICAL POSITION (crouching, climbing, running, sitting IN something, hanging from something — NOT standing)
3. What SPECIFIC part of the location they are in
4. At least 2-3 background objects unique to THIS scene (not repeated from other episodes)

LOCATION MOVEMENT: The story MUST move through at least 2-3 different specific locations across the 5 episodes. Characters should travel, chase, explore — NOT stay rooted in one spot.

In scene_description, ALWAYS specify:
1. The CAMERA ANGLE (from the mandatory pattern above)
2. The EXACT LOCATION (not just "the street" — say "outside the bakery on Maple Street" or "inside the bus on the top deck")  
3. The character's EXACT PHYSICAL ACTION (what their body is doing — climbing, crouching, riding, falling — NOT just standing)
4. Where the main character is positioned in the frame (left, right, center, foreground, background)

NARRATIVE FLOW: Each scene must feel like a CONTINUATION of the previous page. If episode 2 ended running toward the park, episode 3 should START at the park.

*** EMOTION RULES ***
- Use at LEAST 3 DIFFERENT emotions across 5 episodes
- Episodes 1-3 should ESCALATE (e.g. curious → worried → scared)
- Episode 3 MUST NOT be happy or excited
- Episode 5 should be happy, proud, or excited
- Emotions: nervous, excited, scared, determined, happy, curious, sad, proud, worried, surprised, embarrassed, panicked

*** NON-NEGOTIABLE RULES ***
1. At least 2 named supporting characters throughout
2. SETBACK on episode 3
3. Dialogue in at least 3 of 5 episodes
4. Episode 5 resolves the specific problem from episode 1
5. The feature should NOT directly fix the problem alone — a supporting character helps or the character learns to use it differently

Return ONLY valid JSON in this exact format:

{{
  "theme_name": "{theme_name}",
  "episodes": [
    {{
      "episode_num": 1,
      "title": "Episode Title",
      "scene_description": "Detailed scene for the artist...",
      "story_text": "The story text for this page...",
      "emotion": "surprised"
    }},
    {{
      "episode_num": 2,
      "title": "Episode Title",
      "scene_description": "Detailed scene...",
      "story_text": "Story text...",
      "emotion": "worried"
    }},
    {{
      "episode_num": 3,
      "title": "Episode Title",
      "scene_description": "Detailed scene...",
      "story_text": "Story text...",
      "emotion": "scared"
    }},
    {{
      "episode_num": 4,
      "title": "Episode Title",
      "scene_description": "Detailed scene...",
      "story_text": "Story text...",
      "emotion": "determined"
    }},
    {{
      "episode_num": 5,
      "title": "Episode Title",
      "scene_description": "Detailed scene...",
      "story_text": "Story text...",
      "emotion": "happy"
    }}
  ]
}}

Write the full story for {character_name} now. Return ONLY valid JSON.'''

    claude_response = claude_client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}]
    )
    
    text = claude_response.content[0].text.strip()
    
    # Remove markdown code blocks if present
    if text.startswith('```json'):
        text = text[7:]
    if text.startswith('```'):
        text = text[3:]
    if text.endswith('```'):
        text = text[:-3]
    text = text.strip()
    
    start = text.find('{')
    end = text.rfind('}') + 1
    
    if start >= 0 and end > start:
        import json
        json_str = text[start:end]
        data = json.loads(json_str)
        
        # Extract/set emotion for each episode
        def extract_emotion(text):
            text = text.lower()
            emotions = [
                ('scared', ['scared', 'frightened', 'afraid', 'terrified']),
                ('nervous', ['nervous', 'anxious', 'uneasy', 'hesitant']),
                ('excited', ['excited', 'thrilled', 'eager']),
                ('sad', ['sad', 'unhappy', 'disappointed', 'crying']),
                ('curious', ['curious', 'wondering', 'intrigued']),
                ('determined', ['determined', 'resolute', 'focused', 'brave']),
                ('surprised', ['surprised', 'amazed', 'astonished']),
                ('proud', ['proud', 'accomplished', 'triumphant']),
                ('worried', ['worried', 'concerned', 'troubled']),
                ('happy', ['happy', 'joyful', 'delighted', 'cheerful']),
            ]
            for emotion, keywords in emotions:
                if any(kw in text for kw in keywords):
                    return emotion
            return 'curious'
        
        for ep in data.get('episodes', []):
            story = ep.get('story_text', '') + ' ' + ep.get('scene_description', '')
            extracted = extract_emotion(story)
            ep['character_emotion'] = ep.get('emotion') or extracted
        
        return data
    
    raise HTTPException(status_code=500, detail='Failed to parse story response as JSON')
