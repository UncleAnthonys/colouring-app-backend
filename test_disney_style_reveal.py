import google.generativeai as genai

genai.configure(api_key="AIzaSyA0dAL2APhtfRgfM08wgOcLjURlsoZSYns")

try:
    model = genai.GenerativeModel('gemini-2.5-flash-image')
    
    reveal_prompt = '''Create a HIGH-QUALITY Disney/Pixar 3D character reveal:

CHARACTER ONLY (ignore any background elements from original):
- Beautiful 3D rendered girl character  
- VERY LONG flowing blonde hair extending from head nearly to ground
- Crown/spikes on top of head
- Dress with exact colors: RED (top), YELLOW, GREEN, BLUE, ORANGE (bottom)
- Single vertical line of black buttons up middle of dress
- Extremely tall/long proportions (distinctive feature)

STYLE: High-quality Disney/Pixar 3D animation - smooth, polished, professional
BACKGROUND: Magical celebration scene with confetti, rainbows, sparkles
TEXT: "Rainbow - NEW ADVENTURE AWAITS!" in colorful letters

DO NOT recreate any scene elements from original drawing - character only!'''
    
    response = model.generate_content([reveal_prompt])
    
    if response.parts:
        for part in response.parts:
            if hasattr(part, 'inline_data') and part.inline_data:
                with open('rainbow_disney_style.png', 'wb') as f:
                    f.write(part.inline_data.data)
                print('✅ Disney-style reveal with long hair!')
                break
    
except Exception as e:
    print(f"Error: {e}")

