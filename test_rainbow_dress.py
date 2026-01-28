import google.generativeai as genai
import base64

genai.configure(api_key="AIzaSyA0dAL2APhtfRgfM08wgOcLjURlsoZSYns")

with open('/Users/gavinwalker/Downloads/test_drawings/IMG_8885.JPG', 'rb') as f:
    image_data = f.read()

image_b64 = base64.b64encode(image_data).decode('utf-8')

try:
    # Generate reveal with correct dress interpretation
    model_img = genai.GenerativeModel('gemini-2.5-flash-image')
    
    reveal_prompt = '''Create a 3D character based on this child's drawing:

CHARACTER: Young person wearing a colorful striped dress
- Round head with colorful spiky hair (like a rainbow mohawk)
- Simple facial features (blue eyes, small red nose, smile)
- Long dress/gown with horizontal rainbow stripes (red, orange, yellow, green, blue sections)
- Simple arms extending from sides
- Standing pose
- Child-like proportions and simple style

CRITICAL: This is a person in a dress, not a segmented creature. Keep it simple and true to child's drawing style.

Text: "Rainbow - NEW ADVENTURE AWAITS!"'''
    
    reveal_response = model_img.generate_content([reveal_prompt])
    
    if reveal_response.parts:
        for part in reveal_response.parts:
            if hasattr(part, 'inline_data') and part.inline_data:
                with open('rainbow_dress.png', 'wb') as f:
                    f.write(part.inline_data.data)
                print("✅ Rainbow with dress saved!")
                break
    
except Exception as e:
    print(f"Error: {e}")

