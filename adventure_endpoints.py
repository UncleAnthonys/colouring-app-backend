"""
🎨 My Character's Adventures - API Endpoints
=============================================

FastAPI endpoints for the adventure story system.

Add to backend folder: ~/Downloads/kids-colouring-app/backend/adventure_endpoints.py

Then import in app.py:
    from adventure_endpoints import router as adventure_router
    app.include_router(adventure_router, prefix="/adventure", tags=["Adventure"])
"""

import os
import base64
import httpx
from typing import Optional, List
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel

from adventure_config import (
    AGE_RULES,
    ADVENTURE_THEMES,
    FOREST_ADVENTURE,
    MASTER_COLORING_PROMPT,
    CHARACTER_REFERENCE_PROMPT,
    get_age_rules,
    get_story_for_age,
    get_episode_data
)
from adventure_pdf import create_adventure_pdf_base64
from character_extraction import (
    extract_character_from_drawing,
    ExtractedCharacter,
    ExtractionResult,
    build_character_prompt
)

# =============================================================================
# CONFIGURATION
# =============================================================================

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
        "processing_time": result.processing_time,
        "model_used": result.model_used
    }


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
    
    # Generate the image
    image_b64 = await generate_image(full_prompt, request.quality)
    
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
