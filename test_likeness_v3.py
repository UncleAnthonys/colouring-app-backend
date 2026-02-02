"""
Test strengthened likeness prompts - using correct images/edits format
"""

import httpx
import base64
import asyncio
import os

# Strengthened likeness prompt
STRONG_LIKENESS_PROMPT = """Convert this photograph into a colouring book page.

⚠️ FACE ACCURACY IS THE #1 PRIORITY - MORE IMPORTANT THAN ANYTHING ELSE:
- TRACE the exact facial contours from the photo - do NOT reinterpret or stylize
- Match the PRECISE nose shape, eye spacing, mouth width, chin shape
- Copy the EXACT hairstyle - every strand direction, parting, length
- Do NOT cartoon-ify or beautify the faces - keep them REALISTIC outlines
- A parent MUST instantly recognise their specific child - not just "a generic child"
- If there's a baby, it must look like THAT specific baby
- Facial proportions must match the photo EXACTLY - measure and copy

TRACING INSTRUCTIONS:
- Imagine you are placing tracing paper over the photo
- Draw the outline of each person's face following their ACTUAL contours
- The nose bump, the chin angle, the forehead shape - all must match
- Hair should follow the REAL flow and shape, not a generic hairstyle

CRITICAL: Only draw what is ACTUALLY in the photo. DO NOT add extra people, characters, animals, or objects.

PEOPLE AND CLOTHING:
- Keep exact body positions and poses from photo
- Simplify clothing to clean shapes but keep recognisable

BACKGROUND:
- The tractor must be recognisable as that specific tractor
- Simplify trees to simple cloud shapes
- Clean white ground - no texture noise

LINE STYLE:
- Bold black outlines on pure white
- Clean enclosed shapes for colouring
- Medium line thickness

OUTPUT: Bold black lines on pure white. Faces MUST be photo-accurate tracings, not cartoon interpretations."""


async def test_strong_likeness(image_path: str):
    """Test the strengthened prompt using same API format as app.py"""
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: Set OPENAI_API_KEY first")
        return
    
    # Read image bytes
    with open(image_path, 'rb') as f:
        image_bytes = f.read()
    
    print(f"Testing with: {image_path}")
    print(f"Image size: {len(image_bytes)} bytes")
    print(f"\nPrompt preview:\n{STRONG_LIKENESS_PROMPT[:300]}...\n")
    
    headers = {"Authorization": f"Bearer {api_key}"}
    
    # Use multipart form data like app.py does
    files = [
        ("image[]", ("source.jpg", image_bytes, "image/jpeg")),
    ]
    data = {
        "model": "gpt-image-1.5",
        "prompt": STRONG_LIKENESS_PROMPT,
        "n": "1",
        "size": "1024x1536",
        "quality": "low",
    }
    
    print("Calling OpenAI API (images/edits)...")
    
    async with httpx.AsyncClient(timeout=180.0) as client:
        response = await client.post(
            "https://api.openai.com/v1/images/edits",
            headers=headers,
            files=files,
            data=data
        )
        
        if response.status_code == 200:
            result = response.json()
            if "data" in result and len(result["data"]) > 0:
                img_data = result["data"][0]
                if "b64_json" in img_data:
                    with open('test_strong_likeness.png', 'wb') as f:
                        f.write(base64.b64decode(img_data["b64_json"]))
                    print("✅ Saved: test_strong_likeness.png")
                elif "url" in img_data:
                    # Download from URL
                    img_response = await client.get(img_data["url"])
                    with open('test_strong_likeness.png', 'wb') as f:
                        f.write(img_response.content)
                    print("✅ Saved: test_strong_likeness.png")
                    
                print("\nCompare both:")
                print("  open test_current_prompt.png test_strong_likeness.png")
        else:
            print(f"Error: {response.status_code}")
            print(response.text[:1000])


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: OPENAI_API_KEY=xxx python3 test_likeness_v3.py <image_path>")
        sys.exit(1)
    
    asyncio.run(test_strong_likeness(sys.argv[1]))
