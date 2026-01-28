import google.generativeai as genai
import base64

genai.configure(api_key="AIzaSyA0dAL2APhtfRgfM08wgOcLjURlsoZSYns")

with open('/Users/gavinwalker/Downloads/test_drawings/IMG_8885.JPG', 'rb') as f:
    image_data = f.read()

image_b64 = base64.b64encode(image_data).decode('utf-8')

try:
    # Corrected analysis prompt that looks for flowing vs spiky elements
    model = genai.GenerativeModel('gemini-2.5-flash')
    response = model.generate_content([
        """Look at this drawing carefully. I need you to distinguish between:
        
        1. HAIR - Look for long flowing strokes that extend downward from the head. Do NOT confuse long flowing hair with short spiky elements.
        
        2. PROPORTIONS - If there are long yellow strokes extending down the full height of the figure, these are likely LONG FLOWING HAIR, not short spiky hair.
        
        3. CLOTHING - The segmented colorful sections appear to be a dress/gown with horizontal stripes.
        
        Analyze this character focusing on:
        - Long flowing hair (if yellow strokes flow downward)
        - Dress with colored horizontal sections  
        - Crown or accessories on top of head
        - Exact color sequence from top to bottom
        
        Be very specific about hair length and flow direction.""",
        {"mime_type": "image/jpeg", "data": image_b64}
    ])
    
    print("CORRECTED ANALYSIS:")
    print("=" * 50)
    print(response.text[:1000] + "...")
    
except Exception as e:
    print(f"Error: {e}")

