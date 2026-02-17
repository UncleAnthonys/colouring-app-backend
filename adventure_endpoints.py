"""
Adventure Endpoints - Character Extraction & Episode Generation
================================================================
Complete endpoint system for:
1. Extracting characters from children's drawings (Gemini)
2. Generating Pixar-style character reveals (Gemini)
3. Generating age-appropriate coloring page episodes (Gemini)
"""

import io
from PIL import Image
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from adventure_gemini import generate_adventure_reveal_gemini, generate_adventure_episode_gemini, generate_personalized_stories, generate_story_for_theme, create_a4_page_with_text, create_front_cover
from character_extraction_gemini import extract_character_with_extreme_accuracy
from firebase_utils import upload_to_firebase
import google.generativeai as genai
import os
import base64
import httpx
from typing import Optional, List
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel

from adventure_config import (
    ADVENTURE_THEMES,
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
    reveal_description: Optional[str] = None  # Text description for consistency
    reveal_image_b64: Optional[str] = None  # The reveal image for visual consistency
    scene_prompt: Optional[str] = None  # Custom scene from personalized stories
    story_text: Optional[str] = None  # Custom story text from personalized stories
    episode_title: Optional[str] = None  # Custom episode title from personalized stories
    character_emotion: Optional[str] = None  # Character emotion for this scene
    source_type: Optional[str] = "drawing"  # 'drawing' or 'photo' - affects how character is rendered


class GenerateEpisodeResponse(BaseModel):
    """Response from episode generation."""
    episode_num: int
    title: str
    story: str
    image_b64: str
    pdf_b64: Optional[str] = None
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
# STORY GENERATION MODELS
# =============================================================================

class StoryEpisode(BaseModel):
    """A single episode in a story theme."""
    episode_num: int
    title: str
    scene_description: str
    story_text: str


class StoryTheme(BaseModel):
    """A story theme - either a pitch (no episodes) or full story (with episodes)."""
    theme_id: str
    theme_name: str
    theme_description: str
    theme_blurb: Optional[str] = None
    feature_used: Optional[str] = None
    want: Optional[str] = None
    obstacle: Optional[str] = None
    twist: Optional[str] = None
    episodes: Optional[List[StoryEpisode]] = None


class GenerateStoriesRequest(BaseModel):
    """Request to generate personalized stories."""
    character_name: str
    character_description: str
    age_level: str = "age_6"  # age_3, age_4, age_5, age_6, age_7, age_8, age_9, age_10
    writing_style: Optional[str] = None  # e.g. "Rhyming", "Funny", "Adventurous"
    life_lesson: Optional[str] = None  # e.g. "Friendship", "Being brave", "It's OK to make mistakes"


class GenerateStoriesResponse(BaseModel):
    """Response with 3 personalized story theme pitches."""
    character_name: str
    age_level: Optional[str] = None
    themes: List[StoryTheme]


class GenerateStoryForThemeRequest(BaseModel):
    """Request to generate full story for a chosen theme."""
    character_name: str
    character_description: str
    theme_name: str
    theme_description: str
    theme_blurb: str = ""
    feature_used: str = ""
    want: str = ""
    obstacle: str = ""
    twist: str = ""
    age_level: str = "age_6"
    writing_style: Optional[str] = None  # e.g. "Rhyming", "Funny", "Adventurous"
    life_lesson: Optional[str] = None  # e.g. "Friendship", "Being brave", "It's OK to make mistakes"


# =============================================================================
# IMAGE GENERATION HELPERS
# =============================================================================

async def generate_image(prompt: str, quality: str = "low") -> str:
    """Generate an image using OpenAI's gpt-image-1.5 model."""
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
        async with httpx.AsyncClient(timeout=60.0) as client:
            img_response = await client.get(image_data["url"])
            return base64.b64encode(img_response.content).decode('utf-8')
    
    raise HTTPException(status_code=500, detail="No image data in response")


async def generate_image_gemini_flash(prompt: str) -> str:
    """Generate image using Gemini 2.5 Flash Image"""
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


# =============================================================================
# MAIN ENDPOINTS
# =============================================================================

@router.post("/extract-and-reveal")
async def extract_and_reveal(
    image: UploadFile = File(...),
    character_name: str = Form(...)
):
    """
    Extract character from drawing and generate Pixar-style reveal.
    
    This is the main endpoint for creating a character:
    1. Analyzes the child's drawing with Gemini
    2. Generates a beautiful 3D Pixar-style reveal image
    
    Returns both the character data and reveal image.
    """
    try:
        # Read image data
        image_data = await image.read()
        
        # Extract character with Gemini (uses extreme accuracy prompt)
        extraction_result = await extract_character_with_extreme_accuracy(image_data, character_name)
        
        # Convert original drawing to base64 for reveal generation
        image_b64 = base64.b64encode(image_data).decode('utf-8')
        
        # Generate reveal image with Gemini - NOW SEES THE ORIGINAL DRAWING!
        reveal_image = await generate_adventure_reveal_gemini(
            character_data={
                'name': character_name,
                'description': extraction_result['reveal_description'],
                'key_feature': extraction_result['character']['key_feature'],
                'source_type': extraction_result.get('source_type', 'drawing')
            },
            original_drawing_b64=image_b64
        )
        

        # Upload reveal image to Firebase and get URL
        reveal_image_url = upload_to_firebase(reveal_image, folder="adventure/reveals")
        return {
            'character': extraction_result['character'],
            'reveal_description': extraction_result['reveal_description'],
            'reveal_image': reveal_image,
            'reveal_image_url': reveal_image_url,
            'extraction_time': extraction_result['extraction_time'],
            'model_used': 'gemini-2.5-flash',
            'source_type': extraction_result.get('source_type', 'drawing')
        }
        
    except Exception as e:
        import traceback; traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Character extraction failed: {str(e)}")


@router.post("/generate/episode-gemini")
async def generate_episode_gemini_endpoint(request: GenerateEpisodeRequest):
    """
    Generate adventure episode coloring page using Gemini.
    
    Uses reveal_image_b64 as reference for character consistency.
    The reveal image ensures the coloring page character matches exactly.
    """
    char = request.character
    age_level = request.age_level
    episode_num = request.episode_num
    
    # Validate
    if age_level not in AGE_RULES:
        raise HTTPException(status_code=400, detail=f"Invalid age_level: {age_level}")
    
    # Get episode data and story
    ep_data = get_episode_data(request.theme, episode_num, request.choice_path)
    if not ep_data:
        raise HTTPException(status_code=404, detail=f"Episode {episode_num} not found")
    
    # Get story text - use custom if provided, otherwise fallback to hardcoded
    if request.story_text:
        # Use personalized story from Gemini-generated stories
        story = request.story_text.replace("{name}", char.name)
    else:
        # Fallback to hardcoded episode data
        stories = ep_data.get("stories", {})
        story = get_story_for_age(stories if isinstance(stories, dict) else {"age_6": stories}, age_level)
        story = story.replace("{name}", char.name)
    
    # Build scene prompt - use custom if provided, otherwise from episode data
    age_rules = get_age_rules(age_level)
    if request.scene_prompt:
        # Use personalized scene from Gemini-generated stories
        scene_prompt = request.scene_prompt.replace("{name}", char.name)
    else:
        # Fallback to hardcoded episode data
        scene_template = ep_data.get("scene", "")
        scene_prompt = scene_template.format(
            name=char.name,
            character_pose=char.pose,
        character_must_include=f"MUST INCLUDE: {char.key_feature}",
        area_count=age_rules["colourable_areas"]
    )
    
    # Generate coloring page using Gemini WITH reveal image reference
    image_b64 = await generate_adventure_episode_gemini(
        character_data={
            "name": char.name, 
            "description": char.description, 
            "key_feature": char.key_feature
        },
        scene_prompt=scene_prompt,
        age_rules=age_rules["rules"],
        reveal_image_b64=request.reveal_image_b64,  # Pass reveal for consistency
        story_text=story,  # For text at bottom of page
        character_emotion=request.character_emotion,  # Pass emotion for scene-appropriate expression
        source_type=request.source_type or "drawing"  # Pass source type for photo-aware rendering
    )
    
    # Create A4 page with title and story text
    if request.episode_title:
        title = request.episode_title
    else:
        title = ep_data.get("title", f"Episode {episode_num}")
    a4_page_b64 = create_a4_page_with_text(image_b64, story, title)
    
    return {
        "image_b64": image_b64,  # Just the coloring image
        "page_b64": a4_page_b64,  # Full A4 page with title and story
        "story": story,
        "episode_num": episode_num,
        "title": title,
        "is_choice_point": ep_data.get("is_choice_point", False),
        "choices": ep_data.get("choices"),
        "choice_prompt": ep_data.get("choice_prompt")
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
    
    from adventure_config import FOREST_ADVENTURE
    adventure = FOREST_ADVENTURE
    
    episodes = []
    for ep_num in range(1, 6):
        if ep_num <= 5:
            ep_data = adventure["episodes"].get(ep_num, {})
        elif ep_num == 10:
            ep_data = adventure["branch_episodes"].get(10, {})
        else:
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


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    api_key = os.environ.get('GOOGLE_API_KEY') or os.environ.get('GEMINI_API_KEY')
    return {
        "status": "healthy",
        "service": "adventure",
        "themes_available": len(ADVENTURE_THEMES),
        "gemini_configured": bool(api_key),
        "openai_configured": bool(OPENAI_API_KEY)
    }


# =============================================================================
# COMPLETE WORKFLOW ENDPOINT
# =============================================================================

@router.post("/complete-workflow")
async def complete_workflow(
    image: UploadFile = File(...),
    character_name: str = Form(...),
    theme: str = Form("forest"),
    episode_num: int = Form(1),
    age_level: str = Form("age_6"),
    choice_path: str = Form("")
):
    """
    Complete workflow: Upload drawing -> Extract -> Reveal -> Generate Episode
    
    Single endpoint that does everything:
    1. Extracts character from child's drawing
    2. Generates Pixar-style reveal image
    3. Generates coloring page episode using reveal as reference
    
    Returns reveal image, episode coloring page, and story text.
    """
    try:
        # Step 1: Read image
        image_data = await image.read()
        
        # Step 2: Extract character with Gemini
        extraction_result = await extract_character_with_extreme_accuracy(image_data, character_name)
        
        # Step 3: Generate reveal image
        reveal_image = await generate_adventure_reveal_gemini({
            'name': character_name,
            'description': extraction_result['reveal_description'],
            'key_feature': extraction_result['character']['key_feature']
        })
        
        # Step 4: Get episode data
        ep_data = get_episode_data(theme, episode_num, choice_path)
        if not ep_data:
            raise HTTPException(status_code=404, detail=f"Episode {episode_num} not found")
        
        # Step 5: Get story text
        age_rules = get_age_rules(age_level)
        stories = ep_data.get("stories", {})
        story = get_story_for_age(stories if isinstance(stories, dict) else {"age_6": stories}, age_level)
        story = story.replace("{name}", character_name)
        
        # Step 6: Build scene prompt
        scene_template = ep_data.get("scene", "")
        scene_prompt = scene_template.format(
            name=character_name,
            character_pose="standing happily",
            character_must_include=f"MUST INCLUDE: {extraction_result['character']['key_feature']}",
            area_count=age_rules["colourable_areas"]
        )
        
        # Step 7: Generate coloring page using reveal as reference
        episode_image = await generate_adventure_episode_gemini(
            character_data={
                "name": character_name,
                "description": extraction_result['reveal_description'],
                "key_feature": extraction_result['character']['key_feature']
            },
            scene_prompt=scene_prompt,
            age_rules=age_rules["rules"],
            reveal_image_b64=reveal_image,  # Use reveal as reference!
            story_text=story
        )
        
        return {
            "character": extraction_result['character'],
            "reveal_image": reveal_image,
            "episode_image": episode_image,
            "episode_num": episode_num,
            "episode_title": ep_data.get("title", f"Episode {episode_num}"),
            "story": story,
            "theme": theme,
            "age_level": age_level
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Complete workflow failed: {str(e)}")


@router.post("/extract-and-reveal-second")
async def extract_and_reveal_second(
    image: UploadFile = File(...),
    character_name: str = Form(...)
):
    """
    Extract and reveal a SECOND character (supporting character / pet / friend).
    
    Same pipeline as /extract-and-reveal but labelled as a second character.
    Call this BEFORE /generate/full-story when user has added a supporting character.
    
    Returns:
    - character: extracted character data
    - reveal_description: text description for story generation
    - reveal_image: base64 reveal image 
    - reveal_image_url: Firebase URL of reveal image
    - source_type: 'drawing' or 'photo'
    """
    try:
        # Read image data
        image_data = await image.read()
        
        # Extract character with Gemini (uses extreme accuracy prompt)
        extraction_result = await extract_character_with_extreme_accuracy(image_data, character_name)
        
        # Convert original to base64 for reveal generation
        image_b64 = base64.b64encode(image_data).decode('utf-8')
        
        # Generate reveal image with Gemini
        reveal_image = await generate_adventure_reveal_gemini(
            character_data={
                'name': character_name,
                'description': extraction_result['reveal_description'],
                'key_feature': extraction_result['character']['key_feature'],
                'source_type': extraction_result.get('source_type', 'drawing')
            },
            original_drawing_b64=image_b64
        )
        
        # Upload reveal image to Firebase and get URL
        reveal_image_url = upload_to_firebase(reveal_image, folder="adventure/reveals-second")
        return {
            'character': extraction_result['character'],
            'reveal_description': extraction_result['reveal_description'],
            'reveal_image': reveal_image,
            'reveal_image_url': reveal_image_url,
            'extraction_time': extraction_result['extraction_time'],
            'model_used': 'gemini-2.5-flash',
            'source_type': extraction_result.get('source_type', 'drawing')
        }
        
    except Exception as e:
        import traceback; traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Second character extraction failed: {str(e)}")


class ExtractAndRevealSecondRequest(BaseModel):
    """JSON request for second character extraction (accepts base64 instead of file upload)."""
    image_b64: str  # Base64 encoded image
    character_name: str


@router.post("/extract-and-reveal-second-b64")
async def extract_and_reveal_second_b64(request: ExtractAndRevealSecondRequest):
    """
    Extract and reveal a SECOND character using base64 image input.
    
    JSON endpoint - accepts base64 string instead of file upload.
    Use this from FlutterFlow where the image is already in base64 format.
    
    Returns same response as /extract-and-reveal-second.
    """
    try:
        # Decode base64 to image bytes
        image_data = base64.b64decode(request.image_b64)
        
        # Extract character with Gemini
        extraction_result = await extract_character_with_extreme_accuracy(image_data, request.character_name)
        
        # Generate reveal image with Gemini
        reveal_image = await generate_adventure_reveal_gemini(
            character_data={
                'name': request.character_name,
                'description': extraction_result['reveal_description'],
                'key_feature': extraction_result['character']['key_feature'],
                'source_type': extraction_result.get('source_type', 'drawing')
            },
            original_drawing_b64=request.image_b64
        )
        
        # Upload reveal image to Firebase and get URL
        reveal_image_url = upload_to_firebase(reveal_image, folder="adventure/reveals-second")
        return {
            'character': extraction_result['character'],
            'reveal_description': extraction_result['reveal_description'],
            'reveal_image': reveal_image,
            'reveal_image_url': reveal_image_url,
            'extraction_time': extraction_result['extraction_time'],
            'model_used': 'gemini-2.5-flash',
            'source_type': extraction_result.get('source_type', 'drawing')
        }
        
    except Exception as e:
        import traceback; traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Second character extraction failed: {str(e)}")


# =============================================================================
# TEST ENDPOINTS
# =============================================================================



class GenerateFrontCoverRequest(BaseModel):
    """Request to generate a story front cover."""
    character: CharacterData
    theme_name: str
    theme_description: str
    age_level: str = "age_6"
    reveal_image_b64: str  # Character reveal for reference
    source_type: Optional[str] = "drawing"  # 'drawing' or 'photo'


class GenerateFullStoryRequest(BaseModel):
    """Request to generate a complete storybook (front cover + all episodes)."""
    character: CharacterData
    theme_name: str
    theme_description: str
    episodes: Optional[List[dict]] = None  # If provided, use these. If empty/null, generate from pitch fields.
    age_level: str = "age_6"
    reveal_image_b64: Optional[str] = None  # Character reveal base64 (legacy - use URL instead)
    reveal_image_url: Optional[str] = None  # Firebase URL of reveal image (preferred - avoids JSON escaping issues)
    source_type: Optional[str] = "drawing"  # 'drawing' or 'photo'
    # Pitch fields for server-side story generation
    theme_blurb: Optional[str] = None
    feature_used: Optional[str] = None
    want: Optional[str] = None
    obstacle: Optional[str] = None
    twist: Optional[str] = None
    character_description: Optional[str] = None  # Full description for story generation
    # Second character (friend/pet) - optional
    second_character: Optional[CharacterData] = None  # Full character JSON (preferred - matches 'character' format)
    second_character_image_b64: Optional[str] = None  # Reveal/photo of second character
    second_character_image_url: Optional[str] = None  # Firebase URL of second character reveal (preferred)
    second_character_name: Optional[str] = None  # Name of second character (legacy - use second_character.name)
    second_character_description: Optional[str] = None  # Description (legacy - use second_character.description)
    # Writing customization - optional
    writing_style: Optional[str] = None  # e.g. "Rhyming", "Funny", "Adventurous"
    life_lesson: Optional[str] = None  # e.g. "Friendship", "Being brave", "It's OK to make mistakes"


@router.post("/generate/front-cover")
async def generate_front_cover_endpoint(request: GenerateFrontCoverRequest):
    """
    Generate a front cover for a story book.
    
    Creates a coloring page image representing the story theme,
    then formats it as a book cover with title.
    """
    char = request.character
    age_rules = get_age_rules(request.age_level)
    
    # Create a scene prompt for the front cover
    full_title = f"{char.name} and {request.theme_name}"
    
    cover_scene = f"""Create a CHILDREN'S COLORING BOOK FRONT COVER.

This is a FULL PAGE book cover that must include:

TEXT TO INCLUDE:
- At the top: "{full_title}" in large, fun, hand-drawn style lettering
- At the bottom: "A Coloring Story Book" in smaller text

IMAGE:
- {char.name} large and central, looking excited and confident
- Background hints at the adventure: {request.theme_description}
- Dynamic, eye-catching composition
- BLACK AND WHITE LINE ART suitable for coloring in
- Portrait orientation, fills the entire page

Make it look like a real children's coloring book cover you'd see in a shop!
"""
    
    # Generate the cover coloring image
    image_b64 = await generate_adventure_episode_gemini(
        character_data={
            "name": char.name,
            "description": char.description,
            "key_feature": char.key_feature
        },
        scene_prompt=cover_scene,
        age_rules=age_rules["rules"],
        reveal_image_b64=request.reveal_image_b64,
        character_emotion="excited",
        source_type=request.source_type or "drawing"
    )
    
    return {
        "cover_image_b64": image_b64,
        "cover_page_b64": image_b64,
        "title": f"{char.name} and {request.theme_name}"
    }

@router.post("/generate/full-story")
async def generate_full_story_endpoint(request: GenerateFullStoryRequest):
    """
    Generate a complete storybook: front cover + all episode pages.
    """
    # Convert empty strings to None - FlutterFlow sends "" instead of null for optional fields
    if request.second_character_image_b64 is not None and request.second_character_image_b64.strip() == "":
        request.second_character_image_b64 = None
    if request.second_character_name is not None and request.second_character_name.strip() == "":
        request.second_character_name = None
    if request.second_character_description is not None and request.second_character_description.strip() == "":
        request.second_character_description = None
    if request.writing_style is not None and request.writing_style.strip() == "":
        request.writing_style = None
    if request.life_lesson is not None and request.life_lesson.strip() == "":
        request.life_lesson = None
    if request.reveal_image_b64 is not None and request.reveal_image_b64.strip() == "":
        request.reveal_image_b64 = None
    if request.reveal_image_url is not None and request.reveal_image_url.strip() == "":
        request.reveal_image_url = None
    
    # If second_character JSON provided, extract name/description from it
    if request.second_character:
        if not request.second_character_name:
            request.second_character_name = request.second_character.name
        if not request.second_character_description:
            request.second_character_description = request.second_character.description
        print(f"[FULL-STORY] Extracted from second_character JSON: name={request.second_character_name}, desc={request.second_character_description[:50]}...")
    
    # If reveal_image_url provided but no b64, download and convert
    if request.reveal_image_url and not request.reveal_image_b64:
        try:
            import httpx
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(request.reveal_image_url)
                if resp.status_code == 200:
                    request.reveal_image_b64 = base64.b64encode(resp.content).decode('utf-8')
                    print(f"[FULL-STORY] Downloaded reveal from URL, b64 length: {len(request.reveal_image_b64)}")
                else:
                    print(f"[FULL-STORY] Failed to download reveal URL: {resp.status_code}")
        except Exception as e:
            print(f"[FULL-STORY] Error downloading reveal URL: {e}")
    
    # If second_character_image_url provided but no b64, download and convert
    if request.second_character_image_url and not request.second_character_image_b64:
        try:
            import httpx
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(request.second_character_image_url)
                if resp.status_code == 200:
                    request.second_character_image_b64 = base64.b64encode(resp.content).decode('utf-8')
                    print(f"[FULL-STORY] Downloaded second char from URL, b64 length: {len(request.second_character_image_b64)}")
                else:
                    print(f"[FULL-STORY] Failed to download second char URL: {resp.status_code}")
        except Exception as e:
            print(f"[FULL-STORY] Error downloading second char URL: {e}")
    
    # Clean base64 fields - FlutterFlow may escape special chars or add prefixes
    if request.reveal_image_b64:
        clean_b64 = request.reveal_image_b64
        # Remove data URI prefix if present
        if 'base64,' in clean_b64:
            clean_b64 = clean_b64.split('base64,')[1]
        # Remove any whitespace/newlines
        clean_b64 = clean_b64.strip().replace('\n', '').replace('\r', '').replace(' ', '')
        # Fix URL-safe base64
        clean_b64 = clean_b64.replace('-', '+').replace('_', '/')
        # Fix padding
        padding = 4 - len(clean_b64) % 4
        if padding != 4:
            clean_b64 += '=' * padding
        request.reveal_image_b64 = clean_b64
    
    if request.second_character_image_b64:
        clean_b64 = request.second_character_image_b64
        if 'base64,' in clean_b64:
            clean_b64 = clean_b64.split('base64,')[1]
        clean_b64 = clean_b64.strip().replace('\n', '').replace('\r', '').replace(' ', '')
        clean_b64 = clean_b64.replace('-', '+').replace('_', '/')
        padding = 4 - len(clean_b64) % 4
        if padding != 4:
            clean_b64 += '=' * padding
        request.second_character_image_b64 = clean_b64
    
    char = request.character
    age_rules = get_age_rules(request.age_level)
    pages = []
    
    full_title = f"{char.name} and {request.theme_name}"
    
    cover_scene = f"""Create a CHILDREN'S COLORING BOOK FRONT COVER.
TEXT TO INCLUDE:
- At the top: "{full_title}" in large, fun, hand-drawn style lettering
- At the bottom: "A Coloring Story Book" in smaller text
IMAGE:
- {char.name} large and central, looking excited and confident
{f'- {request.second_character_name} next to {char.name}, looking happy and excited' if request.second_character_name else ''}
- Background hints at the adventure: {request.theme_description}
- BLACK AND WHITE LINE ART suitable for coloring in
Make it look like a real children's coloring book cover!
"""
    
    cover_image_b64 = await generate_adventure_episode_gemini(
        character_data={"name": char.name, "description": char.description, "key_feature": char.key_feature},
        scene_prompt=cover_scene,
        age_rules=age_rules["rules"],
        reveal_image_b64=request.reveal_image_b64,
        story_text=request.theme_description,
        character_emotion="excited",
        source_type=request.source_type or "drawing",
        second_character_image_b64=request.second_character_image_b64,
        second_character_name=request.second_character_name,
        second_character_description=request.second_character_description
    )
    
    cover_url = upload_to_firebase(cover_image_b64, folder="adventure/storybooks")
    pages.append({"page_num": 0, "page_type": "cover", "title": full_title, "page_url": cover_url, "story_text": ""})
    
    previous_page_b64 = None  # Track previous page for continuity
    
    # Debug: log all pitch fields received
    print(f"[FULL-STORY] theme_name: {request.theme_name}")
    print(f"[FULL-STORY] theme_description: {request.theme_description}")
    print(f"[FULL-STORY] theme_blurb: {request.theme_blurb}")
    print(f"[FULL-STORY] feature_used: {request.feature_used}")
    print(f"[FULL-STORY] want: {request.want}")
    print(f"[FULL-STORY] obstacle: {request.obstacle}")
    print(f"[FULL-STORY] twist: {request.twist}")
    print(f"[FULL-STORY] character_description: {request.character_description}")
    print(f"[FULL-STORY] episodes provided: {len(request.episodes) if request.episodes else 'None'}")
    
    # If no episodes provided, generate them from pitch fields
    episodes = request.episodes or []
    if not episodes and request.feature_used:
        print(f"[FULL-STORY] No episodes provided, generating from pitch fields...")
        char_desc = request.character_description or request.character.description
        
        # If there's a second character, add them to the description so Sonnet includes them
        if request.second_character_name:
            sc_info = f"\n\nIMPORTANT - SECOND CHARACTER: {request.second_character_name}"
            if request.second_character_description:
                sc_info += f" ({request.second_character_description})"
            sc_info += f". {request.second_character_name} MUST appear in every episode as {char.name}'s companion. Include them in every scene_description with a consistent bracketed tag. They are a main character, not a background extra."
            char_desc += sc_info
            print(f"[FULL-STORY] Second character added to story: {request.second_character_name}")
        
        story_data = await generate_story_for_theme(
            character_name=char.name,
            character_description=char_desc,
            theme_name=request.theme_name,
            theme_description=request.theme_description,
            theme_blurb=request.theme_blurb or "",
            feature_used=request.feature_used or "",
            want=request.want or "",
            obstacle=request.obstacle or "",
            twist=request.twist or "",
            age_level=request.age_level,
            writing_style=request.writing_style,
            life_lesson=request.life_lesson
        )
        episodes = story_data.get("episodes", [])
        print(f"[FULL-STORY] Generated {len(episodes)} episodes from pitch")
    
    print(f"[FULL-STORY] Episodes count: {len(episodes)}")
    
    for i, episode in enumerate(episodes):
        scene_prompt = episode.get("scene_description", "").replace("{name}", char.name)
        story_text = episode.get("story_text", "").replace("{name}", char.name)
        episode_title = episode.get("title", f"Episode {i+1}")
        character_emotion = episode.get("character_emotion", "happy")
        
        image_b64 = await generate_adventure_episode_gemini(
            character_data={"name": char.name, "description": char.description, "key_feature": char.key_feature},
            scene_prompt=scene_prompt,
            age_rules=age_rules["rules"],
            reveal_image_b64=request.reveal_image_b64,
            story_text=story_text,
            character_emotion=character_emotion,
            source_type=request.source_type or "drawing",
            previous_page_b64=previous_page_b64,
            second_character_image_b64=request.second_character_image_b64,
            second_character_name=request.second_character_name,
            second_character_description=request.second_character_description
        )
        
        # Save this page as previous for next iteration
        previous_page_b64 = image_b64
        
        a4_page_b64 = create_a4_page_with_text(image_b64, story_text, episode_title)
        page_url = upload_to_firebase(a4_page_b64, folder="adventure/storybooks")
        pages.append({"page_num": i+1, "page_type": "episode", "title": episode_title, "page_url": page_url, "story_text": story_text})
    
    return {"pages": pages, "title": full_title, "total_pages": len(pages)}


@router.post("/test/gemini-reveal")
async def test_gemini_reveal():
    """Test Gemini reveal generation with sample data"""
    try:
        test_description = """
        Character has a green spherical head with 7 black spikes on top.
        Two gray bolts protrude from sides of head with rectangular notches.
        Eyes have red and blue heterochromia.
        Wide smile showing 4 white pointed fangs.
        Purple rectangular torso with black waist band.
        Green arms with 3 fingers each, blue cuffs on wrists.
        Orange cylindrical legs.
        Green boots with blue accents.
        """
        
        reveal_image = await generate_adventure_reveal_gemini({
            "name": "Tristan",
            "description": test_description,
            "key_feature": "bolts on sides of head and spikes on top"
        })
        
        return {"image_b64": reveal_image, "status": "success"}
        
    except Exception as e:
        return {"error": str(e), "status": "failed"}


@router.post("/test/gemini-coloring")
async def test_gemini_coloring():
    """Test Gemini coloring page generation"""
    try:
        age_rules = get_age_rules("age_6")
        
        image_b64 = await generate_adventure_episode_gemini(
            character_data={
                "name": "Tristan",
                "description": "Friendly monster with spikes on head and bolts on sides",
                "key_feature": "spikes and bolts"
            },
            scene_prompt="Tristan exploring a magical forest with trees, flowers, and woodland creatures",
            age_rules=age_rules["rules"],
            reveal_image_b64=None,
            story_text="Tristan finds a magic tree! A fairy says hello!"
        )
        
        return {"image_b64": image_b64, "status": "success"}
        
    except Exception as e:
        return {"error": str(e), "status": "failed"}


# =============================================================================
# PERSONALIZED STORY GENERATION
# =============================================================================

@router.post("/generate-stories", response_model=GenerateStoriesResponse)
async def generate_stories_endpoint(request: GenerateStoriesRequest):
    """
    Generate 3 personalized story themes based on character and age.
    
    Takes the character name, description (from extraction), and age_level
    to generate 3 complete story themes with 10 episodes each.
    
    Stories are tailored to:
    - Character type (monster, princess, robot, animal, etc.)
    - Child's age (simpler for younger, more complex for older)
    
    Age levels: age_3, age_4, age_5, age_6, age_7, age_8, age_9, age_10
    
    Each episode includes:
    - Episode number and title
    - Scene description (for drawing the coloring page)
    - Story text (age-appropriate, for display below the coloring page)
    
    Use this after extract-and-reveal to get personalized stories,
    then use the episode scene_description with generate/episode-gemini
    to create each coloring page.
    """
    try:
        result = await generate_personalized_stories(
            character_name=request.character_name,
            character_description=request.character_description,
            age_level=request.age_level,
            writing_style=request.writing_style,
            life_lesson=request.life_lesson
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Story generation failed: {str(e)}")


@router.post("/generate-story-for-theme")
async def generate_story_for_theme_endpoint(request: GenerateStoryForThemeRequest):
    """
    Generate full 5-episode story for a single chosen theme.
    
    Call this AFTER the user picks a theme from /generate-stories.
    Pass all the theme fields (theme_name, theme_description, theme_blurb,
    feature_used, want, obstacle, twist) plus the character info.
    
    Returns 5 episodes with scene_description, story_text, and emotion.
    """
    try:
        result = await generate_story_for_theme(
            character_name=request.character_name,
            character_description=request.character_description,
            theme_name=request.theme_name,
            theme_description=request.theme_description,
            theme_blurb=request.theme_blurb,
            feature_used=request.feature_used,
            want=request.want,
            obstacle=request.obstacle,
            twist=request.twist,
            age_level=request.age_level,
            writing_style=request.writing_style,
            life_lesson=request.life_lesson
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Story generation failed: {str(e)}")
@router.post("/generate-stories-from-reveal")
async def generate_stories_from_reveal(
    character_name: str = Form(...),
    reveal_description: str = Form(...),
    age_level: str = Form("age_6")
):
    """
    Generate personalized stories directly from reveal description.
    
    Alternative to the JSON endpoint - accepts form data.
    Use this endpoint from FlutterFlow by passing:
    - character_name: The name entered by the child
    - reveal_description: The description returned from extract-and-reveal
    - age_level: age_3, age_4, age_5, age_6, age_7, age_8, age_9, or age_10
    
    Stories are automatically adjusted for age complexity:
    - age_3: Very simple sentences, basic emotions, familiar settings
    - age_4-5: Simple stories with gentle adventures
    - age_6-7: Fuller stories with mild challenges
    - age_8-9: Complex plots with character development
    - age_10: Sophisticated narratives with depth
    """
    try:
        result = await generate_personalized_stories(
            character_name=character_name,
            character_description=reveal_description,
            age_level=age_level
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Story generation failed: {str(e)}")


@router.post("/generate/storybook-pdf")
async def generate_storybook_pdf(request: dict):
    """
    Combine all storybook page URLs into a single downloadable PDF.
    Expects: {"page_urls": ["https://...", ...], "title": "Story Title"}
    Returns: {"pdf_url": "https://..."}
    """
    import httpx
    
    page_urls = request.get("page_urls", [])
    
    # Also accept full page objects and extract URLs
    if not page_urls:
        pages = request.get("pages", [])
        page_urls = [p.get("page_url", "") for p in pages if p.get("page_url")]
    title = request.get("title", "Storybook")
    
    if not page_urls:
        return {"error": "No page URLs provided"}
    
    print(f"[STORYBOOK-PDF] Generating PDF with {len(page_urls)} pages: {title}")
    
    # Download all page images
    page_images = []
    async with httpx.AsyncClient(timeout=30.0) as client:
        for i, url in enumerate(page_urls):
            try:
                resp = await client.get(url)
                if resp.status_code == 200:
                    img = Image.open(io.BytesIO(resp.content))
                    if img.mode in ('RGBA', 'P'):
                        background = Image.new('RGB', img.size, (255, 255, 255))
                        if img.mode == 'P':
                            img = img.convert('RGBA')
                        background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                        img = background
                    elif img.mode != 'RGB':
                        img = img.convert('RGB')
                    page_images.append(img)
                    print(f"[STORYBOOK-PDF] Downloaded page {i+1}: {img.width}x{img.height}")
                else:
                    print(f"[STORYBOOK-PDF] Failed to download page {i+1}: {resp.status_code}")
            except Exception as e:
                print(f"[STORYBOOK-PDF] Error downloading page {i+1}: {e}")
    
    if not page_images:
        return {"error": "Could not download any pages"}
    
    # Create multi-page PDF
    pdf_buffer = io.BytesIO()
    c = canvas.Canvas(pdf_buffer, pagesize=A4)
    page_width, page_height = A4
    
    for i, img in enumerate(page_images):
        # Scale image to fit A4
        img_aspect = img.width / img.height
        page_aspect = page_width / page_height
        
        if img_aspect > page_aspect:
            final_width = page_width
            final_height = page_width / img_aspect
        else:
            final_height = page_height
            final_width = page_height * img_aspect
        
        x = (page_width - final_width) / 2
        y = (page_height - final_height) / 2
        
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        
        img_reader = ImageReader(img_buffer)
        c.drawImage(img_reader, x, y, width=final_width, height=final_height)
        
        if i < len(page_images) - 1:
            c.showPage()
    
    c.save()
    
    # Upload PDF to Firebase
    pdf_buffer.seek(0)
    pdf_b64 = base64.b64encode(pdf_buffer.read()).decode('utf-8')
    pdf_url = upload_to_firebase(pdf_b64, folder="adventure/storybook-pdfs")
    
    print(f"[STORYBOOK-PDF] Generated PDF: {len(page_images)} pages, uploaded to Firebase")
    
    return {"pdf_url": pdf_url}
