"""
🎨 Character Extraction - Gemini 2.5 Flash
==========================================

Extracts detailed character features from children's drawings
using Gemini 2.5 Flash for maximum accuracy.

Add to backend folder: ~/Downloads/kids-colouring-app/backend/character_extraction.py
"""

import os
import base64
import json
import httpx
from typing import Optional
from pydantic import BaseModel
from fastapi import HTTPException

# =============================================================================
# CONFIGURATION
# =============================================================================

GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
MODEL = "gemini-2.5-flash"
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"


# =============================================================================
# EXTRACTION PROMPT
# =============================================================================

EXTRACTION_PROMPT = """You are analyzing a child's drawing to extract character features for a coloring book adventure.

Look at this drawing carefully and describe the character in PRECISE DETAIL.

Return a JSON object with these fields:
{
  "character_type": "princess/knight/animal/robot/monster/superhero/fairy/etc",
  "name_suggestion": "A fun, child-friendly name based on their appearance",
  "physical_description": "Detailed description of face, hair, body shape, any unique features",
  "clothing_description": "VERY detailed description of what they're wearing - count layers, note exact colors top to bottom, describe patterns, buttons, accessories",
  "key_features": ["list", "of", "distinctive", "features", "that", "MUST", "appear", "in", "every", "image"],
  "colors": ["list", "of", "all", "colors", "used"],
  "personality_vibe": "What personality does this character seem to have based on their expression and style?",
  "drawing_style": "How would you describe the child's art style? (stick figure, cartoon, detailed, etc.)",
  "suggested_adventures": [
    {
      "title": "Creative adventure title",
      "theme": "one word theme like: forest/ocean/space/castle/candy/monster/dinosaur/fairy/robot/pirate",
      "description": "2-3 sentence description of the adventure plot tailored to this specific character",
      "why_it_fits": "Brief explanation of why this adventure suits this character"
    },
    {
      "title": "Another creative title",
      "theme": "different theme",
      "description": "Different adventure idea",
      "why_it_fits": "Why this works for the character"
    },
    {
      "title": "Third option",
      "theme": "another theme",
      "description": "Third unique adventure",
      "why_it_fits": "Why this matches"
    }
  ]
}

BE EXTREMELY SPECIFIC ABOUT THE CHARACTER:
- EXACT number of layers/tiers in clothing (count them!)
- EXACT colors in order from top to bottom
- Number and placement of buttons, dots, or patterns
- Hair style, length, and color
- Any accessories (crown, hat, wings, wand, etc.)
- Facial features and expression

FOR ADVENTURE SUGGESTIONS:
- Base them on the character's appearance and vibe
- A princess might suit magical/fairy tales, a monster might suit spooky/silly adventures
- Be creative! Don't just use generic themes
- Each adventure should feel UNIQUE to this specific character
- Think about what would delight a child who drew this character

This description will be used to recreate the character CONSISTENTLY across 10 coloring pages in an adventure story. 
The child will be looking for THEIR character - accuracy is CRITICAL.

Return ONLY the JSON object, no other text or markdown."""


# =============================================================================
# RESPONSE MODEL
# =============================================================================

class SuggestedAdventure(BaseModel):
    """A suggested adventure based on the character."""
    title: str
    theme: str
    description: str
    why_it_fits: str = ""


class ExtractedCharacter(BaseModel):
    """Extracted character data from a child's drawing."""
    character_type: str
    name_suggestion: str
    physical_description: str
    clothing_description: str
    key_features: list[str]
    colors: list[str]
    personality_vibe: str
    drawing_style: str = "simple"
    suggested_adventures: list[SuggestedAdventure] = []
    
    # Computed fields for adventure generation
    @property
    def adventure_description(self) -> str:
        """Full description for use in image generation prompts."""
        return f"{self.physical_description} {self.clothing_description}"
    
    @property
    def key_feature_summary(self) -> str:
        """Summarized key features for prompt inclusion."""
        return ", ".join(self.key_features[:5])  # Top 5 most important


class ExtractionResult(BaseModel):
    """Full extraction result including metadata."""
    success: bool
    character: Optional[ExtractedCharacter] = None
    error: Optional[str] = None
    model_used: str = MODEL
    processing_time: float = 0.0


# =============================================================================
# EXTRACTION FUNCTION
# =============================================================================

async def extract_character_from_drawing(
    image_b64: str,
    mime_type: str = "image/jpeg"
) -> ExtractionResult:
    """
    Extract character features from a child's drawing using Gemini 2.5 Flash.
    
    Args:
        image_b64: Base64 encoded image string
        mime_type: Image MIME type (image/jpeg, image/png, etc.)
    
    Returns:
        ExtractionResult with character data or error
    """
    import time
    start_time = time.time()
    
    if not GOOGLE_API_KEY:
        return ExtractionResult(
            success=False,
            error="Google API key not configured. Set GOOGLE_API_KEY or GEMINI_API_KEY environment variable."
        )
    
    # Build API request
    url = f"{API_URL}?key={GOOGLE_API_KEY}"
    
    payload = {
        "contents": [{
            "parts": [
                {"text": EXTRACTION_PROMPT},
                {
                    "inline_data": {
                        "mime_type": mime_type,
                        "data": image_b64
                    }
                }
            ]
        }],
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 4096
        }
    }
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, json=payload)
        
        elapsed = time.time() - start_time
        
        if response.status_code != 200:
            return ExtractionResult(
                success=False,
                error=f"API error {response.status_code}: {response.text}",
                processing_time=elapsed
            )
        
        result = response.json()
        
        # Extract text from response - handle multiple parts (thinking + response)
        parts = result["candidates"][0]["content"]["parts"]
        text = ""
        for part in parts:
            if "text" in part:
                text = part["text"]  # Take the last text part (usually the actual response)
        
        if not text:
            return ExtractionResult(
                success=False,
                error="No text in API response",
                processing_time=elapsed
            )
        
        # Clean up JSON (remove markdown code blocks if present)
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
        
        # Parse JSON
        data = json.loads(text)
        
        # Parse suggested adventures
        adventures = []
        for adv in data.get("suggested_adventures", []):
            adventures.append(SuggestedAdventure(
                title=adv.get("title", "Mystery Adventure"),
                theme=adv.get("theme", "forest"),
                description=adv.get("description", ""),
                why_it_fits=adv.get("why_it_fits", "")
            ))
        
        # Create character object
        character = ExtractedCharacter(
            character_type=data.get("character_type", "character"),
            name_suggestion=data.get("name_suggestion", "My Character"),
            physical_description=data.get("physical_description", ""),
            clothing_description=data.get("clothing_description", ""),
            key_features=data.get("key_features", []),
            colors=data.get("colors", []),
            personality_vibe=data.get("personality_vibe", "friendly and adventurous"),
            drawing_style=data.get("drawing_style", data.get("drawing_complexity", "simple")),
            suggested_adventures=adventures
        )
        
        return ExtractionResult(
            success=True,
            character=character,
            processing_time=elapsed
        )
        
    except json.JSONDecodeError as e:
        return ExtractionResult(
            success=False,
            error=f"Failed to parse response as JSON: {e}",
            processing_time=time.time() - start_time
        )
    except Exception as e:
        return ExtractionResult(
            success=False,
            error=f"Extraction failed: {str(e)}",
            processing_time=time.time() - start_time
        )


def extract_character_sync(
    image_b64: str,
    mime_type: str = "image/jpeg"
) -> ExtractionResult:
    """
    Synchronous version of extract_character_from_drawing.
    Use this for testing or non-async contexts.
    """
    import time
    start_time = time.time()
    
    if not GOOGLE_API_KEY:
        return ExtractionResult(
            success=False,
            error="Google API key not configured."
        )
    
    url = f"{API_URL}?key={GOOGLE_API_KEY}"
    
    payload = {
        "contents": [{
            "parts": [
                {"text": EXTRACTION_PROMPT},
                {
                    "inline_data": {
                        "mime_type": mime_type,
                        "data": image_b64
                    }
                }
            ]
        }],
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 4096
        }
    }
    
    try:
        with httpx.Client(timeout=60.0) as client:
            response = client.post(url, json=payload)
        
        elapsed = time.time() - start_time
        
        if response.status_code != 200:
            return ExtractionResult(
                success=False,
                error=f"API error {response.status_code}: {response.text}",
                processing_time=elapsed
            )
        
        result = response.json()
        
        # Extract text from response - handle multiple parts
        parts = result["candidates"][0]["content"]["parts"]
        text = ""
        for part in parts:
            if "text" in part:
                text = part["text"]
        
        # Clean JSON
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        
        data = json.loads(text.strip())
        
        # Parse suggested adventures
        adventures = []
        for adv in data.get("suggested_adventures", []):
            adventures.append(SuggestedAdventure(
                title=adv.get("title", "Mystery Adventure"),
                theme=adv.get("theme", "forest"),
                description=adv.get("description", ""),
                why_it_fits=adv.get("why_it_fits", "")
            ))
        
        character = ExtractedCharacter(
            character_type=data.get("character_type", "character"),
            name_suggestion=data.get("name_suggestion", "My Character"),
            physical_description=data.get("physical_description", ""),
            clothing_description=data.get("clothing_description", ""),
            key_features=data.get("key_features", []),
            colors=data.get("colors", []),
            personality_vibe=data.get("personality_vibe", "friendly and adventurous"),
            drawing_style=data.get("drawing_style", data.get("drawing_complexity", "simple")),
            suggested_adventures=adventures
        )
        
        return ExtractionResult(
            success=True,
            character=character,
            processing_time=elapsed
        )
        
    except Exception as e:
        return ExtractionResult(
            success=False,
            error=str(e),
            processing_time=time.time() - start_time
        )


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def image_file_to_base64(filepath: str) -> tuple[str, str]:
    """
    Convert an image file to base64.
    
    Returns:
        Tuple of (base64_string, mime_type)
    """
    import mimetypes
    
    mime_type, _ = mimetypes.guess_type(filepath)
    if not mime_type:
        mime_type = "image/jpeg"
    
    with open(filepath, "rb") as f:
        image_data = f.read()
    
    return base64.b64encode(image_data).decode("utf-8"), mime_type


def build_character_prompt(character: ExtractedCharacter, character_name: str) -> str:
    """
    Build a detailed character description for use in image generation prompts.
    
    Args:
        character: Extracted character data
        character_name: Name chosen by the child
    
    Returns:
        Formatted character description for prompts
    """
    return f"""Character Name: {character_name}

EXACT APPEARANCE (preserve these details precisely):
{character.physical_description}

CLOTHING (MUST match exactly):
{character.clothing_description}

KEY IDENTIFYING FEATURES (MUST be visible):
{chr(10).join(f"- {feature}" for feature in character.key_features)}

COLORS TO USE: {", ".join(character.colors)}

PERSONALITY: {character.personality_vibe}

⚠️ CRITICAL: This character was designed by a child. They will be looking for THEIR character's unique features in every image. Preserve all details exactly!"""


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "extract_character_from_drawing",
    "extract_character_sync",
    "ExtractedCharacter",
    "ExtractionResult",
    "image_file_to_base64",
    "build_character_prompt",
    "EXTRACTION_PROMPT"
]
