"""
Enhanced Character Extraction for Little Lines
Focus: Extreme accuracy for proportions, hair direction, and ALL visual elements
"""

import google.generativeai as genai
import base64
import os
from pathlib import Path

# Configure Gemini
genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))
model = genai.GenerativeModel('gemini-2.5-flash')


async def extract_character_with_extreme_accuracy(image_data: bytes, character_name: str) -> str:
    """
    Extract character details with EXTREME ACCURACY focusing on:
    - Exact proportions (measurements relative to body)
    - Hair direction and flow analysis
    - Precise counting of elements
    - Distinctive features preservation
    """
    
    # Load and encode image
    # with open(image_path, 'rb') as f:
        # image_data = f.read()
    image_b64 = base64.b64encode(image_data).decode('utf-8')
    
    prompt = f"""You are analyzing a child's drawing of a character named "{character_name}" to create a PERFECT 3D Disney/Pixar reveal.

Your analysis must be EXTREMELY DETAILED and ACCURATE. This analysis will be used to generate a 3D character that looks EXACTLY like this drawing brought to life.

# CRITICAL ANALYSIS PRINCIPLES

## 1. PROPORTIONAL MEASUREMENTS (MOST IMPORTANT!)
Measure EVERYTHING relative to the total figure:

**HEAD-TO-BODY RATIO:**
- What % of total height is the head? (e.g., "Head is 40% of total height - VERY LARGE HEAD")
- Is this a distinctive proportion that defines the character?

**LIMB PROPORTIONS:**
- Legs: What % of total height? (If >50% = EXTREMELY LONG LEGS - KEY FEATURE!)
- Arms: What % of body width? How thick/thin relative to body?
- Record if proportions are UNUSUAL - these become story elements!

**BODY SEGMENTS:**
- Torso: What % of total height?
- Each clothing section: What % of total figure?

**EXAMPLE:** "Legs are 60% of total figure height - DISTINCTIVELY LONG LEGS that make character taller and more elegant"


## 2. HAIR ANALYSIS (CRITICAL - Often Missed!)

**FLOW vs SPIKY DETERMINATION:**
Step 1: Measure stroke length vs total body height
- If strokes extend >25% of body height → LIKELY LONG HAIR
- If strokes are <15% of body height → LIKELY SHORT/SPIKY

Step 2: Analyze direction and flow
- DOWNWARD/DRAPED = LONG FLOWING HAIR (even if strokes look simple)
- UPWARD/OUTWARD SPIKES = SHORT SPIKY HAIR
- WAVY LINES = LONG FLOWING HAIR (waves indicate length)

Step 3: Count and describe
- How many strokes/sections?
- What direction does each flow?
- Does it frame the face or extend past shoulders?

**RED FLAG:** If you see multiple long strokes from the head extending downward, this is NEVER "short spiky hair"

**EXAMPLE:** "6 long yellow strokes extending from head, each reaching 35% down the body, flowing downward and outward - LONG FLOWING BLONDE HAIR past shoulders"


## 3. COUNTING PRECISION (COUNT EXACTLY!)

**RULE: If you see 6 buttons, write "exactly 6 buttons" - NOT "several buttons"**

Count and record EXACTLY:
- Buttons: How many? Where located?
- Spikes/points: Exact count
- Stripes/sections: How many bands?
- Decorative elements: Precise count
- Facial features: How many teeth showing? Eye details?

**NEVER APPROXIMATE** - Count the actual number visible.


## 4. CLOTHING vs BODY RECOGNITION

**SEGMENTED COLORS = CLOTHING SECTIONS:**
- If colors change in horizontal bands = dress/shirt sections
- Record each section's color FROM TOP TO BOTTOM in order
- Note where clothing ends and body begins

**EXAMPLE:** "Dress has 4 distinct horizontal sections: red top section (20% of dress), yellow upper-middle (25%), blue lower-middle (25%), green bottom section (30%)"


## 5. DISTINCTIVE FEATURES (What Makes This Character Unique?)

Identify and EMPHASIZE:
- Unusual proportions (big head, long legs, tiny arms)
- Unique accessories (crown, wings, tail)
- Asymmetric features (different colored eyes, one sided decoration)
- Signature elements (specific pattern, special markings)

**These become STORY ELEMENTS** - treat them as intentional character traits, not drawing mistakes!


## 6. COLOR PRECISION

Record colors in this order:
1. **Skin/body tone** (if visible)
2. **Hair color** (exact shade if possible)
3. **Clothing colors** (top to bottom sequence)
4. **Accessories** (crown, shoes, jewelry)
5. **Distinctive colored features** (colored eyes, lips, etc.)


## 7. FACIAL FEATURES

Describe in detail:
- **Eyes:** Color, shape, size relative to face, expression
- **Mouth:** Open/closed? Showing teeth? How many teeth? Expression?
- **Nose:** Present or absent? Shape?
- **Expression:** Happy, sad, excited, neutral?
- **Accessories:** Anything on/near face (crown, glasses, whiskers)


## 8. POSE AND POSITION

- Standing? Sitting? Action pose?
- Arms position (up, down, out, one different than other)
- Legs position (together, apart, one forward)
- Body orientation (front view, side view, 3/4 view)


# YOUR DETAILED ANALYSIS

Now analyze this drawing of "{character_name}" following ALL rules above.

Structure your response as:

## PROPORTIONAL MEASUREMENTS
[Exact % measurements of head, legs, arms, torso relative to total figure]
[Identify ANY unusual proportions as KEY FEATURES]

## HAIR ANALYSIS  
[Type: flowing vs spiky, based on length and direction]
[Length measurement: X% of body height]
[Flow direction: downward/outward/upward]
[Color and texture details]

## HEAD/FACE DETAILS
[Exact counts and measurements]
[Expression and character personality]

## BODY/CLOTHING STRUCTURE
[Each section identified as clothing vs body]
[Colors listed top-to-bottom with % of coverage]
[Exact counts of buttons, stripes, patterns]

## ARMS/HANDS
[Proportions, position, colors, details]

## LEGS/FEET  
[Proportions (critical!), position, colors, footwear details]

## DISTINCTIVE FEATURES
[List everything unique that defines this character]
[Frame unusual proportions as character traits for storytelling]

## CHARACTER PERSONALITY
[What personality does this drawing convey?]
[How should they move and act in 3D form?]

## 3D TRANSFORMATION NOTES
[How should this 2D drawing translate to living 3D Disney/Pixar character?]
[What materials/textures for each element?]
[How to preserve the drawing's spirit while making it "real"?]


Remember: This analysis creates the 3D character reveal. EXTREME ACCURACY in proportions and details ensures the reveal looks exactly like their drawing brought to life!"""

    try:
        response = model.generate_content([
            prompt,
            {"mime_type": "image/jpeg", "data": image_b64}
        ])
        
        analysis = response.text
        
        print(f"\n{'='*80}")
        print(f"ENHANCED CHARACTER EXTRACTION FOR: {character_name}")
        print(f"{'='*80}")
        print(analysis)
        print(f"\n{'='*80}")
        print(f"Analysis length: {len(analysis)} characters")
        print(f"{'='*80}\n")
        
        return {
            "character": {
                "name": character_name,
                "description": analysis,
                "key_feature": "See detailed analysis"
            },
            "reveal_description": analysis,
            "extraction_time": 0
        }
        
    except Exception as e:
        print(f"Error during character extraction: {str(e)}")
        raise


def generate_reveal_from_analysis(character_name: str, detailed_analysis: str) -> str:
    """
    Generate Disney/Pixar 3D reveal using the detailed character analysis.
    Focus on transforming the CONCEPT to life, not recreating the drawing style.
    """
    
    reveal_prompt = f"""Create a LIVING, BREATHING Disney/Pixar 3D character that brings this child's drawing to life.

# CHARACTER ANALYSIS (from drawing):
{detailed_analysis}


# 3D TRANSFORMATION RULES

**CRITICAL: Interpret the drawing's INTENT, not literal crayon strokes**

## Material Translation:
- Yellow crayon strokes on head → Flowing blonde hair with realistic texture and movement
- Simple circle eyes → Expressive Disney eyes with depth, highlights, and emotion  
- Flat colored sections → Realistic fabric with folds, shadows, and texture
- Stick limbs → Properly modeled 3D limbs with realistic anatomy
- Drawn lines → Smooth 3D surfaces with proper lighting

## Proportion Preservation:
- **PRESERVE unusual proportions from analysis** - they're character features!
- Long legs = Keep them notably long (elegant, graceful character trait)
- Big head = Keep it larger (cute, appealing Disney style)
- Distinctive features = Emphasize them in 3D form

## Disney/Pixar Quality Standards:
- Realistic skin texture (peach/brown tone with subsurface scattering)
- Hair with individual strands and natural flow
- Fabric with realistic draping and texture  
- Professional 3D rendering with proper lighting
- Expressive face showing personality
- Eyes that convey emotion and life

## Scene Requirements:
- Celebration background (colorful balloons, confetti, magical sparkles)
- Warm lighting that makes character glow
- Character centered, full body visible
- Portrait orientation (taller than wide)
- Character looks joyful and alive
- **NO TEXT OVERLAY - pure visual celebration**

## Character Personality:
Based on the drawing analysis, this character should feel:
- [Pull personality traits from analysis]
- Confident, joyful, ready for adventure
- Pose that shows their distinctive features naturally


# FINAL PROMPT FOR IMAGE GENERATION:

Transform "{character_name}" from a child's drawing into a living Disney/Pixar 3D character.

{detailed_analysis}

Create a magical, photorealistic 3D rendering with:
- Disney/Pixar animation quality
- Realistic textures (hair, fabric, skin)
- Expressive face full of personality  
- Character's distinctive proportions preserved (especially if legs are long, head is big, etc.)
- Celebration background with balloons and magical sparkles
- Portrait format, character centered and joyful
- Professional 3D lighting and rendering
- NO TEXT anywhere in image

Bring this drawing to LIFE as a real character!"""

    return reveal_prompt


# Example usage and testing
if __name__ == "__main__":
    
    print("Enhanced Character Extraction System")
    print("="*80)
    print("Focus: Extreme accuracy for proportions, hair, and all visual elements")
    print("="*80)
    
    # This will be called from the API with actual image paths
    # For now, this demonstrates the enhanced analysis structure
    
    print("\nKey improvements:")
    print("1. Proportional measurements as % of total figure")
    print("2. Hair flow analysis with length measurement")  
    print("3. Exact counting (not approximations)")
    print("4. Clothing vs body segment identification")
    print("5. Distinctive features emphasized as character traits")
    print("6. 3D transformation guidance")
    print("\nReady for integration with adventure_endpoints.py")
