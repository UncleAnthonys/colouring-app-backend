"""
Test v4 - UNIVERSAL prompt for any photo
"""

import httpx
import base64
import asyncio
import os

STRONG_LIKENESS_PROMPT_UNIVERSAL = """Convert this photograph into a colouring book page.

⚠️ CRITICAL - KEEP EVERY SINGLE PERSON:
- Include EVERY person visible in the photo - do NOT remove anyone
- If someone is holding a baby or child, that baby/child MUST appear
- Count the people carefully and ensure ALL of them are in the drawing
- Do NOT simplify by removing people

⚠️ FACE ACCURACY IS THE #1 PRIORITY:
- TRACE the exact facial contours from the photo - do NOT reinterpret or stylize
- Match the PRECISE nose shape, eye spacing, mouth width, chin shape for EVERY person
- Copy the EXACT hairstyle for each person - length, parting, texture
- Do NOT cartoon-ify the faces - keep them REALISTIC outlines
- A parent MUST instantly recognise their specific children
- Every face must look like THAT specific person, not a generic person

TRACING INSTRUCTIONS:
- Imagine you are placing tracing paper over the photo
- Draw the outline of EACH person's face following their ACTUAL contours
- The nose shape, chin angle, forehead - all must match the real person
- Hair should follow the REAL flow and shape

CRITICAL: Draw EXACTLY what is in the photo.
- Do NOT remove any people (including babies being held)
- Do NOT add any extra people
- Do NOT add pets, animals or objects not in the photo

PEOPLE AND CLOTHING:
- Keep exact body positions and poses from photo
- If someone is holding/carrying another person, show this
- Simplify clothing but keep it recognisable

BACKGROUND:
- Keep the main background elements recognisable
- Simplify trees/foliage to simple shapes
- Clean up ground texture

LINE STYLE:
- Bold black outlines on pure white
- Clean enclosed shapes for colouring
- Medium line thickness

OUTPUT: Bold black lines on pure white. Every person's face must be photo-accurate. Do NOT remove anyone."""


async def test_strong_likeness(image_path: str):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: Set OPENAI_API_KEY first")
        return
    
    with open(image_path, 'rb') as f:
        image_bytes = f.read()
    
    print(f"Testing UNIVERSAL prompt with: {image_path}")
    print(f"Key: Keep ALL people, accurate faces\n")
    
    headers = {"Authorization": f"Bearer {api_key}"}
    
    files = [
        ("image[]", ("source.jpg", image_bytes, "image/jpeg")),
    ]
    data = {
        "model": "gpt-image-1.5",
        "prompt": STRONG_LIKENESS_PROMPT_UNIVERSAL,
        "n": "1",
        "size": "1024x1536",
        "quality": "low",
    }
    
    print("Calling OpenAI API...")
    
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
                    with open('test_universal.png', 'wb') as f:
                        f.write(base64.b64decode(img_data["b64_json"]))
                    print("✅ Saved: test_universal.png")
                elif "url" in img_data:
                    img_response = await client.get(img_data["url"])
                    with open('test_universal.png', 'wb') as f:
                        f.write(img_response.content)
                    print("✅ Saved: test_universal.png")
                    
                print("\nOpen: open test_universal.png")
        else:
            print(f"Error: {response.status_code}")
            print(response.text[:1000])


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: OPENAI_API_KEY=xxx python3 test_likeness_v4.py <image_path>")
        sys.exit(1)
    
    asyncio.run(test_strong_likeness(sys.argv[1]))
