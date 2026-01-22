"""
Kids Colouring App - FastAPI Backend
Completely separate from YOW
"""

import os
import base64
import json
import httpx
from datetime import datetime
from pathlib import Path
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

app = FastAPI(title="Kids Colouring App API", version="1.0.0")

# CORS for FlutterFlow
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Config
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
BASE_URL = "https://api.openai.com/v1"

# Load prompts
PROMPTS_FILE = Path(__file__).parent / "prompts" / "themes.json"

def load_prompts():
    with open(PROMPTS_FILE) as f:
        return json.load(f)

CONFIG = None

@app.on_event("startup")
async def startup():
    global CONFIG
    CONFIG = load_prompts()
    print(f"✅ Loaded {len(CONFIG.get('themes', {}))} themes")


# ============================================
# PROMPT BUILDERS
# ============================================

def build_custom_theme_overlay(custom_input: str) -> str:
    """Build a custom theme overlay from user input"""
    return f"""Apply theme: {custom_input}

COSTUME REQUIREMENT (CRITICAL - DO THIS FIRST):
- Dress ALL people in costumes or outfits related to: {custom_input}
- If the theme involves animals, dress people AS those animals (animal onesies, ears, tails, etc.)
- If the theme involves professions, dress people in those uniforms
- If the theme involves fantasy, add magical costume elements
- This is the most important part of the theme

SCENE REQUIREMENT:
- Fill the scene with elements and objects related to: {custom_input}
- Add multiple instances of themed elements throughout the background
- Keep everything fun, friendly, and child-appropriate
- Make it magical and engaging for children

IMPORTANT:
- All elements must be FULLY VISIBLE and NOT cut off at any edge
- Preserve the original subjects (people/pets) from the photo but transform them into the theme"""


def build_photo_prompt(age_level: str = "age_5", theme: str = "none", custom_theme: str = None) -> str:
    """Build prompt for photo-to-colouring mode"""
    
    # UNDER 3 - blob shapes bypass
    if age_level == "under_3":
        theme_name = custom_theme if custom_theme else theme
        if theme_name == "none":
            theme_name = "the scene"
        return f"""Create the SIMPLEST possible BLACK AND WHITE colouring page for a 2 year old baby.

DRAW:
- The people from the photo as VERY simple blob shapes (round heads, simple body)
- ONE simple {theme_name} object next to them

STYLE:
- BLACK OUTLINES ON WHITE ONLY - no colour, no grey, no shading
- EXTREMELY THICK black outlines
- Blob/kawaii style - super rounded and chunky
- Faces: just dots for eyes, simple curve for mouth
- NO fingers, NO detailed features, NO hair details
- Bodies as simple rounded shapes
- Maximum 8-10 colourable areas TOTAL

BACKGROUND:
- PURE WHITE - absolutely nothing else
- No ground, no shadows, nothing

OUTPUT: Simple black outline blob figures on pure white. NO COLOUR."""

    # AGE 3 - super simple bypass
    if age_level == "age_3":
        theme_name = custom_theme if custom_theme else theme
        if theme_name == "none":
            theme_name = "the scene"
        return f"""Create an EXTREMELY SIMPLE toddler colouring page.

STYLE: "My First Colouring Book" - for 3 year olds.

DRAW ONLY:
- One or two simple figures (people from photo as very basic shapes)
- One simple {theme_name} object next to them
- THAT IS ALL - NOTHING ELSE

ABSOLUTE REQUIREMENTS:
- PURE WHITE BACKGROUND - no sky, no clouds, no ground, no grass, nothing
- VERY THICK black outlines only
- MAXIMUM 10-12 large colourable areas in the ENTIRE image
- NO patterns, NO details, NO small elements
- Simple blob-like shapes

OUTPUT: Thick simple outlines on pure white. Nothing in background."""

    # AGE 4 - simple figures with costumes bypass
    if age_level == "age_4":
        theme_name = custom_theme if custom_theme else theme
        if theme_name == "none":
            theme_name = "the scene"
        return f"""Create a SIMPLE colouring page for a 4 year old.

DRAW:
- The people from the photo as simple figures with basic {theme_name} costumes
- One simple {theme_name} character/object next to them

STYLE:
- BLACK OUTLINES ON WHITE ONLY - NO grey, NO shading, NO texture, NO gradients
- THICK black outlines
- Simple rounded figures
- Faces: dots for eyes, simple smile, basic hair shape
- Simple clothing - NO frills, NO layered skirts, NO patterns
- Bodies still chunky and simple
- Maximum 15-18 colourable areas

BACKGROUND:
- PURE WHITE BACKGROUND - NOTHING ELSE
- NO ground, NO sky, NO clouds, NO rainbow
- Just figures on white

OUTPUT: Thick black outlines on pure white. No background."""

    # AGE 5 - slightly more detail, minimal background
    if age_level == "age_5":
        theme_name = custom_theme if custom_theme else theme
        if theme_name == "none":
            theme_name = "the scene"
        return f"""Create a colouring page for a 5 year old.

DRAW:
- The people from the photo wearing simple {theme_name} costumes (basic outfits, not elaborate)
- One {theme_name} character/object next to them

STYLE:
- BLACK OUTLINES ON WHITE ONLY - NO grey, NO shading, NO texture
- Medium-thick black outlines
- Simple but recognisable figures
- Faces: simple eyes, smile, basic hair shape
- Clothing: simple shapes, NO frills, NO layered skirts, NO intricate patterns
- Maximum 20-25 colourable areas

BACKGROUND:
- MINIMAL background only
- Simple ground line
- Maybe 1-2 simple clouds
- NO rainbow, NO detailed scenery, NO flowers, NO stars scattered around

OUTPUT: Clean black outlines with minimal simple background. Keep it simple."""

    # AGE 7 - more detail within objects, fuller scenes
    if age_level == "age_7":
        theme_name = custom_theme if custom_theme else theme
        if theme_name == "none":
            theme_name = "the scene"
        return f"""Create a colouring page for a 7 year old.

DRAW:
- The people from the photo in detailed {theme_name} costumes
- 2-3 {theme_name} characters/objects around them
- Background scene appropriate to theme

STYLE:
- BLACK OUTLINES ON WHITE ONLY - NO grey, NO shading, NO texture, NO noise, NO random dots
- Medium black outlines
- More detail WITHIN objects:
  - Hair with individual sections/strands to colour separately
  - Clothing with simple patterns (stripes, stars, dots as outlines)
  - Faces more expressive
- Keep all areas CLEAN - pure white inside lines
- 30-35 colourable areas

BACKGROUND:
- Fuller background scene
- Ground, sky, clouds
- A few themed elements (but not cluttered)
- All clean outlines, no shading

CRITICAL: Every area must be pure white inside black outlines. NO pencil texture. NO grey fills. Clean colourable spaces.

OUTPUT: Detailed black line drawing with clean white spaces throughout."""

    # PHOTO-ACCURATE MODE - completely different prompt for "none" theme
    if theme == "none" and not custom_theme:
        base_prompt = """Convert this photograph into a colouring book page.

FACES AND PEOPLE (HIGHEST PRIORITY):
- Faces MUST be recognisable as the actual people in the photo
- Keep exact hairstyles - long hair stays long, short stays short
- Keep real facial features - this is the most important thing
- A parent must recognise their children
- Simplify clothing but keep it accurate to photo

BACKGROUND (SIMPLIFY):
- Keep the real setting from the photo
- But simplify heavily for colouring:
  - Dense trees become simple tree shapes with cloud-like foliage
  - Hundreds of leaves become a few scattered leaves
  - Keep the scene recognisable but colourable

LINE STYLE:
- Bold black outlines on white
- Clean enclosed shapes for colouring
- No tiny details or dense textures

OUTPUT: Bold black lines on pure white background."""

        if age_level == "age_3":
            base_prompt += """

AGE 3-4 SIMPLIFICATION (CRITICAL):
- VERY thick bold outlines
- VERY simple shapes - maximum 15-20 colourable areas total
- Remove most background detail - just 2-3 simple trees
- Large simple shapes only - nothing fiddly
- This must be EXTREMELY simple for a toddler"""
        elif age_level == "age_7_8":
            base_prompt += """

AGE 7-8 DETAIL:
- Can include more detail than younger ages
- Thinner lines acceptable
- More background elements allowed
- More intricate patterns okay"""
        
        return base_prompt

    # THEMED MODE - use master prompt + overlays
    parts = [CONFIG["master_base_prompt"]["prompt"]]
    
    if age_level in CONFIG["age_levels"]:
        parts.append("\n\n" + CONFIG["age_levels"][age_level]["overlay"])
    
    if custom_theme:
        parts.append("\n\n" + build_custom_theme_overlay(custom_theme))
    elif theme in CONFIG["themes"]:
        overlay = CONFIG["themes"][theme].get("overlay", "")
        if overlay:
            parts.append("\n\n" + overlay)
    
    return "".join(parts)


def build_text_to_image_prompt(description: str, age_level: str = "age_5") -> str:
    """Build prompt for text-to-image mode (no photo)"""
    
    # TODDLER MODE (age 3-4) - super simple single object
    if age_level == "age_3":
        return f"""Create an EXTREMELY SIMPLE toddler colouring page.

STYLE: "My First Colouring Book" - for 3 year olds.

DRAW ONLY:
- One simple {description} character or object
- THAT IS ALL - NOTHING ELSE

ABSOLUTE REQUIREMENTS:
- PURE WHITE BACKGROUND - no sky, no clouds, no ground, no grass, nothing
- VERY THICK black outlines only
- MAXIMUM 10-12 large colourable areas in the ENTIRE image
- NO patterns, NO details, NO small elements
- Simple blob-like shapes

REFERENCE: Think of a chunky tractor or simple horse drawing in a baby's colouring book - just the object on white, nothing else.

OUTPUT: Thick simple outlines on pure white. Nothing in background."""
    
    base = f"""Create a printable black-and-white colouring page for children featuring: {description}

STYLE: Classic children's colouring book - simple, clean, easy to colour.

CRITICAL - CLEAN OUTPUT:
- ABSOLUTELY NO dots, specks, noise, or scattered marks anywhere
- ABSOLUTELY NO ground texture or grass texture
- NO tiny details or fine lines
- Every line must be smooth and bold
- If in doubt, LEAVE IT OUT - simpler is better

LINE QUALITY:
- Thick, bold black outlines only
- ALL lines must connect perfectly - no gaps
- Pure white background - no grey tones
- All shapes fully enclosed for colouring
- Clean enclosed shapes - like a classic 1990s colouring book

COMPOSITION:
- Fill the page with a fun scene
- All elements must be FULLY VISIBLE - nothing cut off at edges
- Maximum 15-20 main elements
- Lots of WHITE SPACE between elements
- No title text or banners

SCENE:
- Feature iconic elements of {description}
- Include 2-3 cute children or characters
- Add fun related objects
- Make it magical and child-friendly

BANNED:
- Dots, specks, or scattered marks
- Ground texture or grass blades
- Tiny fiddly details
- Sketchy or broken lines
- Any visual noise

OUTPUT: Bold black lines on pure white background. No grey. No texture."""

    if age_level in CONFIG["age_levels"]:
        base += "\n\n" + CONFIG["age_levels"][age_level]["overlay"]

    return base


# ============================================
# OPENAI API CALLS
# ============================================

async def generate_from_photo(prompt: str, image_b64: str, quality: str = "low") -> dict:
    """Generate colouring page from photo using images/edits endpoint"""
    
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
    image_bytes = base64.b64decode(image_b64)
    
    files = [
        ("image[]", ("source.jpg", image_bytes, "image/jpeg")),
    ]
    data = {
        "model": "gpt-image-1.5",
        "prompt": prompt,
        "n": "1",
        "size": "1024x1536",
        "quality": quality,
    }
    
    async with httpx.AsyncClient(timeout=180.0) as client:
        response = await client.post(
            f"{BASE_URL}/images/edits",
            headers=headers,
            files=files,
            data=data
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        
        return response.json()


async def generate_from_text(prompt: str, quality: str = "low") -> dict:
    """Generate colouring page from text using images/generations endpoint"""
    
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "gpt-image-1.5",
        "prompt": prompt,
        "n": 1,
        "size": "1024x1536",
        "quality": quality,
    }
    
    async with httpx.AsyncClient(timeout=180.0) as client:
        response = await client.post(
            f"{BASE_URL}/images/generations",
            headers=headers,
            json=data
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        
        return response.json()


# ============================================
# API ENDPOINTS
# ============================================

@app.get("/")
async def root():
    return {"status": "ok", "app": "Kids Colouring App API", "version": "1.0.0"}


@app.get("/health")
async def health():
    return {"status": "healthy", "openai_configured": bool(OPENAI_API_KEY)}


@app.get("/themes")
async def list_themes():
    """List all available themes"""
    themes = []
    for key, data in CONFIG.get("themes", {}).items():
        themes.append({
            "key": key,
            "name": data.get("name", key),
            "description": data.get("description", "")
        })
    return {"themes": themes, "count": len(themes)}


@app.get("/age-levels")
async def list_age_levels():
    """List available age levels"""
    levels = []
    for key, data in CONFIG.get("age_levels", {}).items():
        levels.append({
            "key": key,
            "name": data.get("name", key),
            "min_age": data.get("min_age"),
            "max_age": data.get("max_age")
        })
    return {"age_levels": levels}


class PhotoGenerateRequest(BaseModel):
    image_b64: str
    theme: str = "none"
    custom_theme: Optional[str] = None
    age_level: str = "age_5"
    quality: str = "low"


@app.post("/generate/photo")
async def generate_from_photo_endpoint(request: PhotoGenerateRequest):
    """
    Generate colouring page from uploaded photo
    
    - image_b64: Base64 encoded image
    - theme: Theme key from /themes OR "none"
    - custom_theme: Custom theme text (overrides theme if provided)
    - age_level: Age level key from /age-levels
    - quality: "low" or "medium"
    """
    
    if not OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="OpenAI API key not configured")
    
    # Build prompt
    prompt = build_photo_prompt(
        age_level=request.age_level,
        theme=request.theme,
        custom_theme=request.custom_theme
    )
    
    # Generate
    start = datetime.now()
    result = await generate_from_photo(prompt, request.image_b64, request.quality)
    elapsed = (datetime.now() - start).total_seconds()
    
    # Get image
    image_data = result["data"][0]
    
    # Return base64 or URL
    if "b64_json" in image_data:
        output_image = image_data["b64_json"]
        output_type = "base64"
    else:
        output_image = image_data["url"]
        output_type = "url"
    
    return {
        "success": True,
        "image": output_image,
        "image_type": output_type,
        "generation_time": elapsed,
        "theme_used": request.custom_theme or request.theme,
        "age_level": request.age_level
    }


class TextGenerateRequest(BaseModel):
    description: str
    age_level: str = "age_5"
    quality: str = "low"


@app.post("/generate/text")
async def generate_from_text_endpoint(request: TextGenerateRequest):
    """
    Generate colouring page from text description (no photo)
    
    - description: What to draw (e.g., "Paris", "dinosaurs playing soccer")
    - age_level: Age level key from /age-levels
    - quality: "low" or "medium"
    """
    
    if not OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="OpenAI API key not configured")
    
    # Build prompt
    prompt = build_text_to_image_prompt(request.description, request.age_level)
    
    # Generate
    start = datetime.now()
    result = await generate_from_text(prompt, request.quality)
    elapsed = (datetime.now() - start).total_seconds()
    
    # Get image
    image_data = result["data"][0]
    
    if "b64_json" in image_data:
        output_image = image_data["b64_json"]
        output_type = "base64"
    else:
        output_image = image_data["url"]
        output_type = "url"
    
    return {
        "success": True,
        "image": output_image,
        "image_type": output_type,
        "generation_time": elapsed,
        "description": request.description,
        "age_level": request.age_level
    }


# ============================================
# RUN
# ============================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
