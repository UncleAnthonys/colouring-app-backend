import google.generativeai as genai
import base64

genai.configure(api_key="AIzaSyA0dAL2APhtfRgfM08wgOcLjURlsoZSYns")

try:
    model = genai.GenerativeModel('gemini-2.5-flash-image')
    
    reveal_prompt = '''Create a vibrant 3D Disney/Pixar style character reveal image:

CHARACTER: Rainbow - tall figure with:
- VERY LONG flowing blonde hair that extends from head nearly to the ground (almost full body length)
- Round head with blue eyes, red smile  
- Tall dress with exact color sections from top to bottom: RED, YELLOW, GREEN, BLUE, ORANGE
- Each dress section has small black dots/buttons
- Crown/spiky elements on very top of head

BACKGROUND: Celebration scene with confetti, colorful particles, bright sky, rainbows - NOT matching original drawing background

TEXT: "Rainbow - NEW ADVENTURE AWAITS!" in colorful letters

Style: Full-color 3D rendered character with celebration background'''
    
    response = model.generate_content([reveal_prompt])
    
    if response.parts:
        for part in response.parts:
            if hasattr(part, 'inline_data') and part.inline_data:
                with open('rainbow_perfect_reveal.png', 'wb') as f:
                    f.write(part.inline_data.data)
                print('✅ Perfect reveal with long hair and celebration background!')
                break
    
except Exception as e:
    print(f"Error: {e}")

