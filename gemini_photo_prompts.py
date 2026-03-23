"""
gemini_photo_prompts.py
-----------------------
B2B photo-to-colouring pipeline using Gemini 2.5 Flash Image.

Used for age_5 through age_10 where face likeness matters.
Ages under_3, age_3, age_4 are handled by gpt-image-1.5 in app.py.

Usage:
    from gemini_photo_prompts import build_gemini_photo_prompt, generate_gemini_colouring_page

Model: gemini-2.5-flash-image (~$0.039/image)
Two-step pipeline: Gemini (face accuracy) -> GPT-image-1.5 low (line thickening)
"""

import os
from google import genai
from google.genai import types


# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────

GEMINI_MODEL = "gemini-2.5-flash-image"

VALID_AGES = ["age_5", "age_6", "age_7", "age_8", "age_9", "age_10"]

# Appended to every prompt
COLOURING_PAGE_STYLE = """

COLOURING PAGE REQUIREMENTS - CRITICAL:
- This must look like a PAGE FROM A PRINTED CHILDREN'S COLOURING BOOK - not a sketch, not line art
- ALL outlines must be THICK BOLD BLACK - like drawn with a thick black marker pen
- Every closed shape must be completely filled with pure white inside
- Think classic colouring book style - THICK outlines, BIG colourable areas
- NO thin detail lines - if a line isn't thick enough to colour between, remove it
- The page must be immediately recognisable as something a child would want to colour in"""

# Prepended to every prompt
PHOTO_AWARENESS = """IMPORTANT - DRAW ONLY WHAT IS IN THE PHOTO:
- If the photo contains ONLY animals (pets, wildlife) with NO people: draw ONLY the animals. Do NOT invent or add any human characters, cartoon people, or faces.
- If the photo is a landscape or scene with NO people and NO animals: draw ONLY the landscape/scene. Do NOT add any characters, people, or animals.
- If the photo contains people: follow all face, hair, and clothing instructions as normal.
- NEVER invent subjects that are not in the original photo.

"""

# Universal count + face + hair block applied to all ages
UNIVERSAL_BLOCK = """CRITICAL - COUNT THE SUBJECTS:
- Count EVERY person and animal visible in the photo. Draw EXACTLY that many - NO MORE, NO LESS.
- NEVER add extra people not in the photo. NEVER remove anyone.
- Keep the EXACT age of every person - a child must look like a child, an adult like an adult. Do NOT age up or age down anyone.

FACE ACCURACY (HIGHEST PRIORITY):
- Draw the REAL face of every person - match their actual nose shape, eye spacing, mouth width, chin shape
- A parent must INSTANTLY recognise their child
- Eyes: clean simple outlines only - NO dark shading, NO heavy fill, NO thick lashes
- NO pink cheeks, NO blush, NO rosy marks - pure black lines only
- NO generic cartoon faces - these must look like the actual people in the photo

HAIR ACCURACY:
- Copy the EXACT hairstyle for each person - long/short, curly/straight, parting, bunches, bald
- Hair as clean outline shape - NOT filled solid black
- Every person must have their own distinct recognisable hairstyle"""


# GPT thickening prompts per age (used in step 2 of pipeline)
GPT_THICKEN_PROMPTS = {
    "age_5":  "VERY THICK bold black outlines - like a thick Sharpie marker. Maximum 20-25 large simple colourable areas. Simple clean shapes.",
    "age_6":  "THICK bold black outlines - like a thick felt tip pen. 25-30 colourable areas. Clean shapes with clothing detail.",
    "age_7":  "MEDIUM-THICK black outlines - confident bold lines. 30-35 colourable areas. Good clothing and scene detail.",
    "age_8":  "MEDIUM black outlines - solid confident lines. 35-40 colourable areas. Detailed clothing, background elements.",
    "age_9":  "MEDIUM-THIN black outlines - clean precise lines. 40-45 colourable areas. Rich detail throughout.",
    "age_10": "SLIGHTLY THINNER black outlines - precise clean lines. 45-50 colourable areas. Maximum detail, almost adult colouring book level.",
}

GPT_THICKEN_BASE = """This is a children's colouring book line art page. Redraw it as a professional printed children's colouring book page. Keep every face, person, pose and background element EXACTLY the same. Pure black lines on pure white background only. No colour, no shading, no grey. DO NOT add any text, titles, labels or words anywhere on the image.

LINE STYLE FOR THIS AGE: {age_instruction}"""


# ─────────────────────────────────────────────────────────────────────────────
# PROMPT BUILDER
# ─────────────────────────────────────────────────────────────────────────────

def build_gemini_photo_prompt(age_level: str) -> str:
    """
    Build a Gemini-optimised photo-to-colouring prompt for age_5 through age_10.
    All ages include: subject count, face accuracy, hair accuracy.
    Detail and complexity increase progressively with age.
    """

    if age_level not in VALID_AGES:
        raise ValueError(f"Invalid age level: {age_level}. Must be one of {VALID_AGES}")

    age_prompts = {

        "age_5": f"""{UNIVERSAL_BLOCK}

DRAW:
- All people from the photo as clear recognisable figures with real faces and hairstyles
- Clothing simplified into clear outlines - stripes stay as stripes, basic patterns kept
- Simple background scene - basic shapes of the real setting only

STYLE:
- BLACK OUTLINES ON WHITE ONLY - no colour, no shading
- Medium-thick outlines
- 20-25 colourable areas - keep it simple for young children
- Clean enclosed shapes easy to colour

BACKGROUND:
- Include the most prominent background element from the photo as a simple outline
- e.g. if at a pool: simple pool edge and 1-2 loungers. If at beach: simple water line. If indoors: simple furniture outline
- Just the ONE main background element - keep it simple, not a full scene
- Pure white everywhere else

OUTPUT: Recognisable figures with real faces and hairstyles, plus one simple background element. No colour anywhere.""",

        "age_6": f"""{UNIVERSAL_BLOCK}

DRAW:
- All people with real recognisable faces, distinct hairstyles and clothing details
- Stripes, patterns and clothing features simplified but clearly present
- Background scene simplified but recognisable - main setting elements visible
- More clothing detail than age 5 - collars, pockets, jacket details as simple outlines

STYLE:
- BLACK OUTLINES ON WHITE ONLY - no colour, no shading
- Medium-thick outlines
- 25-30 colourable areas
- Real setting visible but not cluttered

OUTPUT: Real faces, distinct hairstyles, clothing detail, recognisable scene. No colour anywhere.""",

        "age_7": f"""{UNIVERSAL_BLOCK}

DRAW:
- All people with accurate faces, exact hairstyles and detailed clothing
- Fuller background scene - trees, clouds, water with wave details
- Interesting details within objects - fabric folds, shoe details, accessory details
- Background setting clearly recognisable with multiple elements

STYLE:
- BLACK OUTLINES ON WHITE ONLY - no colour, no shading
- Medium outlines
- 30-35 colourable areas
- More scene elements than age 6

OUTPUT: Detailed faces, exact hairstyles, clothing detail, fuller scene. No colour anywhere.""",

        "age_8": f"""{UNIVERSAL_BLOCK}

DRAW:
- All people with highly accurate faces, exact hairstyles and fully detailed clothing
- Rich background - detailed setting elements, cloud formations, environmental features
- Fine details on clothing - buttons, zips, patterns, shoe details
- Background scene fills the page with colourable areas

STYLE:
- BLACK OUTLINES ON WHITE ONLY - no colour, no shading
- Medium outlines, slightly thinner than younger ages
- 35-40 colourable areas
- Detailed scene fills the page

OUTPUT: Highly accurate faces, exact hairstyles, rich clothing and scene detail. No colour anywhere.""",

        "age_9": f"""{UNIVERSAL_BLOCK}

DRAW:
- All people with precise facial likeness, exact hairstyles and fully detailed clothing
- Fabric textures rendered as simple line patterns (stripes, checks, dots)
- Detailed background with multiple layers - foreground, midground, background elements
- Fine environmental details - foliage, water ripples, surface textures

STYLE:
- BLACK OUTLINES ON WHITE ONLY - no colour, no shading
- Slightly thinner outlines acceptable
- 40-45 colourable areas
- Complex scene with lots to colour

OUTPUT: Maximum face and hair accuracy, intricate clothing and scene detail. No colour anywhere.""",

        "age_10": f"""{UNIVERSAL_BLOCK}

DRAW:
- All people with maximum facial accuracy, exact hairstyles and fully detailed realistic clothing
- Rich detailed background - multiple scene layers, full environmental detail
- All clothing fully detailed - every pattern, button, texture visible as clean lines
- Additional scene elements - distant features, reflections, fine environmental detail
- Page completely filled with interesting areas to colour

STYLE:
- BLACK OUTLINES ON WHITE ONLY - no colour, no shading
- Thinner precise outlines - this is for older children
- 45-50 colourable areas
- Most complex version - like an adult colouring book but age appropriate

OUTPUT: Maximum detail throughout - faces, hair, clothing, scene all highly accurate. No colour anywhere.""",
    }

    core_prompt = f"""Convert this photo into a children's colouring book page for a {age_level.replace('_', ' ')} year old.

{age_prompts[age_level]}"""

    return PHOTO_AWARENESS + core_prompt + COLOURING_PAGE_STYLE


def build_gpt_thicken_prompt(age_level: str) -> str:
    """
    Build the GPT-image-1.5 line thickening prompt for step 2 of the pipeline.
    Line thickness decreases progressively as age increases.
    """
    if age_level not in VALID_AGES:
        raise ValueError(f"Invalid age level: {age_level}. Must be one of {VALID_AGES}")

    return GPT_THICKEN_BASE.format(
        age_instruction=GPT_THICKEN_PROMPTS[age_level]
    )


# ─────────────────────────────────────────────────────────────────────────────
# GENERATION FUNCTION
# ─────────────────────────────────────────────────────────────────────────────

async def generate_gemini_colouring_page(
    photo_bytes: bytes,
    age_level: str,
    mime_type: str = "image/jpeg",
    api_key: str = None,
) -> bytes:
    """
    Step 1: Generate colouring page from photo using Gemini 2.5 Flash Image.
    Returns thin line art with accurate faces/hair.
    Feed output into GPT-image-1.5 with build_gpt_thicken_prompt() for step 2.
    """
    key = api_key or os.environ.get("GEMINI_API_KEY")
    if not key:
        raise RuntimeError("GEMINI_API_KEY not set")

    client = genai.Client(api_key=key)
    prompt = build_gemini_photo_prompt(age_level)

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=[
            types.Part.from_bytes(data=photo_bytes, mime_type=mime_type),
            types.Part.from_text(text=prompt),
        ],
        config=types.GenerateContentConfig(
            response_modalities=["TEXT", "IMAGE"],
        ),
    )

    for part in response.candidates[0].content.parts:
        if part.inline_data:
            return part.inline_data.data

    raise RuntimeError("Gemini returned no image in response")


# ─────────────────────────────────────────────────────────────────────────────
# ROUTER FUNCTION
# ─────────────────────────────────────────────────────────────────────────────

def should_use_gemini(age_level: str) -> bool:
    """
    Returns True if this age level should use Gemini pipeline (age_5+).
    Returns False for under_3, age_3, age_4 which use gpt-image-1.5 directly.
    """
    return age_level in VALID_AGES


# ─────────────────────────────────────────────────────────────────────────────
# QUICK TEST
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    age = sys.argv[1] if len(sys.argv) > 1 else "age_8"
    print(f"\n=== Gemini prompt for {age} ===\n")
    print(build_gemini_photo_prompt(age))
    print(f"\n=== GPT thicken prompt for {age} ===\n")
    print(build_gpt_thicken_prompt(age))
    print(f"\nGemini prompt length: {len(build_gemini_photo_prompt(age))} chars")
