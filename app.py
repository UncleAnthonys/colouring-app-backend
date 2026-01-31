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
from pattern_endpoints import pattern_router
from PIL import Image
import io
from pdf_utils import create_a4_pdf
import firebase_admin
from firebase_admin import credentials, storage
import uuid
from adventure_endpoints import router as adventure_router
from firebase_utils import init_firebase, upload_to_firebase

app = FastAPI(title="Kids Colouring App API", version="1.0.0")

# CORS for FlutterFlow
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include pattern coloring router
app.include_router(pattern_router)
app.include_router(adventure_router, prefix="/adventure", tags=["Adventure"])

# Config
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
BASE_URL = "https://api.openai.com/v1"

# Failure logging
FAILURE_LOG = Path(__file__).parent / "generation_failures.log"

# Load prompts
PROMPTS_FILE = Path(__file__).parent / "prompts" / "themes.json"


def normalize_age_level(age_input: str) -> str:
    """Convert age inputs like age_2.0 to correct format"""
    valid_levels = ["under_3", "age_3", "age_4", "age_5", "age_6", "age_7", "age_8", "age_9", "age_10"]
    if age_input in valid_levels:
        return age_input
    try:
        num_str = age_input.replace("age_", "").replace(".0", "")
        age_num = int(float(num_str))
        if age_num <= 2:
            return "under_3"
        elif age_num >= 10:
            return "age_10"
        else:
            return f"age_{age_num}"
    except:
        return "age_5"
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
# IMAGE VALIDATION & LOGGING
# ============================================

def is_valid_coloring_page(image_b64: str, brightness_threshold: int = 200) -> tuple:
    """
    Check if image has white background (not grey/black failure).
    Returns (is_valid, avg_brightness)
    
    A proper coloring page is mostly white (brightness ~240-255).
    A failed dark image has brightness below 200.
    """
    try:
        image_bytes = base64.b64decode(image_b64)
        image = Image.open(io.BytesIO(image_bytes)).convert('L')  # Convert to grayscale
        
        # Calculate average brightness
        pixels = list(image.getdata())
        avg_brightness = sum(pixels) / len(pixels)
        
        return avg_brightness >= brightness_threshold, avg_brightness
    except Exception as e:
        print(f"Error checking image brightness: {e}")
        return True, 255  # Assume valid if check fails


def log_generation_attempt(prompt_preview: str, attempt: int, success: bool, brightness: float, retried: bool = False):
    """Log each generation attempt for tracking failure rates"""
    try:
        with open(FAILURE_LOG, "a") as f:
            entry = {
                "timestamp": datetime.now().isoformat(),
                "prompt_preview": prompt_preview[:100].replace("\n", " "),
                "attempt": attempt,
                "success": success,
                "brightness": round(brightness, 1),
                "retried": retried
            }
            f.write(json.dumps(entry) + "\n")
    except Exception as e:
        print(f"Error logging generation attempt: {e}")


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
        # NO THEME - photo only
        if theme == "none" and not custom_theme:
            return """Create the SIMPLEST possible BLACK AND WHITE colouring page for a 2 year old baby.

CRITICAL: Only draw what is ACTUALLY in the photo. DO NOT add anything not in the original image.

DRAW:
- The people from the photo as VERY simple blob shapes
- THAT IS ALL - NOTHING ELSE

STYLE:
- BLACK OUTLINES ON WHITE ONLY
- EXTREMELY THICK black outlines
- Blob/kawaii style
- Maximum 8-10 colourable areas TOTAL

BACKGROUND:
- PURE WHITE - absolutely nothing else

OUTPUT: Simple blob figures on pure white. ONLY the people."""

        theme_name = custom_theme if custom_theme else theme

        if theme_name == "none":
            theme_name = "the scene"
        # Special handling for alphabet themes
        if theme.startswith("alphabet_"):
            letter = theme.replace("alphabet_", "").upper()
            return f"""Create the SIMPLEST possible BLACK AND WHITE colouring page for a 2 year old baby.

DRAW:
- The people from the photo as VERY simple blob shapes (round heads, simple body)
- A big friendly letter {letter} CHARACTER with a cute face, arms and legs standing next to them

STYLE:
- BLACK OUTLINES ON WHITE ONLY - no colour, no grey, no shading
- EXTREMELY THICK black outlines
- Blob/kawaii style - super rounded and chunky
- Faces: just dots for eyes, simple curve for mouth
- Maximum 8-10 colourable areas TOTAL

BACKGROUND:
- PURE WHITE - absolutely nothing else

OUTPUT: Simple blob figures with friendly letter {letter} character on pure white."""

        return f"""Create the SIMPLEST possible BLACK AND WHITE colouring page for a 2 year old baby.

CRITICAL: Only draw what is ACTUALLY in the photo. DO NOT add any animals, objects, or elements not in the original image.

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
        # NO THEME - photo accurate only
        if theme == "none" and not custom_theme:
            return """Create an EXTREMELY SIMPLE colouring page for a 3 year old.

CRITICAL: Only draw what is ACTUALLY in the photo. DO NOT add anything not in the original image.

DRAW:
- The people from the photo as simple figures
- THAT IS ALL - NOTHING ELSE

STYLE:
- BLACK OUTLINES ON WHITE ONLY
- VERY THICK black outlines
- Simple rounded shapes
- Maximum 10-12 colourable areas TOTAL

BACKGROUND:
- PURE WHITE - absolutely nothing else

OUTPUT: Simple black outline figures on pure white. ONLY the people from the photo."""

        theme_name = custom_theme if custom_theme else theme

        if theme_name == "none":
            theme_name = "the scene"
        
        # Special handling for alphabet themes
        if theme.startswith("alphabet_"):
            letter = theme.replace("alphabet_", "").upper()
            return f"""Create an EXTREMELY SIMPLE toddler alphabet colouring page for letter {letter}.

CRITICAL: Only draw what is ACTUALLY in the photo. DO NOT add any animals, objects, or elements not in the original image.

DRAW:
- The people from the photo as VERY simple blob shapes (round heads, simple chunky body)
- Plain simple clothing - NO patterns, NO costumes
- A big friendly letter {letter} CHARACTER standing next to them with a cute face, arms and legs

STYLE:
- BLACK OUTLINES ON WHITE ONLY - no colour, no grey, no shading
- EXTREMELY THICK black outlines
- Blob/kawaii style - super rounded and chunky figures
- Faces: just dots for eyes, simple curve for mouth
- NO fingers, NO detailed features
- Bodies as simple rounded shapes
- Maximum 10-12 colourable areas TOTAL

BACKGROUND:
- PURE WHITE - absolutely nothing else
- No ground, no shadows, nothing

OUTPUT: Simple black outline blob figures standing next to a friendly letter {letter} character on pure white."""
        
        return f"""Create an EXTREMELY SIMPLE toddler colouring page.

CRITICAL: Only draw what is ACTUALLY in the photo. DO NOT add any animals, objects, or elements not in the original image.

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
        # NO THEME - photo only
        if theme == "none" and not custom_theme:
            return """Create a SIMPLE colouring page for a 4 year old.

CRITICAL: Only draw what is ACTUALLY in the photo. DO NOT add anything not in the original image.

DRAW:
- The people from the photo as simple cute figures
- ONE simple object from the photo background (e.g. their bike, a fence, a ball)
- THAT IS ALL - NOTHING ELSE

STYLE:
- BLACK OUTLINES ON WHITE ONLY
- THICK black outlines
- Simple rounded figures
- Maximum 15-18 colourable areas TOTAL

BACKGROUND:
- PURE WHITE - no sky, no ground, no scenery

OUTPUT: Simple figures with one object from the photo on pure white."""

        theme_name = custom_theme if custom_theme else theme
        if theme_name == "none":
            theme_name = "the scene"
        
        # Special handling for alphabet themes
        if theme.startswith("alphabet_"):
            letter = theme.replace("alphabet_", "").upper()
            return f"""Create a SIMPLE alphabet colouring page for letter {letter} for a 4 year old.

CRITICAL: Only draw what is ACTUALLY in the photo. DO NOT add any animals, objects, or elements not in the original image.

DRAW:
- The people from the photo as simple cute figures
- A big friendly letter {letter} CHARACTER with a cute face, arms and legs standing with them
- 2-3 simple objects that start with {letter} (e.g. for E: elephant, egg)

STYLE:
- BLACK OUTLINES ON WHITE ONLY
- THICK black outlines  
- Simple rounded cartoon figures
- The letter {letter} must be LARGE and clearly visible
- Maximum 15-18 colourable areas

NO TEXT - do not write any words or labels

BACKGROUND:
- PURE WHITE - no ground, no scenery

OUTPUT: Simple figures with friendly letter character and a few {letter} objects. No text."""
        
        return f"""Create a SIMPLE colouring page for a 4 year old.

CRITICAL: Only draw what is ACTUALLY in the photo. DO NOT add any animals, objects, or elements not in the original image.

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
        # NO THEME - photo accurate
        if theme == "none" and not custom_theme:
            return """Create a colouring page for a 5 year old.

CRITICAL: Only draw what is ACTUALLY in the photo. DO NOT add any animals, pets, or objects not in the original image.

DRAW:
- The people from the photo as simple figures
- Background elements from the photo (simplified)
- THAT IS ALL - NOTHING ELSE

STYLE:
- BLACK OUTLINES ON WHITE ONLY
- Medium-thick black outlines
- Simple but recognisable figures
- Maximum 20-25 colourable areas

BACKGROUND:
- MINIMAL - simple ground line, 1-2 clouds maximum

DO NOT ADD: Any pets, animals, or objects not in the original photo.

OUTPUT: Simple figures with minimal background. Photo accurate."""

        theme_name = custom_theme if custom_theme else theme
        if theme_name == "none":
            theme_name = "the scene"
        
        # Special handling for alphabet themes
        if theme.startswith("alphabet_"):
            letter = theme.replace("alphabet_", "").upper()
            return f"""Create an alphabet colouring page for letter {letter} for a 5 year old.

DRAW:
- The people from the photo wearing simple COSTUMES that start with {letter} (e.g. for E: explorer outfit with hat)
- A big friendly letter {letter} CHARACTER with a cute face, arms and legs
- 3-4 objects that start with {letter} (e.g. for E: elephant, eggs, envelope)

IMPORTANT: Do NOT put the letter {letter} printed on clothing - dress them in themed COSTUMES instead

STYLE:
- BLACK OUTLINES ON WHITE ONLY - NO grey, NO shading
- Medium-thick black outlines
- Simple but clear figures
- The letter {letter} must be LARGE and clearly visible
- Maximum 20-25 colourable areas

NO TEXT - do not write any words or labels

BACKGROUND:
- MINIMAL - simple ground line, maybe 1-2 clouds
- Keep mostly white

OUTPUT: People in {letter}-themed costumes with friendly letter character and several {letter} objects."""
        
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
    # PHOTO-ACCURATE MODE - completely different prompt for "none" theme
    if theme == "none" and not custom_theme:
        base_prompt = """Convert this photograph into a colouring book page.

CRITICAL: Only draw what is ACTUALLY in the photo. DO NOT add any animals, people, or objects that are not in the original image.

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

DO NOT ADD: Any pets, animals, extra people, or objects not visible in the original photo.

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
    
    # CHECK FOR TEXT-ONLY THEMES FIRST (maths, times tables, etc.)
    
    # Handle "dot_to_dot X" dynamic theme
    if description.startswith("dot_to_dot "):
        subject = description.replace("dot_to_dot ", "")
        base_prompt = f"""Create a children's dot-to-dot activity page featuring: {subject}

⚠️ ABSOLUTE REQUIREMENT - 100% BLACK AND WHITE:
- ONLY black lines/dots on pure white background
- NO grey anywhere - not even light grey
- NO shading, NO gradients

MAIN ELEMENT - DOT TO DOT OUTLINE:
- Create the outline of a {subject} using ONLY DOTS (black circles)
- The dots should form the shape of {subject} but NOT be connected
- Space the dots evenly so a child can connect them with a pencil
- NO NUMBERS on the dots - just plain dots
- The shape should be recognizable as {subject} when connected
- Make dots fairly large and clear

SURROUNDING SCENE:
- Add a few simple related items around the dot-to-dot (fully drawn, not dots)
- Include 1-2 children holding pencils/crayons
- Keep background minimal

The child's task is to connect the dots to reveal the {subject}."""
        
        if age_level in CONFIG["age_levels"]:
            base_prompt += "\n\n" + CONFIG["age_levels"][age_level]["overlay"]
        
        return base_prompt

    # Handle "find_the X" dynamic theme
    if description.startswith("find_the "):
        subject = description.replace("find_the ", "")
        base_prompt = f"""Create a children's colouring book page - a "find and seek" game featuring: {subject}

⚠️ ABSOLUTE REQUIREMENT - 100% BLACK AND WHITE:
- ONLY black lines on pure white background
- NO grey anywhere - not even light grey
- NO shading, NO gradients, NO filled areas
- Every area must be PURE WHITE inside black outlines

SCENE: Create an appropriate NATURAL HABITAT for {subject}:
- If animal: their natural environment (rabbit=field with grass and burrows, fish=underwater with coral, bird=forest with trees)
- If object: where you would find it (football=pitch with goals, car=street with buildings)

IMPORTANT - Hide 8-12 copies of {subject} throughout the scene:
- Some fully visible in the open
- Some peeking out from behind things (bushes, rocks, trees)
- Some partially hidden
- Some small in the background
- Scatter them ALL OVER the scene

DO NOT INCLUDE:
- Any numbers
- Any text or words  
- Any people or children
- Any other animals (ONLY {subject})

Just the habitat scene with multiple {subject} hidden throughout to find."""
        
        if age_level in CONFIG["age_levels"]:
            base_prompt += "\n\n" + CONFIG["age_levels"][age_level]["overlay"]
        
        return base_prompt
    
    # Check in themes section for text_only themes
    if "themes" in CONFIG and description in CONFIG["themes"]:
        theme_data = CONFIG["themes"][description]
        if theme_data.get("text_only", False):
            # Use master_text_prompt + theme overlay
            base_prompt = CONFIG.get("master_text_prompt", {}).get("prompt", "")
            base_prompt += "\n\n" + theme_data.get("overlay", "")
            
            # Add age level overlay if exists
            if age_level in CONFIG["age_levels"]:
                base_prompt += "\n\n" + CONFIG["age_levels"][age_level]["overlay"]
            
            return base_prompt
    
    # Check in times_tables section (legacy)
    if "times_tables" in CONFIG and description in CONFIG["times_tables"]:
        theme_data = CONFIG["times_tables"][description]
        base_prompt = CONFIG.get("master_text_prompt", {}).get("prompt", "")
        base_prompt += "\n\n" + theme_data.get("prompt", "")
        
        # Add age level overlay if exists
        if age_level in CONFIG["age_levels"]:
            base_prompt += "\n\n" + CONFIG["age_levels"][age_level]["overlay"]
        
        return base_prompt
    
    # TODDLER MODE (age 3-4) - super simple single object
    if age_level == "age_3":
        return f"""Create an EXTREMELY SIMPLE toddler colouring page.

CRITICAL: Only draw what is ACTUALLY in the photo. DO NOT add any animals, objects, or elements not in the original image.

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


async def _generate_from_text_single(prompt: str, quality: str = "low") -> dict:
    """Single generation attempt for text-to-image"""
    
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


async def generate_from_text(prompt: str, quality: str = "low", max_retries: int = 3) -> dict:
    """
    Generate colouring page from text with auto-retry for dark/grey images.
    Logs all attempts for failure rate tracking.
    """
    
    for attempt in range(1, max_retries + 1):
        result = await _generate_from_text_single(prompt, quality)
        
        image_b64 = result["data"][0].get("b64_json")
        
        if image_b64:
            is_valid, brightness = is_valid_coloring_page(image_b64)
            
            # Log this attempt
            log_generation_attempt(
                prompt_preview=prompt,
                attempt=attempt,
                success=is_valid,
                brightness=brightness,
                retried=(attempt > 1)
            )
            
            if is_valid:
                if attempt > 1:
                    print(f"✅ Attempt {attempt}: Success after retry (brightness={brightness:.0f})")
                return result
            
            print(f"⚠️ Attempt {attempt}/{max_retries}: Dark image detected (brightness={brightness:.0f}), retrying...")
        else:
            # URL response - can't check brightness, just return it
            return result
    
    # All retries failed - return last attempt anyway (user sees it, we logged it)
    print(f"❌ WARNING: All {max_retries} attempts produced dark images for prompt")
    return result


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


@app.get("/failure-stats")
async def get_failure_stats():
    """Get generation failure statistics"""
    try:
        if not FAILURE_LOG.exists():
            return {"total": 0, "failures": 0, "failure_rate": 0, "retries_needed": 0}
        
        with open(FAILURE_LOG, "r") as f:
            lines = f.readlines()
        
        total = len(lines)
        failures = sum(1 for line in lines if '"success": false' in line)
        retries = sum(1 for line in lines if '"retried": true' in line)
        
        return {
            "total_attempts": total,
            "failures": failures,
            "failure_rate": round(failures / total * 100, 1) if total > 0 else 0,
            "retries_needed": retries,
            "retry_rate": round(retries / (total - retries) * 100, 1) if (total - retries) > 0 else 0
        }
    except Exception as e:
        return {"error": str(e)}


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
        age_level=normalize_age_level(request.age_level),
        theme=request.theme,
        custom_theme=request.custom_theme
    )
    
    # Generate
    start = datetime.now()
    result = await generate_from_photo(prompt, request.image_b64, request.quality)
    elapsed = (datetime.now() - start).total_seconds()
    
    # Get image
    image_data = result["data"][0]
    
    # Get base64 image
    if "b64_json" in image_data:
        output_b64 = image_data["b64_json"]
    else:
        # If OpenAI returns URL, download it
        async with httpx.AsyncClient() as client:
            resp = await client.get(image_data["url"])
            output_b64 = base64.b64encode(resp.content).decode('utf-8')
    
    # Upload image to Firebase and get URL
    try:
        image_url = upload_to_firebase(output_b64, folder="generations")
    except Exception as e:
        print(f"Firebase upload failed: {e}")
        # Fallback to returning base64 if Firebase fails
        return {
            "success": True,
            "image": output_b64,
            "image_type": "base64",
            "pdf": None,
            "generation_time": elapsed,
            "theme_used": request.custom_theme or request.theme,
            "age_level": request.age_level
        }
    
    # Generate PDF and upload to Firebase
    pdf_url = None
    try:
        pdf_b64 = create_a4_pdf(output_b64)
        pdf_url = upload_to_firebase(pdf_b64, folder="pdfs")
    except Exception as e:
        print(f"PDF generation/upload failed: {e}")
    
    return {
        "success": True,
        "image_url": image_url,
        "pdf_url": pdf_url,
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
    prompt = build_text_to_image_prompt(request.description, normalize_age_level(request.age_level))
    
    # Generate (with auto-retry for dark images)
    start = datetime.now()
    result = await generate_from_text(prompt, request.quality)
    elapsed = (datetime.now() - start).total_seconds()
    
    # Get image
    image_data = result["data"][0]
    
    # Get base64 image
    if "b64_json" in image_data:
        output_b64 = image_data["b64_json"]
    else:
        # If OpenAI returns URL, download it
        async with httpx.AsyncClient() as client:
            resp = await client.get(image_data["url"])
            output_b64 = base64.b64encode(resp.content).decode('utf-8')
    
    # Upload image to Firebase and get URL
    try:
        image_url = upload_to_firebase(output_b64, folder="generations")
    except Exception as e:
        print(f"Firebase upload failed: {e}")
        # Fallback to returning base64 if Firebase fails
        return {
            "success": True,
            "image": output_b64,
            "image_type": "base64",
            "pdf": None,
            "generation_time": elapsed,
            "description": request.description,
            "age_level": request.age_level
        }
    
    # Generate PDF and upload to Firebase
    pdf_url = None
    try:
        pdf_b64 = create_a4_pdf(output_b64)
        pdf_url = upload_to_firebase(pdf_b64, folder="pdfs")
    except Exception as e:
        print(f"PDF generation/upload failed: {e}")
    
    return {
        "success": True,
        "image_url": image_url,
        "pdf_url": pdf_url,
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
