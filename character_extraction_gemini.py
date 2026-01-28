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
    - UNIQUE ATTACHMENTS (bolts, antennae, wings, etc.)
    """
    
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

**STEP 1: LOOK FOR HAIR IN THE RIGHT PLACES**
Hair is NOT just on top of the head! Look for colored strokes:
- BESIDE the body (on left and right sides)
- BEHIND the body (visible on edges)
- BELOW the head extending DOWNWARD

**STEP 2: MEASURE FROM START TO END**
- Where does the hair START? (usually at the head)
- Where does the hair END? (shoulders? waist? knees? floor?)
- If hair extends DOWN past the shoulders → LONG FLOWING HAIR
- If hair extends DOWN to waist or beyond → VERY LONG HAIR (like Rapunzel!)
- If hair reaches near the feet/floor → EXTREMELY LONG FLOOR-LENGTH HAIR

**STEP 3: DIRECTION ANALYSIS**
- Strokes going DOWN alongside the body = LONG FLOWING HAIR
- Small spikes pointing UP from TOP of head only = could be SHORT SPIKY HAIR or CROWN
- If there are BOTH small spikes on top AND long strokes going down = CROWN + LONG HAIR

**STEP 4: DISTINGUISH CROWN FROM HAIR**
- Small pointed shapes sitting ON TOP of the head = likely CROWN/TIARA
- Long strokes extending DOWN the sides of the body = HAIR
- A character can have BOTH a crown AND long hair!
- Crowns are usually: small, on top, pointed, may be different color
- Long hair is usually: extends far down, flows beside/behind body

**CRITICAL RED FLAGS:**
- If you see yellow/blonde strokes extending DOWN past the shoulders on BOTH SIDES of the body → this is DEFINITELY LONG FLOWING HAIR, not spiky hair!
- If strokes reach the waist, hips, or floor → EXTREMELY LONG HAIR (Rapunzel-style)
- Do NOT confuse small crown points on TOP with the main hair

**EXAMPLE:** "Character has a small 3-pointed crown on top of head, PLUS extremely long flowing blonde hair that extends from the head DOWN both sides of the body, reaching nearly to the floor - approximately 70% of total figure height. This is RAPUNZEL-STYLE floor-length hair."


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


## 9. UNIQUE ATTACHMENTS & PROTRUSIONS (CRITICAL - OFTEN MISSED!)

**THIS IS EXTREMELY IMPORTANT** - Look for ANY elements attached to or extending from the character that are NOT hair:

**SIDE OF HEAD ATTACHMENTS (like Frankenstein bolts):**
- Are there structures on the SIDES of the head? (bolts, cylinders, ladder-shapes, rectangles)
- Location: Describe EXACTLY where (sides of head, temples, ears area)
- These are NOT ears - they are mechanical/decorative attachments
- Count segments/notches if present
- Describe shape (cylindrical, rectangular, ladder-like with rungs)

**OTHER HEAD ATTACHMENTS:**
- Antennae - thin lines extending upward from head
- Horns - pointed extensions from top or sides
- Ear-like structures - unusual ear shapes or decorations
- Crown/tiara elements - points, jewels, decorations

**BODY ATTACHMENTS:**
- Wings - on back or sides (count, shape, color)
- Tail - extending from back/bottom (length, shape, color)
- Extra limbs - more than 2 arms/legs
- Mechanical parts - gears, bolts, plates, wires
- Backpack/cape/accessories on body

**FOR EACH ATTACHMENT, DESCRIBE:**
1. LOCATION: WHERE exactly on the body (e.g., "extending horizontally from SIDES OF HEAD at eye level")
2. SHAPE: What does it look like (cylindrical, ladder-like, rectangular, etc.)
3. COUNT: How many? (EXACT number - e.g., "2 bolts, one on each side")
4. DETAILS: Segments, notches, patterns (e.g., "each bolt has 3-4 horizontal notches/rungs")
5. COLOR: What color are they?
6. SIZE: How big relative to head/body?

**EXAMPLE:** "2 dark gray bolt-like structures extending horizontally from SIDES OF HEAD (like Frankenstein's monster). Each bolt is ladder-shaped with 4-5 horizontal rungs/notches. They extend outward about 15% of the head width on each side. These are SIGNATURE FEATURES of the character."

**WARNING:** Do NOT confuse these with ears, hair, or other features. If there are rectangular/mechanical shapes on the sides of the head, they are likely BOLTS or ATTACHMENTS.


## 10. CHARACTER TYPE IDENTIFICATION

What TYPE of character is this?
- Human child/person
- Monster/creature
- Animal (specify which)
- Robot/mechanical being
- Fantasy creature (fairy, dragon, etc.)
- Hybrid (part human, part something else)

**This affects how the 3D character should be rendered!**
- Monsters should look like MONSTERS (not frogs or animals)
- Robots should have smooth metallic surfaces
- Humans should have realistic skin and hair


# YOUR DETAILED ANALYSIS

Now analyze this drawing of "{character_name}" following ALL rules above.

Structure your response as:

## PROPORTIONAL MEASUREMENTS
[Exact % measurements of head, legs, arms, torso relative to total figure]
[Identify ANY unusual proportions as KEY FEATURES]

## HAIR ANALYSIS
[Apply the flow vs spiky analysis - measure stroke length!]
[If strokes extend significantly downward = LONG FLOWING HAIR]

## UNIQUE ATTACHMENTS & PROTRUSIONS
[CRITICAL: Look for bolts, antennae, wings, tails, mechanical parts]
[Describe EXACTLY where they are located - especially SIDE OF HEAD attachments]
[Count segments/notches if present]

## HEAD/FACE DETAILS
[Eyes, mouth, nose, expression - with EXACT counts]

## BODY/CLOTHING DETAILS  
[Color sequence top to bottom, exact button counts, patterns]

## LIMBS DETAILS
[Arms, hands, legs, feet - positions and details]

## COLOR PALETTE
[All colors in order from top to bottom of character]

## POSE AND EXPRESSION
[Body position, arm/leg positions, facial expression]

## CHARACTER TYPE
[What kind of character is this - human, monster, robot, etc.]

## DISTINCTIVE FEATURES SUMMARY
[List the 3-5 MOST distinctive features that MUST be preserved in 3D]
[Include any unusual proportions, unique attachments, signature elements]

Be EXTREMELY thorough - every detail matters for the 3D reveal!"""

    try:
        response = model.generate_content([
            {"mime_type": "image/jpeg", "data": image_b64},
            prompt
        ])
        
        detailed_analysis = response.text
        
        print("\n" + "="*80)
        print(f"Analysis length: {len(detailed_analysis)} characters")
        print("="*80 + "\n")
        
        return {
            "character": {
                "name": character_name,
                "description": detailed_analysis[:500] + "..." if len(detailed_analysis) > 500 else detailed_analysis,
                "key_feature": "Distinctive features from original drawing - see full analysis"
            },
            "reveal_description": detailed_analysis,
            "reveal_prompt": generate_reveal_from_analysis(character_name, detailed_analysis),
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
- Side-of-head attachments (bolts) → Metallic/mechanical 3D bolts in EXACT same position

## Proportion Preservation:
- **PRESERVE unusual proportions from analysis** - they're character features!
- Long legs = Keep them notably long (elegant, graceful character trait)
- Big head = Keep it larger (cute, appealing Disney style)
- Distinctive features = Emphasize them in 3D form

## ATTACHMENT PLACEMENT (CRITICAL!):
- If analysis mentions bolts/attachments on SIDES OF HEAD → Place them on SIDES OF HEAD (not neck, not shoulders)
- If analysis mentions antennae on top of head → Place them on TOP OF HEAD
- Match the EXACT location described in the analysis
- These attachments are SIGNATURE FEATURES - get the placement RIGHT

## Disney/Pixar Quality Standards:
- **EXPRESSIVE PIXAR FACE (CRITICAL!):**
  - BIG expressive eyes with visible highlights/reflections (like Elsa, Rapunzel, Woody)
  - Eyes should show EMOTION and LIFE - not blank doll eyes
  - Proper eyebrows that convey expression
  - Cute nose (small button nose for humans, appropriate for character type)
  - Expressive mouth with personality
  - The face should look like it belongs in a Pixar movie - ALIVE and EMOTIONAL
- Realistic skin texture (appropriate for character type - smooth for monsters, peach/brown for humans)
- Hair with individual strands and natural flow (if human)
- Fabric with realistic draping and smooth solid texture (NOT knitted, NOT woolen)
- Professional 3D rendering with proper lighting
- Eyes that convey emotion and life

## FACE QUALITY IS NON-NEGOTIABLE:
- NEVER create blank, doll-like, or emotionless faces
- The character's face is the most important part - it must show personality
- Look at Rapunzel, Elsa, Woody, Buzz - their faces are ALIVE with expression
- Even monsters like Mike and Sulley have incredibly expressive faces

## Clothing Texture (IMPORTANT):
- Clothing should be SMOOTH SOLID MATERIAL like Woody's shirt or Buzz Lightyear's suit
- NO knitted texture, NO wool texture, NO visible fabric weave
- Think: plastic toy clothing appearance, clean and smooth

## Scene Requirements:
- Celebration background (colorful balloons, confetti, magical sparkles)
- Warm lighting that makes character glow
- Character centered, full body visible
- Portrait orientation (taller than wide)
- Character looks joyful and alive
- **ABSOLUTELY NO TEXT - no words, no letters, no captions anywhere**

## Character Type Rendering:
- If MONSTER: Render as a MONSTER (not a frog, not an animal) - like Sulley or Mike from Monsters Inc
- If HUMAN: Render with realistic human features
- If ROBOT: Render with smooth metallic surfaces
- Green skin on a monster = GREEN MONSTER, not a frog


# FINAL PROMPT FOR IMAGE GENERATION:

Transform "{character_name}" from a child's drawing into a living Disney/Pixar 3D character.

{detailed_analysis}

Create a magical, photorealistic 3D rendering with:
- Disney/Pixar animation quality (like Monsters Inc, Toy Story, Inside Out)
- Smooth textures (NOT knitted, NOT woolen - smooth like Pixar characters)
- Expressive face full of personality  
- Character's distinctive proportions preserved
- ALL ATTACHMENTS in their CORRECT positions (bolts on SIDES OF HEAD if that's where they are in the drawing)
- Celebration background with confetti and magical sparkles
- Portrait format, character centered and joyful
- Professional 3D lighting and rendering
- ABSOLUTELY NO TEXT anywhere in image

Bring this drawing to LIFE as a real character!"""

    return reveal_prompt


# Example usage and testing
if __name__ == "__main__":
    
    print("Enhanced Character Extraction System")
    print("="*80)
    print("Focus: Extreme accuracy for proportions, hair, and all visual elements")
    print("="*80)
    
    print("\nKey improvements:")
    print("1. Proportional measurements as % of total figure")
    print("2. Hair flow analysis with length measurement")  
    print("3. Exact counting (not approximations)")
    print("4. Clothing vs body segment identification")
    print("5. Distinctive features emphasized as character traits")
    print("6. UNIQUE ATTACHMENTS section (bolts, antennae, wings, etc.)")
    print("7. Character type identification (monster vs human vs robot)")
    print("8. 3D transformation guidance with correct attachment placement")
    print("\nReady for integration with adventure_endpoints.py")
