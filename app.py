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
from job_endpoints import job_router
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
app.include_router(job_router, tags=["Jobs"])

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
    # Handle slider display values like "age_Under 3" and "age_10+"
    if "Under 3" in age_input or "under_3" in age_input or "under 3" in age_input.lower():
        return "under_3"
    if "10+" in age_input:
        return "age_10"
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

def normalize_theme(theme_input: str) -> str:
    """Convert theme inputs to standard keys - handles caps, spaces, ampersands"""
    if not theme_input:
        return "none"
    # Lowercase and replace spaces/ampersands with underscores
    normalized = theme_input.lower().replace(" & ", "_").replace(" ", "_").replace("&", "_")
    return normalized

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
    """Build prompt for photo-to-colouring mode - wrapper that adds universal photo instruction"""
    
    prompt = _build_photo_prompt_inner(age_level, theme, custom_theme)
    
    # Only add photo awareness for actual photo prompts, NOT alphabet or find-and-seek
    description = custom_theme or theme or "none"
    is_alphabet = description.startswith("alphabet_")
    is_find_seek = description.startswith("find_the ")
    is_pattern = description.startswith("pattern_")
    
    if not is_alphabet and not is_find_seek and not is_pattern:
        PHOTO_AWARENESS = """

IMPORTANT - DRAW ONLY WHAT IS IN THE PHOTO:
- If the photo contains ONLY animals (pets, wildlife) with NO people: draw ONLY the animals. Do NOT invent or add any human characters, cartoon people, or faces. Ignore any instructions about human faces, hair, clothing, smiles, noses, or eyes — those only apply when people are present in the photo.
- If the photo is a landscape or scene with NO people and NO animals: draw ONLY the landscape/scene. Do NOT add any characters, people, or animals.
- If the photo contains people: follow all face, hair, and clothing instructions as normal.
- NEVER invent subjects that are not in the original photo."""
        prompt = PHOTO_AWARENESS + "\n" + prompt
    
    return prompt


def _build_photo_prompt_inner(age_level: str = "age_5", theme: str = "none", custom_theme: str = None) -> str:
    """Build prompt for photo-to-colouring mode"""
    
    # UNDER 3 - blob shapes bypass
    if age_level == "under_3":
        # NO THEME - photo only
        if theme == "none" and not custom_theme:
            return """Create the SIMPLEST possible BLACK AND WHITE colouring page for a 2 year old baby.

CRITICAL: Only draw what is ACTUALLY in the photo. DO NOT add anything not in the original image.

CRITICAL - COUNT THE SUBJECTS: Look at the photo carefully. Count EVERY person and animal visible. Draw EXACTLY that many - NO MORE, NO LESS. NEVER add or remove anyone.

DRAW:
- The subjects from the photo (people and/or animals) as VERY simple blob characters
- THAT IS ALL - NOTHING ELSE

STYLE:
- BLACK OUTLINES ON WHITE ONLY - absolutely NO colour, NO pink cheeks, NO blush, NO shading
- EXTREMELY THICK black outlines - thicker than a normal colouring book
- Blob/kawaii style - super rounded and chunky
- Faces: just dots for eyes, single curved line smile - NOT an open mouth, just one simple upward curve
- Hair as simple outline shape only - NOT filled in, NOT solid black
- NO solid black fill anywhere - sunglasses, hair, accessories must all be HOLLOW outlines only
- Clothing as simple outer shapes only (e.g. t-shirt neckline, shorts outline) - NO internal detail, NO pockets, NO buttons, NO patterns, NO stitching
- If full body visible, arms and legs as short thick rounded stubs - same chunky thickness as the body, NOT thin sticks
- If wearing clothes, assume shoes - draw simple chunky shoe shapes, NOT bare feet
- Small slits on ends of hands and feet to suggest fingers/toes - NOT full fingers, just small indentations
- Maximum 8-10 colourable areas TOTAL

BACKGROUND:
- PURE WHITE - absolutely nothing else

OUTPUT: Simple blob figures on pure white. ONLY the subjects from the photo."""

        theme_name = custom_theme if custom_theme else theme

        if theme_name == "none":
            theme_name = "the scene"
        # Special handling for alphabet themes
        if theme.startswith("alphabet_"):
            letter = theme.replace("alphabet_", "").upper()
            best_object = {
                'a': 'apple', 'b': 'ball', 'c': 'cat', 'd': 'dog', 'e': 'elephant',
                'f': 'fish', 'g': 'goat', 'h': 'hat', 'i': 'ice cream', 'j': 'jellyfish',
                'k': 'kite', 'l': 'lion', 'm': 'monkey', 'n': 'nose', 'o': 'owl',
                'p': 'penguin', 'q': 'queen', 'r': 'rainbow', 's': 'star', 't': 'tiger',
                'u': 'umbrella', 'v': 'violin', 'w': 'whale', 'x': 'xylophone',
                'y': 'yo-yo', 'z': 'zebra'
            }.get(letter.lower(), 'apple')
            return f"""Create the SIMPLEST possible BLACK AND WHITE colouring page for a 2 year old baby.

DRAW:
- The subjects from the photo (people and/or animals) as VERY simple blob shapes (round heads, simple body)
- A big bold UPPERCASE CAPITAL letter {letter} as a FLAT 2D PROP (plain block letter or bubble letter - NOT a character - NO face, NO arms, NO legs, NO shoes, NO eyes, NO mouth - just a plain letter shape). Nobody holds or wears the letter.
- ONE simple {best_object} next to the letter

STYLE:
- BLACK OUTLINES ON WHITE ONLY - no colour, no grey, no shading
- EXTREMELY THICK black outlines
- Blob/kawaii style - super rounded and chunky
- Faces: just dots for eyes, simple curve for mouth
- Maximum 8-10 colourable areas TOTAL
- NO dots, NO speckles, NO texture, NO noise anywhere on the page
- Every area must be PURE WHITE inside black outlines
- ALL lines must connect perfectly - no gaps
- Clean, smooth lines - no sketchy or broken lines

BACKGROUND:
- PURE WHITE - absolutely nothing else

OUTPUT: Simple blob figures with friendly letter {letter} character on pure white."""

        return f"""Create the SIMPLEST possible BLACK AND WHITE colouring page for a 2 year old baby.

CRITICAL - COUNT THE SUBJECTS: Look at the photo carefully. Count the humans and count the pets/animals. Draw EXACTLY that many of each - NO MORE, NO LESS. If there are 0 people, draw 0 people. If there is 1 person, draw 1 person. If there is 1 dog, draw 1 dog. NEVER add extra humans not in the photo - no random girls, boys, men, women, babies or children. NEVER duplicate pets from the photo. Themed elements (e.g. safari animals, dinosaurs) ARE allowed as separate additions to the scene.
Keep the EXACT age of every person - a baby MUST look like a baby, a toddler like a toddler. Do NOT age up or age down anyone.

DRAW:
- The subjects from the photo (people and/or animals) as VERY simple blob characters
- Give them simple {theme_name} costume elements (e.g. a hat or simple outfit shape)
- 1-2 simple {theme_name} themed elements next to them (NOT a person - e.g. safari animal, pirate treasure chest, superhero lightning bolt)

STYLE:
- BLACK OUTLINES ON WHITE ONLY - no colour, no grey, no shading
- EXTREMELY THICK black outlines - thicker than a normal colouring book
- Blob/kawaii style - super rounded and chunky
- Faces: TINY pinpoint dots for eyes (like a period, not big circles), single curved line smile - NOT an open mouth, just one simple upward curve
- NO detailed features
- Small slits on ends of hands and feet to suggest fingers/toes - NOT full fingers, just small indentations
- Hair as simple outline shape only - NOT filled in, NOT solid black
- NO solid black fill anywhere - sunglasses, hair, accessories must all be HOLLOW outlines only
- Clothing as simple outer shapes only (e.g. t-shirt neckline, shorts outline) - NO internal detail, NO pockets, NO buttons, NO patterns, NO stitching
- Rounded feet on every character (chunky shoes if wearing thcat push_notifications.pyem, rounded blob feet if barefoot or animal)
- Bodies as simple rounded shapes
- Maximum 10-12 colourable areas TOTAL

BACKGROUND:
- PURE WHITE - no background scene

OUTPUT: Simple blob figures in {theme_name} costumes with themed elements on white."""

    # AGE 3 - super simple bypass
    if age_level == "age_3":
        # NO THEME - photo accurate only
        if theme == "none" and not custom_theme:
            return """Create an EXTREMELY SIMPLE colouring page for a 3 year old.

CRITICAL: Only draw what is ACTUALLY in the photo. DO NOT add anything not in the original image.

CRITICAL - COUNT THE SUBJECTS: Look at the photo carefully. Count EVERY person and animal visible. Draw EXACTLY that many - NO MORE, NO LESS. NEVER add or remove anyone.

DRAW:
- The subjects from the photo (people and/or animals) as very basic shapes - blob-like but recognisable
- THAT IS ALL - NOTHING ELSE

STYLE:
- BLACK OUTLINES ON WHITE ONLY - absolutely NO colour, NO pink cheeks, NO blush, NO shading anywhere
- VERY THICK black outlines
- Simple blob-like shapes
- Faces: dot eyes, small curved line nose on EVERY face, single curved line smile - NOT an open mouth
- Hair as simple outline shape only - NOT filled in, NOT solid black
- NO solid black fill anywhere - sunglasses, hair, accessories must all be HOLLOW outlines only
- Match the crop of the photo EXACTLY - if photo is waist up, ONLY draw waist up, do NOT invent legs or feet below the crop line. If full body visible, draw rounded feet (chunky shoes if wearing them, rounded blob feet if barefoot or animal)
- Maximum 10-12 colourable areas TOTAL

BACKGROUND:
- PURE WHITE - absolutely nothing else

OUTPUT: Simple black outline figures on pure white. ONLY the subjects from the photo. ZERO colour anywhere - no pink, no grey, no shading, no cheek circles, no blush marks. Pure black lines on pure white only."""

        theme_name = custom_theme if custom_theme else theme

        if theme_name == "none":
            theme_name = "the scene"
        
        # Special handling for alphabet themes
        if theme.startswith("alphabet_"):
            letter = theme.replace("alphabet_", "").upper()
            best_object = {
                'a': 'apple', 'b': 'ball', 'c': 'cat', 'd': 'dog', 'e': 'elephant',
                'f': 'fish', 'g': 'goat', 'h': 'hat', 'i': 'ice cream', 'j': 'jellyfish',
                'k': 'kite', 'l': 'lion', 'm': 'monkey', 'n': 'nose', 'o': 'owl',
                'p': 'penguin', 'q': 'queen', 'r': 'rainbow', 's': 'star', 't': 'tiger',
                'u': 'umbrella', 'v': 'violin', 'w': 'whale', 'x': 'xylophone',
                'y': 'yo-yo', 'z': 'zebra'
            }.get(letter.lower(), 'apple')
            return f"""Create an EXTREMELY SIMPLE toddler alphabet colouring page for letter {letter}.

DRAW:
- The subjects from the photo (people and/or animals) as VERY simple blob shapes (round heads, simple chunky body)
- Plain simple clothing - NO patterns, NO costumes
- A big bold UPPERCASE CAPITAL letter {letter} as a FLAT 2D PROP (plain block letter or bubble letter - NOT a character - NO face, NO arms, NO legs, NO shoes, NO eyes, NO mouth - just a plain letter shape). Nobody holds or wears the letter.
- ONE simple {best_object} next to the letter

STYLE:
- BLACK OUTLINES ON WHITE ONLY - no colour, no grey, no shading
- EXTREMELY THICK black outlines
- Blob/kawaii style - super rounded and chunky figures
- Faces: just dots for eyes, simple curve for mouth
- NO fingers, NO detailed features
- Bodies as simple rounded shapes
- Maximum 10-12 colourable areas TOTAL
- NO dots, NO speckles, NO texture, NO noise anywhere on the page
- Every area must be PURE WHITE inside black outlines
- ALL lines must connect perfectly - no gaps
- Clean, smooth lines - no sketchy or broken lines

BACKGROUND:
- PURE WHITE - absolutely nothing else
- No ground, no shadows, nothing

OUTPUT: Simple black outline blob figures standing next to a friendly letter {letter} character on pure white."""
        
        return f"""Create an EXTREMELY SIMPLE toddler colouring page.

CRITICAL - COUNT THE SUBJECTS: Look at the photo carefully. Count the humans and count the pets/animals. Draw EXACTLY that many of each - NO MORE, NO LESS. If there are 0 people, draw 0 people. If there is 1 person, draw 1 person. If there is 1 dog, draw 1 dog. NEVER add extra humans not in the photo - no random girls, boys, men, women, babies or children. NEVER duplicate pets from the photo. Themed elements (e.g. safari animals, dinosaurs) ARE allowed as separate additions to the scene.
Keep the EXACT age of every person - a baby MUST look like a baby, a toddler like a toddler. Do NOT age up or age down anyone.

DRAW ONLY:
- The subjects from the photo (people and/or animals) as very basic shapes
- Give them simple {theme_name} costume elements (e.g. a hat or simple outfit shape)
- 2 simple {theme_name} themed elements next to them
- THAT IS ALL - NOTHING ELSE

ABSOLUTE REQUIREMENTS:
- PURE WHITE BACKGROUND - no sky, no clouds, no ground, no grass, nothing
- VERY THICK black outlines only
- Simple blob-like shapes
- Faces: dot eyes, small curved line nose on EVERY face, single curved line smile - NOT an open mouth
- Hair as simple outline shape only - NOT filled in, NOT solid black
- NO solid black fill anywhere - sunglasses, hair, accessories must all be HOLLOW outlines only
- MAXIMUM 10-12 large colourable areas in the ENTIRE image
- NO patterns, NO details, NO small elements

OUTPUT: Thick simple outlines on pure white. Nothing in background."""

    # AGE 4 - simple figures with costumes bypass
    if age_level == "age_4":
        # NO THEME - photo only
        if theme == "none" and not custom_theme:
            return """Create a SIMPLE colouring page for a 4 year old.

CRITICAL: Only draw what is ACTUALLY in the photo. DO NOT add anything not in the original image.

DRAW:
- The subjects from the photo (people and/or animals) as simplified but real outlines (NOT round blobs - actual shapes of people, clothes, hair)
- The most prominent object from the photo background as a VERY SIMPLE outline only (no internal details, no complex parts - just the basic shape)
- THAT IS ALL - NOTHING ELSE

STYLE:
- BLACK OUTLINES ON WHITE ONLY
- THICK black outlines
- Simple rounded shapes
- NO internal details on objects - just outer outline
- Maximum 15-18 colourable areas TOTAL

BACKGROUND:
- PURE WHITE - no sky, no ground, no scenery

OUTPUT: Simple blob figures with a basic outline of the main background object. Keep everything chunky and simple."""

        theme_name = custom_theme if custom_theme else theme
        if theme_name == "none":
            theme_name = "the scene"
        
        # Special handling for alphabet themes
        if theme.startswith("alphabet_"):
            letter = theme.replace("alphabet_", "").upper()
            best_object = {
                'a': 'apple', 'b': 'ball', 'c': 'cat', 'd': 'dog', 'e': 'elephant',
                'f': 'fish', 'g': 'goat', 'h': 'hat', 'i': 'ice cream', 'j': 'jellyfish',
                'k': 'kite', 'l': 'lion', 'm': 'monkey', 'n': 'nose', 'o': 'owl',
                'p': 'penguin', 'q': 'queen', 'r': 'rainbow', 's': 'star', 't': 'tiger',
                'u': 'umbrella', 'v': 'violin', 'w': 'whale', 'x': 'xylophone',
                'y': 'yo-yo', 'z': 'zebra'
            }.get(letter.lower(), 'apple')
            letter_objects = {
                'a': 'apple, airplane, ant, alligator, anchor, arrow, acorn, avocado, axe, ambulance, armadillo, angelfish, apron',
                'b': 'ball, butterfly, banana, bear, boat, book, balloon, bee, bell, bird, bicycle, bucket, bus, basket, bow, bridge, bone',
                'c': 'cat, car, cake, castle, crown, cow, cloud, crab, candle, carrot, caterpillar, clock, cup, compass, cherry, camel',
                'd': 'dog, dinosaur, dolphin, drum, duck, daisy, diamond, door, dragonfly, dice, deer, dragon, domino, dove',
                'e': 'elephant, egg, envelope, eagle, ear, earth, elf, emerald, easel, emu, eye, engine',
                'f': 'fish, flower, frog, flag, feather, fox, fire, flamingo, fan, fence, fork, fairy, flute, fern',
                'g': 'giraffe, grapes, guitar, ghost, goat, glasses, globe, gorilla, gift, goldfish, garden gate, gem, glove, grasshopper',
                'h': 'hat, horse, house, heart, helicopter, hippo, hammer, harp, hedgehog, hen, honey jar, hook, hose, hummingbird, harmonica',
                'i': 'ice cream, igloo, iguana, iron, island, ivy, icicle, insect, ink bottle',
                'j': 'jellyfish, jam jar, jigsaw puzzle, jug, jacket, jet, jewel, jump rope, jester hat',
                'k': 'kite, key, kangaroo, king, kitten, kettle, kayak, koala, knight shield, kazoo',
                'l': 'lion, ladder, leaf, lemon, lighthouse, lizard, lamp, lollipop, log, lobster, lock, llama, lantern',
                'm': 'monkey, moon, mushroom, mouse, mountain, mermaid, mittens, magnet, map, muffin, medal, microscope, mailbox, mask, marble',
                'n': 'nest, needle, newt, net, necklace, notebook, nut, narwhal',
                'o': 'octopus, orange, owl, otter, onion, orchid, ostrich, orca, ornament, oar',
                'p': 'penguin, pizza, parrot, pumpkin, piano, pear, pig, pirate hat, paintbrush, pencil, popcorn, panda, present, puzzle piece, palm tree',
                'q': 'queen, quilt, question mark, quail, quiver of arrows',
                'r': 'rocket, rainbow, robot, rabbit, rose, ring, ruler, rain cloud, reindeer, rooster, rope, racket, rhinoceros, radio',
                's': 'star, sun, snake, ship, strawberry, snowman, scissors, shell, spider, skateboard, sword, sunflower, snail, scarf, seahorse',
                't': 'turtle, train, tree, trumpet, tiger, telescope, tent, tractor, teapot, teddy bear, tooth, tomato, treasure chest, tambourine',
                'u': 'umbrella, unicorn, ukulele, UFO, uniform',
                'v': 'violin, volcano, vase, van, vine, vulture, valentine heart',
                'w': 'whale, watermelon, windmill, wagon, watch, wizard hat, wolf, worm, web, window, watering can, walrus, wings, wand',
                'x': 'xylophone, x-ray, x marks the spot',
                'y': 'yacht, yo-yo, yak, yarn ball',
                'z': 'zebra, zip, zoo gate, zigzag, zeppelin',
            }.get(letter.lower(), 'apple, airplane, ant')
            return f"""Create a SIMPLE alphabet colouring page for letter {letter} for a 4 year old.

DRAW:
- The subjects from the photo (people and/or animals) as simple cute figures
- A big bold UPPERCASE CAPITAL letter {letter} as a FLAT 2D PROP (plain block letter or bubble letter - NOT a character - NO face, NO arms, NO legs, NO shoes, NO eyes, NO mouth - just a plain letter shape). Nobody holds or wears the letter.
- A {best_object} and one other object ONLY from this list: {letter_objects}

CRITICAL: EVERY object in this image MUST start with the letter {letter}. Do NOT draw anything that does not start with {letter}.

STYLE:
- BLACK OUTLINES ON WHITE ONLY
- THICK black outlines  
- Simple rounded figures
- The letter {letter} must be LARGE and clearly visible
- Maximum 15-18 colourable areas
- NO dots, NO speckles, NO texture, NO noise anywhere on the page
- Every area must be PURE WHITE inside black outlines
- ALL lines must connect perfectly - no gaps
- Clean, smooth lines - no sketchy or broken lines

NO TEXT - do not write any words or labels

BACKGROUND:
- PURE WHITE - no ground, no scenery

OUTPUT: Simple figures with friendly letter character and a few {letter} objects. No text."""
        
        return f"""Create a SIMPLE colouring page for a 4 year old.

CRITICAL - COUNT THE SUBJECTS: Look at the photo carefully. Count the humans and count the pets/animals. Draw EXACTLY that many of each - NO MORE, NO LESS. If there are 0 people, draw 0 people. If there is 1 person, draw 1 person. If there is 1 dog, draw 1 dog. NEVER add extra humans not in the photo - no random girls, boys, men, women, babies or children. NEVER duplicate pets from the photo. Themed elements (e.g. safari animals, dinosaurs) ARE allowed as separate additions to the scene.
Keep the EXACT age of every person - a baby MUST look like a baby, a toddler like a toddler. Do NOT age up or age down anyone.

DRAW:
- The subjects from the photo (people and/or animals) as simplified but real outlines (NOT round blobs - actual shapes of people, clothes, hair) with basic {theme_name} costumes
- 2-3 {theme_name} themed elements around them (NOT extra people - e.g. safari animals, pirate treasure, superhero shields)
- 1 simple {theme_name} scene element (e.g. simple building outline, tree, vehicle)

STYLE:
- BLACK OUTLINES ON WHITE ONLY - NO grey, NO shading, NO texture, NO gradients
- THICK black outlines
- Simple rounded figures
- Faces: dots for eyes, small curved line nose on EVERY face, single curved line smile - NOT an open mouth, basic hair shape
- Hair as simple outline shape only - NOT filled in, NOT solid black
- NO solid black fill anywhere - sunglasses, hair, accessories must all be HOLLOW outlines only
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

CRITICAL: Only draw what is ACTUALLY in the photo. DO NOT add any animals, pets, or objects not in the original image. Keep EVERY person visible - do NOT remove anyone (including babies being held).

DRAW:
- The subjects from the photo (people and/or animals) as simplified but real outlines (NOT round blobs - actual shapes of people, clothes, hair)
- Background elements from the photo (simplified)
- THAT IS ALL - NOTHING ELSE

STYLE:
- BLACK OUTLINES ON WHITE ONLY
- THICK black outlines - easy for small hands
- Draw the REAL outline shapes of people and objects but with NO internal detail
- NO tyre treads, NO window details, NO ground texture, NO clothing patterns
- Faces: properly drawn eyes with simple detail, nose, smile - recognisable features matching the photo
- Objects: just the outer silhouette shape, no internal lines
- Maximum 15-20 colourable areas

BACKGROUND:
- MINIMAL - simple ground line only, mostly white

DO NOT ADD: Any pets, animals, or objects not in the original photo.

OUTPUT: Thick simplified outlines of REAL shapes on white. Halfway between cartoon blobs and detailed drawing."""

        theme_name = custom_theme if custom_theme else theme
        if theme_name == "none":
            theme_name = "the scene"
        
        # Special handling for alphabet themes
        if theme.startswith("alphabet_"):
            letter = theme.replace("alphabet_", "").upper()
            letter_objects = {
                'a': 'apple, airplane, ant, alligator, anchor, arrow, acorn, avocado, axe, ambulance, armadillo, angelfish, apron',
                'b': 'ball, butterfly, banana, bear, boat, book, balloon, bee, bell, bird, bicycle, bucket, bus, basket, bow, bridge, bone',
                'c': 'cat, car, cake, castle, crown, cow, cloud, crab, candle, carrot, caterpillar, clock, cup, compass, cherry, camel',
                'd': 'dog, dinosaur, dolphin, drum, duck, daisy, diamond, door, dragonfly, dice, deer, dragon, domino, dove',
                'e': 'elephant, egg, envelope, eagle, ear, earth, elf, emerald, easel, emu, eye, engine',
                'f': 'fish, flower, frog, flag, feather, fox, fire, flamingo, fan, fence, fork, fairy, flute, fern',
                'g': 'giraffe, grapes, guitar, ghost, goat, glasses, globe, gorilla, gift, goldfish, garden gate, gem, glove, grasshopper',
                'h': 'hat, horse, house, heart, helicopter, hippo, hammer, harp, hedgehog, hen, honey jar, hook, hose, hummingbird, harmonica',
                'i': 'ice cream, igloo, iguana, iron, island, ivy, icicle, insect, ink bottle',
                'j': 'jellyfish, jam jar, jigsaw puzzle, jug, jacket, jet, jewel, jump rope, jester hat',
                'k': 'kite, key, kangaroo, king, kitten, kettle, kayak, koala, knight shield, kazoo',
                'l': 'lion, ladder, leaf, lemon, lighthouse, lizard, lamp, lollipop, log, lobster, lock, llama, lantern',
                'm': 'monkey, moon, mushroom, mouse, mountain, mermaid, mittens, magnet, map, muffin, medal, microscope, mailbox, mask, marble',
                'n': 'nest, needle, newt, net, necklace, notebook, nut, narwhal',
                'o': 'octopus, orange, owl, otter, onion, orchid, ostrich, orca, ornament, oar',
                'p': 'penguin, pizza, parrot, pumpkin, piano, pear, pig, pirate hat, paintbrush, pencil, popcorn, panda, present, puzzle piece, palm tree',
                'q': 'queen, quilt, question mark, quail, quiver of arrows',
                'r': 'rocket, rainbow, robot, rabbit, rose, ring, ruler, rain cloud, reindeer, rooster, rope, racket, rhinoceros, radio',
                's': 'star, sun, snake, ship, strawberry, snowman, scissors, shell, spider, skateboard, sword, sunflower, snail, scarf, seahorse',
                't': 'turtle, train, tree, trumpet, tiger, telescope, tent, tractor, teapot, teddy bear, tooth, tomato, treasure chest, tambourine',
                'u': 'umbrella, unicorn, ukulele, UFO, uniform',
                'v': 'violin, volcano, vase, van, vine, vulture, valentine heart',
                'w': 'whale, watermelon, windmill, wagon, watch, wizard hat, wolf, worm, web, window, watering can, walrus, wings, wand',
                'x': 'xylophone, x-ray, x marks the spot',
                'y': 'yacht, yo-yo, yak, yarn ball',
                'z': 'zebra, zip, zoo gate, zigzag, zeppelin',
            }.get(letter.lower(), 'apple, airplane, ant')
            letter_costumes = {
                'a': 'astronaut, archer, artist, acrobat',
                'b': 'builder, ballerina, beekeeper',
                'c': 'cowboy, chef, clown',
                'd': 'doctor, dinosaur onesie, detective',
                'e': 'explorer with hat and binoculars, elf',
                'f': 'firefighter, fairy, farmer',
                'g': 'gardener with tools and apron, gorilla onesie, gymnast',
                'h': 'hippo onesie, horse rider outfit, hiker',
                'i': 'ice skater, insect onesie',
                'j': 'jester, jockey',
                'k': 'king, knight, karate outfit',
                'l': 'lion onesie, ladybird onesie, lifeguard',
                'm': 'magician, mermaid costume, monkey onesie',
                'n': 'ninja, nurse',
                'o': 'owl onesie, octopus costume',
                'p': 'pirate, princess, pilot',
                'q': 'queen',
                'r': 'robot costume, racing driver, Robin Hood',
                's': 'superhero, sailor, scientist',
                't': 'train conductor, tiger onesie',
                'u': 'unicorn onesie, umpire',
                'v': 'viking, vet',
                'w': 'wizard, witch',
                'x': 'superhero with X on chest, x-ray technician',
                'y': 'yak onesie, yachtsman',
                'z': 'zookeeper, zebra onesie',
            }.get(letter.lower(), 'astronaut')
            return f"""Create an alphabet colouring page for letter {letter} for a 5 year old.

DRAW:
- The subjects from the photo (people and/or animals) wearing COSTUMES from this list ONLY: {letter_costumes}
- A big bold UPPERCASE CAPITAL letter {letter} displayed prominently as a FLAT 2D PROP in the background (plain block letter or bubble letter - NOT a character - NO face, NO arms, NO legs, NO shoes, NO eyes, NO mouth - just a plain letter shape). Nobody holds or wears the letter.
- 3-4 objects ONLY from this list: {letter_objects}

CRITICAL: EVERY single object and costume in this image MUST start with the letter {letter}. If it does not start with {letter}, DO NOT DRAW IT. ONLY use objects from the list above.
IMPORTANT: Do NOT put the letter {letter} printed on clothing - dress them in themed COSTUMES instead

STYLE:
- BLACK OUTLINES ON WHITE ONLY - NO grey, NO shading
- Medium-thick black outlines
- Simple but clear figures
- The letter {letter} must be LARGE and clearly visible
- Maximum 20-25 colourable areas
- NO dots, NO speckles, NO texture, NO noise anywhere on the page
- Every area must be PURE WHITE inside black outlines
- ALL lines must connect perfectly - no gaps
- Clean, smooth lines - no sketchy or broken lines

NO TEXT - do not write any words or labels

BACKGROUND:
- MINIMAL - simple ground line, maybe 1-2 clouds
- Keep mostly white

OUTPUT: People in {letter}-themed costumes with a big flat UPPERCASE CAPITAL letter {letter} and several {letter} objects. The letter must be a flat 2D shape - NOT a character, NOT held by anyone, NOT worn as clothing."""
        
        return f"""Create a colouring page for a 5 year old.

CRITICAL - COUNT THE SUBJECTS: Look at the photo carefully. Count the humans and count the pets/animals. Draw EXACTLY that many of each - NO MORE, NO LESS. If there are 0 people, draw 0 people. If there is 1 person, draw 1 person. If there is 1 dog, draw 1 dog. NEVER add extra humans not in the photo - no random girls, boys, men, women, babies or children. NEVER duplicate pets from the photo. Themed creatures and objects (e.g. safari animals, dinosaurs) ARE allowed as separate additions to the scene.
Keep the EXACT age of every person - a baby MUST look like a baby, a toddler like a toddler. Do NOT age up or age down anyone.

DRAW:
- The subjects from the photo (people and/or animals) wearing simple {theme_name} costumes (basic outfits, not elaborate)
- 3-4 {theme_name} themed elements around the scene (NOT extra people - e.g. safari animals, pirate ships, superhero city elements)
- 2-3 {theme_name} scene elements to build a fuller themed scene (e.g. trees, vehicles, landscape features)

STYLE:
- BLACK OUTLINES ON WHITE ONLY - NO grey, NO shading, NO texture
- Medium-thick black outlines
- Simple but recognisable figures
- Faces: keep REAL facial features from the photo - recognisable nose, eyes, mouth shape
- Keep the EXACT age of every person - a baby MUST look like a baby, not a child
- Copy the EXACT hairstyle - length, parting, texture
- Do NOT make faces cartoonish or generic - this is a likeness
- Hair as simple outline shape only - NOT filled in, NOT solid black
- NO solid black fill anywhere - sunglasses, hair, accessories must all be HOLLOW outlines only
- Clothing: simple shapes, NO frills, NO layered skirts, NO intricate patterns
- Maximum 20-25 colourable areas

BACKGROUND:
- Fully immersive {theme_name} scene with themed scenery
- Themed landscape, ground, sky elements

OUTPUT: Recognisable figures in {theme_name} costumes with theme items and simplified photo background."""

    # AGE 6 - recognisable figures with face accuracy
    if age_level == "age_6":
        if theme == "none" and not custom_theme:
            return """Create a colouring page for a 6 year old based on this photo.

CRITICAL: Only draw what is ACTUALLY in the photo. DO NOT add extra people, animals, pets, or objects not in the original image. Keep EVERY person visible - do NOT remove anyone (including babies being held).

FACE ACCURACY (HIGHEST PRIORITY):
- TRACE the exact facial contours from the photo - do NOT reinterpret or stylize
- Match the PRECISE nose shape, eye spacing, mouth width, chin shape for EVERY person
- Copy the EXACT hairstyle for each person - length, parting, texture
- A parent MUST instantly recognise their specific children
- Keep real clothing details - specific shoes, patterns, stripes, accessories

DRAW:
- The subjects from the photo (people and/or animals) as recognisable figures
- Background elements from the photo (simplified)
- THAT IS ALL - NOTHING ELSE

STYLE:
- BLACK OUTLINES ON WHITE ONLY
- Medium-thick black outlines
- Simple but recognisable figures
- Maximum 25-30 colourable areas

BACKGROUND:
- Simple background from the photo
- 1-2 clouds, simple ground

DO NOT ADD: Any pets, animals, or objects not in the original photo.

OUTPUT: Recognisable figures with accurate faces and simple background."""


    # AGE 7 - more detail within objects, fuller scenes
    # PHOTO-ACCURATE MODE - completely different prompt for "none" theme
    if theme == "none" and not custom_theme:
        base_prompt = """Convert this photograph into a colouring book page.

CRITICAL: Only draw what is ACTUALLY in the photo. DO NOT add extra people, animals, or objects not in the original image. Keep EVERY person visible in the photo - do NOT remove anyone (including babies being held).

FACE ACCURACY (HIGHEST PRIORITY):
- TRACE the exact facial contours from the photo - do NOT reinterpret or stylize
- Match the PRECISE nose shape, eye spacing, mouth width, chin shape for EVERY person
- Copy the EXACT hairstyle for each person - length, parting, texture
- A parent MUST instantly recognise their specific children
- Keep real clothing details - specific shoes, patterns, stripes, accessories

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

    # Add face accuracy for all themed modes
    if age_level not in ["under_3"]:
        parts.append("\n\nFACE ACCURACY (HIGHEST PRIORITY):\n- TRACE the exact facial contours from the photo - do NOT reinterpret or stylize\n- Match the PRECISE nose shape, eye spacing, mouth width, chin shape for EVERY person\n- Copy the EXACT hairstyle for each person - length, parting, texture\n- A parent MUST instantly recognise their specific children\n- Keep real clothing details - specific shoes, patterns, stripes, accessories\n- Keep EVERY person visible in the photo - do NOT remove anyone (including babies being held)\n- Keep the EXACT age of every person - a baby MUST look like a baby, a toddler like a toddler, a child like a child. Do NOT age up or age down anyone\n- Do NOT make faces cartoonish or generic - this is a likeness, not a cartoon character")
    
    if custom_theme:
        parts.append("\n\n" + build_custom_theme_overlay(custom_theme))
    elif theme in CONFIG["themes"]:
        overlay = CONFIG["themes"][theme].get("overlay", "")
        if overlay:
            parts.append("\n\n" + overlay)
    elif theme != "none":
        # Theme not in presets - treat as custom theme text
        parts.append("\n\n" + build_custom_theme_overlay(theme))
    
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

        # ── UNDER_3 find and seek ──
        if age_level == "under_3":
            return f"""Create a children's colouring book page - a "find and seek" game.

⚠️ CRITICAL: Do NOT write ANY text, words, titles, labels, or numbers ANYWHERE on the image. ZERO text of any kind.

The OBJECT to find is: {subject}
Draw {subject} as a LITERAL OBJECT — the actual physical thing called "{subject}".

⚠️ 100% BLACK AND WHITE - ONLY black lines on pure white background. NO grey, NO shading, NO gradients, NO filled areas, NO stippling, NO dots for texture.

STYLE: Blob/kawaii style — super rounded and chunky. EXTREMELY THICK black outlines — thicker than a normal colouring book. Everything drawn in cute kawaii style.

SCENE: Draw a simple kawaii version of where {subject} ACTUALLY belongs in real life. The scene should match {subject} — a kawaii workshop for tools, a kawaii kitchen for food, a kawaii garden for animals, etc. But draw it VERY simply — only 2-3 basic background objects (e.g. a workbench and a toolbox for spanners, a table and an oven for food). All drawn in the same chunky kawaii style with thick outlines. Plenty of white space.

Hide exactly 5 copies of {subject} in the scene. Draw every copy the SAME WAY — big, chunky, kawaii. Most should be easy to spot — a couple slightly behind background objects but still obvious.

STRICT RULES:
- Scene MUST match where {subject} belongs — NOT a random scene
- Maximum 2-3 background objects, all kawaii style
- Do NOT draw any animals, people, children, or characters that are NOT {subject}
- NOTHING alive in the scene except copies of {subject} if it is an animal"""

        # ── AGE_3 find and seek ──
        if age_level == "age_3":
            return f"""Create a children's colouring book page - a "find and seek" game.

⚠️ CRITICAL: Do NOT write ANY text, words, titles, labels, or numbers ANYWHERE on the image. ZERO text of any kind.

The OBJECT to find is: {subject}
Draw {subject} as a LITERAL OBJECT — the actual physical thing called "{subject}".

⚠️ 100% BLACK AND WHITE - ONLY black lines on pure white background. NO grey, NO shading, NO gradients, NO filled areas, NO stippling, NO dots for texture.

STYLE: Blob-like but recognisable shapes. VERY THICK black outlines. Simple and chunky — NOT detailed or realistic.

SCENE: Draw a simple version of where {subject} ACTUALLY belongs in real life. The scene should match {subject} — a simple workshop for tools, a simple kitchen for food, a simple garden for animals, etc. Draw 3-4 background objects that belong in that location, all in chunky simple style. Keep good white space between objects.

Hide 6-7 copies of {subject} in the scene. Draw every copy the SAME WAY — chunky, simple style. Most clearly visible, some peeking out from behind background objects. Easy to spot for a young child.

STRICT RULES:
- Scene MUST match where {subject} belongs — NOT a random scene
- Maximum 3-4 background objects
- Do NOT draw any animals, people, children, or characters that are NOT {subject}
- NOTHING alive in the scene except copies of {subject} if it is an animal"""

        # ── AGE_4 find and seek ──
        if age_level == "age_4":
            return f"""Create a children's colouring book page - a "find and seek" game.

⚠️ CRITICAL: Do NOT write ANY text, words, titles, labels, or numbers ANYWHERE on the image. ZERO text of any kind.

The OBJECT to find is: {subject}
Draw {subject} as a LITERAL OBJECT — the actual physical thing called "{subject}".

⚠️ 100% BLACK AND WHITE - ONLY black lines on pure white background. NO grey, NO shading, NO gradients, NO filled areas, NO stippling, NO dots for texture.

STYLE: Simplified but real outlines (NOT blobs). THICK black outlines. Simple shapes with minimal internal detail.

SCENE: Draw a simplified version of where {subject} ACTUALLY belongs in real life. The scene should match {subject} — a workshop for tools, a kitchen for food, a habitat for animals, a playroom for toys, etc. Draw 5-6 background objects that belong in that location. Keep it clean with white space — not overly cluttered.

Hide 8-10 copies of {subject} among and around the scene objects. Draw every copy the SAME WAY each time.

HOW TO HIDE: Some in plain sight, some peeking out from behind background objects, some partially hidden. Mix of easy and slightly harder to spot.

STRICT RULES:
- Scene MUST match where {subject} belongs — NOT a random scene
- Maximum 5-6 background objects
- Do NOT draw any animals, people, children, or characters that are NOT {subject}
- NOTHING alive in the scene except copies of {subject} if it is an animal"""

        # ── AGE_5+ find and seek (full detail) ──
        base_prompt = f"""Create a children's colouring book page - a "find and seek" game.

⚠️ CRITICAL: Do NOT write ANY text, words, titles, labels, or numbers ANYWHERE on the image. NO title like "Find and Seek". NO count like "Find 10". The image must contain ZERO text of any kind.

The OBJECT to find is: {subject}
Draw {subject} as a LITERAL OBJECT — the actual physical thing called "{subject}". NOT an animal, NOT a character, NOT a mascot. The actual real-world object/thing.

⚠️ ABSOLUTE REQUIREMENT - 100% BLACK AND WHITE:
- ONLY black lines on pure white background
- NO grey anywhere - not even light grey
- NO shading, NO gradients, NO filled areas
- Every area must be PURE WHITE inside black outlines

SCENE: Think about where {subject} ACTUALLY lives or is used in real life. Draw THAT specific location as a detailed scene. Do NOT default to a generic outdoor park scene.
- Food/drink items (e.g. ketchup, pizza, cupcake): MUST be a kitchen, dining table, pantry, or restaurant
- Musical instruments: MUST be a music room, stage, or concert hall
- Animals (e.g. cat, dog, giraffe): their natural habitat or a home
- Outdoor sports/vehicles (e.g. planes, bikes): the place you'd find them (airport, road, sky)
- Toys/dolls (e.g. barbie, teddy bear): a playroom, bedroom, or toy shop
- Indoor items: the room you'd find them in

Fill the scene with objects, furniture, and scenery that BELONG in that location. Then hide 8-12 copies of {subject} (the LITERAL object, drawn the SAME WAY each time) scattered among the scene objects.

HOW TO HIDE {subject}:
- Some fully visible in the open
- Some peeking out from behind other objects
- Some partially hidden behind furniture/scenery
- Some small in the background
- Scatter them ALL OVER the scene — top, bottom, left, right, centre

STRICT RULES:
- Every hidden item MUST be {subject} — the same literal object repeated
- Do NOT draw any animals, people, children, or living characters
- Do NOT draw mascots, cartoon characters, or anthropomorphic versions
- Do NOT include any numbers or text
- The ONLY living/recognisable thing in the scene should be copies of {subject} (if {subject} is alive) or NOTHING alive (if {subject} is an object)
- NOTHING alive in the scene except copies of {subject} if it is an animal"""
        
        if age_level in CONFIG["age_levels"]:
            base_prompt += "\n\n" + CONFIG["age_levels"][age_level]["overlay"]
        
        return base_prompt
    
    # Handle alphabet themes with age-specific prompts
    if description.startswith("alphabet_"):
        letter = description.replace("alphabet_", "").upper()
        letter_lower = letter.lower()
        
        # Best single object for each letter - hardcoded for consistency
        best_object = {
            'a': 'apple',
            'b': 'ball',
            'c': 'cat',
            'd': 'dog',
            'e': 'elephant',
            'f': 'fish',
            'g': 'goat',
            'h': 'hat',
            'i': 'ice cream',
            'j': 'jellyfish',
            'k': 'kite',
            'l': 'lion',
            'm': 'monkey',
            'n': 'nose',
            'o': 'owl',
            'p': 'penguin',
            'q': 'queen',
            'r': 'rainbow',
            's': 'star',
            't': 'tiger',
            'u': 'umbrella',
            'v': 'violin',
            'w': 'whale',
            'x': 'xylophone',
            'y': 'yo-yo',
            'z': 'zebra',
        }.get(letter_lower, 'apple')
        
        # Full objects list per letter for ages 6+
        letter_objects = {
            'a': 'apple, airplane, ant, alligator, anchor, arrow, acorn, avocado, axe, ambulance, armadillo, angelfish, apron',
            'b': 'ball, butterfly, banana, bear, boat, book, balloon, bee, bell, bird, bicycle, bucket, bus, basket, bow, bridge, bone',
            'c': 'cat, car, cake, castle, crown, cow, cloud, crab, candle, carrot, caterpillar, clock, cup, compass, cherry, camel',
            'd': 'dog, dinosaur, dolphin, drum, duck, daisy, diamond, door, dragonfly, dice, deer, dragon, domino, dove',
            'e': 'elephant, egg, envelope, eagle, ear, earth, elf, emerald, easel, emu, eye, engine',
            'f': 'fish, flower, frog, flag, feather, fox, fire, flamingo, fan, fence, fork, fairy, flute, fern',
            'g': 'giraffe, grapes, guitar, ghost, goat, glasses, globe, gorilla, gift, goldfish, garden gate, gem, glove, grasshopper',
            'h': 'hat, horse, house, heart, helicopter, hippo, hammer, harp, hedgehog, hen, honey jar, hook, hose, hummingbird, harmonica',
            'i': 'ice cream, igloo, iguana, iron, island, ivy, icicle, insect, ink bottle',
            'j': 'jellyfish, jam jar, jigsaw puzzle, jug, jacket, jet, jewel, jump rope, jester hat',
            'k': 'kite, key, kangaroo, king, kitten, kettle, kayak, koala, knight shield, kazoo',
            'l': 'lion, ladder, leaf, lemon, lighthouse, lizard, lamp, lollipop, log, lobster, lock, llama, lantern',
            'm': 'monkey, moon, mushroom, mouse, mountain, mermaid, mittens, magnet, map, muffin, medal, microscope, mailbox, mask, marble',
            'n': 'nest, needle, newt, net, necklace, notebook, nut, narwhal',
            'o': 'octopus, orange, owl, otter, onion, orchid, ostrich, orca, ornament, oar',
            'p': 'penguin, pizza, parrot, pumpkin, piano, pear, pig, pirate hat, paintbrush, pencil, popcorn, panda, present, puzzle piece, palm tree',
            'q': 'queen, quilt, question mark, quail, quiver of arrows',
            'r': 'rocket, rainbow, robot, rabbit, rose, ring, ruler, rain cloud, reindeer, rooster, rope, racket, rhinoceros, radio',
            's': 'star, sun, snake, ship, strawberry, snowman, scissors, shell, spider, skateboard, sword, sunflower, snail, scarf, seahorse',
            't': 'turtle, train, tree, trumpet, tiger, telescope, tent, tractor, teapot, teddy bear, tooth, tomato, treasure chest, tambourine',
            'u': 'umbrella, unicorn, ukulele, UFO, uniform',
            'v': 'violin, volcano, vase, van, vine, vulture, valentine heart',
            'w': 'whale, watermelon, windmill, wagon, watch, wizard hat, wolf, worm, web, window, watering can, walrus, wings, wand',
            'x': 'xylophone, x-ray, x marks the spot',
            'y': 'yacht, yo-yo, yak, yarn ball',
            'z': 'zebra, zip, zoo gate, zigzag, zeppelin',
        }.get(letter_lower, 'apple, airplane, ant')
        
        letter_costumes = {
            'a': 'astronaut, archer, artist, acrobat',
            'b': 'builder, ballerina, beekeeper',
            'c': 'cowboy, chef, clown',
            'd': 'doctor, dinosaur onesie, detective',
            'e': 'explorer with hat and binoculars, elf',
            'f': 'firefighter, fairy, farmer',
            'g': 'gardener with tools and apron, gorilla onesie, gymnast',
            'h': 'hippo onesie, horse rider outfit, hiker',
            'i': 'ice skater, insect onesie',
            'j': 'jester, jockey',
            'k': 'king, knight, karate outfit',
            'l': 'lion onesie, ladybird onesie, lifeguard',
            'm': 'magician, mermaid costume, monkey onesie',
            'n': 'ninja, nurse',
            'o': 'owl onesie, octopus costume',
            'p': 'pirate, princess, pilot',
            'q': 'queen',
            'r': 'robot costume, racing driver, Robin Hood',
            's': 'superhero, sailor, scientist',
            't': 'train conductor, tiger onesie',
            'u': 'unicorn onesie, umpire',
            'v': 'viking, vet',
            'w': 'wizard, witch',
            'x': 'superhero with X on chest, x-ray technician',
            'y': 'yak onesie, yachtsman',
            'z': 'zookeeper, zebra onesie',
        }.get(letter_lower, 'astronaut')

        # UNDER 3 - big clear letter + one hardcoded object
        if age_level == "under_3":
            return f"""Create the SIMPLEST possible BLACK AND WHITE colouring page for a 2 year old baby.

DRAW:
- A big bold letter {letter} taking up a large portion of the page (plain block letter or bubble letter - NO face, NO arms, NO legs)
- ONE simple {best_object} next to it

STYLE:
- BLACK OUTLINES ON WHITE ONLY - no colour, no grey, no shading
- NO pink cheeks, NO blush, NO rosy cheeks - pure black lines only
- EXTREMELY THICK black outlines
- The letter must be clearly recognizable as {letter}
- Maximum 8-10 colourable areas TOTAL
- NO dots, NO speckles, NO texture, NO noise anywhere on the page
- Every area must be PURE WHITE inside black outlines
- ALL lines must connect perfectly - no gaps
- Clean, smooth lines - no sketchy or broken lines

BACKGROUND:
- PURE WHITE - absolutely nothing else

OUTPUT: Big clear letter {letter} with one {best_object} on pure white. The letter must NOT have a face, arms, or legs."""

        # AGE 3 - big clear letter + one hardcoded object
        if age_level == "age_3":
            return f"""Create an EXTREMELY SIMPLE toddler alphabet colouring page for letter {letter}.

DRAW:
- A big bold letter {letter} taking up a large portion of the page (plain block letter or bubble letter - NO face, NO arms, NO legs)
- ONE simple {best_object} next to it

STYLE:
- BLACK OUTLINES ON WHITE ONLY - no colour, no grey, no shading
- NO pink cheeks, NO blush, NO rosy cheeks - pure black lines only
- EXTREMELY THICK black outlines
- The letter must be clearly recognizable as {letter}
- Maximum 10-12 colourable areas TOTAL
- NO dots, NO speckles, NO texture, NO noise anywhere on the page
- Every area must be PURE WHITE inside black outlines
- ALL lines must connect perfectly - no gaps
- Clean, smooth lines - no sketchy or broken lines

BACKGROUND:
- PURE WHITE - absolutely nothing else

OUTPUT: Big clear letter {letter} with one {best_object} on pure white. The letter must NOT have a face, arms, or legs."""

        # AGE 4 - big clear letter + a couple objects
        if age_level == "age_4":
            return f"""Create a SIMPLE alphabet colouring page for letter {letter} for a 4 year old.

DRAW:
- A big bold letter {letter} taking up a large portion of the page (plain block letter or bubble letter - NO face, NO arms, NO legs)
- A {best_object} and one other object ONLY from this list: {letter_objects}

CRITICAL: EVERY object in this image MUST start with the letter {letter}. Do NOT draw anything that does not start with {letter}.

STYLE:
- BLACK OUTLINES ON WHITE ONLY - no colour, no grey, no shading
- NO pink cheeks, NO blush, NO rosy cheeks - pure black lines only
- THICK black outlines
- The letter {letter} must be LARGE and clearly recognizable
- Maximum 15-18 colourable areas
- NO dots, NO speckles, NO texture, NO noise anywhere on the page
- Every area must be PURE WHITE inside black outlines
- ALL lines must connect perfectly - no gaps
- Clean, smooth lines - no sketchy or broken lines

NO TEXT - do not write any words or labels

BACKGROUND:
- PURE WHITE - no ground, no scenery

OUTPUT: Big clear letter {letter} with a {best_object} and one other {letter} object. The letter must NOT have a face, arms, or legs. No text."""

        # AGE 5 - big letter + children in costumes + objects
        if age_level == "age_5":
            return f"""Create an alphabet colouring page for letter {letter} for a 5 year old.

DRAW:
- A big bold letter {letter} displayed prominently in the scene (plain block letter or bubble letter - NO face, NO arms, NO legs)
- 1-2 cute children wearing COSTUMES from this list ONLY: {letter_costumes}
- 3-4 objects ONLY from this list: {letter_objects}

CRITICAL: EVERY single object and costume in this image MUST start with the letter {letter}. If it does not start with {letter}, DO NOT DRAW IT. ONLY use objects from the list above.
IMPORTANT: Do NOT put the letter {letter} printed on clothing - dress them in themed COSTUMES instead

STYLE:
- BLACK OUTLINES ON WHITE ONLY - NO grey, NO shading
- NO pink cheeks, NO blush, NO rosy cheeks - pure black lines only
- Medium-thick black outlines
- Simple but clear figures
- Maximum 20-25 colourable areas
- NO dots, NO speckles, NO texture, NO noise anywhere on the page
- Every area must be PURE WHITE inside black outlines
- ALL lines must connect perfectly - no gaps
- Clean, smooth lines - no sketchy or broken lines

NO TEXT - do not write any words or labels (only the letter {letter} itself)

BACKGROUND:
- MINIMAL - simple ground line, maybe 1-2 clouds
- Keep mostly white

OUTPUT: Large clear letter {letter} with children in costumes and several {letter} objects. The letter must NOT have a face, arms, or legs."""

        # AGE 6 - themed scene with prominent letter
        if age_level == "age_6":
            return f"""Create an alphabet colouring page for letter {letter} for a 6 year old.

DRAW:
- A large bold letter {letter} prominently placed in the scene (block letter or bubble letter - NO face, NO arms, NO legs)
- 1-2 children wearing COSTUMES from this list ONLY: {letter_costumes}
- 6-8 objects from this list: {letter_objects}
- ONLY draw objects from the list above - nothing else

STYLE:
- BLACK OUTLINES ON WHITE ONLY - NO grey, NO shading
- NO pink cheeks, NO blush, NO rosy cheeks - pure black lines only
- Medium-thick black outlines
- More detail than younger ages but still clear
- Maximum 25-30 colourable areas
- NO dots, NO speckles, NO texture, NO noise anywhere on the page
- Every area must be PURE WHITE inside black outlines
- ALL lines must connect perfectly - no gaps
- Clean, smooth lines - no sketchy or broken lines
- BACKGROUND BETWEEN OBJECTS MUST BE PURE WHITE - no decorative stars, flowers, dots, swirls, or filler shapes between objects
- Leave WHITE SPACE between objects - do not fill every gap

NO TEXT - do not write any words or labels (only the letter {letter} itself)

BACKGROUND:
- Simple themed background related to {letter}

OUTPUT: Fun {letter}-themed scene with large letter {letter}, children, and multiple {letter} objects. The letter must NOT have a face, arms, or legs."""

        # AGE 7-8 - detailed scene
        if age_level in ("age_7", "age_8"):
            return f"""Create a detailed alphabet colouring page for letter {letter} for a {age_level.replace('age_', '')} year old.

DRAW:
- A large bold letter {letter} as a focal point (plain block letter or bubble letter - NO face, NO arms, NO legs, NO patterns or detail inside the letter - keep it HOLLOW and clean)
- A creative scene where EVERYTHING relates to the letter {letter}
- 8-10 objects from this list: {letter_objects}
- ONLY draw objects from the list above - nothing else
- Optional: 1-2 children wearing COSTUMES from this list ONLY: {letter_costumes}

STYLE:
- BLACK OUTLINES ON WHITE ONLY - NO grey, NO shading
- NO pink cheeks, NO blush, NO rosy cheeks - pure black lines only
- Medium black outlines with more detail
- NO dots, NO speckles, NO texture, NO noise anywhere on the page
- Every area must be PURE WHITE inside black outlines
- ALL lines must connect perfectly - no gaps
- Clean, smooth lines - no sketchy or broken lines
- BACKGROUND BETWEEN OBJECTS MUST BE PURE WHITE - no decorative stars, flowers, dots, swirls, or filler shapes between objects
- Leave WHITE SPACE between objects - do not fill every gap
- Maximum 30-40 colourable areas

NO TEXT - do not write any words or labels (only the letter {letter} itself)

OUTPUT: Detailed {letter}-themed scene with clean hollow letter and many {letter} objects. The letter must NOT have a face, arms, or legs."""

        # AGE 9-10 - complex educational scene
        if age_level in ("age_9", "age_10"):
            return f"""Create a complex alphabet colouring page for letter {letter} for a {age_level.replace('age_', '')} year old.

DRAW:
- A large bold letter {letter} as centrepiece (plain block letter or bubble letter - NO face, NO arms, NO legs, NO patterns or detail inside the letter - keep it HOLLOW and clean)
- An elaborate scene built around the letter {letter}
- 10-12 objects from this list: {letter_objects}
- ONLY draw objects from the list above - nothing else


STYLE:
- BLACK OUTLINES ON WHITE ONLY - NO grey, NO shading
- NO pink cheeks, NO blush, NO rosy cheeks - pure black lines only
- Finer black outlines with lots of detail
- Intricate patterns suggested by line work only - NO filled textures
- Many small colourable areas for patient colouring
- Maximum 40-50+ colourable areas
- NO dots, NO speckles, NO texture, NO noise anywhere on the page
- Every area must be PURE WHITE inside black outlines
- ALL lines must connect perfectly - no gaps
- Clean, smooth lines - no sketchy or broken lines
- BACKGROUND BETWEEN OBJECTS MUST BE PURE WHITE - no decorative stars, flowers, dots, swirls, or filler shapes between objects
- Leave WHITE SPACE between objects - do not fill every gap

NO TEXT - do not write any words or labels (only the letter {letter} itself)

OUTPUT: Complex detailed {letter}-themed illustration with artistic letter and many {letter} objects. The letter must NOT have a face, arms, or legs."""

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
    
    # BABY MODE (under 3) - simplest possible single object
    if age_level == "under_3":
        return f"""Create the SIMPLEST possible BLACK AND WHITE colouring page for a 2 year old baby.

DRAW:
- ONE simple {description} character or object in the centre of the page
- THAT IS ALL - NOTHING ELSE

STYLE:
- BLACK OUTLINES ON WHITE ONLY - no colour, no grey, no shading
- NO pink cheeks, NO blush, NO rosy cheeks - pure black lines only
- EXTREMELY THICK black outlines
- Blob/kawaii style - super rounded and chunky
- Maximum 8-10 colourable areas TOTAL
- NO dots, NO speckles, NO texture, NO noise anywhere on the page
- Every area must be PURE WHITE inside black outlines
- ALL lines must connect perfectly - no gaps
- Clean, smooth lines - no sketchy or broken lines

BACKGROUND:
- PURE WHITE - absolutely nothing else
- No ground, no sky, no clouds, no grass, nothing

OUTPUT: One simple chunky {description} on pure white. Nothing else on the page."""

    # TODDLER MODE (age 3-4) - super simple single object
    if age_level == "age_3":
        return f"""Create an EXTREMELY SIMPLE toddler colouring page.

CRITICAL: Only draw what is ACTUALLY in the photo. DO NOT add extra people, characters, animals, or objects not in the original image.

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

OUTPUT: Bold black lines on pure white background. No grey. No texture.

CRITICAL - NO BORDER: Do NOT add any border, frame, or rounded corners around the image. The drawing must fill the entire canvas edge to edge with NO border whatsoever."""

    if age_level in CONFIG["age_levels"]:
        base += "\n\n" + CONFIG["age_levels"][age_level]["overlay"]

    return base


# ============================================
# OPENAI API CALLS
# ============================================

async def generate_from_photo(prompt: str, image_b64: str, quality: str = "low") -> dict:
    """Generate colouring page from photo using images/edits endpoint"""
    from PIL import Image
    import io
    
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
    image_bytes = base64.b64decode(image_b64)
    
    # Detect orientation from input image
    from PIL import ImageOps
    img = Image.open(io.BytesIO(image_bytes))
    img = ImageOps.exif_transpose(img)
    width, height = img.size
    
    # Match output orientation to input
    if width > height:
        # Landscape input -> landscape output
        size = "1536x1024"
    else:
        # Portrait or square input -> portrait output
        size = "1024x1536"
    
    print(f"[ORIENTATION] Input: {width}x{height} -> Output: {size}")
    
    files = [
        ("image[]", ("source.jpg", image_bytes, "image/jpeg")),
    ]
    data = {
        "model": "gpt-image-1.5",
        "prompt": prompt,
        "n": "1",
        "size": size,
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
        "background": "opaque",
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
    
    # DEBUG - log received values
    print(f"DEBUG: age_level={request.age_level}, normalized={normalize_age_level(request.age_level)}, theme={request.theme}, custom_theme={request.custom_theme}")
    
    # Build prompt
    prompt = build_photo_prompt(
        age_level=normalize_age_level(request.age_level),
        theme=normalize_theme(request.theme),
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

    # Detect orientation from generated image
    output_img = Image.open(io.BytesIO(base64.b64decode(output_b64)))
    is_landscape = output_img.width > output_img.height

    return {
        "success": True,
        "image_url": image_url,
        "pdf_url": pdf_url,
        "is_landscape": is_landscape,
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


# ============================================
# EMAIL PDF ENDPOINT
# ============================================

class EmailPDFRequest(BaseModel):
    pdf_url: str
    email: str
    theme_name: str = "your colouring page"

@app.post("/send-pdf-email")
async def send_pdf_email(request: EmailPDFRequest):
    """Send a colouring page PDF to the user's email"""
    import boto3
    from botocore.exceptions import ClientError
    from email.mime.multipart import MIMEMultipart
    from email.mime.base import MIMEBase
    from email.mime.text import MIMEText
    from email import encoders
    
    try:
        # Download the PDF from Firebase URL
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(request.pdf_url)
            if resp.status_code != 200:
                raise HTTPException(status_code=400, detail="Could not download PDF")
            pdf_bytes = resp.content
        
        # Build the email
        msg = MIMEMultipart()
        msg["Subject"] = f"Your Little Lines Colouring Page - {request.theme_name}"
        msg["From"] = "Little Lines <noreply@littlefortstudios.com>"
        msg["To"] = request.email
        
        # Compress PDF if over 9MB - rebuild from rendered pages
        if len(pdf_bytes) > 9_000_000:
            try:
                import subprocess
                import tempfile
                import io as _io
                
                with tempfile.TemporaryDirectory() as tmp_dir:
                    # Write original PDF to temp file
                    orig_path = f"{tmp_dir}/original.pdf"
                    with open(orig_path, "wb") as f:
                        f.write(pdf_bytes)
                    
                    # Use pdftoppm to convert pages to JPEG images
                    subprocess.run([
                        "pdftoppm", "-jpeg", "-r", "200", "-jpegopt", "quality=80",
                        orig_path, f"{tmp_dir}/page"
                    ], check=True, timeout=60)
                    
                    # Collect page images in order
                    import glob
                    page_files = sorted(glob.glob(f"{tmp_dir}/page-*.jpg"))
                    
                    if page_files:
                        # Rebuild PDF from compressed images using reportlab
                        from reportlab.lib.units import mm
                        from reportlab.pdfgen import canvas as rl_canvas
                        
                        output_buf = _io.BytesIO()
                        first_img = Image.open(page_files[0])
                        img_w, img_h = first_img.size
                        # Use image dimensions as page size (in points, 1px at 150dpi)
                        page_w = img_w * 72.0 / 150.0
                        page_h = img_h * 72.0 / 150.0
                        
                        c = rl_canvas.Canvas(output_buf)
                        for pf in page_files:
                            c.setPageSize((page_w, page_h))
                            c.drawImage(pf, 0, 0, width=page_w, height=page_h)
                            c.showPage()
                        c.save()
                        
                        new_bytes = output_buf.getvalue()
                        if len(new_bytes) < len(pdf_bytes):
                            pdf_bytes = new_bytes
                        print(f"Compressed PDF to {len(pdf_bytes)} bytes")
                    else:
                        print("No page images generated, using original")
            except Exception as e:
                print(f"PDF compression failed, using original: {e}")
        
        # Determine email content
        is_storybook = len(pdf_bytes) > 5_000_000
        if is_storybook:
            body = MIMEText(
                f"Hi there!\n\n"
                f"Your Little Lines storybook is attached: {request.theme_name}\n\n"
                f"Print it out and enjoy reading together!\n\n"
                f"From the Little Lines team",
                "plain"
            )
        else:
            body = MIMEText(
                f"Hi there!\n\n"
                f"Here\'s your Little Lines colouring page: {request.theme_name}\n\n"
                f"Print it out and enjoy colouring!\n\n"
                f"From the Little Lines team",
                "plain"
            )
        msg.attach(body)
        
        # Attach PDF or send download link
        if len(pdf_bytes) < 9_000_000:
            pdf_attachment = MIMEBase("application", "pdf")
            pdf_attachment.set_payload(pdf_bytes)
            encoders.encode_base64(pdf_attachment)
            filename = f"Little_Lines_{request.theme_name.replace(' ', '_')}.pdf"
            pdf_attachment.add_header("Content-Disposition", f"attachment; filename={filename}")
            msg.attach(pdf_attachment)
        else:
            msg = MIMEMultipart()
            msg["Subject"] = f"Your Little Lines Storybook - {request.theme_name}"
            msg["From"] = "Little Lines <noreply@littlefortstudios.com>"
            msg["To"] = request.email
            html_body = f"""<html>
<body style="font-family: Arial, sans-serif; background-color: #f0f8ff; padding: 30px;">
  <div style="max-width: 500px; margin: 0 auto; background: white; border-radius: 16px; padding: 40px; text-align: center;">
    <h1 style="color: #4a3f8a; font-size: 24px; margin-bottom: 8px;">Your Storybook is Ready!</h1>
    <p style="color: #666; font-size: 16px; margin-bottom: 24px;">{request.theme_name}</p>
    <a href="{request.pdf_url}&response-content-disposition=attachment" style="display: inline-block; background: linear-gradient(135deg, #ff6b9d, #ff8a80); color: white; text-decoration: none; padding: 16px 40px; border-radius: 30px; font-size: 18px; font-weight: bold;">Download Your Storybook</a>
    <p style="color: #999; font-size: 13px; margin-top: 24px;">This link downloads your PDF directly from the Little Lines app. It was created just for you.</p>
    <p style="color: #999; font-size: 13px; margin-top: 16px;">From the Little Lines team</p>
  </div>
</body>
</html>"""
            body = MIMEText(html_body, "html")
            msg.attach(body)
        
        # Send via SES
        ses_client = boto3.client(
            "ses",
            region_name=os.getenv("AWS_REGION", "eu-north-1"),
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        )
        
        ses_client.send_raw_email(
            Source="Little Lines <noreply@littlefortstudios.com>",
            Destinations=[request.email],
            RawMessage={"Data": msg.as_string()},
        )
        
        return {"success": True, "message": "Email sent"}
    
    except ClientError as e:
        error_msg = e.response["Error"]["Message"]
        print(f"SES error: {error_msg}")
        raise HTTPException(status_code=500, detail=f"Email failed: {error_msg}")
    except Exception as e:
        print(f"Email error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
