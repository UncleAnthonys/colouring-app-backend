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


def detect_image_type(image_data: bytes) -> str:
    """
    Detect whether the uploaded image is a child's drawing or a real photo.
    Uses Gemini 2.0 Flash for accurate classification (~$0.0001 per call).
    
    Returns: 'drawing' or 'photo'
    """
    import google.generativeai as genai
    
    try:
        api_key = os.environ.get('GOOGLE_API_KEY') or os.environ.get('GEMINI_API_KEY')
        genai.configure(api_key=api_key)
        
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        # Convert bytes to base64 for Gemini
        image_b64 = base64.b64encode(image_data).decode('utf-8')
        
        response = model.generate_content([
            """Look at this image carefully. Classify it as ONE of these:

DRAWING - A child's artwork or drawing is the MAIN SUBJECT. This includes:
          - Photos/scans OF drawings (you can see paper, table, etc but the SUBJECT is a drawing)
          - Hand-drawn pictures, sketches, paintings, doodles by children
          - Digital drawings or artwork
          - If the main subject was DRAWN BY HAND with crayons, markers, pencils, paint = DRAWING

PHOTO - A real-world subject photographed with a camera/phone. The subject itself is real:
        - Real children, real people, real pets, real animals
        - Real toys, stuffed animals, figurines
        - Real objects in the real world

KEY TEST: Is the SUBJECT of the image something drawn/painted by a child, or is it a real-world thing?
A photo OF a drawing = DRAWING (because the subject is artwork)
A photo OF a real dog = PHOTO (because the subject is a real animal)

Reply with EXACTLY one word: DRAWING or PHOTO""",
            {"mime_type": "image/jpeg", "data": image_b64}
        ])
        
        result_text = response.text.strip().upper()
        result = "drawing" if "DRAWING" in result_text else "photo"
        
        print(f"\n[IMAGE DETECTION] Gemini says: {result_text} -> {result}")
        
        return result
        
    except Exception as e:
        import time
        error_str = str(e)
        if "429" in error_str:
            print(f"[IMAGE DETECTION] Rate limited, retrying in 5s...")
            time.sleep(5)
            try:
                response = model.generate_content([
                    """Look at this image carefully. Classify it as ONE of these:

DRAWING - A child's artwork or drawing is the MAIN SUBJECT. This includes:
          - Photos/scans OF drawings (you can see paper, table, etc but the SUBJECT is a drawing)
          - Hand-drawn pictures, sketches, paintings, doodles by children
          - Digital drawings or artwork
          - If the main subject was DRAWN BY HAND with crayons, markers, pencils, paint = DRAWING

PHOTO - A real-world subject photographed with a camera/phone. The subject itself is real:
        - Real children, real people, real pets, real animals
        - Real toys, stuffed animals, figurines
        - Real objects in the real world

KEY TEST: Is the SUBJECT of the image something drawn/painted by a child, or is it a real-world thing?
A photo OF a drawing = DRAWING (because the subject is artwork)
A photo OF a real dog = PHOTO (because the subject is a real animal)

Reply with EXACTLY one word: DRAWING or PHOTO""",
                    {"mime_type": "image/jpeg", "data": image_b64}
                ])
                result_text = response.text.strip().upper()
                result = "drawing" if "DRAWING" in result_text else "photo"
                print(f"\n[IMAGE DETECTION] Retry success: {result_text} -> {result}")
                return result
            except Exception as e2:
                print(f"[IMAGE DETECTION] Retry failed: {e2}, defaulting to drawing")
        else:
            print(f"[IMAGE DETECTION] Error: {e}, defaulting to drawing")
        return "drawing"


async def extract_character_with_extreme_accuracy(image_data: bytes, character_name: str) -> str:
    """
    Extract character details with EXTREME ACCURACY focusing on:
    - Exact proportions (measurements relative to body)
    - Hair direction and flow analysis
    - Precise counting of elements
    - Distinctive features preservation
    - UNIQUE ATTACHMENTS (bolts, antennae, wings, etc.)
    
    Automatically detects whether input is a drawing or photo and adapts accordingly.
    """
    
    image_b64 = base64.b64encode(image_data).decode('utf-8')
    
    # Detect if this is a drawing or a photo (pure image analysis, zero cost)
    image_type = detect_image_type(image_data)
    print(f"\n[DETECTION] Image type: {image_type}")
    
    if image_type == "photo":
        return await _extract_from_photo(image_b64, character_name)
    
    return await _extract_from_drawing(image_b64, character_name)


async def _extract_from_photo(image_b64: str, character_name: str) -> dict:
    """
    Extract character details from a REAL PHOTO (toy, pet, child, object).
    Adapts analysis for physical subjects rather than drawn characters.
    """
    
    prompt = f"""You are a character designer extracting VISUAL ATTRIBUTES from a reference image to illustrate a fictional Pixar-style animated character named "{character_name}".

This is a reference image. Your task is METADATA EXTRACTION for character illustration — NOT identity analysis, NOT measurement of any real person, NOT facial recognition. You are extracting stylistic cues (hair style, clothing, accessories, setting, activity) to help an artist design a fictional animated character inspired by the reference.

# EXTRACTION PRINCIPLES

## 1. SUBJECT CATEGORY (for illustration style guidance)
Choose the illustration style that best fits:
- Plush toy / stuffed animal → Toy-alive style (Toy Story, Forky)
- Animal / pet → Anthropomorphic animal style (Zootopia, Finding Nemo)
- Person → Pixar-stylized human character (Inside Out, Coco, Brave)
- Object → Personified-object style (Cars, Wall-E)
- Other creature → Creature style (Monsters Inc)

## 2. VISUAL STYLE CUES (what to carry into illustration)

**HAIR / TOP OF HEAD:**
- Hair style (curly, straight, wavy, braids, pigtails, short, long, tied up)
- Hair texture cue
- Any headwear (hat, hair clip, crown, headband)

**CLOTHING / OUTFIT:**
- Top: style (t-shirt, dress, jumper, striped top, collared shirt) — describe shape and pattern, not precise colours
- Bottom: style (trousers, shorts, skirt, leggings)
- Footwear: style (trainers, boots, wellies)
- Any distinctive clothing features (stripes, polka dots, characters on clothes, pockets, buttons)

**ACCESSORIES:**
- Glasses, watch, jewellery, backpack, bag
- Anything being held or worn

## 3. ACTIVITY AND OBJECTS (CRITICAL — drives story personalisation)

This is the most important section for story generation. Look carefully at WHAT IS HAPPENING in the image.

**OBJECTS BEING HELD OR USED:**
Is the subject holding or using anything? (bike, scooter, football, paintbrush, book, musical instrument, toy, balloon, fishing rod, bucket, magic wand, teddy bear, etc.)

**ACTIVITY:**
What is the subject doing? (riding, jumping, climbing, dancing, painting, kicking a ball, reading, swimming, running, building, cooking, etc.)

**ACTIVITY-SPECIFIC GEAR:**
Ballet shoes, superhero cape, football kit, chef's hat, wellies, swim goggles, crown, fairy wings — anything signalling what the activity is.

**FOR EACH OBJECT/ACTIVITY:**
1. WHAT it is (be specific — "football" not "ball")
2. HOW the subject is interacting with it
3. WHAT IT LOOKS LIKE (shape, pattern — avoid precise colours)
4. STORY POTENTIAL (is this the main focus of the image?)

This drives the personalised story. A subject riding a bike gets a bike adventure. A subject with a magnifying glass becomes a detective. A subject in ballet shoes dances through their story.

If NO specific activity: say "No specific activity detected — subject is in a neutral pose."

## 4. SETTING / BACKGROUND (brief)
One-line description of where the image appears to be taken (garden, bedroom, beach, park, living room, woodland, indoor, outdoor). This hints at the story world.

## 5. EXPRESSION / MOOD (from face — general cue only)
One word for the feeling the character should convey: happy, curious, determined, mischievous, calm, excited, thoughtful. Do NOT describe facial features in detail. Do NOT analyse the face beyond extracting the ONE expression word.

## 6. DISTINCTIVE STYLE FEATURES
The 3–5 things that will make the illustrated character recognisable as inspired by this reference:
- e.g., "curly shoulder-length hair", "striped t-shirt", "holding a football", "wellies", "sits on a swing"
These are ILLUSTRATION CUES — style features the artist will carry into the drawing.

# STRICT BOUNDARIES

- DO NOT estimate age of any person
- DO NOT measure proportions of any person (head-to-body ratios, limb lengths)
- DO NOT analyse facial features in detail (eye shape, nose shape, skin tone)
- DO NOT describe anyone as "a child", "a girl", "a boy", "a young person" — use "the subject" or the character's chosen name
- DO NOT comment on any person's appearance beyond hair style and clothing
- Non-person subjects (toys, pets, creatures) can be described with more detail — the above restrictions apply ONLY to people

# OUTPUT FORMAT

## SUBJECT CATEGORY
[Pixar illustration style category]

## HAIR / HEADWEAR
[Style cues only — no measurements]

## CLOTHING
[Top, bottom, footwear — shape and pattern, not precise colours]

## ACCESSORIES
[Any items worn or held]

## ACTIVITY AND OBJECTS
[What is happening, what is being held/used — this drives the story]

## SETTING
[One-line where the image appears taken]

## EXPRESSION
[One word mood cue]

## DISTINCTIVE STYLE FEATURES
[3–5 bullet points — the illustration cues that make this character recognisable]

Keep the entire analysis under 500 words. Brief, illustration-focused, no clinical detail."""

    try:
        response = model.generate_content([
            {"mime_type": "image/jpeg", "data": image_b64},
            prompt
        ])
        
        detailed_analysis = response.text
        
        print("\n" + "="*80)
        print(f"[PHOTO MODE] Analysis length: {len(detailed_analysis)} characters")
        print("="*80 + "\n")
        
        return {
            "character": {
                "name": character_name,
                "description": detailed_analysis,
                "key_feature": "Distinctive features from original photo - see full analysis"
            },
            "reveal_description": detailed_analysis,
            "reveal_prompt": generate_reveal_from_photo_analysis(character_name, detailed_analysis),
            "extraction_time": 0,
            "source_type": "photo"
        }
        
    except Exception as e:
        print(f"Error during photo character extraction: {str(e)}")
        raise


def generate_reveal_from_photo_analysis(character_name: str, detailed_analysis: str) -> str:
    """
    Generate Disney/Pixar 3D reveal prompt from a PHOTO analysis.
    Adapts the transformation language for real-world subjects.
    """
    
    reveal_prompt = f"""Create a LIVING, BREATHING Disney/Pixar 3D character that brings this real-world subject to life.

# CHARACTER ANALYSIS (from photo):
{detailed_analysis}


# 3D TRANSFORMATION RULES

**CRITICAL: Transform the REAL subject into a Pixar character while preserving what makes it recognizable**

## Transformation By Subject Type:
- **Stuffed toy** → Bring to LIFE like Toy Story! Keep fabric texture hints but add real expressions and movement. Think Lotso the bear but with THIS character's exact features.
- **Real animal/pet** → Anthropomorphize like Zootopia! Keep the species, breed characteristics, and coloring. Add big expressive eyes, standing posture, personality.
- **Person** → Pixar-stylize like Riley from Inside Out or Miguel from Coco! Keep hair style, clothing, and personality.
- **Object** → Personify like Forky or the Cars characters! Keep the shape and color but add face, limbs if needed, personality.

## Proportion Preservation:
- **PRESERVE unusual proportions from analysis** - they're character features!
- Long floppy arms on a toy = Keep them long and expressive
- Oversized head = Keep it larger (cute, appealing)
- Stubby legs = Keep them short and endearing
- These proportions ARE the character's personality!

## Disney/Pixar Quality Standards:
- **EXPRESSIVE PIXAR FACE (CRITICAL!):**
  - BIG expressive eyes with visible highlights/reflections
  - Eyes should show EMOTION and LIFE
  - Proper eyebrows that convey expression
  - Cute nose appropriate to character type
  - Expressive mouth with personality
  - The face should look like it belongs in a Pixar movie
- Professional 3D rendering with proper lighting
- Warm, appealing character design

## Texture Translation:
- Plush fur → Soft 3D fur with subsurface scattering (like Sulley or Lotso)
- Real fur → Detailed 3D fur rendering (like Bolt)
- Fabric → Realistic fabric with folds and texture
- Skin → Smooth Pixar skin with warmth

## Background (CRITICAL — DO NOT KEEP ORIGINAL PHOTO BACKGROUND!):
- COMPLETELY REMOVE the original photo background — no trace of the real-world environment (no living rooms, gardens, bedrooms, parks, or any real location)
- REPLACE with a vibrant ILLUSTRATED celebration scene: colorful confetti, streamers, sparkles, and magical particles
- The background must be ILLUSTRATED/ANIMATED style matching the Pixar character — NOT a photograph
- Think: the confetti-filled reveal moment from a Pixar movie trailer
- Bright, saturated colors — this is a celebration moment!
- Warm lighting that makes character glow

## Composition:
- Character centered, full body visible
- Portrait orientation (taller than wide)
- Character looks joyful and alive
- **ABSOLUTELY NO TEXT - no words, no letters, no captions anywhere**


# FINAL PROMPT FOR IMAGE GENERATION:

Transform "{character_name}" from a real-world subject into a living Disney/Pixar 3D character.

{detailed_analysis}

Create a magical, photorealistic 3D rendering with:
- Disney/Pixar animation quality (like Toy Story, Zootopia, Inside Out)
- Character's distinctive features and proportions preserved
- Expressive face full of personality and JOY
- Textures appropriate to the subject type
- Celebration background with confetti and magical sparkles
- Portrait format, character centered and joyful
- Professional 3D lighting and rendering
- ABSOLUTELY NO TEXT anywhere in image

Bring this subject to LIFE as a real Pixar character!"""

    return reveal_prompt


async def _extract_from_drawing(image_b64: str, character_name: str) -> dict:
    """
    Extract character details from a CHILD'S DRAWING.
    This is the original extraction logic, unchanged.
    """
    
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


## 8. ARM AND LIMB COMPARISON (CRITICAL — PREVENTS MISIDENTIFICATION!)

**BEFORE classifying ANY appendage as a "hook", "handle", "attachment", or "special feature":**

COMPARE both sides of the character:
- If the character has TWO similar-looking appendages on opposite sides of the body (same size, same color, same general shape) → they are BOTH ARMS
- A curved or bent arm (e.g., hand on hip, arm akimbo) is NOT a hook, handle, or C-shaped attachment — it is just an ARM IN A DIFFERENT POSE
- Children often draw one arm straight down and one arm curved on the hip — this is a COMMON POSE, not an extra feature
- If both appendages end in similar hand/finger shapes → they are BOTH HANDS, regardless of arm angle

**SPECIFIC RED FLAGS — DO NOT MAKE THESE MISTAKES:**
- "C-shaped hook on right side" → WRONG if the left side has a similar arm. It's just a BENT ARM
- "Handle on waist" → WRONG if it's an arm resting on the hip
- "Unique attachment on one side" → CHECK if the other side has a matching limb first

**RULE: If in doubt, it's an ARM. Only classify something as a hook/handle/attachment if it looks COMPLETELY DIFFERENT from any arm on the character (different material, different color, mechanical-looking, no hand shape).**


## 9. POSE AND POSITION

- Standing? Sitting? Action pose?
- Arms position (up, down, out, one different than other)
- Legs position (together, apart, one forward)
- Body orientation (front view, side view, 3/4 view)


## 10. UNIQUE ATTACHMENTS & PROTRUSIONS (CRITICAL - OFTEN MISSED!)

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


## 11. CHARACTER TYPE IDENTIFICATION

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
        print(f"[DRAWING MODE] Analysis length: {len(detailed_analysis)} characters")
        print("="*80 + "\n")
        
        # === LIMB COUNTING VERIFICATION ===
        # Separate focused call to count body parts accurately
        # The main extraction often normalises odd numbers (e.g. 3 legs → 2)
        # This call forces left-to-right counting which is much more accurate
        try:
            print("[LIMB-COUNT] Running body part verification...")
            count_response = model.generate_content([
                """Count EVERY body part on this character one by one, LEFT TO RIGHT. Children draw creatures with ANY number of body parts — 3 legs is normal, 5 eyes is normal. Do NOT default to human numbers.

LEGS (limbs touching the ground):
- Leftmost leg: describe position
- Next leg to the right: describe position
- Keep going until no more legs.
TOTAL LEGS: ?

ARMS (limbs NOT touching the ground, on sides of body):
- Leftmost arm: describe position
- Next arm: describe position
- Keep going until no more arms.
TOTAL ARMS: ?

EYES:
- Leftmost eye: describe position
- Next eye: describe position
- Keep going until no more eyes.
TOTAL EYES: ?

ANTENNAE/HORNS on top of head:
- Count each one left to right.
TOTAL ANTENNAE: ?

TEETH visible in mouth:
- Count each one.
TOTAL TEETH: ?

Give FINAL COUNTS on separate lines:
LEGS: [number]
ARMS: [number]
EYES: [number]
ANTENNAE: [number]
TEETH: [number]""",
                {"mime_type": "image/png", "data": base64.b64decode(image_b64)}
            ])
            
            count_text = count_response.text
            print(f"[LIMB-COUNT] Raw response: {count_text[-200:]}")
            
            # Parse the final counts
            import re
            counts = {}
            for line in count_text.split("\n"):
                line = line.strip()
                for part in ["LEGS", "ARMS", "EYES", "ANTENNAE", "TEETH"]:
                    match = re.match(rf"^{part}:\s*(\d+)", line)
                    if match:
                        counts[part] = int(match.group(1))
            
            if counts:
                # Build a strong override that explicitly calls out wrong numbers
                count_summary = "\n\n⚠️🚨 CRITICAL OVERRIDE — VERIFIED BODY PART COUNTS 🚨⚠️\n"
                count_summary += "THE FOLLOWING COUNTS ARE THE ONLY CORRECT ONES.\n"
                count_summary += "ANY OTHER COUNTS MENTIONED EARLIER IN THIS DESCRIPTION ARE WRONG AND MUST BE IGNORED:\n"
                for part, num in counts.items():
                    count_summary += f"- {part}: exactly {num}\n"
                count_summary += "DRAW THESE EXACT NUMBERS. NO MORE. NO LESS.\n"
                detailed_analysis += count_summary
                print(f"[LIMB-COUNT] ✅ Verified counts: {counts}")
            else:
                print("[LIMB-COUNT] ⚠️ Could not parse counts, using original extraction")
                
        except Exception as e:
            print(f"[LIMB-COUNT] ⚠️ Counting failed, using original: {str(e)[:100]}")
        
        return {
            "character": {
                "name": character_name,
                "description": detailed_analysis,  # Full description - needed for story generation!
                "key_feature": "Distinctive features from original drawing - see full analysis"
            },
            "reveal_description": detailed_analysis,
            "reveal_prompt": generate_reveal_from_analysis(character_name, detailed_analysis),
            "extraction_time": 0,
            "source_type": "drawing"
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

## Background (CRITICAL — DO NOT KEEP ORIGINAL DRAWING BACKGROUND!):
- COMPLETELY REMOVE the original drawing's background — no trace of paper, table, or any real-world environment
- REPLACE with a vibrant ILLUSTRATED celebration scene: colorful confetti, streamers, sparkles, and magical particles
- The background must be ILLUSTRATED/ANIMATED style matching the Pixar character — NOT a photograph
- Think: the confetti-filled reveal moment from a Pixar movie trailer
- Bright, saturated colors — this is a celebration moment!
- Warm lighting that makes character glow

## Composition:
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
