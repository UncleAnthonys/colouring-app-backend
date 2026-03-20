"""
FULL COLOUR PIXAR STORYBOOK TEST
=================================
Generates a full colour Pixar-style storybook using the same pipeline as Little Lines
but with full colour rendering instead of colouring page line art.

Run from the backend directory:
    cd /Users/gavinwalker/Downloads/kids-colouring-app/backend
    python3 /path/to/colour_book_test.py

Output: colour_book_test_output/ folder with individual page PNGs + a combined PDF
"""

import asyncio
import base64
import os
import sys
import io
from PIL import Image, ImageDraw, ImageFont
import textwrap

# ── CONFIG ──────────────────────────────────────────────────────────────────
# Reuse the same Gav character and Room Seventeen story as the last test
CHARACTER_NAME = "Gav"
CHARACTER_DESCRIPTION = """
Pixar-style child character. Voluminous curly brown hair. Thin-rimmed round glasses.
Grey Illinois university sweatshirt with dark navy ILLINOIS text across the chest.
Grey sweatpants. Friendly, curious, determined expression. Human child proportions.
"""
STORY_TITLE = "Gav and The Secret of Room Seventeen"

EPISODES = [
    {
        "title": "Episode 1",
        "emotion": "surprised",
        "scene": """WIDE ESTABLISHING SHOT: A school corridor stretching into the distance with lockers lining both walls. 
In the center, a mysterious wooden door glows with soft golden light. The word ILLINOIS shimmers on it in raised letters. 
Gav (child with voluminous curly brown hair, round glasses, grey Illinois sweatshirt) stands staring at it open-mouthed. 
A small girl with pigtails and a backpack (Luna) walks toward the door in the background, following strange music.""",
        "story_text": '"Help! HELP!" The voice came from behind the glowing door. Gav\'s heart went THUMP-THUMP-THUMP! Luna had followed the mysterious music inside — and now the door had LOCKED! "We have to get her out before sunset," Gav said. "That\'s when magic doors disappear!" Gav looked down. The door said ILLINOIS. Gav\'s sweatshirt said ILLINOIS too. Was THIS the key?'
    },
    {
        "title": "Episode 2",
        "emotion": "determined",
        "scene": """MEDIUM ACTION SHOT: Gav pressed right up against the glowing door, both hands flat against it at shoulder height, 
body angled forward pushing hard, one foot braced behind. The ILLINOIS letters on the door glow brighter where Gav's hands touch. 
The soft sweatshirt fabric squishes against the wood. Luna's small backpack is visible on the floor beside the door.""",
        "story_text": 'Gav pressed both hands against the door. PUSH! PUSH! PUUUUSH! But nothing happened. The soft sweatshirt fabric just squished against the wood like a marshmallow. "Gav, are you PUSHING?" Luna\'s voice called from inside. "I\'m TRYING!" Gav shouted back. This wasn\'t working. The sweatshirt was too soft and squishy! How do you open a door when you\'re wearing something as fluffy as a cloud?'
    },
    {
        "title": "Episode 3",
        "emotion": "scared",
        "scene": """CLOSE-UP EMOTIONAL SHOT: Gav crouched low against the door, forehead resting against it in frustration. 
Both hands flat against the door at face level. The curly hair falls forward, partially covering the glasses. 
A clock on the wall behind shows 4 o\'clock. The ILLINOIS letters on the door pulse with faint golden light.""",
        "story_text": 'Gav tried again. And AGAIN! Push with hands. Push with shoulder. Even push with Gav\'s back! SQUISH-SQUASH-SMOOSH! The sweatshirt was too soft every single time! The clock now said 4 o\'clock. "Gav? It\'s getting dark in here..." Luna\'s voice was quieter now. Gav felt scared. What if the door disappeared FOREVER with Luna still inside? Think, think, THINK! There had to be a way!'
    },
    {
        "title": "Episode 4",
        "emotion": "excited",
        "scene": """DYNAMIC ANGLE — overhead view looking DOWN: Gav standing very close to the door, chest pressed directly against it. 
Looking down at the top of Gav\'s curly-haired head. Gav\'s hands positioned on either side of the ILLINOIS letters on the sweatshirt, 
pressing them firmly against the matching letters on the door. Golden light erupts from where the letters meet. 
A teacher in the background points excitedly.""",
        "story_text": '"Wait!" A teacher passing by stopped. "Gav, those letters on your sweatshirt — they\'re slightly RAISED! Feel them!" Gav\'s fingers traced the letters. She was right! They were bumpy like puzzle pieces! Gav pressed the sweatshirt letters right against the door letters — ILLINOIS against ILLINOIS, like a perfect stamp! CLICK-CLICK-CLIIIIICK! The door began to glow brighter! "It\'s WORKING!" Gav shouted. The raised letters were the key all along!'
    },
    {
        "title": "Episode 5",
        "emotion": "happy",
        "scene": """NEW LOCATION — MEDIUM SHOT: The door now wide open, revealing a magical room filled with floating musical notes 
made of light and shelves of glowing books. Gav stands in the doorway, one arm raised in victory, the other reaching to help 
Luna (small girl with pigtails and backpack) step through. The teacher and other students cheer in the background corridor. 
Warm golden light spills out from the magical room.""",
        "story_text": 'CREAK! WHOOOOSH! The door swung open wide! Luna tumbled out, laughing and dizzy. "That was the COOLEST music room ever!" she giggled. Gav grinned. From that day on, whenever Gav wore that ILLINOIS sweatshirt, the door appeared. And Gav? Gav ALWAYS knew exactly how to open it. CLICK!'
    }
]

OUTPUT_DIR = "/Users/gavinwalker/Downloads/colour_book_test_output"

# ── FULL COLOUR IMAGE GENERATION ────────────────────────────────────────────

async def generate_colour_page(scene: str, story_text: str, emotion: str, character_name: str, character_description: str, reveal_image_b64: str = None, previous_page_b64: str = None) -> str:
    """Generate a full colour Pixar-style illustration for a storybook page."""
    
    from google import genai
    from google.genai import types

    api_key = os.environ.get('GOOGLE_API_KEY') or os.environ.get('GEMINI_API_KEY')
    client = genai.Client(api_key=api_key)

    prompt = f"""Create a FULL COLOUR Pixar/Disney animated movie illustration for a children's hardback storybook.

This is NOT a colouring page. This is a FULL COLOUR painted illustration — rich, vibrant, cinematic.

STYLE: Pixar animated movie still. Think Incredibles, Coco, Inside Out. 
- Warm, rich colours with beautiful lighting
- Soft volumetric light and gentle shadows
- Painterly textures, depth, atmosphere
- Characters have big expressive eyes, smooth rounded features
- Backgrounds are detailed and immersive
- Overall mood: magical, warm, exciting

CHARACTER: {character_name}
{character_description}

SCENE TO ILLUSTRATE:
{scene}

CHARACTER EMOTION: {character_name} must look {emotion} in this scene.

STORY TEXT (for mood reference): {story_text}

COMPOSITION RULES:
- Follow the camera direction in the scene description exactly
- Characters must be DOING the action described, not posing
- Rich background detail — this is a premium hardback book illustration
- Cinematic lighting — warm golden tones where magical, cool blues where scary

🚫 NO TEXT OR WORDS IN THE IMAGE — illustrations only.
"""

    parts = [types.Part(text=prompt)]
    
    # Add reveal image as reference if available
    if reveal_image_b64:
        parts.append(types.Part(
            inline_data=types.Blob(
                mime_type="image/png",
                data=base64.b64decode(reveal_image_b64)
            )
        ))
    
    # Add previous page for consistency
    if previous_page_b64:
        parts.append(types.Part(
            inline_data=types.Blob(
                mime_type="image/png", 
                data=base64.b64decode(previous_page_b64)
            )
        ))
        parts.append(types.Part(text="Previous page shown above — maintain visual consistency with setting and supporting characters, but use a completely different composition and camera angle."))

    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash-image",
                contents=types.Content(parts=parts),
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE", "TEXT"],
                    image_config=types.ImageConfig(
                        aspect_ratio="3:4",
                    )
                )
            )
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'inline_data') and part.inline_data:
                    return base64.b64encode(part.inline_data.data).decode('utf-8')
            print(f"  Attempt {attempt+1}: no image returned, retrying...")
        except Exception as e:
            print(f"  Attempt {attempt+1} error: {e}")
    
    raise Exception("Failed to generate image after 3 attempts")


async def generate_colour_cover(title: str, character_name: str, character_description: str) -> str:
    """Generate a full colour Pixar-style cover image."""

    from google import genai
    from google.genai import types

    api_key = os.environ.get('GOOGLE_API_KEY') or os.environ.get('GEMINI_API_KEY')
    client = genai.Client(api_key=api_key)

    prompt = f"""Create a FULL COLOUR Pixar/Disney animated movie BOOK COVER illustration.

STYLE: Premium children's hardback book cover. Think Pixar movie poster quality.
- Vibrant, rich colours
- Dramatic cinematic lighting  
- Character front and centre, large and heroic
- Magical atmosphere with golden glowing light
- Detailed background that hints at the adventure

BOOK TITLE: {title}
MAIN CHARACTER: {character_name} — {character_description}

SCENE: {character_name} standing triumphantly in front of a large wooden door with glowing ILLINOIS letters, 
arms raised in excitement. School corridor with lockers behind. Magical golden light spilling from the door cracks.
Big hero pose — this character is the star of the story.

This is the COVER IMAGE — make it spectacular, eye-catching, and full of wonder.
Warm magical lighting. Rich saturated colours. Pixar movie poster energy.

🚫 NO TEXT — title and branding will be added separately.
"""

    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash-image",
                contents=types.Content(parts=[types.Part(text=prompt)]),
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE", "TEXT"],
                    image_config=types.ImageConfig(
                        aspect_ratio="3:4",
                    )
                )
            )
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'inline_data') and part.inline_data:
                    return base64.b64encode(part.inline_data.data).decode('utf-8')
            print(f"  Cover attempt {attempt+1}: no image returned, retrying...")
        except Exception as e:
            print(f"  Cover attempt {attempt+1} error: {e}")

    raise Exception("Failed to generate cover after 3 attempts")


# ── PAGE LAYOUT (same as colouring but no border, full bleed image) ──────────

def create_colour_a4_page(image_b64: str, story_text: str) -> str:
    """Create A4 page with full colour illustration and story text below."""
    
    A4_WIDTH = 1240
    A4_HEIGHT = 1754

    img_data = base64.b64decode(image_b64)
    page_img = Image.open(io.BytesIO(img_data)).convert('RGB')

    a4_page = Image.new('RGB', (A4_WIDTH, A4_HEIGHT), 'white')

    max_height = int(A4_HEIGHT * 0.82)
    max_width = A4_WIDTH - 60

    img_ratio = page_img.width / page_img.height
    if img_ratio > (max_width / max_height):
        new_width = max_width
        new_height = int(new_width / img_ratio)
    else:
        new_height = max_height
        new_width = int(new_height * img_ratio)

    page_img = page_img.resize((new_width, new_height), Image.LANCZOS)
    x_offset = (A4_WIDTH - new_width) // 2
    y_offset = 30

    a4_page.paste(page_img, (x_offset, y_offset))

    # Thin border
    draw = ImageDraw.Draw(a4_page)
    draw.rectangle(
        [x_offset - 2, y_offset - 2, x_offset + new_width + 2, y_offset + new_height + 2],
        outline='black', width=2
    )

    # Story text
    text_area_top = y_offset + new_height + 20
    available_height = A4_HEIGHT - text_area_top - 30
    text_margin = 70
    max_text_width = A4_WIDTH - (text_margin * 2)

    import re
    story_text = re.sub(r'\n+', ' ', story_text).strip()

    def wrap_pixels(text, font, max_w):
        words = text.split()
        lines = []
        current = []
        for word in words:
            test = ' '.join(current + [word])
            tw = font.getbbox(test)[2] - font.getbbox(test)[0]
            if tw > max_w and current:
                lines.append(' '.join(current))
                current = [word]
            else:
                current.append(word)
        if current:
            lines.append(' '.join(current))
        return lines

    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    for fs, ls in zip([24, 21, 19, 17, 15], [34, 30, 27, 24, 22]):
        try:
            font = ImageFont.truetype(font_path, fs)
        except:
            font = ImageFont.load_default()
        lines = wrap_pixels(story_text, font, max_text_width)
        if len(lines) * ls <= available_height:
            break

    total_h = len(lines) * ls
    start_y = text_area_top + max(0, (available_height - total_h) // 2)

    for line in lines:
        if start_y + ls > A4_HEIGHT - 10:
            break
        bbox = draw.textbbox((0, 0), line, font=font)
        lw = bbox[2] - bbox[0]
        lx = max(text_margin, (A4_WIDTH - lw) // 2)
        draw.text((lx, start_y), line, fill='black', font=font)
        start_y += ls

    buf = io.BytesIO()
    a4_page.save(buf, format='PNG', dpi=(150, 150))
    buf.seek(0)
    return base64.b64encode(buf.read()).decode('utf-8')


def create_colour_cover_page(image_b64: str, title: str) -> str:
    """Add title text overlay to cover image."""
    from PIL import Image, ImageDraw, ImageFont
    import textwrap

    img_data = base64.b64decode(image_b64)
    cover = Image.open(io.BytesIO(img_data)).convert('RGB')
    w, h = cover.size
    draw = ImageDraw.Draw(cover)

    script_dir = "/Users/gavinwalker/Downloads/kids-colouring-app/backend"
    font_candidates = [
        os.path.join(script_dir, "fonts", "LilitaOne-Regular.ttf"),
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]

    def load_font(size):
        for fp in font_candidates:
            try:
                return ImageFont.truetype(fp, size)
            except:
                continue
        return ImageFont.load_default()

    title_size = max(56, int(w * 0.09))
    subtitle_size = max(24, int(w * 0.035))
    title_font = load_font(title_size)
    subtitle_font = load_font(subtitle_size)

    def bubble_text(draw, x, y, text, font, ow=5):
        for ox in range(-ow, ow + 1):
            for oy in range(-ow, ow + 1):
                if ox*ox + oy*oy <= ow*ow:
                    draw.text((x+ox, y+oy), text, fill='black', font=font)
        draw.text((x, y), text, fill='white', font=font)

    title_y = int(h * 0.04)
    wrapped = textwrap.fill(title, width=28)
    padding = int(w * 0.08)
    max_w = w - padding * 2
    ow = max(4, int(w * 0.007))

    for line in wrapped.split('\n'):
        bbox = draw.textbbox((0, 0), line, font=title_font)
        lw = bbox[2] - bbox[0]
        lh = bbox[3] - bbox[1]
        f = title_font
        if lw > max_w:
            f = load_font(int(title_size * max_w / lw))
            bbox = draw.textbbox((0, 0), line, font=f)
            lw = bbox[2] - bbox[0]
            lh = bbox[3] - bbox[1]
        bubble_text(draw, (w - lw) // 2, title_y, line, f, ow)
        title_y += lh + int(h * 0.008)

    sub = "A Little Lines Story Book"
    sbbox = draw.textbbox((0, 0), sub, font=subtitle_font)
    sw = sbbox[2] - sbbox[0]
    sh = sbbox[3] - sbbox[1]
    bubble_text(draw, (w - sw) // 2, h - sh - int(h * 0.05), sub, subtitle_font, max(2, ow-1))

    buf = io.BytesIO()
    cover.save(buf, format='PNG')
    buf.seek(0)
    return base64.b64encode(buf.read()).decode('utf-8')


def save_pages_as_pdf(pages_b64: list, output_path: str):
    """Combine all pages into a single PDF."""
    from reportlab.pdfgen import canvas as rl_canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.utils import ImageReader

    A4_W, A4_H = A4
    buf = io.BytesIO()
    c = rl_canvas.Canvas(buf, pagesize=A4)

    for page_b64 in pages_b64:
        img_data = base64.b64decode(page_b64)
        img = Image.open(io.BytesIO(img_data)).convert('RGB')
        img_buf = io.BytesIO()
        img.save(img_buf, format='PNG')
        img_buf.seek(0)
        c.drawImage(ImageReader(img_buf), 0, 0, width=A4_W, height=A4_H)
        c.showPage()

    c.save()
    buf.seek(0)
    with open(output_path, 'wb') as f:
        f.write(buf.read())
    print(f"PDF saved: {output_path}")


# ── MAIN ─────────────────────────────────────────────────────────────────────

async def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"\n{'='*60}")
    print("FULL COLOUR PIXAR STORYBOOK TEST")
    print(f"{'='*60}\n")

    pages_b64 = []

    # Cover
    print("Generating cover...")
    cover_img = await generate_colour_cover(STORY_TITLE, CHARACTER_NAME, CHARACTER_DESCRIPTION)
    cover_page = create_colour_cover_page(cover_img, STORY_TITLE)
    pages_b64.append(cover_page)
    cover_path = os.path.join(OUTPUT_DIR, "page_00_cover.png")
    with open(cover_path, 'wb') as f:
        f.write(base64.b64decode(cover_page))
    print(f"  ✅ Cover saved: {cover_path}")

    # Episodes
    previous_b64 = None
    for i, ep in enumerate(EPISODES):
        print(f"Generating page {i+1}/5: {ep['title']}...")
        img = await generate_colour_page(
            scene=ep['scene'],
            story_text=ep['story_text'],
            emotion=ep['emotion'],
            character_name=CHARACTER_NAME,
            character_description=CHARACTER_DESCRIPTION,
            previous_page_b64=previous_b64
        )
        page = create_colour_a4_page(img, ep['story_text'])
        pages_b64.append(page)
        previous_b64 = img

        page_path = os.path.join(OUTPUT_DIR, f"page_0{i+1}.png")
        with open(page_path, 'wb') as f:
            f.write(base64.b64decode(page))
        print(f"  ✅ Page {i+1} saved: {page_path}")

    # PDF
    print("\nBuilding PDF...")
    pdf_path = os.path.join(OUTPUT_DIR, "colour_storybook_test.pdf")
    save_pages_as_pdf(pages_b64, pdf_path)

    print(f"\n{'='*60}")
    print(f"✅ DONE — {len(pages_b64)} pages generated")
    print(f"📁 Output: {OUTPUT_DIR}")
    print(f"📄 PDF: {pdf_path}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    asyncio.run(main())
