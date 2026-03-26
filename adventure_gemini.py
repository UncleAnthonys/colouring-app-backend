"""
Adventure Gemini - Simplified Universal Character Reveal
Focus on: PROPORTIONS, COLORS, PIXAR FACE - in that priority order
"""

import os
print(f"[FONT-DEBUG] CWD: {os.getcwd()}")
print(f"[FONT-DEBUG] Script dir: {os.path.dirname(os.path.abspath(__file__))}")
print(f"[FONT-DEBUG] fonts/ exists: {os.path.exists('fonts/ComicNeue-Bold.ttf')}")
print(f"[FONT-DEBUG] /app/fonts/ exists: {os.path.exists('/app/fonts/ComicNeue-Bold.ttf')}")
_script_dir = os.path.dirname(os.path.abspath(__file__))
print(f"[FONT-DEBUG] script-relative exists: {os.path.exists(os.path.join(_script_dir, 'fonts', 'ComicNeue-Bold.ttf'))}")
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

    # Collapse Sonnet's sentence-per-line newlines into flowing paragraph text
    import re
    story_text = re.sub(r'\n+', ' ', story_text).strip()
    
    # Wrap and draw story text - DYNAMIC sizing with PIXEL-BASED wrapping
    text_margin = 70  # Left and right margin for comfortable reading
    available_text_height = A4_HEIGHT - current_y - 30  # Space remaining to bottom
    max_text_width = A4_WIDTH - (text_margin * 2)
    
    # Pixel-based word wrapping function
    def wrap_text_pixel(text, font, max_width):
        """Wrap text based on actual pixel width, not character count."""
        paragraphs = text.split('\n')
        all_lines = []
        for para in paragraphs:
            words = para.split()
            if not words:
                all_lines.append('')
                continue
            current_line = []
            for word in words:
                test_line = ' '.join(current_line + [word])
                tw = font.getbbox(test_line)[2] - font.getbbox(test_line)[0]
                if tw > max_width and current_line:
                    all_lines.append(' '.join(current_line))
                    current_line = [word]
                else:
                    current_line.append(word)
            if current_line:
                all_lines.append(' '.join(current_line))
        return all_lines
    
    # Try font sizes from large to small until text fits
    font_sizes = [24, 21, 19, 17, 15]
    line_spacings = [34, 30, 27, 24, 22]
    
    best_font_size = font_sizes[-1]
    best_spacing = line_spacings[-1]
    best_lines = []
    best_font = None
    
    for fs, ls in zip(font_sizes, line_spacings):
        try:
            test_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", fs)
        except:
            test_font = ImageFont.load_default()
        
        lines = wrap_text_pixel(story_text, test_font, max_text_width)
        total_height = len(lines) * ls
        
        if total_height <= available_text_height:
            best_font_size = fs
            best_spacing = ls
            best_lines = lines
            best_font = test_font
            break
    else:
        # Even smallest font doesn't fit — use smallest
        try:
            best_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_sizes[-1])
        except:
            best_font = ImageFont.load_default()
        best_lines = wrap_text_pixel(story_text, best_font, max_text_width)
    
    story_font_final = best_font
    
    # Center text block vertically in available space
    total_text_height = len(best_lines) * best_spacing
    start_y = current_y + max(0, (available_text_height - total_text_height) // 2)

    for line in best_lines:
        if start_y + best_spacing > A4_HEIGHT - 10:
            break  # Safety — never draw below page
        line_bbox = draw.textbbox((0, 0), line, font=story_font_final)
        line_width = line_bbox[2] - line_bbox[0]
        line_x = max(text_margin, (A4_WIDTH - line_width) // 2)
        draw.text((line_x, start_y), line, fill='black', font=story_font_final)
        start_y += best_spacing
    
    # Convert to base64
    buffer = io.BytesIO()
    a4_page.save(buffer, format='PNG', dpi=(150, 150))
    buffer.seek(0)
    
    return base64.b64encode(buffer.read()).decode('utf-8')






async def validate_episode_image(image_b64: str) -> dict:
    """Check a generated episode image for duplicate main characters.
    Returns {"pass": True/False, "reason": "..."} 
    Cost: ~$0.0005 per call
    """
    import google.generativeai as genai
    
    api_key = os.environ.get('GOOGLE_API_KEY') or os.environ.get('GEMINI_API_KEY')
    if not api_key:
        return {"pass": True, "reason": "No API key, skipping validation"}
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        response = model.generate_content([
            """You are a quality control checker for a children's coloring book image.

Check for ONE thing only: Is the MAIN character duplicated?

- Is the same main character (same hair, face, outfit) drawn MORE THAN ONCE in the scene?
- If there are meant to be two different main characters, do they actually look like DIFFERENT people or are they the same character drawn twice?

Supporting/background characters are fine. Only check the 1-2 largest, most prominent characters.

Answer with ONLY one word: PASS or FAIL""",
            {"mime_type": "image/png", "data": base64.b64decode(image_b64)}
        ])
        
        result = response.text.strip().upper()
        passed = "PASS" in result
        print(f"[VALIDATION] {'✅ PASS' if passed else '❌ FAIL'}: {response.text.strip()[:100]}")
        return {"pass": passed, "reason": response.text.strip()[:200]}
    except Exception as e:
        print(f"[VALIDATION] ⚠️ Error, skipping: {str(e)[:100]}")
        return {"pass": True, "reason": f"Validation error: {str(e)[:100]}"}

def create_front_cover(image_b64: str, full_title: str, character_name: str) -> str:
    """
    Overlay bubble-letter title directly onto Gemini's cover image.
    Big bold white text with black outline — reads over any illustration and is colourable!
    
    Returns: Base64 encoded PNG image with text overlaid
    """
    from PIL import Image, ImageDraw, ImageFont
    import io
    import textwrap
    
    # Decode Gemini's cover image
    img_data = base64.b64decode(image_b64)
    cover_img = Image.open(io.BytesIO(img_data)).convert('RGB')
    
    # Remove any border line Gemini may have added — paint outer 20px white
    img_w, img_h = cover_img.size
    border_kill = ImageDraw.Draw(cover_img)
    strip = 20
    border_kill.rectangle([0, 0, img_w, strip], fill='white')           # top
    border_kill.rectangle([0, img_h - strip, img_w, img_h], fill='white')  # bottom
    border_kill.rectangle([0, 0, strip, img_h], fill='white')           # left
    border_kill.rectangle([img_w - strip, 0, img_w, img_h], fill='white')  # right
    
    img_width, img_height = cover_img.size
    draw = ImageDraw.Draw(cover_img)
    
    # Load fonts
    _script_dir = os.path.dirname(os.path.abspath(__file__))
    font_candidates = [
        os.path.join(_script_dir, "fonts", "LilitaOne-Regular.ttf"),
        "/app/fonts/LilitaOne-Regular.ttf",
        "fonts/LilitaOne-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]
    
    def load_font(size):
        for fp in font_candidates:
            try:
                return ImageFont.truetype(fp, size)
            except (OSError, IOError):
                continue
        return ImageFont.load_default()
    
    # Scale font sizes relative to image — BIG and bold like a real children's book
    title_size = max(56, int(img_width * 0.09))
    subtitle_size = max(24, int(img_width * 0.035))
    
    title_font = load_font(title_size)
    subtitle_font = load_font(subtitle_size)
    
    def draw_bubble_text(draw, x, y, text, font, outline_width=5):
        """Draw text with black outline and white fill — bubble letter effect."""
        for ox in range(-outline_width, outline_width + 1):
            for oy in range(-outline_width, outline_width + 1):
                if ox * ox + oy * oy <= outline_width * outline_width:
                    draw.text((x + ox, y + oy), text, fill='black', font=font)
        draw.text((x, y), text, fill='white', font=font)
    
    # === TITLE at top — bubble text overlaid on image ===
    title_y = int(img_height * 0.07)
    wrapped_title = textwrap.fill(full_title, width=20)
    title_lines = wrapped_title.split('\n')
    
    outline_w = max(4, int(img_width * 0.007))
    
    padding = int(img_width * 0.12)  # 8% padding each side
    max_title_width = img_width - (padding * 2)
    
    for line in title_lines:
        bbox = draw.textbbox((0, 0), line, font=title_font)
        line_width = bbox[2] - bbox[0]
        line_height = bbox[3] - bbox[1]
        
        # If line is too wide, reduce font size for this cover
        actual_font = title_font
        if line_width > max_title_width:
            scale = max_title_width / line_width
            smaller_size = int(title_size * scale)
            actual_font = load_font(smaller_size)
            bbox = draw.textbbox((0, 0), line, font=actual_font)
            line_width = bbox[2] - bbox[0]
            line_height = bbox[3] - bbox[1]
        
        line_x = (img_width - line_width) // 2
        draw_bubble_text(draw, line_x, title_y, line, actual_font, outline_width=outline_w)
        title_y += line_height + int(img_height * 0.008)
    
    # === BRANDING at bottom — smaller bubble text ===
    bottom_text = "A Little Lines Story Book"
    bottom_bbox = draw.textbbox((0, 0), bottom_text, font=subtitle_font)
    bottom_width = bottom_bbox[2] - bottom_bbox[0]
    bottom_height = bottom_bbox[3] - bottom_bbox[1]
    bottom_x = (img_width - bottom_width) // 2
    bottom_y = img_height - bottom_height - int(img_height * 0.10)
    draw_bubble_text(draw, bottom_x, bottom_y, bottom_text, subtitle_font, outline_width=max(2, outline_w - 1))
    
    # Convert to base64
    buffer = io.BytesIO()
    cover_img.save(buffer, format='PNG')
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

===== BACKGROUND (CRITICAL!) =====
- COMPLETELY REMOVE the original photo background — no trace of any real-world environment (no kitchens, no gardens, no bedrooms, no walls, no furniture)
- REPLACE with a vibrant ILLUSTRATED celebration scene: bright colorful confetti, streamers, sparkles, and magical particles
- The background must be ILLUSTRATED/ANIMATED style — NOT a photograph, NOT a real room with confetti added on top
- Think: the character reveal moment from a Pixar movie trailer — pure animated magic

===== REQUIREMENTS =====
- Portrait orientation - show FULL figure
- Character should be STANDING/POSED in a confident, joyful pose
- Character looks ALIVE and full of personality — like the hero of their own movie
- The character must look like a FRAME FROM A PIXAR MOVIE — not a photo with a filter, not a 3D render of a doll, not a craft project
- ABSOLUTELY NO WATERMARKS, NO SIGNATURES, NO TEXT, NO LOGOS anywhere in the image
- NO TEXT anywhere on image

IMPORTANT: The output should make a child say "WOW that's me as a CARTOON!" — not "that's just my photo with a weird filter." Go BIG on the cartoon stylization. The character must be COMPLETELY RE-RENDERED as an animated character — not the original photo modified.'''
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

**RULE 3 - PIXAR MOVIE STILL QUALITY:**
- This should look like a CHARACTER from an actual Pixar film — same rendering quality, same level of detail and life
- Eyes: Big expressive eyes with GLOSSY IRISES, multiple SPECULAR CATCHLIGHTS, visible light reflections, and depth — even on angry or scary characters
- Skin: Warm SUBSURFACE SCATTERING (light glowing through skin like real Pixar characters)
- Lighting: Cinematic THREE-POINT LIGHTING with warm key light and cool rim light to make the character POP
- Surfaces: Smooth appealing 3D with proper material definition — NOT a toy, NOT a figurine, NOT felt, NOT knitted, NOT woollen, NOT craft, NOT stop-motion, NOT claymation — a LIVING animated movie character
- This is a movie character with LIFE and SOUL, not a 3D render of a doll

===== BACKGROUND (CRITICAL!) =====
- COMPLETELY REMOVE any trace of the original drawing's background — no paper, no table, no real-world environment
- REPLACE with a vibrant ILLUSTRATED celebration scene: bright colorful confetti, streamers, sparkles, and magical particles
- The background must be fully ANIMATED style matching the Pixar character — NOT a photograph

===== RENDERING QUALITY (CRITICAL!) =====
- The character must look like it belongs in an ACTUAL PIXAR FILM — Monsters Inc, Inside Out, Toy Story quality
- Smooth appealing 3D surfaces with proper material definition
- NOT felt, NOT woolly, NOT fuzzy texture, NOT craft-like, NOT stop-motion, NOT claymation
- Even if the original drawing looks like a soft toy, render it as a SMOOTH 3D ANIMATED character with proper skin/surface materials
- Pixar characters have SMOOTH CLEAN SURFACES with subsurface scattering — not fabric textures

===== REQUIREMENTS =====
- Portrait orientation - show FULL figure
- ABSOLUTELY NO WATERMARKS, NO SIGNATURES, NO TEXT, NO LOGOS anywhere in the image
- This is original art - do not copy or include any watermarks from any source
- NO TEXT anywhere on image
- Character looks ALIVE and full of personality — MATCH the expression from the drawing (if angry, be angry. if happy, be happy. if scared, be scared)

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
        full_prompt = f'''[STRICT CONTROLS]: Monochrome black and white 1-bit line art only.
[VISUAL DOMAIN]: Technical Vector Graphic / Die-cut sticker template.
[COLOR CONSTRAINTS]: Strictly binary 1-bit color palette. Output must contain #000000 (Black) and #FFFFFF (White) ONLY. Any other color or shade of grey is a FAILURE and the image must be regenerated.

[STYLE]: Clean, bold, uniform-weight black outlines. Pure white empty interiors. Thick, heavy marker outlines. Bold 5pt vector strokes.

[MANDATORY EXCLUSIONS]: No gradients. No volume. No depth. No shadows. No grayscale. No shading. No color leaks. No 3D volume. Paper-white fills only. No grey fills on clothing. No solid black fills on clothing or hair. ALL markings, spots, stripes, patterns, masks, and eye patches must be HOLLOW OUTLINES ONLY.

[REFERENCE USE]: Use the attached image ONLY for the character's shape and silhouette. Completely ignore all color, value, and shading data from the reference. DO NOT use the colors or lighting from the reference.

Create a professional kids' COLORING BOOK PAGE — pure BLACK LINES on WHITE PAPER.

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

[REFERENCE USE]: Use the attached reference image(s) ONLY for the character's shape and silhouette. Completely ignore all color, value, and shading data. DO NOT use the colors or lighting from the reference. DO NOT copy the POSE or COMPOSITION from the reference — only copy the character's APPEARANCE (body shape, features, clothing style).

CHARACTER: {character_name}
Use the reference image for SHAPE AND FORM ONLY — completely ignore all colors:
- Body shape, proportions, and size
- Distinctive features (number of eyes, horns, fur texture, etc.)
- Clothing style and accessories (but NOT their colors)

⚠️ CRITICAL — COUNT AND MATCH EVERY FEATURE FROM THE REFERENCE IMAGE EXACTLY:
- Count the EXACT number of LEGS in the reference. If there are 3 legs, draw 3 legs. Not 2. Not 4. Exactly 3.
- Count the EXACT number of ARMS in the reference. Match it precisely.
- Count the EXACT number of EYES in the reference. Match it precisely.
- Count the EXACT number of ANTENNAE in the reference. Match it precisely.
- Count the EXACT number of FINGERS on each hand. Match it precisely on EVERY page.
- Count ANY other distinctive features (horns, teeth, spots, tails). Match the count EVERY time.
- These counts must be IDENTICAL on EVERY page of the storybook. A character with 3 legs on page 1 MUST have 3 legs on page 2, 3, 4, and 5.
- Getting a feature count wrong RUINS the storybook for the child who drew this character. It matters.

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

🚨 ENVIRONMENT SURFACES — COMMON COLOUR LEAK 🚨
Gemini: you keep filling environment surfaces with their "real" colours. STOP. This is a COLORING BOOK — children add the colours themselves.
- GRASS and FIELDS: WHITE with blade/texture lines. NOT green. Never green.
- TENNIS COURTS / SPORTS FIELDS: WHITE with court line markings. NOT green. NOT any colour.
- SKY: WHITE. Not blue. Not any tint. Just white with maybe cloud outlines.
- WATER / OCEAN / RIVERS / POOLS: WHITE with ripple lines. NOT blue.
- SAND / BEACHES: WHITE with texture dots/lines. NOT yellow or beige.
- ROADS / PATHS: WHITE with edge lines. NOT grey.
- TREE TRUNKS: WHITE with bark texture lines. NOT brown.
- LEAVES / FOLIAGE: WHITE outlines of leaf shapes. NOT green.
- FLOWERS: WHITE with petal outlines. NOT any colour.
- MUD / DIRT: WHITE with speckle lines. NOT brown.
- SUNSET / SUNRISE: WHITE. NOT orange or pink.
THE CHILD COLOURS EVERYTHING. You draw ONLY black outlines on white paper.

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
5. All enclosed areas must be HOLLOW - empty white space inside black outlines for children to color in
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


async def generate_personalized_stories(character_name: str, character_description: str, age_level: str = "age_6", writing_style: str = None, life_lesson: str = None, custom_theme: str = None, second_character_name: str = None, second_character_description: str = None) -> dict:
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
- Rhythmic text works well but DO NOT rhyme unless the user specifically chose "Rhyming" style
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

CRITICAL: DO NOT use the same story as the examples above. Apply these principles to create something ORIGINAL.
Create completely original scenarios based on the character.

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
- Aim for 15-20 words per episode. Short and punchy but every sentence must have personality.
- At least one sound effect or exclamation per episode
- Final episode: shortest of all (under 12 words)
- If you find yourself writing more than 2 sentences, you are writing TOO MUCH for a toddler
- Think: "Hop hop hop! Oh no — SPLAT! Sam fell in the mud." = PERFECT length
""",

        "age_4": """
AGE GROUP: 4 YEARS OLD

*** WRITING STYLE ***
- DO NOT rhyme unless the user specifically chose "Rhyming" style
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
- 2-3 sentences per episode (40-60 words). Every sentence must EARN its place — physical comedy, funny dialogue, or specific chaos.
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
The weirder and more creative the use, the better the story. Find an unexpected angle.

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
- 2-3 sentences per episode (30-50 words, aim for 60-80 words max)
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
- Episode 5: Climax and resolution — but NOT the obvious solution. The ending must surprise the reader while still making sense. A specific detail from episode 1 must reappear in a new light. The final line lands with a laugh, a warm punch, or an unexpected image — NEVER a lesson or summary statement like "[name] learned that..." or "Sometimes all you need is..."

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
- 3-4 sentences per episode (40-60 words, aim for 80-110 words max)
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
- Episode 5: Climactic resolution with a genuine twist — not the solution the reader predicted. The ending reframes something specific from episode 1 in a new light. The final line must be specific to THIS character and THIS story — a laugh, an image, or an emotional beat. NEVER a moral lesson, NEVER a summary statement like "[name] learned that..." or "And from that day on..."

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
- 3-4 sentences per episode (50-70 words, aim for 100-130 words max)
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
    age_level = "age_3" if age_level == "under_3" else age_level
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
        
        
        # Build optional style/theme override block
        # Build optional style/theme override block
        style_theme_block = ""
        if writing_style:
            style_theme_block += f"""
*** WRITING STYLE OVERRIDE ***
The user has chosen a specific writing style: "{writing_style}"
Adapt ALL story text to match this style:
- If "Rhyming": Every episode's story_text should rhyme. Use couplets or AABB rhyme schemes. Make it flow like a poem.
- If "Gentle": Soft, calming language. Quiet moments of wonder. Cozy settings. Warm resolutions.
- If "Silly": Over-the-top nonsense, made-up words, ridiculous situations, characters being goofy.
- If "Repetition": Use a repeating phrase or pattern that builds across episodes — like "He tried and he tried but it STILL wouldn't work!" The phrase should evolve slightly each time, building anticipation. Think We're Going on a Bear Hunt or The Gruffalo. Kids love predicting what comes next.
- If "Call and Response": Write with questions and answers that a parent and child can read together — "Did Simon give up? NO HE DIDN'T! Did Simon run away? NO HE DIDN'T! Did Simon save the day? YES HE DID!" Each episode should have at least one call-and-response moment.
- If "Suspenseful": End each episode (except the last) on a mini cliffhanger. Use dramatic pauses, "And then...", "But what they didn't know was...", "Behind the door was something NOBODY expected." Build tension across episodes.
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
- If "Patience": The character learns that rushing makes things worse and that waiting, slowing down, or taking their time leads to better results.
- If "Teamwork": The character tries to do everything alone and struggles, then discovers that working together with others achieves much more.
- If "Trying new things": The character is reluctant or scared to try something unfamiliar, but discovers something wonderful when they do.
- If "Saying sorry": The character makes a mistake that hurts someone, struggles to apologise, but learns that saying sorry and making amends fixes things.
- If "Listening to others": The character ignores advice or doesn't listen, things go wrong, then they learn that hearing other perspectives helps everyone.
- If "Gratitude": The character takes something for granted, loses it or nearly loses it, and learns to appreciate what they have.
- For any other lesson: interpret it naturally and weave it throughout the story arc.
IMPORTANT: The lesson should emerge THROUGH THE STORY, not through lecturing or moralising. Show don't tell. The character EXPERIENCES the lesson through what happens to them.
"""
        if custom_theme:
            style_theme_block += f"""
*** CUSTOM THEME FROM PARENT ***
The parent has written a personal note about what this story should include: "{custom_theme}"
This could be a birthday ("It's Tom's 5th birthday!"), a milestone ("Tom just learned to ride a bike"), a new experience ("Tom starts school on Monday"), or anything personal.
ALL 3 story pitches must weave this personal detail naturally into the story:
- It should feel like the story was written specifically for THIS moment in the child's life
- The custom theme should be a central part of the plot, not just a passing mention
- Combine it creatively with the character's features — e.g. if the theme is "birthday" and the character has big boots, maybe the boots are a birthday present, or they bounce to their birthday party
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

⚠️ GENDER: Do NOT assume the character's gender from their name. Use the character's NAME instead of pronouns wherever possible. If you must use pronouns, use "they/them" unless the character description explicitly states gender.

⚠️ ABSOLUTELY NO FAMILY MEMBERS OR RELATIVES IN ANY STORY:
- No grandparents, grandmas, grandads, nans, grandpas
- No cousins, aunts, uncles, siblings, brothers, sisters, mums, dads, parents
- Family members may be deceased or estranged in real life — including them can cause genuine distress
- Use FRIENDS, CLASSMATES, NEIGHBOURS, or invented named characters instead
- This rule is absolute, no exceptions

{second_char_block}

STEP 1 - IDENTIFY THE MOST UNUSUAL FEATURES (in order of priority):
Look at the character description. Find the WEIRDEST, most UNUSUAL things:

⚠️ CRITICAL — HUMAN/PERSON CHARACTERS:
If the character is a REAL CHILD, PERSON, or HUMAN (not a monster, animal, toy, or drawing):

PHYSICAL APPEARANCE CAN AND SHOULD BE USED — but ONLY as a SUPERPOWER or something WONDERFUL:
- Glasses → can see things others can't, spots the tiny clue nobody else noticed, lenses catch light in a magical way
- Curly hair → catches the wind like a sail, collects magical seeds, springs back from anything
- Freckles → glow under moonlight, form a map, each one marks a different adventure
- Braces → pick up radio signals, let them talk to robots, make the most amazing smile that unlocks something
- ANY physical feature → find the magical version of it. What superpower does it secretly grant?
- RULE: the physical feature must make the child feel AMAZING about it after reading. A child with glasses should finish the story wanting to wear them MORE. A child with curly hair should feel their hair is the coolest thing about them.
- NEVER use a physical feature as something to be fixed, hidden, overcome, or apologised for. It is always already perfect and powerful.

OBJECTS AND ACTIVITIES ARE ALSO BRILLIANT — use these if present:
- If the child is holding, riding, or using something (ukulele, bike, scooter, tennis racket, paintbrush, magnifying glass, hula hoop, skateboard, football, kite, fishing rod, etc.) — build the ENTIRE story around this. A child with a ukulele = music-themed adventure where strumming solves problems. A child on a bike = an epic ride through magical places.
- Clothing and accessories: a bow tie, cardigan, favourite hat, backpack, special shoes — all great story elements
- Poses and habits: always has hands in pockets, never takes off their hat, carries a lucky charm

PRIORITY ORDER FOR HUMAN CHARACTERS:
1. Objects being held or used (most specific, most personal)
2. Distinctive clothing or accessories
3. Physical features — used as superpowers only, always in a positive, magical way
4. Personality trait — if truly nothing else is available

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

PRIORITY 3 - Distinctive features treated as SUPERPOWERS:
- Every feature has a magical version. Your job is to find it.
- Big ears → hears things from miles away, picks up magical frequencies, fans away danger
- Long nose → sniffs out treasure, detects lies, reaches around corners
- Tiny size → fits through gaps nobody else can, sees the world differently, invisible to danger
- Unusual texture → sticks to walls, repels water, conducts electricity
- Distinctive markings → form a map, glow at certain times, each one means something
- Think: "what is the MAGICAL VERSION of this feature?" — then build the story around that

PRIORITY 4 - Colors and patterns (only use if nothing else):
- Only use color if there is truly nothing more unusual about the character

DO NOT make stories about:
- "camouflage" or "blending in" (boring!)
- "colors fading" or "restoring colors" (overdone!)
- Body shape unless it is truly unusual

⚠️ ABSOLUTELY NO FAMILY MEMBERS OR RELATIVES IN ANY STORY:
- No grandparents, grandmas, grandads, nans, grandpas
- No cousins, aunts, uncles, siblings, brothers, sisters, mums, dads, parents
- Family members may be deceased or estranged in real life — including them can cause genuine distress
- Use FRIENDS, CLASSMATES, NEIGHBOURS, or invented named characters instead
- This rule is absolute and applies to every single story, no exceptions

THE GOLDEN RULE FOR ALL FEATURES:
Every story must pass this test: "Could this exact story exist with a different character?"
If yes — the story is not personalised enough. Keep rewriting until the answer is NO.
The character's specific feature must be the ONLY reason the story resolves the way it does.

STEP 2 - PICK AND ADAPT A SCENARIO

For each of your 3 themes:
1. Pick a scenario that the character's unique feature would be PERFECT for
2. ADAPT it — don't copy it word-for-word. Change details, combine ideas, make it your own
3. The character's feature should be essential to the story but in a SURPRISING way

The scenario is the STARTING POINT. The character's feature determines HOW they deal with it.
Example: "A duplicating machine made 50 copies of the headteacher" + a character with many eyes = each eye can track a different copy, but they keep getting confused when copies swap clothes. Eventually they spot the real one because only the original has a coffee stain on their tie.

Each theme MUST use a DIFFERENT unique feature as the main plot device.

*** CRITICAL: EVERY THEME MUST HAVE A CLEAR "WANT" ***
Before writing each theme, define:
- WANT: What does the character specifically want, and WHY? (NOT vague like "help others" or "explore" — SPECIFIC like "rescue the stuck kitten before the tide comes in" or "find their lost friend who wandered into the spooky forest" or "win the sandcastle competition to prove the grumpy judge wrong"). The WHY is essential — a 5-year-old listening should understand what happened to make the character want this. If the character is apologising, what did they DO? If they're searching, what did they LOSE and how? If they're helping, why does it MATTER?
- OBSTACLE: How does their special feature make this HARDER? (The feature should cause funny, specific problems)
- TWIST: How does the feature eventually help in an UNEXPECTED way? (Not the obvious use)

Stories without a clear WANT are boring. "Character walks around and their feature causes random chaos" is NOT a story.
"Character desperately wants X but their feature keeps causing Y" IS a story.
NEVER include specific body part numbers in theme names.

*** CREATING ORIGINAL STORIES ***

DO NOT reuse common children's story tropes like runaway cakes, shrinking people, or broken machines unless they genuinely fit. 
Think CREATIVELY and SPECIFICALLY about THIS character. What situations would be uniquely funny, challenging, or meaningful for a character with THESE specific features?

Consider scenarios from many different worlds:
- Everyday situations gone wrong (school, home, park, shops, holidays)
- Jobs and workplaces the character stumbles into (restaurant, hospital, space station, farm, theatre)
- Competitions and events (talent show, sports day, cooking contest, science fair)
- Adventures in unexpected places (underground, underwater, tiny world, upside-down town)
- Helping someone with a specific problem (lost pet, broken thing, missing person, scared friend)
- Celebrations and milestones (birthday, first day, moving house, new sibling)

For EACH of the 3 themes:
1. Pick a DIFFERENT character feature
2. Invent a SPECIFIC, ORIGINAL scenario where that feature causes hilarious problems
3. Make sure the want, obstacle, and twist are tightly connected to the character's actual features
4. Each theme should feel completely different from the others — different setting, different tone, different type of story

{age_guide}

CRITICAL: Follow the age guidelines above exactly for sentence length, vocabulary, and complexity.

*** FORMAT ***

For each theme provide:
1. Theme name (fun, age-appropriate, MAX 6 words, MAX 35 characters)
2. Theme description (1 sentence)
3. Theme blurb (ONE short punchy sentence, MAX 15 words. This is the most important line — it must make a parent gasp and think "this was written ONLY for my child." Rules:
- MUST include {character_name}'s name
- MUST name the feature DIRECTLY — glasses, curls, jumper, tail, hat, whatever it is. Naming it IS what makes it feel personal.
- Make the feature sound MAGICAL or EXCITING — not clinical or boring
- The sentence should make the reader immediately curious about the story
- NEVER be vague — vague blurbs feel generic and could be about anyone
- NEVER use the formula "good thing [character] knows how to..." or "but will it be enough?" — these are weak and lazy
- NEVER end with a generic personality trait like "never gives up" or "always finds a way"
- E.g. if feature is "glasses": "Our Gav's glasses can see through walls — but what's hiding on the other side?"
- E.g. if feature is "curly hair": "Our Gav's curls caught something in the wind that nobody else could feel — and now everything depends on it"
- E.g. if feature is "ukulele": "One song from Our Gav's ukulele could save the whole town — if only the strings would stop tangling"
- E.g. if feature is "Illinois jumper": "The answer was written on Our Gav's jumper all along — nobody thought to look until now"
- The blurb should make a parent think: "my child is going to LOVE seeing their [feature] do that")
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
4. ENDING: Episode 5 resolves the specific problem from episode 1. No generic happy endings. The resolution must be SURPRISING — not the obvious solution the reader predicted. The final line must be specific to THIS story and THIS character, never a moral lesson or summary statement.
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
      "theme_blurb": "Example Monster needs to spot every floating student before they escape — good thing nothing escapes that gaze!",
      "feature_used": "big eye",
      "want": "catch all the floating students before they drift out the windows — the gravity experiment was Example Monster's idea so it's their responsibility to fix it",
      "obstacle": "the eye keeps getting distracted tracking too many floating objects at once",
      "twist": "uses the eye as a magnifying glass to focus sunlight and melt the anti-gravity device"
    }},
    {{
      "theme_id": "the_missing_socks_mystery",
      "theme_name": "The Missing Socks Mystery",
      "theme_description": "Every sock in town has vanished overnight and Example Monster must follow the trail of woolly clues to find the thief.",
      "theme_blurb": "Example Monster must find the stolen socks — but can anyone reach into the thief's tiny hiding spot?",
      "feature_used": "long arms",
      "want": "find who stole all the socks before the big football match — Example Monster promised the team they'd solve it",
      "obstacle": "long arms keep accidentally knocking over clues and evidence",
      "twist": "uses arms to reach into the tiny mouse hole where the sock-hoarding mice live"
    }},
    {{
      "theme_id": "the_worlds_worst_haircut",
      "theme_name": "The World's Worst Haircut",
      "theme_description": "The new barber is a robot who has gone haywire, giving everyone ridiculous haircuts, and Example Monster must stop it.",
      "theme_blurb": "The robot barber is out of control — but Example Monster might be the one thing its scissors can't handle!",
      "feature_used": "spiky head",
      "want": "stop the robot barber before it reaches the school photo — Example Monster accidentally turned it on by pressing the wrong button",
      "obstacle": "the robot keeps trying to cut the character's spikes thinking they're messy hair",
      "twist": "the spikes jam the robot's scissors, causing it to short-circuit and reset"
    }}
  ]
}}

⚠️ CRITICAL: OBSTACLE and TWIST must form ONE coherent cause-and-effect chain.
The feature creates ONE specific problem (the obstacle). The twist must solve THAT EXACT problem — not a different one.
- If the obstacle is "the coat knocks walls down," the twist must be about how the coat STOPS knocking walls down or how the knocking becomes useful
- NEVER introduce a second unrelated problem in the twist
- Test: read the obstacle, then read the twist. Does the twist DIRECTLY fix the obstacle? If not, rewrite.
- BAD: obstacle="coat is too bulky to move fast" → twist="coat blocks the dog" (these are two different problems)
- GOOD: obstacle="coat is too bulky to stack snow blocks" → twist="the puffy coat packs snow tighter when they hug the blocks, making super-strong walls"

*** BANNED STORY PATTERNS — THESE WILL BE REJECTED ***
- "Runaway" anything (runaway cake, runaway pancake, runaway cart, runaway balloon, runaway pet, runaway anything)
- Hair getting caught/tangled in things
- Carrying a tray/plate and spilling it
- Chasing something that rolled/bounced/flew away
- A bake sale gone wrong
- Paint/ink/colour splashing everywhere
- Something stuck in a tree
If your theme matches ANY of these patterns, DELETE IT and write something original.

*** THE 3 THEMES MUST BE IN 3 DIFFERENT WORLDS ***
Theme 1 must be set in an EVERYDAY location (school, park, shops, home, neighbourhood)
Theme 2 must be set in an UNUSUAL or FANTASTICAL location — examples include underwater city, inside a volcano, shrunk to ant-size, dinosaur era, frozen planet, inside a painting, a world made of music, a floating market. NEVER default to clouds or sky kingdoms — pick something surprising and original each time
Theme 3 must involve a SPECIFIC JOB, EVENT, or MISSION (detective mystery, cooking contest, sports day, rescue mission, science fair, treasure hunt, talent show audition)
No two themes can share the same type of setting, premise, or story structure.

*** CONCEPT SIMPLICITY BY AGE — THIS OVERRIDES EVERYTHING ABOVE FOR YOUNG AGES ***

FOR AGES UNDER_3 AND AGE_3 (toddlers):
🚨 SIMPLE CONCEPTS ONLY. A toddler cannot understand abstract worlds, magic systems, or multi-step logic.

WHAT A TODDLER CAN UNDERSTAND:
- Big thing in small space (or small thing in big space)
- Something keeps falling down / running away / getting lost
- Trying to reach something that's too high / too far
- Making a mess and trying to clean it up
- An animal that makes a funny noise
- Something that won't stop bouncing / rolling / growing
- Hiding and finding (peek-a-boo logic)
- Trying to give someone something but it keeps going wrong

WHAT A TODDLER CANNOT UNDERSTAND:
- Magic kingdoms, enchanted worlds, alternate dimensions
- "Hair as a danger warning system" or any feature-as-signal concept
- Characters with abstract motivations ("save the kingdom", "restore the balance")
- Multi-step cause-and-effect chains (A causes B which triggers C)
- Named royal characters (queens, kings) in fantasy settings
- Any concept that requires EXPLAINING to a toddler before they can follow the story
- Recipes, potions, spells, prophecies, missions

TEST: Describe the story concept in ONE sentence using only words a 3-year-old knows. If you can't, the concept is too complex.
- GOOD: "Dog tries to catch a ball but it keeps bouncing away" ✅
- GOOD: "Monster is too loud and scares all the birds away" ✅
- GOOD: "Cat tries to fit in a box but the box is too small" ✅
- BAD: "Dog enters a bubble kingdom where ears create ripples that pop the recipe bubble" ❌
- BAD: "Character's hair bounces as a warning signal in a glowing mushroom cave" ❌

FOR THIS AGE, OVERRIDE THE "3 DIFFERENT WORLDS" RULE ABOVE:
- Theme 1: EVERYDAY location (home, park, garden, shops, bath time, bed time, meal time)
- Theme 2: SLIGHTLY magical version of an everyday location (the park at night, a puddle that's deeper than expected, a cupboard that's bigger inside, a sandpit with something buried in it) — NOT a fantasy kingdom
- Theme 3: A simple event or activity (bath time, dinner time, bedtime, a walk, a picnic, a trip to the shops, playing in the garden, going to the playground)

FOR AGE_4:
Concepts can be slightly more complex but must still pass the "one sentence" test.
Fantasy locations are OK but must be VISUALLY simple and immediately understandable:
- GOOD: "Shrunk to ant-size in the garden" (kid can picture this instantly)
- GOOD: "Everything in the kitchen comes alive at night" (simple, visual)
- BAD: "A kingdom where everything is made of bubbles and there's a recipe bubble that holds the realm together" (too many abstract concepts stacked)
The WANT must be something a 4-year-old experiences: wanting a toy, wanting to win, wanting to help a friend, wanting to fix something they broke, wanting to not get in trouble.

*** VISUAL VARIETY — THIS IS A COLOURING BOOK ***

We are a COLOURING PAGE business. A child colours each page. If multiple pages show the same location from the same angle with the same objects, the child is colouring the same picture repeatedly. That is a bad experience.

RULE: No more than 2 out of 5 episodes should share the same location. The story should move through at least 2-3 visually distinct settings.
- Design the WANT/OBSTACLE/TWIST so the plot naturally takes characters to different places
- If a story must stay in one broad area, make sure each episode shows a distinctly different PART of that area with different objects and surroundings
- Every page a child colours should feel like a NEW picture, not a repeat of the last one

*** NUMBERS AND COUNTS — GET THEM RIGHT ***
When mentioning a character's features in theme names, blurbs, or descriptions:
- READ the character description carefully for EXACT counts (how many legs, arms, eyes, fingers, etc.)
- NEVER guess or round numbers. If the description says 3 legs, it is 3 legs — not 4, not "several"
- NEVER claim a feature can do something that requires a specific number unless you've checked the actual count
- If you say "exactly the right number of fingers" — you better have counted them from the description
- Getting a number wrong is WORSE than not mentioning the number at all
- When in doubt, describe the feature WITHOUT a number: "Tim's sturdy legs" not "Tim's four sturdy legs"

*** FINAL QUALITY CHECK BEFORE GENERATING ***
For each theme, ask yourself:
1. "Would a parent read this blurb and think 'wow, this is clever and unique to my child'?" — if the answer is "this could be about any character", throw it away and start again.
2. "Does the want/obstacle/twist chain make LOGICAL sense?" — read them as one sentence: "[character] wants [want] but [obstacle] until [twist]". If it sounds forced, contrived, or silly in a bad way, rewrite it.
3. "Is this story ACTUALLY interesting?" — would a real children's book author be proud of this idea, or is it lazy filler? Be honest. If a 5-year-old would say "that's boring" after hearing the premise, it IS boring.

NOW generate 3 theme PITCHES for {character_name}. Each theme must use a DIFFERENT character feature. Include theme_id, theme_name, theme_description, theme_blurb, feature_used, want, obstacle, and twist. Do NOT generate full episodes — just the pitches. Return ONLY the JSON, no other text.'''
        
        claude_response = claude_client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2000,
            system="You are the most imaginative children's story writer alive. You NEVER write boring, predictable stories. You HATE clichés. Every story idea you create should make someone say 'I've never heard that before!' Think like Roald Dahl — weird, surprising, darkly funny, completely original. If an idea feels safe or obvious, throw it away immediately. You would rather write something bizarre and memorable than something safe and forgettable.",
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
            
            # Ensure every theme has a blurb — fallback to description if missing
            if "themes" in data:
                for theme in data["themes"]:
                    if not theme.get("theme_blurb"):
                        theme["theme_blurb"] = theme.get("theme_description", "A brand new adventure awaits!")
            
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
    custom_theme: str = None,
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
        "age_2": """AGE UNDER 3: Aim for 15-20 words per episode — keep it very short. A parent reads this to a toddler. 1-2 very short sentences. Sound effects and rhythm are essential. Every word must be simple enough for a toddler to understand. Example quality: 'SPLAT! Oh no — Sam fell in the mud! Silly Sam!'""",
        "age_3": """AGE 3: Aim for 20-35 words per episode. A parent reads this aloud — short and punchy but with PERSONALITY. Use repetitive phrases, sound effects, dialogue, and rhythm. 2-3 short sentences. The story must make sense to a 3-year-old — simple cause and effect, no abstract concepts. Example quality: 'TOOT went the trumpet! The dog ran away — ZOOM! "Come back!" said Dom. But the dog was GONE.'""",
        "age_4": """AGE 4: Aim for 40-60 words per episode. Parent reads aloud. Sound effects, dialogue, fun vocabulary, and clear emotions. 2-3 sentences that feel like a REAL story — not captions. Every sentence should have personality, physical comedy, or a funny detail. Familiar settings with one magical or silly element. The text should reward re-reading — parents should enjoy reading it too.""",
        "age_5": """AGE 5: Aim for 60-80 words per episode. Natural storytelling voice. Fun words: "super-duper", "ginormous", "absolutely bonkers". Sound effects. Dialogue in at least 3 of 5 episodes. At least one genuinely funny moment. Mix of narration and character voices. Parent reads aloud but child follows along.""",
        "age_6": """AGE 6: Aim for 80-110 words per episode. Richer vocabulary. Subplots with supporting characters. Emotional complexity. Humor through situation and character. Dialogue-driven storytelling. Child starting to read along.""",
        "age_7": """AGE 7: Aim for 100-130 words per episode. More sophisticated plots. Character development. Themes of friendship, perseverance. Multiple supporting characters with distinct personalities. Child reads with some help.""",
        "age_8": """AGE 8: Aim for 120-150 words per episode. Complex narrative structure. Red herrings, plot twists. Deeper emotional arcs. Witty dialogue. Child reads independently.""",
        "age_9": """AGE 9: Aim for 130-160 words per episode. Sophisticated storytelling. Multiple storylines. Nuanced characters. Themes of identity and belonging. Independent reader.""",
        "age_10": """AGE 10+: Aim for 140-180 words per episode. Near-novel quality. Complex themes. Rich descriptions. Layered humor. Character growth across episodes. Confident independent reader.""",
    }
    
    age_level = "age_3" if age_level == "under_3" else age_level
    age_guide = age_guidelines.get(age_level, age_guidelines["age_5"])
    
    # Reinforce writing style within the age guide so it doesn't get overridden
    if writing_style:
        age_guide += f"""
⚠️ STYLE REMINDER: The writing style "{writing_style}" MUST be applied to ALL story_text at this age level. The age guide above tells you HOW MUCH to write and what vocabulary to use — the writing style tells you HOW it should sound. Both apply simultaneously. Do NOT drop the style to simplify for the age."""
        if writing_style == "Rhyming":
            age_guide += """
⚠️ RHYMING IS NON-NEGOTIABLE: Every episode MUST contain at least one rhyming couplet. Simple nursery-rhyme rhymes are PERFECT for young ages. Example for age 3: "The ball rolled IN with a PLOP and a PLIP! Pip started crying — 'My ball took a trip!' Incy looked at the bush, all prickly and mean. The sharpest and thorniest bush they had seen!" — This is simple vocabulary AND it rhymes. BOTH ARE POSSIBLE AT EVERY AGE."""
    style_theme_block = ""
    if writing_style:
        style_descriptions = {
            "Rhyming": """Every episode MUST rhyme in couplets (AABB pattern). The rhythm and rhyme should feel NATURAL, like a real children's book poet wrote it — not forced or awkward.
  USE THESE TECHNIQUES:
  * Consistent meter: Each line should have a similar beat/syllable count. Read it aloud — does it bounce? If not, rewrite.
  * Natural word order: "The cake fell SPLAT upon the floor" NOT "Upon the floor the cake did fall" — don't twist sentences just to make them rhyme
  * Strong rhymes: Use real rhymes (cat/hat, blue/flew), not near-rhymes (gone/room) or forced ones
  * Sound effects still work: "CRASH went the plates, BANG went the door — now there was cake upon the floor!"
  * Vary line length for drama: Short lines for impact ("And then... SPLAT!"), longer lines for storytelling
  * Dialogue can break the rhyme scheme briefly — a character speaking doesn't need to rhyme
  * DO NOT sacrifice story quality for rhyme. If you can't make a plot point rhyme naturally, use a short prose bridge and resume rhyming
  * Example quality: "Mr Oink marched down the street, with muddy prints on both his feet. He knocked on doors, he rang each bell — but everyone just ran pell-mell!" """,
            "Gentle": """This story should feel like a warm hug. Soft, calming, cozy — a bedtime story that leaves the child feeling safe and happy.
  USE THESE TECHNIQUES:
  * Soft sensory language: "The warm breeze whispered through the leaves", "Soft golden light danced on the water"
  * Slow pacing: Let moments breathe. Don't rush from one event to the next. Describe the quiet details.
  * Cozy settings: Warm kitchens, soft blankets, gentle rain outside a window, a garden on a still afternoon
  * Emotions described gently: "A small, wobbly feeling grew in Mr Oink's tummy" rather than "Mr Oink was scared"
  * Nature and seasons: Falling leaves, snow settling, flowers opening, stars appearing
  * The setback should be quiet disappointment, not chaos: Something doesn't work, something goes missing, a friend is sad
  * Resolution through kindness, patience, or quiet understanding — not through big dramatic action
  * Repetitive soothing phrases: "And everything was just right" or "Soft and warm and still"
  * Example quality: "The last leaf floated down, slow and easy, and landed right on Mr Oink's nose. He blinked. Then he smiled — just a little." """,
            "Silly": """This story should be ABSURD. Over-the-top, ridiculous, chaotic, and gleefully nonsensical. The kind of story where kids are shrieking with laughter.
  USE THESE TECHNIQUES:
  * Made-up words: "flibbertigibbet", "splonktacular", "wobbledy-bonk" — invent silly words and use them confidently
  * Ridiculous escalation: Things don't just go wrong, they go IMPOSSIBLY wrong. One sandwich becomes a hundred. A small puddle becomes a lake. A tiny noise becomes an earthquake.
  * Absurd characters: Supporting characters with ridiculous traits — a fish who's afraid of water, a bird who can't remember how to fly, a chef who only cooks invisible food
  * Physical slapstick in the text: "BONK! Right on the head. SPLAT! Right in the face. WHOMP! Right on the bottom."
  * Breaking expectations: Set up something serious, then make it completely silly. "The king stood up. He cleared his throat. He opened his mouth and said... 'BAAAA!' He was actually a sheep."
  * Character reactions should be exaggerated: Eyes popping, jaws dropping, spinning around in circles
  * NEVER explain the joke. Let the absurdity speak for itself.
  * Example quality: "The cake didn't just fall. It BOUNCED. Off the table, off the cat, off the ceiling, and — SPLODGE — right onto the mayor's hat. 'Delicious hat,' said the mayor." """,
            "Repetition": """Use a repeating phrase or pattern that builds across ALL 5 episodes. The phrase should evolve slightly each time, getting bigger or changing meaning. Think "We're Going on a Bear Hunt" or "Brown Bear, Brown Bear."
  USE THESE TECHNIQUES:
  * ONE core phrase that appears in EVERY episode — not a different phrase each time
  * The phrase EVOLVES: It gets longer, louder, or changes meaning as the story progresses
    - Episode 1: "Not yet, not yet!"
    - Episode 2: "Not yet, NOT YET!"
    - Episode 3: "NOT YET, NOT YET — oh no, too late!"
    - Episode 4: "Not yet... wait... almost..."
    - Episode 5: "NOW! RIGHT NOW!"
  * The phrase should feel like a drumbeat — kids should be ANTICIPATING it on each page and joining in
  * Surrounding text can vary freely, but the repeated element must anchor each episode
  * The phrase should connect to the story's emotional arc: hopeful at start, desperate in the middle, triumphant at the end
  * Consider call-backs: The final episode's version of the phrase should echo the first but with a twist
  * AVOID just repeating the same sentence identically — that's boring. The repetition must BUILD.
  * Example quality: Episode 1: "Shake, shake, shake — nothing happened." Episode 3: "SHAKE, SHAKE, SHAKE — everything happened AT ONCE!" Episode 5: "One tiny shake... and it was perfect." """,
            "Call and Response": """Write interactive text where the parent reads a line and the child responds. But NOT just "Was X? YES!" over and over — that's boring for age 4+.
  USE THESE TECHNIQUES:
  * Varied question types: "What do you think happened next?", "And WHO was standing behind the tree?", "How many sandwiches fell? Count them!"
  * Response phrases, not just yes/no: Parent reads "And Incy shook and shook and..." Child finishes: "OUT fell the leaves!"
  * Repeated refrains that BUILD: A catchphrase that gets bigger each time. Episode 1: "Uh oh, here we go again!" Episode 3: "UH OH, HERE WE GO AGAIN — and this time it's WORSE!"
  * Character dialogue as call-and-response: One character asks, another answers. "Can you fix it?" / "I can TRY!"
  * Physical participation: "Can you shake like Incy? SHAKE SHAKE SHAKE!" or "Blow on the page to help!"
  * NEVER use more than 2 yes/no questions per episode. Mix in open questions, finish-the-sentence moments, and refrains.
  * The interaction should feel like a GAME between parent and child, not a quiz with one-word answers.""",
            "Suspenseful": """Build genuine tension throughout the story. Each page should make the reader DESPERATE to turn to the next one.
  USE THESE TECHNIQUES:
  * End episodes 1-4 on mini cliffhangers: "And behind the door was..." / "But then they heard a sound..." / "The light flickered and went OUT."
  * Short sentences for tension: "It was dark. Very dark. Something moved." — let the gaps between sentences create fear
  * Longer sentences for relief: When tension breaks, let the prose flow and breathe
  * Sensory dread: "A cold drip landed on Mr Oink's ear. Then another. Then another." — build unease through small details
  * False relief: Something seems safe... then it ISN'T. "They laughed. They relaxed. Then the floor began to SHAKE."
  * Countdown pressure: "Three doors. Two were wrong. One chance." / "The clock showed five minutes. Then four."
  * The resolution should EARN the relief — the scarier the build-up, the more satisfying the ending
  * Keep it age-appropriate: The tension comes from mystery and uncertainty, NOT from anything genuinely frightening
  * Example quality: "Mr Oink tiptoed closer. Closer. The door handle was cold. He turned it slowly... slowly... CREEEEAK." """,
        }
        style_detail = style_descriptions.get(writing_style, f"Interpret '{writing_style}' naturally and apply consistently.")
        
        # Age-aware style modifiers — adjust HOW the style is applied based on age bracket
        young_ages = ["age_2", "age_3", "age_4"]
        older_ages = ["age_8", "age_9", "age_10"]
        
        age_style_modifiers = {
            "Rhyming": {
                "young": "FOR THIS YOUNG AGE: You MUST still rhyme — but use simple nursery rhyme patterns with very short lines. 'Hop hop hop, time to stop! Splish splosh splish, found a fish!' Short bouncy couplets. One or two couplets per episode is enough. Sound effects can be the rhyming words. The rhyme is MORE important at this age, not less — toddlers love rhythm and rhyme above all else.",
                "older": "FOR THIS OLDER AGE: Use more sophisticated rhyming. Internal rhymes, varied line lengths, occasional half-rhymes for effect. Can sustain 3-4 couplets per episode. Wordplay and clever rhymes over simple ones."
            },
            "Gentle": {
                "young": "FOR THIS YOUNG AGE: Lullaby simplicity. 'Soft, soft, soft went the rain. Warm, warm, warm went the blanket.' Repeated soothing words. Bedtime rhythm. Almost no conflict — just gentle discovery and comfort.",
                "older": "FOR THIS OLDER AGE: Poetic and reflective. Can explore quiet emotions — loneliness, nostalgia, wonder. Metaphor and imagery: 'The last leaf didn't fall — it floated, like it had somewhere important to be.' Gentle doesn't mean simple."
            },
            "Silly": {
                "young": "FOR THIS YOUNG AGE: Maximum silliness through sounds and visuals. Made-up words are ESSENTIAL: 'wobbledy-bonk', 'splonk', 'flibberty-gibbets'. Toilet humour is fine — burps, splats, bottoms. Physical chaos over verbal cleverness.",
                "older": "FOR THIS OLDER AGE: Absurdist humour. Fourth-wall breaks ('This story is going terribly wrong'). Subverted expectations — set up something serious then make it ridiculous. Characters can be self-aware about the absurdity."
            },
            "Repetition": {
                "young": "FOR THIS YOUNG AGE: The repeated phrase should be VERY simple — 3-5 words max. It should barely change between episodes. Kids this age want to predict and chant along: 'Not in there! Not in THERE! NOT IN THERE!' Sameness is comfort.",
                "older": "FOR THIS OLDER AGE: The repeated phrase can be longer and evolve more dramatically in meaning across episodes. It can shift from funny to serious and back. The repetition should feel like a literary device, not just a chant."
            },
            "Call and Response": {
                "young": "FOR THIS YOUNG AGE: Keep questions VERY simple. 'Where's the ball? Is it HERE? Nooooo! Is it THERE? ... YESSS!' Mostly yes/no and where/who questions. Physical actions: 'Can you clap? CLAP CLAP CLAP!' The child should feel like they're playing a game.",
                "older": "FOR THIS OLDER AGE: Questions can be more complex — 'What do you think will happen next?', 'Can you guess who was hiding?' Include moments where the reader predicts outcomes. Less physical participation, more intellectual engagement."
            },
            "Suspenseful": {
                "young": "FOR THIS YOUNG AGE: Suspense means peek-a-boo and hide-and-seek tension. 'What's behind the door? One... two... THREE! A BUNNY!' Keep it exciting, never scary. The 'danger' should always be silly or immediately resolved. Short breath-holding moments only.",
                "older": "FOR THIS OLDER AGE: Build genuine mystery. Red herrings, unreliable clues, multiple suspects. Cliffhangers can be more dramatic. Characters can sit with uncertainty. The atmosphere can be genuinely eerie (dark forest, strange sounds) as long as the resolution is reassuring."
            },
        }
        
        style_modifier = ""
        if writing_style in age_style_modifiers:
            if age_level in young_ages:
                style_modifier = age_style_modifiers[writing_style].get("young", "")
            elif age_level in older_ages:
                style_modifier = age_style_modifiers[writing_style].get("older", "")
            # Middle ages (5-7) use the base description as-is — no modifier needed
        
        modifier_block = f"\n\n{style_modifier}" if style_modifier else ""
        
        style_theme_block += f"""
*** WRITING STYLE: {writing_style} ***
The user chose "{writing_style}" style. Apply this to ALL story_text.
DO NOT rhyme unless the style is "Rhyming". DO NOT use any other style — ONLY "{writing_style}".

{style_detail}{modifier_block}
"""
    else:
        # Default style varies by age
        default_styles = {
            "age_2": """Write in a rhythmic, rhyming style perfect for toddlers being read to.
Use LOTS of sound effects: "SPLASH!", "SPLORT!", "KABOOM!", "WHOOOOSH!"
Repetition is key — repeat phrases with slight variation each time.
Fun made-up words: "splishy-sploshy", "rumbly-tumbly", "snore-a-saurus"
Direct address: "Uh oh!", "Oh no!", "Can YOU see it?"
Keep it bouncy and musical — a parent should naturally do funny voices reading this.""",
            "age_3": """Write in a rhythmic, rhyming style perfect for young children being read to.
Use LOTS of sound effects: "SPLASH!", "SPLORT!", "KABOOM!", "WHOOOOSH!"
Repetition is key — repeat phrases with slight variation each time.
Fun made-up words: "splishy-sploshy", "rumbly-tumbly", "snore-a-saurus"
Direct address: "Uh oh!", "Oh no!", "Can YOU see it?"
A catchphrase or repeated question works great as a story thread.
Keep it bouncy and musical — a parent should naturally do funny voices reading this.""",
            "age_4": """Write in a fun, energetic style with some rhyming and lots of sound effects.
Sound effects on every page: "KERPLUNK!", "tip-toe-tip-toe", "KABOOM!"
Funny comparisons: "as tall as a house!", "louder than a thunderstorm!"
Questions to the reader: "What do YOU think happened next?"
A catchphrase or repeated question works great as a story thread.
Simple but vivid — a parent reads this aloud and both parent and child enjoy it.""",
            "age_5": """Write in a natural, engaging storytelling voice. Light rhyming is fine but not required.
Fun vocabulary: "super-duper", "ginormous", "absolutely bonkers"
Sound effects still welcome: "CRASH!", "SPLORT!"
Mix of dialogue and narration. At least one genuinely funny moment per episode.
Characters should have distinct voices when they speak.""",
        }
        default_style = default_styles.get(age_level, """Write in a natural, engaging storytelling voice — like a skilled children's book author.
DO NOT rhyme. Use clear, vivid prose with a mix of dialogue, action, and description.
Vary sentence length for rhythm. Show don't tell. Make every word count.
Characters should have distinct voices when they speak.""")
        
        style_theme_block += f"""
*** WRITING STYLE: Standard ***
{default_style}
"""
    if life_lesson:
        style_theme_block += f"""
*** LIFE LESSON: {life_lesson} ***
Weave this life lesson naturally into the story: "{life_lesson}".
The character should EXPERIENCE this lesson through what happens — not through lecturing.
The lesson should emerge from the story events, especially through the setback in episode 3 and the resolution in episodes 4-5.
At least ONE episode's story_text must have a moment where the character EXPLICITLY feels or talks about {life_lesson} — through dialogue, internal thought, or a clear action that demonstrates it. "Naturally" does not mean "invisible" — the reader should be able to point to a specific moment and say "that's the {life_lesson} part."
"""
    if custom_theme:
        style_theme_block += f"""
*** CUSTOM THEME FROM PARENT ***
The parent wants this personal detail woven into the story: "{custom_theme}"
Make this a central part of the narrative — not just a passing mention. The story should feel like it was written specifically for this moment in the child's life.
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

    # Build theme block — custom theme replaces all pitch data
    if custom_theme:
        theme_block = f"""
CUSTOM STORY THEME (written by the parent):
"{custom_theme}"

This is a PERSONAL story request. The parent has described exactly what they want the story to be about.
Build the ENTIRE 5-episode story around this custom theme. You must create your own:
- Feature used: pick the most interesting feature from the character description
- WANT: what does the character want in this story? Derive it from the custom theme.
- OBSTACLE: what makes it hard? Create a fun, age-appropriate challenge.
- TWIST: how do they solve it in a surprising way?

The custom theme should be the HEART of the story — not a side detail.
"""
    else:
        # Build feature line only if feature_used is provided
        if feature_used:
            theme_block = f"""
CHOSEN THEME: {theme_name}
THEME DESCRIPTION: {theme_description}
THEME BLURB: {theme_blurb}

STORY PLAN:
- Feature used: {feature_used}
- WANT: {want}
- OBSTACLE: {obstacle}
- TWIST: {twist}

⚠️ ONE PROBLEM RULE: This story has ONE central problem, not two. The OBSTACLE is the problem. The TWIST is the solution to THAT SAME problem. Episodes 2-3 must show the OBSTACLE getting worse. Episodes 4-5 must show the TWIST solving THAT SAME OBSTACLE. Do not introduce a new unrelated problem partway through. Every episode must be about the same struggle.

⚠️ THE TWIST IS MANDATORY — DO NOT INVENT YOUR OWN RESOLUTION:
The TWIST written above is the EXACT resolution for this story. You MUST use it. Do NOT replace it with your own idea.
- If the twist says "uses antennae to press the last 2 buttons" → the character MUST use their antennae, not their teeth, not their nose, not something else you made up
- If the twist says "the coat becomes a parachute" → the coat MUST become a parachute
- The twist was carefully designed to use a SPECIFIC character feature in a SURPRISING way. Your job is to write it brilliantly, not to replace it with something generic.
- Episode 4-5 must execute the EXACT twist described above. Read it again before writing episodes 4 and 5.
"""
        else:
            theme_block = f"""
CHOSEN THEME: {theme_name}
THEME BLURB: {theme_blurb}

STORY PLAN (this is a PRE-WRITTEN story structure — follow it EXACTLY):
- WANT: {want}
- OBSTACLE: {obstacle}
- TWIST: {twist}

⚠️ CHARACTER FEATURE: Look at the CHARACTER DESCRIPTION above and pick ONE distinctive physical feature (e.g. floppy ears, shaggy fur, big paws, long tail, sparkly wings, wobbly antenna). Weave this feature into the story naturally — it should cause funny moments, help or hinder the character, and play a role in the resolution. The feature adds personality and comedy but the WANT/OBSTACLE/TWIST above are the PRIMARY story drivers.

⚠️ HARDCODED THEME RULES:
Follow the WANT/OBSTACLE/TWIST precisely:
- Episode 1: Set up the WANT — why does the character want this? Make it urgent and specific. Show how the character's distinctive feature reacts to the situation.
- Episodes 2-3: Show the OBSTACLE getting worse. Each attempt to solve the problem makes it funnier/bigger/more chaotic. The character's feature should add comedy or complications.
- Episode 4: The TWIST begins — something unexpected happens that reframes the whole situation. The character's feature may play a surprising role.
- Episode 5: The TWIST resolves everything — but NOT in the obvious way. The resolution must surprise the reader. Ask: what is the LEAST expected way this could resolve while still making sense? The final beat should reveal something about the character (not just fix the plot). Avoid "character uses their skill/feature and it magically works" — instead the resolution should come from a decision, a mistake that becomes useful, or an unexpected consequence of the chaos. One specific detail from episode 1 must reappear in episode 5 in a new light. The final LINE of story_text should land emotionally or with a laugh — NOT a generic lesson or summary statement like "Han learned that..." or "Some problems just need the right song."

⚠️ ONE PROBLEM RULE: This story has ONE central problem, not two. The OBSTACLE is the problem. The TWIST is the solution to THAT SAME problem. Do not introduce a new unrelated problem partway through.

⚠️ SUPPORTING CHARACTERS: Every new character MUST have a NAME and a BRACKETED DESCRIPTION that includes species/size/one accessory. Example: "Captain Zoom (tall rabbit with goggles and cape)". Use the EXACT SAME bracketed description every time that character appears in a scene_description. The artist has NO MEMORY between pages.

⚠️ ABSENT OR REPLACED BODY PARTS: If the story involves a character missing a normally-present body part (e.g. a unicorn without its horn, a bird with clipped wings, a robot missing an arm), the scene_description MUST explicitly state what is NOT there. Example: "Sparkle (medium unicorn — NO HORN, flat forehead, wearing a party hat where the horn would be)". Never rely on the artist to infer this from the story — they will draw the default version of the creature unless you explicitly negate the missing part every single time that character appears.

⚠️ THE TWIST CHARACTER: If the twist involves a specific character (e.g. a villain, a helper, a creature), that character MUST be visually distinct and named from their FIRST appearance. Give them a memorable name and clear visual description. They must be clearly visible and recognisable in the illustrations — not tiny or hidden.
"""

    # Build age-appropriate story structure
    young_pattern_ages = ["age_2", "age_3"]
    transitional_age = ["age_4"]
    
    if age_level in young_pattern_ages:
        story_structure = f"""*** STORY STRUCTURE — REPEATING PATTERN (for ages 2-3) ***
⚠️ THIS IS NOT A NARRATIVE ARC. Do NOT write a problem→setback→resolution story. Children this age don't follow plot — they follow PATTERNS.

Structure: The SAME thing happens in episodes 1-4 with ONE thing different each time. Episode 5 is the satisfying payoff.

HOW IT WORKS:
- Episode 1: Establish a simple situation and a PATTERN. The character encounters something and the same outcome happens. Example: "{character_name}'s bow tie flew to a DOG! Is that {character_name}'s bow tie? That's not YOUR bow tie, dog! WHOOSH — off it flew!"
- Episode 2: SAME pattern, different thing. "{character_name}'s bow tie flew to a CAT! Is that {character_name}'s bow tie? That's not YOUR bow tie, cat! WHOOSH — off it flew!"
- Episode 3: SAME pattern, different thing, maybe BIGGER or SILLIER. "{character_name}'s bow tie flew to an ELEPHANT! Is that {character_name}'s bow tie? That's not YOUR bow tie, elephant! WHOOSH — off it flew!"
- Episode 4: SAME pattern but something CHANGES — a twist on the pattern. The child notices it's different. "{character_name}'s bow tie flew to... a BUTTERFLY! The butterfly didn't let go! It flew it RIGHT BACK to {character_name}!"
- Episode 5: Resolution. Short, warm, satisfying. Callback to the pattern. "{character_name}'s bow tie was back! No more WHOOSH! {character_name} smiled the BIGGEST smile."

KEY RULES:
- Use the EXACT SAME repeated phrase in episodes 1-3 (with only the subject changing)
- A child hearing this should be SHOUTING the repeated phrase by episode 3
- Each episode introduces ONE new animal/character/object — that's the variety
- Sound effects are essential in the repeated phrase
- Episode 4 BREAKS the pattern in a satisfying way
- Episode 5 is short and warm

The supporting characters should be the things/animals/objects the character encounters in each episode — NOT complex characters with backstories. Just "a dog", "a cat", "an elephant" etc. Include species/size in brackets for the scene_description.

Think: Dear Zoo, Brown Bear Brown Bear, We're Going on a Bear Hunt, Each Peach Pear Plum.

⚠️ RESOLUTION MUST MAKE PHYSICAL SENSE FOR YOUNG AGES (under_3, age_3, age_4):
A toddler or young child cannot infer WHY something works — they need to SEE it.
- The resolution must be a PHYSICAL ACTION that obviously solves the problem
- If a child looking at the PICTURE can't understand why the problem is fixed, the resolution is too abstract
- BAD: "put a flower on the dog's nose so it can only do small sniffs" (WHY would a flower reduce sniffing? Not obvious)
- BAD: "listened to the quiet antenna" (a 3-year-old doesn't understand signal filtering)
- GOOD: "covered his nose with both paws" (physically blocking = obviously can't smell)
- GOOD: "closed his eyes and counted to ten really slowly" (simple action any child understands)
- GOOD: "sat on the noisy thing to make it stop" (physical cause and effect)
The test: describe the resolution to a 3-year-old WITHOUT explaining it. Would they understand from the picture alone? If you need to explain WHY it works, it's too complex."""
    elif age_level in transitional_age:
        story_structure = f"""*** STORY STRUCTURE — SIMPLE PATTERN WITH ARC (for age 4) ***
This age is transitional. Use a REPEATING PATTERN but with a simple problem→solution thread running through it.

Structure: Like Three Billy Goats Gruff — same situation repeats but ESCALATES, then resolves.

- Episode 1: Set up a simple problem. Introduce the character and what they want. ONE named supporting character with a fun personality (include species/size/accessories in brackets). Keep it simple.
- Episode 2: First attempt to solve it. Same obstacle appears. A pattern begins.
- Episode 3: Second attempt. Same pattern but BIGGER or SILLIER. The problem escalates.
- Episode 4: Third attempt — but this time something different happens. A helper or a new idea. The pattern breaks.
- Episode 5: Happy ending. Short and punchy. Connects back to episode 1.

KEY RULES:
- Still has repetition and pattern — kids this age still love predicting
- But now there's a simple WHY (character wants something) and a resolution (they get it)
- Emotions can be named simply: "{character_name} felt sad", "{character_name} felt brave"
- ONE supporting character is enough — don't overcomplicate
- Each episode should have clear cause and effect

Think: The Gruffalo, Three Billy Goats Gruff, Goldilocks, The Tiger Who Came to Tea.

⚠️ RESOLUTION MUST MAKE OBVIOUS SENSE FOR AGE 4:
The twist/resolution must be something a 4-year-old understands without explanation.
- The character must DO something physically obvious that fixes the problem
- A child looking at the picture should immediately understand what happened and why it worked
- If a parent would need to explain the logic, the resolution is too abstract"""
    else:
        story_structure = f"""*** STORY STRUCTURE ***
- Episode 1: Set up the problem AND establish WHY the character wants what they want. The reader must understand what happened BEFORE the story starts. If the character is apologising — show or explain what they did wrong. If they're searching — show what they lost. If they're helping — show why it matters to them. Introduce 2 named supporting characters with funny personalities (in scene_description, include species/size/accessories in brackets after each name — but NEVER in story_text). The companion character (if present) should react to the problem in their own way.
- Episode 2: First attempt using the character's feature. Things start going wrong. The companion character's features or personality may contribute to the chaos.
- Episode 3: SETBACK — but NOT always sad! Pick ONE setback style from below and commit to it:
  * COMIC DISASTER: Everything goes hilariously, catastrophically wrong. Total chaos. Things flying, breaking, multiplying. The character isn't sad — they're overwhelmed by absurd mayhem. Think slapstick.
  * SURPRISE REVERSAL: The character thinks they've fixed it, maybe even celebrates — then realises they haven't. Rug-pull moment. Emotion is shock, not sadness.
  * ESCALATION: The problem gets BIGGER and WILDER. One mess becomes ten. One escaped animal becomes twenty. Character is frantically trying to contain the chaos, not sitting down crying.
  * TICKING CLOCK: They run out of time, or something urgent forces a deadline. Panic and urgency, not defeat.
  * EMOTIONAL MOMENT: Genuine sadness or frustration. Character sits with the failure. Quiet, intimate. USE THIS SPARINGLY — not every story needs a cry.
  The setback must still make the OBSTACLE worse. But the TONE and ENERGY should vary. Not every setback is a child sitting alone looking sad.
- Episode 4: Creative solution — uses feature DIFFERENTLY based on the twist. The companion character OR a supporting character helps or suggests the new approach. The companion's own features might be key to the solution.
- Episode 5: Resolution that connects back to episode 1. Short and punchy ending. Do NOT summarise or moralise."""

    prompt = f'''You are writing a complete 5-episode story for a children's coloring book app.
{style_theme_block}
CHARACTER: {character_name}
CHARACTER DESCRIPTION: {character_description}

⚠️ GENDER: Do NOT assume the character's gender from their name. Use the character's NAME instead of pronouns wherever possible. If you must use pronouns, use "they/them" unless the character description explicitly states gender. Getting a child's gender wrong ruins the story for the family.

{second_char_story_block}

{theme_block}

⚠️ IF THE CHARACTER IS A REAL CHILD/PERSON (not a monster, animal, or toy):
NEVER base the story on their PHYSICAL BODY features (skin colour, hair type, body shape, facial features, height, weight, disability).
Clothing and accessories (bow tie, cardigan, hat, backpack) ARE fine as story features — keep using them.
If the "feature used" describes a physical body trait, treat it as a minor character quirk and focus the story on the scenario, the character's personality, and their interactions with supporting characters instead.

{age_guide}

{story_structure}

*** SCENE DESCRIPTIONS ***
- Start each with LOCATION: "In the kitchen...", "At the park..."
- Show the ACTION mid-happening, not characters standing around
- Include VISIBLE CONSEQUENCES (things scattered, flying, broken)
- Include character's BODY LANGUAGE
- 3-4 background objects to colour
- SUPPORTING CHARACTERS: Every time they appear, include species/size/accessories in brackets. Example: "Pip (small duck with bow tie)". NO COLOURS. Use SAME description each time.
- CRITICAL: Bracketed character descriptions are for scene_description ONLY — NEVER in story_text. In story_text, introduce characters naturally through narrative: "A small duck in a bow tie waddled over. 'I'm Pip!' he said." NEVER write "Pip (small duck with bow tie)" or "Rangers Maya (tall woman with backpack)" in story_text. If you put brackets in story_text, the story is BROKEN.
- If same location as previous episode, REPEAT key setting objects

*** STORY TEXT RULES ***
⚠️ Apply these rules at the appropriate level for the age. For ages 2-4, keep language simple but the PRINCIPLES still apply — the character should still drive the action, funny details should still be specific, and dialogue should still have personality.
- PROTAGONIST AGENCY: The main character must DRIVE the action — they make decisions, hatch plans, cause chaos. They should NOT just react to what other characters do. Ask: whose idea was it? Who took the risk? Who made the key move? It must be the protagonist EVERY time.
- INNER VOICE: At least 2 episodes must include what the character is THINKING — not just what they do. Example: "This was NOT how Han had planned it." or "Seven unicorns. SEVEN. This was getting out of hand." This is what makes readers feel close to the character.
- DIALOGUE QUALITY: Dialogue must sound like a real personality, not a plot update. BAD: "Oh no, the magic is fading!" GOOD: "Dewdrop pressed their nose against Han's knee. 'You're our only hope,' they whispered. 'Also we are very sorry about the confetti.'" Every line of dialogue should be funny, reveal character, or both.
- COMIC SPECIFICITY: Funny details must be SPECIFIC not generic. BAD: "everything went wrong" GOOD: "the confetti cannon fired directly into Han's left ear". The more specific the chaos, the funnier it is.
- VARY SENTENCE RHYTHM: Mix short punchy sentences with longer ones. Short sentences land jokes and dramatic moments. Example: "Han played louder. And louder. And then — silence."

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
5. NEGATIONS: If any character is missing a normally-present body part (horn, wings, tail, etc.), write it explicitly: "NO horn — flat forehead with party hat instead". The illustrator defaults to the standard version of every creature — you must override this every time.

LOCATION MOVEMENT: The story MUST move through at least 2-3 different specific locations across the 5 episodes. Characters should travel, chase, explore — NOT stay rooted in one spot.

In scene_description, ALWAYS specify:
1. The CAMERA ANGLE (from the mandatory pattern above)
2. The EXACT LOCATION (not just "the street" — say "outside the bakery on Maple Street" or "inside the bus on the top deck")  
3. The character's EXACT PHYSICAL ACTION (what their body is doing — climbing, crouching, riding, falling — NOT just standing)
4. Where the main character is positioned in the frame (left, right, center, foreground, background)

NARRATIVE FLOW: Each scene must feel like a CONTINUATION of the previous page. If episode 2 ended running toward the park, episode 3 should START at the park.

*** EMOTION RULES ***
- Use at LEAST 3 DIFFERENT emotions across 5 episodes
- Episode 5 should be happy, proud, or excited
- Emotions: nervous, excited, scared, determined, happy, curious, sad, proud, worried, surprised, embarrassed, panicked

*** NON-NEGOTIABLE RULES ***
1. Episode 5 resolves the specific problem/situation from episode 1
2. Keep to the word count guidance for each age — shorter for young ages, more substantial for older ages
3. Use the character's NAME not pronouns
4. Scene descriptions must specify camera angle, physical action, and position in frame
5. Every story_text must match the chosen WRITING STYLE

⚠️ SELF-CHECK BEFORE WRITING:
Before you write, verify your plan:
1. Does the story follow the STORY STRUCTURE instructions above? (Pattern-based for young ages, narrative arc for older ages)
2. Does episode 5 resolve or complete what started in episode 1?
3. Is the story about ONE thing from start to finish? (Not two unrelated problems)
4. Is each episode's story_text substantial enough to feel like a real storybook page?
5. Does the writing style match what was requested?
If any answer is NO, fix your plan before writing.

⚠️ WORD COUNT GUIDANCE: Each story_text should follow the word count guidance in the age guide above. Younger ages (under_3, age_3, age_4) need shorter text — a parent reads a few punchy sentences aloud. Older ages (age_5+) should feel like a real storybook page. Quality matters MORE than hitting an exact count — a brilliant 45-word page beats a boring 30-word page every time. But don't let young-age pages bloat past their range.

Return ONLY valid JSON in this exact format:

{{
  "theme_name": "{theme_name}",
  "story_title": "GENERATE A CREATIVE TITLE - format: {character_name} and The [Something Fun]",
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

    # Debug: log key parts of the prompt
    print(f"[STORY-GEN] theme_block preview: {theme_block[:300]}")
    print(f"[STORY-GEN] style_theme_block preview: {style_theme_block[:300]}")
    print(f"[STORY-GEN] custom_theme param: {custom_theme}")

    claude_response = claude_client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4000,
        system="You are the most imaginative children\'s story writer alive. You NEVER write boring, predictable stories. You HATE clichés. Every page should make someone say \'I\'ve never read that before!\' Think like Roald Dahl — weird, surprising, darkly funny, completely original. Every sentence must earn its place. If a line is filler, cut it. If a joke isn\'t funny, replace it. The story must be so good that parents enjoy reading it as much as kids enjoy hearing it.",
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
        import re
        json_str = text[start:end]
        
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError:
            repaired = json_str
            repaired = re.sub(r'(?<!\\)\n', ' ', repaired)
            repaired = re.sub(r'(?<!\\)\t', ' ', repaired)
            try:
                data = json.loads(repaired)
            except json.JSONDecodeError as e:
                try:
                    from json_repair import repair_json
                    data = json.loads(repair_json(json_str))
                except ImportError:
                    raise ValueError(f"Story JSON could not be parsed after repair attempts: {e}")
        
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
