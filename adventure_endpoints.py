"""
Adventure Endpoints - Character Extraction & Episode Generation
================================================================
Complete endpoint system for:
1. Extracting characters from children's drawings (Gemini)
2. Generating Pixar-style character reveals (Gemini)
3. Generating age-appropriate coloring page episodes (Gemini)
"""

from adventure_gemini import generate_adventure_reveal_gemini, generate_adventure_episode_gemini, generate_personalized_stories, create_a4_page_with_text, create_front_cover
from character_extraction_gemini import extract_character_with_extreme_accuracy
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
    """A complete story theme with 10 episodes."""
    theme_id: str
    theme_name: str
    theme_description: str
    episodes: List[StoryEpisode]


class GenerateStoriesRequest(BaseModel):
    """Request to generate personalized stories."""
    character_name: str
    character_description: str
    age_level: str = "age_6"  # age_3, age_4, age_5, age_6, age_7, age_8, age_9, age_10


class GenerateStoriesResponse(BaseModel):
    """Response with 3 personalized story themes."""
    character_name: str
    age_level: Optional[str] = None
    themes: List[StoryTheme]


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
                'key_feature': extraction_result['character']['key_feature']
            },
            original_drawing_b64=image_b64
        )
        
        return {
            'character': extraction_result['character'],
            'reveal_description': extraction_result['reveal_description'],
            'reveal_image': reveal_image,
            'extraction_time': extraction_result['extraction_time'],
            'model_used': 'gemini-2.5-flash'
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Character extraction failed: {str(e)}')


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
        character_emotion=request.character_emotion  # Pass emotion for scene-appropriate expression
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
    for ep_num in range(1, 11):
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
        story_text=request.theme_description,
        character_emotion="excited"
    )
    
    # Return Gemini's image directly as the cover - it includes its own text
    return {
        "cover_image_b64": image_b64,
        "cover_page_b64": image_b64,  # Same image - Gemini handles text on cover
        "title": f"{char.name} and {request.theme_name}"
    }


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
            age_level=request.age_level
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
