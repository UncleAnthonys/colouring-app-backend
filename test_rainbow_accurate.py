import google.generativeai as genai
import base64

genai.configure(api_key="AIzaSyA0dAL2APhtfRgfM08wgOcLjURlsoZSYns")

with open('/Users/gavinwalker/Downloads/test_drawings/IMG_8885.JPG', 'rb') as f:
    image_data = f.read()

image_b64 = base64.b64encode(image_data).decode('utf-8')

try:
    # First get accurate analysis of what's actually in the drawing
    model = genai.GenerativeModel('gemini-2.5-flash')
    response = model.generate_content([
        "Look at this child's drawing. Describe EXACTLY what you see - the actual shapes, colors, and proportions the child drew. Don't embellish or fantasize. What are the literal visual elements?",
        {"mime_type": "image/jpeg", "data": image_b64}
    ])
    
    print("✅ Accurate analysis:")
    print(response.text)
    
    # Now generate reveal that matches the actual drawing
    model_img = genai.GenerativeModel('gemini-2.5-flash-image')
    
    reveal_prompt = f'''Create a 3D character that looks like this child's actual drawing:

CRITICAL: Stay true to the child's original drawing style and proportions.

Based on analysis: {response.text[:300]}

Create a simple, child-friendly 3D version that maintains the same basic shapes, colors, and proportions as the original drawing. Don't add fantasy elements or elaborate details not in the original.

Text: "Rainbow - NEW ADVENTURE AWAITS!"'''
    
    reveal_response = model_img.generate_content([reveal_prompt])
    
    if reveal_response.parts:
        for part in reveal_response.parts:
            if hasattr(part, 'inline_data') and part.inline_data:
                with open('rainbow_accurate.png', 'wb') as f:
                    f.write(part.inline_data.data)
                print("✅ Accurate Rainbow reveal saved!")
                break
    
except Exception as e:
    print(f"Error: {e}")

