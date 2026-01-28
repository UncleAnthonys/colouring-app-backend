from adventure_gemini import generate_adventure_reveal_gemini, generate_adventure_episode_gemini
from character_extraction_gemini import extract_character_gemini
import google.generativeai as genai
import os
import base64
import httpx
from typing import Optional, List
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel

from adventure_config import (
    AGE_RULES,
    get_age_rules,
    get_episode_data,
    get_story_for_age
)

from adventure_pdf import create_adventure_pdf_base64

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
MODEL = "gpt-image-1.5"
IMAGE_SIZE = "1024x1536"  # Portrait
IMAGE_QUALITY = "low"  # Cost effective at ~$0.01 per image

router = APIRouter()


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class CharacterData(BaseModel):
    """Character data extracted from child's drawing."""
    name: str
    description: str
    key_feature: str
    pose: str = "standing confidently"
    colors: List[str] = []
    personality: str = "brave and friendly"


class GenerateEpisodeRequest(BaseModel):
    """Request to generate a single episode."""
    character: CharacterData
    theme: str = "forest"
    episode_num: int
    age_level: str = "age_6"
    choice_path: str = ""  # e.g., "", "A", "AA", "AB"
    quality: str = "low"
    reveal_description: Optional[str] = None  # The analyzed reveal description for consistency


class GenerateEpisodeResponse(BaseModel):
    """Response from episode generation."""
    episode_num: int
    title: str
    story: str
    image_b64: str
    pdf_b64: str
    is_choice_point: bool = False
    choices: Optional[dict] = None
    choice_prompt: Optional[str] = None


class GenerateReferenceRequest(BaseModel):
    """Request to generate character reference image."""
    character: CharacterData
    quality: str = "low"


class GenerateReferenceResponse(BaseModel):
    """Response from reference generation."""
    image_b64: str
    character_name: str


class ThemeInfo(BaseModel):
    """Information about an adventure theme."""
    key: str
    name: str
    description: str
    icon: str


class GetThemesResponse(BaseModel):
    """Response listing available themes."""
    themes: List[ThemeInfo]


class EpisodePreview(BaseModel):
    """Preview information for an episode."""
    episode_num: int
    title: str
    is_choice_point: bool
    is_locked: bool = False


class GetEpisodesResponse(BaseModel):
    """Response listing episodes for a theme."""
    theme: str
    episodes: List[EpisodePreview]


# =============================================================================
# IMAGE GENERATION HELPER
# =============================================================================

async def generate_image(prompt: str, quality: str = "low") -> str:
    """
    Generate an image using OpenAI's gpt-image-1.5 model.
    
    Returns:
        Base64 encoded image string
    """
    if not OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="OpenAI API key not configured")
    
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "n": 1,
        "size": IMAGE_SIZE,
        "quality": quality
    }
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            "https://api.openai.com/v1/images/generations",
            headers=headers,
            json=payload
        )
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"OpenAI API error: {response.text}"
            )
        
        result = response.json()
    
    image_data = result["data"][0]
    
    if "b64_json" in image_data:
        return image_data["b64_json"]
    elif "url" in image_data:
        # Fetch image from URL
        async with httpx.AsyncClient(timeout=60.0) as client:
            img_response = await client.get(image_data["url"])
            return base64.b64encode(img_response.content).decode('utf-8')
    
    raise HTTPException(status_code=500, detail="No image data in response")


async def generate_image_with_reference(prompt: str, reference_image_b64: str, quality: str = "low") -> str:
    """
    Generate an image using OpenAI's gpt-image-1.5 model with a reference image.
    
    The reference image helps GPT understand the character's appearance better.
    
    Args:
        prompt: Text description of what to generate
        reference_image_b64: Base64 encoded reference image (child's drawing)
        quality: Image quality ("low" or "high")
    
    Returns:
        Base64 encoded generated image
    """
    if not OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="OpenAI API key not configured")
    
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Use the chat completions endpoint with vision + image generation
    payload = {
        "model": "gpt-4o",  # Use GPT-4o for vision understanding
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"""Look at this child's drawing carefully. I need you to describe it in extreme detail so we can recreate it as a professional Disney/Pixar style character.

Then generate an image based on this prompt:
{prompt}

CRITICAL: The generated character MUST match the child's drawing exactly - same colors, same features, same proportions. The child will be looking for THEIR character."""
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{reference_image_b64}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": 1000
    }
    
    # First, get GPT-4o to understand the image
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload
        )
        
        if response.status_code != 200:
            # Fall back to regular generation without reference
            return await generate_image(prompt, quality)
        
        result = response.json()
        enhanced_description = result["choices"][0]["message"]["content"]
    
    # Now generate with the enhanced description
    enhanced_prompt = f"""{prompt}

ADDITIONAL DETAILS FROM REFERENCE:
{enhanced_description}

Style: Disney/Pixar 3D animated character, vibrant colors, magical sparkles, professional quality."""
    
    return await generate_image(enhanced_prompt, quality)


async def generate_coloring_from_reference(prompt: str, reference_image_b64: str, quality: str = "low") -> str:
    """
    Generate a coloring page using the reveal image as reference.
    
    This ensures all episode coloring pages match the reveal character.
    
    Args:
        prompt: The coloring page prompt (scene description)
        reference_image_b64: Base64 encoded REVEAL image (not original drawing)
        quality: Image quality ("low" or "high")
    
    Returns:
        Base64 encoded coloring page image
    """
    if not OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="OpenAI API key not configured")
    
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Use GPT-4o to analyze the reveal image and extract character details
    analysis_payload = {
        "model": "gpt-4o",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": """Analyze this character image in EXTREME detail. List:
1. Exact body shape and proportions
2. Facial features (eyes, mouth, nose, expression)
3. Hair/head features (spikes, color, style)
4. Body parts and colors
5. Any accessories or unique features
6. Clothing details

Be VERY specific - count exact numbers (e.g., "7 spikes", "3 fingers").
This will be used to recreate the character as a coloring page."""
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{reference_image_b64}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": 1000
    }
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=analysis_payload
        )
        
        if response.status_code != 200:
            # Fall back to regular generation
            return await generate_image(prompt, quality)
        
        result = response.json()
        character_analysis = result["choices"][0]["message"]["content"]
    
    # Now generate coloring page with the analysis
    enhanced_prompt = f"""{prompt}

=== CHARACTER REFERENCE (MUST MATCH EXACTLY) ===
{character_analysis}

⚠️ CRITICAL: The character in this coloring page MUST look IDENTICAL to the reference image above.
Same proportions, same features, same number of spikes/fingers/etc.
The child will be comparing this to their character reveal - it MUST match!"""
    
    return await generate_image(enhanced_prompt, quality)


async def analyze_reveal_image(reveal_image_b64: str, character_name: str) -> str:
    """
    Analyze the reveal image with Gemini 2.5 to create a detailed description.
    
    This description will be stored and used for ALL episode generations,
    ensuring character consistency without re-analyzing the image each time.
    """
    import os
    
    GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    
    if not GOOGLE_API_KEY:
        return f"A character named {character_name}"
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GOOGLE_API_KEY}"
    
    prompt = f"""Create a BRIEF character reference sheet for "{character_name}" from this image.

FORMAT (fill in each line):
- HEAD: [color] [shape] head
- HAIR/SPIKES: exactly [NUMBER] [color] spikes/hair pieces
- EYES: [color] [shape] eyes
- MOUTH: [description including teeth if visible]
- BODY: [color] [shape] torso/body
- ARMS: [color] arms, [NUMBER] fingers per hand
- LEGS: [color] legs
- FEET: [color] feet
- SPECIAL: [any unique accessories like antenna, bolts, etc.]

MUST-HAVE FEATURES (list 3-5 things that MUST appear):
1. 
2.
3.

Be EXACT with counts. Keep response under 300 words."""

    payload = {
        "contents": [{
            "parts": [
                {"text": prompt},
                {
                    "inline_data": {
                        "mime_type": "image/png",
                        "data": reveal_image_b64
                    }
                }
            ]
        }],
        "generationConfig": {
            "temperature": 0.1,
            "maxOutputTokens": 1024
        }
    }
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, json=payload)
        
        if response.status_code != 200:
            return f"A character named {character_name}"
        
        result = response.json()
        
        # Extract text - handle multiple parts (thinking + response)
        parts = result["candidates"][0]["content"]["parts"]
        text = ""
        for part in parts:
            if "text" in part:
                text = part["text"]
        
        return text.strip() if text else f"A character named {character_name}"
        
    except Exception as e:
        return f"A character named {character_name}"


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.post("/extract-character")
async def extract_character(
    image: UploadFile = File(...),
    character_name: Optional[str] = Form(None)
):
    """
    Extract character features from a child's drawing using Gemini 2.5 Flash.
    
    This analyzes the uploaded drawing and returns detailed character data
    that can be used to generate consistent coloring pages.
    
    Args:
        image: The child's drawing (JPEG, PNG, etc.)
        character_name: Optional name for the character (child can provide)
    
    Returns:
        Extracted character data including physical description, clothing,
        key features, colors, and personality.
    """
    # Read and encode image
    image_data = await image.read()
    image_b64 = base64.b64encode(image_data).decode("utf-8")
    
    # Determine MIME type
    content_type = image.content_type or "image/jpeg"
    
    # Extract character features
    result = await extract_character_from_drawing(image_b64, content_type)
    
    if not result.success:
        raise HTTPException(status_code=500, detail=result.error)
    
    # Build response
    character = result.character
    
    # Use provided name or suggestion
    final_name = character_name if character_name else character.name_suggestion
    
    # Format adventures for response
    adventures = [
        {
            "title": adv.title,
            "theme": adv.theme,
            "description": adv.description,
            "why_it_fits": adv.why_it_fits
        }
        for adv in character.suggested_adventures
    ]
    
    return {
        "success": True,
        "character": {
            "name": final_name,
            "type": character.character_type,
            "name_suggestion": character.name_suggestion,
            "physical_description": character.physical_description,
            "clothing_description": character.clothing_description,
            "key_features": character.key_features,
            "colors": character.colors,
            "personality": character.personality_vibe,
            "drawing_style": character.drawing_style,
            # Pre-built for episode generation
            "full_description": character.adventure_description,
            "key_feature_summary": character.key_feature_summary
        },
        "suggested_adventures": adventures,
        "processing_time": result.processing_time,
        "model_used": result.model_used
    }


@router.post("/extract-and-reveal")
async def extract_and_reveal(
    image: UploadFile = File(...),
    character_name: str = Form(...)
):
    """Extract character using pure Gemini and generate reveal image"""
    try:
        # Read image data
        image_data = await image.read()
        
        # Extract character with Gemini
        extraction_result = await extract_character_gemini(image_data, character_name)
        
        # Generate reveal image with Gemini
        reveal_image = await generate_adventure_reveal_gemini({
            'name': character_name,
            'description': extraction_result['reveal_description'],
            'key_feature': extraction_result['character']['key_feature']
        })
        
        return {
            'character': extraction_result['character'],
            'reveal_description': extraction_result['reveal_description'],
            'reveal_image': reveal_image,
            'extraction_time': extraction_result['extraction_time'],
            'model_used': 'gemini-2.5-flash'
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Pure Gemini extraction failed: {str(e)}')

@router.post("/extract-character-base64")
async def extract_character_base64(
    image_b64: str,
    mime_type: str = "image/jpeg",
    character_name: Optional[str] = None
):
    """
    Extract character features from a base64-encoded image.
    
    Alternative to file upload for FlutterFlow integration.
    """
    result = await extract_character_from_drawing(image_b64, mime_type)
    
    if not result.success:
        raise HTTPException(status_code=500, detail=result.error)
    
    character = result.character
    final_name = character_name if character_name else character.name_suggestion
    
    # Format adventures for response
    adventures = [
        {
            "title": adv.title,
            "theme": adv.theme,
            "description": adv.description,
            "why_it_fits": adv.why_it_fits
        }
        for adv in character.suggested_adventures
    ]
    
    return {
        "success": True,
        "character": {
            "name": final_name,
            "type": character.character_type,
            "name_suggestion": character.name_suggestion,
            "physical_description": character.physical_description,
            "clothing_description": character.clothing_description,
            "key_features": character.key_features,
            "colors": character.colors,
            "personality": character.personality_vibe,
            "drawing_style": character.drawing_style,
            "full_description": character.adventure_description,
            "key_feature_summary": character.key_feature_summary
        },
        "suggested_adventures": adventures,
        "processing_time": result.processing_time,
        "model_used": result.model_used
    }


@router.get("/themes", response_model=GetThemesResponse)
async def get_themes():
    """Get list of available adventure themes."""
    themes = [
        ThemeInfo(
            key=key,
            name=data["name"],
            description=data["description"],
            icon=data["icon"]
        )
        for key, data in ADVENTURE_THEMES.items()
    ]
    return GetThemesResponse(themes=themes)


@router.get("/episodes/{theme}", response_model=GetEpisodesResponse)
async def get_episodes(theme: str):
    """Get list of episodes for a theme."""
    if theme not in ADVENTURE_THEMES:
        raise HTTPException(status_code=404, detail=f"Theme '{theme}' not found")
    
    # For now, all themes use forest adventure structure
    # TODO: Add theme-specific episode data
    adventure = FOREST_ADVENTURE
    
    episodes = []
    for ep_num in range(1, 11):
        if ep_num <= 5:
            ep_data = adventure["episodes"].get(ep_num, {})
        elif ep_num == 10:
            ep_data = adventure["branch_episodes"].get(10, {})
        else:
            # For branching episodes, just show the first variant
            if ep_num == 6:
                ep_data = adventure["branch_episodes"].get("6A", {})
            elif ep_num == 7:
                ep_data = adventure["branch_episodes"].get("7A", {})
            elif ep_num == 8:
                ep_data = adventure["branch_episodes"].get(8, {})
            elif ep_num == 9:
                ep_data = adventure["branch_episodes"].get("9AA", {})
        
        episodes.append(EpisodePreview(
            episode_num=ep_num,
            title=ep_data.get("title", f"Episode {ep_num}"),
            is_choice_point=ep_data.get("is_choice_point", False)
        ))
    
    return GetEpisodesResponse(theme=theme, episodes=episodes)


@router.post("/generate/reference", response_model=GenerateReferenceResponse)
async def generate_character_reference(request: GenerateReferenceRequest):
    """
    Generate a colored character reference image (Disney/Pixar style).
    This is the "hero reveal" image shown when the character is first created.
    """
    char = request.character
    
    prompt = CHARACTER_REFERENCE_PROMPT.format(
        name=char.name,
        character_description=char.description,
        personality=char.personality,
        colors=", ".join(char.colors) if char.colors else "vibrant, appealing colors"
    )
    
    image_b64 = await generate_image(prompt, request.quality)
    
    return GenerateReferenceResponse(
        image_b64=image_b64,
        character_name=char.name
    )


@router.post("/generate/episode", response_model=GenerateEpisodeResponse)
async def generate_episode(request: GenerateEpisodeRequest):
    """
    Generate a single episode coloring page with story.
    
    For choice episodes (5 and 8), also returns the available choices.
    For episodes after choices (6-7, 9-10), requires choice_path to be set.
    """
    char = request.character
    age_level = request.age_level
    episode_num = request.episode_num
    choice_path = request.choice_path
    
    # Validate
    if age_level not in AGE_RULES:
        raise HTTPException(status_code=400, detail=f"Invalid age_level: {age_level}")
    
    if episode_num < 1 or episode_num > 10:
        raise HTTPException(status_code=400, detail="episode_num must be 1-10")
    
    # Get episode data
    ep_data = get_episode_data(request.theme, episode_num, choice_path)
    
    if not ep_data:
        raise HTTPException(status_code=404, detail=f"Episode {episode_num} not found")
    
    # Get story text for this age
    stories = ep_data.get("stories", {})
    
    # Handle episodes with path-specific stories (like episode 8)
    if isinstance(stories, dict) and choice_path and choice_path[0] in stories:
        stories = stories[choice_path[0]]
    
    # Handle episode 10's special structure
    if episode_num == 10 and "base" in ep_data.get("stories", {}):
        base_story = ep_data["stories"]["base"]
        ending = ep_data["stories"]["endings"].get(choice_path, "")
        story = get_story_for_age({"age_6": base_story}, age_level) + ending
    else:
        story = get_story_for_age(stories if isinstance(stories, dict) else {"age_6": stories}, age_level)
    
    # Replace {name} placeholder
    story = story.replace("{name}", char.name)
    
    # Build the scene prompt
    age_rules = get_age_rules(age_level)
    master_prompt = MASTER_COLORING_PROMPT.format(age_rules=age_rules["rules"])
    
    scene_template = ep_data.get("scene", "")
    scene_prompt = scene_template.format(
        name=char.name,
        character_pose=char.pose,
        character_must_include=f"MUST INCLUDE: {char.key_feature}",
        area_count=age_rules["colourable_areas"]
    )
    
    full_prompt = f"""{master_prompt}

=== CHARACTER: {char.name} ===
{char.description}

KEY FEATURE THAT MUST BE VISIBLE: {char.key_feature}

{scene_prompt}

OUTPUT: Black lines on pure white background. NO text in image.
"""
    
    # If we have a reveal_description, add it for consistency
    if request.reveal_description:
        full_prompt = f"""{master_prompt}

=== CHARACTER: {char.name} ===
{char.description}

=== EXACT CHARACTER APPEARANCE (FROM REVEAL IMAGE - MUST MATCH!) ===
{request.reveal_description}

KEY FEATURE THAT MUST BE VISIBLE: {char.key_feature}

{scene_prompt}

⚠️ CRITICAL: The character MUST look IDENTICAL to the reveal image description above.
Same proportions, same features, same colors, same number of spikes/fingers/etc.

OUTPUT: Black lines on pure white background. NO text in image.
"""
    
    # Generate the image
    image_b64 = await generate_image_gemini_flash(full_prompt)
    
    # Generate PDF
    choice_info = None
    if ep_data.get("is_choice_point") and choice_path:
        choices = ep_data.get("choices", {})
        if choice_path and choice_path[-1] in choices:
            chosen = choices[choice_path[-1]]
            choice_info = f"{chosen.get('icon', '')} {chosen.get('label', '')}"
    
    pdf_b64 = create_adventure_pdf_base64(
        image_b64=image_b64,
        episode_num=episode_num,
        episode_title=ep_data.get("title", f"Episode {episode_num}"),
        story_text=story,
        character_name=char.name,
        age_level=age_level,
        total_episodes=10,
        choice_info=choice_info
    )
    
    # Build response
    response = GenerateEpisodeResponse(
        episode_num=episode_num,
        title=ep_data.get("title", f"Episode {episode_num}"),
        story=story,
        image_b64=image_b64,
        pdf_b64=pdf_b64,
        is_choice_point=ep_data.get("is_choice_point", False)
    )
    
    # Add choice info for choice episodes
    if ep_data.get("is_choice_point"):
        response.choices = ep_data.get("choices")
        response.choice_prompt = ep_data.get("choice_prompt", "").replace("{name}", char.name)
    
    return response


@router.post("/generate/full-adventure")
async def generate_full_adventure(
    character: CharacterData,
    theme: str = "forest",
    age_level: str = "age_6",
    choice_1: str = "A",
    choice_2: str = "A",
    quality: str = "low"
):
    """
    Generate a complete 10-episode adventure.
    
    This is a convenience endpoint that generates all episodes at once.
    For production, you'd likely generate episodes one at a time.
    
    Returns a list of all episode responses.
    """
    episodes = []
    choice_path = ""
    
    for ep_num in range(1, 11):
        # Update choice path
        if ep_num == 6:
            choice_path = choice_1
        elif ep_num == 9:
            choice_path = choice_1 + choice_2
        
        request = GenerateEpisodeRequest(
            character=character,
            theme=theme,
            episode_num=ep_num,
            age_level=age_level,
            choice_path=choice_path,
            quality=quality
        )
        
        episode = await generate_episode(request)
        episodes.append(episode)
    
    return {
        "character": character.name,
        "theme": theme,
        "age_level": age_level,
        "path": choice_1 + choice_2,
        "episodes": episodes,
        "total_cost_estimate": f"${len(episodes) * 0.01:.2f}"
    }


@router.get("/age-levels")
async def get_age_levels():
    """Get information about available age levels."""
    return {
        "age_levels": [
            {
                "key": key,
                "display_name": data["age"],
                "colourable_areas": data["colourable_areas"]
            }
            for key, data in AGE_RULES.items()
        ]
    }


# =============================================================================
# HEALTH CHECK
# =============================================================================

@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "adventure",
        "themes_available": len(ADVENTURE_THEMES),
        "api_key_configured": bool(OPENAI_API_KEY)
    }

async def generate_image_gemini_flash(prompt: str) -> str:
    """Generate image using Gemini 2.5 Flash Image"""
    import os
    
    api_key = os.environ.get('GOOGLE_API_KEY') or os.environ.get('GEMINI_API_KEY')
    if not api_key:
        raise HTTPException(status_code=500, detail='Google API key not configured')
    
    genai.configure(api_key=api_key)
    
    try:
        model = genai.GenerativeModel('gemini-2.5-flash-image')
        response = model.generate_content([prompt])
        
        if response.parts:
            for part in response.parts:
                if hasattr(part, 'inline_data') and part.inline_data:
                    return base64.b64encode(part.inline_data.data).decode('utf-8')
        
        raise HTTPException(status_code=500, detail='No image generated')
    except Exception as e:
        print(f'Gemini error: {e}')
        raise HTTPException(status_code=500, detail=f'Gemini failed: {str(e)}')

@router.post("/test/gemini-image")
async def test_gemini_image():
    """Test Gemini image generation"""
    try:
        prompt = '''Create a coloring page with BLACK LINES ONLY on PURE WHITE BACKGROUND.
        
        CHARACTER: Tristan - friendly monster with these EXACT features:
        - Green spherical head with exactly 5-7 black spikes on top
        - 2 dark gray bolts protruding from sides of head (with rectangular notches)
        - Heterochromia eyes: LEFT eye red iris, RIGHT eye blue iris  
        - Wide smile showing 2-4 white pointed fangs
        - Purple rectangular torso with black waist band
        - Green arms with 3 fingers each, blue cuffs on wrists
        - Orange cylindrical legs
        - Green boots with blue accents
        
        SCENE: Tristan exploring a magical forest with tall trees, flowers, mushrooms, and woodland creatures like squirrels and birds. Tristan should be walking happily through the forest.
        
        CRITICAL: Output must be BLACK OUTLINES ONLY on WHITE BACKGROUND - suitable for children to color in. No shading, no gray areas, just clean black lines.'''
        
        image_b64 = await generate_image_gemini_flash(prompt)
        return {"image_b64": image_b64, "status": "success"}
        
    except Exception as e:
        return {"error": str(e), "status": "failed"}


@router.post("/test/gemini-reveal")
async def test_gemini_reveal():
    """Test Gemini reveal generation"""
    try:
        prompt = '''Create a REVEAL IMAGE showing Tristan character for age 6 kids:
        
        STYLE: Disney/Pixar 3D rendered character with full vibrant colors
        - Green spherical head with exactly 7 black spikes
        - 2 gray bolts on sides of head (3 notches each)  
        - Heterochromia eyes: LEFT red, RIGHT blue
        - 4 white fangs in smile
        - Purple rectangular torso with black waist band
        - Green arms, blue wrist cuffs, 3 fingers each
        - Orange legs
        - Green boots with blue soles and stripes
        
        Background: Cheerful outdoor scene with bright colors
        Output: Full-color 3D character reveal image'''
        
        image_b64 = await generate_image_gemini_flash(prompt)
        return {"image_b64": image_b64, "type": "reveal"}
        
    except Exception as e:
        return {"error": str(e)}

@router.post("/test/gemini-coloring")  
async def test_gemini_coloring():
    """Test Gemini coloring page generation"""
    try:
        prompt = '''Create a COLORING PAGE for age 6 kids:
        
        CRITICAL: BLACK LINES ONLY on PURE WHITE BACKGROUND - NO COLOR FILL
        
        CHARACTER: Tristan with exact features:
        - Round head with 7 triangular spikes on top
        - 2 cylindrical bolts on sides of head
        - Large round eyes  
        - Smiling mouth with 4 small fangs
        - Rectangular body with waist band
        - Arms with 3 fingers, cuffs on wrists
        - Straight legs
        - Boots with stripes on front
        
        SCENE: Forest with trees, flowers, mushrooms for Episode 1
        
        OUTPUT: Black outlines only, white background, suitable for children to color in'''
        
        image_b64 = await generate_image_gemini_flash(prompt)
        return {"image_b64": image_b64, "type": "coloring"}
        
    except Exception as e:
        return {"error": str(e)}

@router.post("/adventure/generate/episode-gemini")
async def generate_episode_gemini(request: GenerateEpisodeRequest):
    """
    Generate adventure episode using Gemini 2.5 Flash Image (separate from main app)
    """
    char = request.character
    age_level = request.age_level
    episode_num = request.episode_num
    
    # Validate
    if age_level not in AGE_RULES:
        raise HTTPException(status_code=400, detail=f"Invalid age_level: {age_level}")
    
    # Get episode data and story (same logic as original)
    ep_data = get_episode_data(request.theme, episode_num, request.choice_path)
    if not ep_data:
        raise HTTPException(status_code=404, detail=f"Episode {episode_num} not found")
    
    # Get story text
    stories = ep_data.get("stories", {})
    story = get_story_for_age(stories if isinstance(stories, dict) else {"age_6": stories}, age_level)
    story = story.replace("{name}", char.name)
    
    # Build scene prompt
    age_rules = get_age_rules(age_level)
    scene_template = ep_data.get("scene", "")
    scene_prompt = scene_template.format(
        name=char.name,
        character_pose=char.pose,
        character_must_include=f"MUST INCLUDE: {char.key_feature}",
        area_count=age_rules["colourable_areas"]
    )
    
    # Generate image using Gemini
    image_b64 = await generate_adventure_episode_gemini(
        character_data={"name": char.name, "description": char.description, "key_feature": char.key_feature},
        scene_prompt=scene_prompt,
        age_rules=age_rules["rules"]
    )
    
    # Return the same format as original
    return {
        "image_b64": image_b64,
        "story": story,
        "episode_num": episode_num,
        "is_choice_point": ep_data.get("is_choice_point", False),
        "choices": ep_data.get("choices"),
        "choice_prompt": ep_data.get("choice_prompt")
    }


def convert_to_structure_only(reveal_description: str) -> str:
    """Convert detailed color description to structure-only for coloring pages"""
    
    # Extract key structural elements while removing color references
    structure_desc = f"""Friendly character with:
- Round head with spikes on top
- Cylindrical bolts on sides of head with notches  
- Large round eyes with pupils
- Wide smiling mouth showing pointed fangs
- Rectangular torso with waist band
- Cylindrical arms with fingers, cuffs on wrists
- Straight legs  
- Boot-shaped feet with stripes
- Distinctive proportions and features from original drawing"""
    
    return structure_desc

@router.post("/adventure/extract-and-generate")
async def extract_and_generate_adventure(
    image: UploadFile = File(...),
    character_name: str = Form(...),
    episode_num: int = Form(1),
    theme: str = Form("forest"),
    age_level: str = Form("age_6")
):
    """
    Complete workflow: Extract character -> Generate reveal -> Generate episode
    Works with any uploaded drawing automatically
    """
    try:
        # Step 1: Extract character with full color details
        extraction_result = await extract_and_reveal_internal(image, character_name)
        
        # Step 2: Convert to structure-only description for episodes
        structure_description = convert_to_structure_only(extraction_result['reveal_description'])
        
        # Step 3: Generate episode using structure-only description
        character_data = {
            "name": character_name,
            "description": structure_description,
            "key_feature": "distinctive features from original drawing"
        }
        
        # Get episode data
        ep_data = get_episode_data(theme, episode_num, None)
        age_rules = get_age_rules(age_level)
        
        scene_prompt = ep_data.get("scene", "").format(
            name=character_name,
            character_pose="standing happily",
            character_must_include="MUST INCLUDE: character's distinctive features",
            area_count=age_rules["colourable_areas"]
        )
        
        # Generate episode using Gemini
        episode_image = await generate_adventure_episode_gemini(
            character_data=character_data,
            scene_prompt=scene_prompt,
            age_rules=age_rules["rules"]
        )
        
        return {
            "reveal_image": extraction_result['reveal_image'],
            "episode_image": episode_image,
            "character": extraction_result['character'],
            "structure_description": structure_description,
            "episode_num": episode_num
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Adventure generation failed: {str(e)}")


@router.post("/adventure/extract-gemini-only")
async def extract_gemini_only(
    image: UploadFile = File(...),
    character_name: str = Form(...)
):
    """Extract character using only Gemini - no OpenAI needed"""
    try:
        # Read image
        image_data = await image.read()
        image_b64 = base64.b64encode(image_data).decode('utf-8')
        
        # Use Gemini for character analysis
        api_key = os.environ.get('GOOGLE_API_KEY') or os.environ.get('GEMINI_API_KEY')
        if not api_key:
            raise HTTPException(status_code=500, detail='Google API key not configured')
        
        genai.configure(api_key=api_key)
        
        # Analyze character with Gemini
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content([
            "Analyze this child's drawing and describe the character in detail for creating a 3D reveal image:",
            {"mime_type": "image/jpeg", "data": image_b64}
        ])
        
        character_description = response.text
        
        # Generate reveal image with Gemini
        reveal_image = await generate_adventure_reveal_gemini({
            "name": character_name,
            "description": character_description,
            "key_feature": "distinctive features from drawing"
        })
        
        return {
            "character": {
                "name": character_name,
                "description": character_description
            },
            "reveal_image": reveal_image
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gemini extraction failed: {str(e)}")


@router.post("/adventure/extract-gemini-only")
async def extract_gemini_only(
    image: UploadFile = File(...),
    character_name: str = Form(...)
):
    """Extract character using only Gemini - no OpenAI needed"""
    try:
        # Read image
        image_data = await image.read()
        image_b64 = base64.b64encode(image_data).decode('utf-8')
        
        # Use Gemini for character analysis
        api_key = os.environ.get('GOOGLE_API_KEY') or os.environ.get('GEMINI_API_KEY')
        if not api_key:
            raise HTTPException(status_code=500, detail='Google API key not configured')
        
        genai.configure(api_key=api_key)
        
        # Analyze character with Gemini
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content([
            "Analyze this child's drawing and describe the character in detail for creating a 3D reveal image:",
            {"mime_type": "image/jpeg", "data": image_b64}
        ])
        
        character_description = response.text
        
        # Generate reveal image with Gemini
        reveal_image = await generate_adventure_reveal_gemini({
            "name": character_name,
            "description": character_description,
            "key_feature": "distinctive features from drawing"
        })
        
        return {
            "character": {
                "name": character_name,
                "description": character_description
            },
            "reveal_image": reveal_image
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gemini extraction failed: {str(e)}")

