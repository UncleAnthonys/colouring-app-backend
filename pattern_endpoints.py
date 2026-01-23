"""
Pattern Coloring API Endpoint
Add this to your existing FastAPI main.py
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import random

from pattern_config import (
    generate_pattern_prompt,
    generate_pattern_prompt_deterministic,
    AGE_CONFIG,
    PATTERN_POOLS,
)

# Create router for pattern endpoints
pattern_router = APIRouter(prefix="/pattern", tags=["pattern"])


class PatternRequest(BaseModel):
    """Request model for pattern coloring generation"""
    shape: str  # e.g., "dog", "car", "butterfly"
    age_level: str  # e.g., "age_5", "age_10"
    quality: Optional[str] = "low"  # "low" or "high"
    deterministic: Optional[bool] = False  # Use deterministic pattern selection
    pattern_index: Optional[int] = 0  # Starting pattern index for deterministic mode


class PatternResponse(BaseModel):
    """Response model for pattern coloring"""
    image: str  # Base64 encoded image
    prompt_used: str  # The prompt that was generated
    shape: str
    age_level: str
    pattern_count: int


@pattern_router.post("/generate", response_model=PatternResponse)
async def generate_pattern_coloring(request: PatternRequest):
    """
    Generate a pattern coloring page for any shape at any age level.
    
    - **shape**: The item to draw (e.g., "dog", "car", "butterfly", "heart")
    - **age_level**: Age level from age_2 to age_10
    - **quality**: Image quality - "low" for faster, "high" for better
    - **deterministic**: If true, uses consistent pattern selection
    - **pattern_index**: Starting index for deterministic pattern selection
    """
    # Validate age level
    if request.age_level not in AGE_CONFIG:
        valid_ages = list(AGE_CONFIG.keys())
        raise HTTPException(
            status_code=400,
            detail=f"Invalid age_level. Must be one of: {valid_ages}"
        )
    
    # Generate the prompt
    if request.deterministic:
        prompt = generate_pattern_prompt_deterministic(
            request.shape,
            request.age_level,
            request.pattern_index
        )
    else:
        prompt = generate_pattern_prompt(request.shape, request.age_level)
    
    # Get pattern count for response
    config = AGE_CONFIG[request.age_level]
    pattern_count = config["count"]
    
    # Generate the image using your existing image generation function
    # This assumes you have a generate_image function that takes a prompt
    try:
        # Import your existing image generation function
        from main import generate_image_from_prompt  # Adjust import as needed
        
        image_base64 = await generate_image_from_prompt(
            prompt=prompt,
            quality=request.quality
        )
        
        return PatternResponse(
            image=image_base64,
            prompt_used=prompt,
            shape=request.shape,
            age_level=request.age_level,
            pattern_count=pattern_count
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Image generation failed: {str(e)}"
        )


@pattern_router.get("/patterns/{age_level}")
async def get_patterns_for_age(age_level: str):
    """
    Get the available patterns for a specific age level.
    
    - **age_level**: Age level from age_2 to age_10
    """
    if age_level not in PATTERN_POOLS:
        valid_ages = list(PATTERN_POOLS.keys())
        raise HTTPException(
            status_code=400,
            detail=f"Invalid age_level. Must be one of: {valid_ages}"
        )
    
    return {
        "age_level": age_level,
        "patterns": PATTERN_POOLS[age_level],
        "config": AGE_CONFIG[age_level]
    }


@pattern_router.get("/config")
async def get_pattern_config():
    """
    Get the full pattern configuration for all age levels.
    """
    return {
        "age_config": AGE_CONFIG,
        "pattern_pools": PATTERN_POOLS
    }


@pattern_router.post("/preview-prompt")
async def preview_prompt(request: PatternRequest):
    """
    Preview the prompt that would be generated without creating an image.
    Useful for testing and debugging.
    """
    if request.age_level not in AGE_CONFIG:
        valid_ages = list(AGE_CONFIG.keys())
        raise HTTPException(
            status_code=400,
            detail=f"Invalid age_level. Must be one of: {valid_ages}"
        )
    
    if request.deterministic:
        prompt = generate_pattern_prompt_deterministic(
            request.shape,
            request.age_level,
            request.pattern_index
        )
    else:
        prompt = generate_pattern_prompt(request.shape, request.age_level)
    
    config = AGE_CONFIG[request.age_level]
    
    return {
        "prompt": prompt,
        "shape": request.shape,
        "age_level": request.age_level,
        "pattern_count": config["count"],
        "layout": config["layout"],
        "available_patterns": PATTERN_POOLS[request.age_level]
    }


# Integration instructions for main.py:
"""
To integrate this into your existing FastAPI app, add the following to your main.py:

1. Import the router:
   from pattern_endpoints import pattern_router

2. Include the router in your app:
   app.include_router(pattern_router)

3. Make sure pattern_config.py is in the same directory or adjust imports.

Example usage after integration:

POST /pattern/generate
{
    "shape": "dog",
    "age_level": "age_7",
    "quality": "low"
}

GET /pattern/patterns/age_7
GET /pattern/config
POST /pattern/preview-prompt
"""
