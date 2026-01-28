import google.generativeai as genai
import base64
import os

# Set API key
genai.configure(api_key="AIzaSyA0dAL2APhtfRgfM08wgOcLjURlsoZSYns")

# Read the Rainbow image
with open('/Users/gavinwalker/Downloads/test_drawings/IMG_8885.JPG', 'rb') as f:
    image_data = f.read()

image_b64 = base64.b64encode(image_data).decode('utf-8')

try:
    # Extract character with Gemini
    model = genai.GenerativeModel('gemini-2.5-flash')
    response = model.generate_content([
        "Analyze this child's drawing and describe the character in detail:",
        {"mime_type": "image/jpeg", "data": image_b64}
    ])
    
    print("✅ Gemini character extraction:")
    print(response.text[:500] + "...")
    
    # Now generate reveal image with Gemini
    model_img = genai.GenerativeModel('gemini-2.5-flash-image')
    
    reveal_prompt = f'''Create a vibrant 3D Disney/Pixar style reveal image:
    
    Character: Rainbow - {response.text[:200]}
    
    Style: Full-color 3D rendered character
    Text: "Rainbow - NEW ADVENTURE AWAITS!" in colorful letters'''
    
    reveal_response = model_img.generate_content([reveal_prompt])
    
    if reveal_response.parts:
        for part in reveal_response.parts:
            if hasattr(part, 'inline_data') and part.inline_data:
                with open('rainbow_reveal_standalone.png', 'wb') as f:
                    f.write(part.inline_data.data)
                print("✅ Rainbow reveal image saved!")
                break
    
except Exception as e:
    print(f"Error: {e}")

