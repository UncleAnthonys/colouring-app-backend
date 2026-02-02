"""
Test strengthened likeness prompts without changing production code.
Run locally against the running server.
"""

import httpx
import base64
import json
import asyncio
from pathlib import Path

# Strengthened likeness prompt
STRONG_LIKENESS_PROMPT = """Convert this photograph into a colouring book page.

⚠️ FACE ACCURACY IS THE #1 PRIORITY - MORE IMPORTANT THAN ANYTHING ELSE:
- TRACE the exact facial contours from the photo - do NOT reinterpret
- Match the PRECISE nose shape, eye spacing, mouth width, chin shape
- Copy the EXACT hairstyle - every strand direction, parting, length
- Do NOT stylize, cartoon-ify, or beautify the faces
- A parent MUST instantly recognise their specific child - not just "a child"
- If there's a baby, it must look like THAT baby, not a generic baby
- Facial proportions must match the photo EXACTLY

CRITICAL: Only draw what is ACTUALLY in the photo. DO NOT add extra people, characters, animals, or objects not in the original image.

PEOPLE AND CLOTHING:
- Keep exact body positions and poses from photo
- Simplify clothing but keep it recognisable (jacket stays a jacket)
- Keep relative heights and positions accurate

BACKGROUND (SIMPLIFY BUT RECOGNISE):
- The tractor must be recognisable as that specific tractor
- Simplify trees to simple shapes but keep the scene
- Remove ground texture noise - make it clean white or simple

LINE STYLE:
- Bold black outlines on pure white
- Clean enclosed shapes for colouring
- Medium line thickness - good for age 5-7
- No tiny details or dense textures
- Maximum 30-40 colourable areas

OUTPUT: Bold black lines on pure white. Faces must be photo-accurate."""


async def test_likeness(image_path: str):
    """Test the strengthened prompt"""
    
    # Read and encode image
    with open(image_path, 'rb') as f:
        image_b64 = base64.b64encode(f.read()).decode('utf-8')
    
    print(f"Testing with: {image_path}")
    print(f"Image size: {len(image_b64)} bytes (base64)")
    
    # Call local server
    async with httpx.AsyncClient(timeout=180.0) as client:
        # Test 1: Current production prompt (no theme, age 5)
        print("\n1. Testing CURRENT production prompt...")
        response1 = await client.post(
            "http://localhost:8000/generate/photo",
            json={
                "image_b64": image_b64,
                "theme": "none",
                "age_level": "age_5",
                "quality": "low"
            }
        )
        
        if response1.status_code == 200:
            data1 = response1.json()
            if 'image_url' in data1:
                print(f"   Result URL: {data1['image_url']}")
                # Download and save
                img_response = await client.get(data1['image_url'])
                with open('test_current_prompt.png', 'wb') as f:
                    f.write(img_response.content)
                print("   Saved: test_current_prompt.png")
            elif 'image' in data1:
                with open('test_current_prompt.png', 'wb') as f:
                    f.write(base64.b64decode(data1['image']))
                print("   Saved: test_current_prompt.png")
        else:
            print(f"   Error: {response1.status_code} - {response1.text}")
        
        # Test 2: Strengthened likeness prompt (direct API call)
        print("\n2. Testing STRENGTHENED likeness prompt...")
        
        # We need to call OpenAI directly for this test
        import os
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("   Error: OPENAI_API_KEY not set")
            return
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        
        data = {
            "model": "gpt-image-1",
            "prompt": STRONG_LIKENESS_PROMPT,
            "n": 1,
            "size": "1024x1536",
            "quality": "low",
            "image": f"data:image/jpeg;base64,{image_b64}"
        }
        
        response2 = await client.post(
            "https://api.openai.com/v1/images/edits",
            headers=headers,
            json=data
        )
        
        if response2.status_code == 200:
            result = response2.json()
            if "data" in result and len(result["data"]) > 0:
                img_data = result["data"][0]
                if "b64_json" in img_data:
                    with open('test_strong_likeness.png', 'wb') as f:
                        f.write(base64.b64decode(img_data["b64_json"]))
                    print("   Saved: test_strong_likeness.png")
                elif "url" in img_data:
                    print(f"   Result URL: {img_data['url']}")
        else:
            print(f"   Error: {response2.status_code}")
            print(f"   {response2.text[:500]}")

    print("\n✅ Done! Compare:")
    print("   open test_current_prompt.png test_strong_likeness.png")


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python3 test_likeness.py <image_path>")
        print("Make sure local server is running and OPENAI_API_KEY is set")
        sys.exit(1)
    
    asyncio.run(test_likeness(sys.argv[1]))
