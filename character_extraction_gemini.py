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
        
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        # Convert bytes to base64 for Gemini
        image_b64 = base64.b64encode(image_data).decode('utf-8')
        
        response = model.generate_content([
            """Look at this image carefully. Classify it as ONE of these:

DRAWING - A child's artwork made with crayons, markers, colored pencils, paint, etc. on paper. 
          Includes: hand-drawn pictures, sketches, paintings, doodles by children.

PHOTO - A real photograph taken with a camera/phone.
        Includes: photos of toys, stuffed animals, pets, children, people, objects.

Reply with EXACTLY one word: DRAWING or PHOTO""",
            {"mime_type": "image/jpeg", "data": image_b64}
        ])
        
        result_text = response.text.strip().upper()
        result = "drawing" if "DRAWING" in result_text else "photo"
        
        print(f"\n[IMAGE DETECTION] Gemini says: {result_text} -> {result}")
        
        return result
        
    except Exception as e:
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
    
    prompt = f"""You are analyzing a REAL PHOTOGRAPH of a subject named "{character_name}" to create a PERFECT 3D Disney/Pixar character version.

This is NOT a child's drawing - it is a photograph of a real physical subject (could be a stuffed toy, a pet, a child, or any real object). Your job is to analyze it with extreme detail so we can create an amazing Pixar-style 3D character from it.

# CRITICAL ANALYSIS PRINCIPLES

## 1. SUBJECT IDENTIFICATION
What is the subject?
- Stuffed animal / plush toy (specify animal type)
- Real pet / animal (specify species, breed if applicable)
- Child / person
- Action figure / doll / toy
- Real-world object brought to life
- Other (describe)

**This determines how to "Pixar-ify" the character!**
- Plush toy → Bring to life like Toy Story (Lotso, Woody, Forky)
- Pet/animal → Anthropomorphize like Zootopia, Finding Nemo, Puss in Boots
- Child/person → Stylize like Inside Out, Coco, Brave
- Object → Give personality like Cars, Spoon from Toy Story

## 2. PROPORTIONAL MEASUREMENTS (MOST IMPORTANT!)
Measure EVERYTHING relative to the total figure:

**HEAD-TO-BODY RATIO:**
- What % of total height is the head?
- Is this distinctive? (e.g., plush toys often have oversized heads)

**LIMB PROPORTIONS:**
- Arms/legs/paws: What % of total height?
- Are they unusually long, short, floppy, stiff?
- Record if proportions are UNUSUAL - these become story character traits!

**LIMB CLASSIFICATION (CRITICAL FOR MONSTERS/CREATURES):**
- LEGS = limbs that touch or nearly touch the GROUND and support the body's weight
- ARMS = limbs that are raised, positioned at the sides of the upper body, or used for grasping
- If a creature has 6 limbs, count how many touch the ground (those are LEGS) and how many are raised/at sides (those are ARMS)
- Do NOT classify a limb as a "leg" just because it's at the bottom — if it's raised and not touching the ground, it's an ARM
- Example: A monster with 2 limbs touching ground + 4 limbs raised = 2 legs + 4 arms, NOT 4 legs + 2 arms

**BODY SHAPE:**
- Round? Elongated? Squat? Lanky?
- What makes this body shape distinctive?

## 3. SURFACE & TEXTURE (Critical for photos!)
- Fur texture: fluffy, smooth, shaggy, curly, wiry?
- Material: plush fabric, real fur, skin, plastic, metal?
- Color patterns: solid, multi-toned, patches, gradients?
- Wear and character: any loved-looking patches, worn areas (adds personality!)

## 4. FACIAL FEATURES
- **Eyes:** Size, color, shape, material (bead eyes? glass? real?)
- **Nose:** Shape, color, texture
- **Mouth:** Visible? Stitched? Expression?
- **Ears:** Shape, position, size relative to head
- **Expression:** What emotion does the face convey?

## 5. COLOR PALETTE (Precise!)
Record all colors from top to bottom:
1. Head/face colors
2. Body colors
3. Limb colors
4. Any contrasting areas (paws, belly, face patches)
5. Eye color

## 6. DISTINCTIVE FEATURES (What makes THIS subject unique?)
- Unusual proportions (extra long arms, tiny body, huge head)
- Special markings or patterns
- Accessories or clothing
- Pose or personality cues
- Texture contrasts (dark face, light body, etc.)

**These become the CHARACTER TRAITS that drive personalized stories!**
**Treat every distinctive feature as an INTENTIONAL character trait!**

## 7. ACTIVITY AND OBJECTS (CRITICAL FOR STORY PERSONALIZATION!)

**This is one of the MOST IMPORTANT sections. Look carefully at what the child is DOING and HOLDING.**

**OBJECTS THE CHILD IS HOLDING OR USING:**
- Is the child holding ANYTHING? (bike, scooter, hula hoop, tennis racket, skateboard, football, paintbrush, magnifying glass, kite, fishing rod, bucket and spade, musical instrument, toy sword, magic wand, balloon, book, etc.)
- Is the child ON or IN something? (bicycle, scooter, climbing frame, swing, trampoline, skateboard, surfboard, kayak, horse, go-kart, etc.)
- Is the child WEARING something activity-specific? (ballet shoes, swimming goggles, superhero cape, karate belt, football kit, chef hat, crown, fairy wings, etc.)

**ACTIVITY THE CHILD IS DOING:**
- What ACTION is the child performing? (riding, jumping, climbing, dancing, painting, digging, kicking, swinging, balancing, swimming, running, etc.)
- Describe the activity in detail — this will become a KEY PLOT ELEMENT in their personalized story

**FOR EACH OBJECT/ACTIVITY FOUND, DESCRIBE:**
1. WHAT it is (be specific — not just "ball" but "football" or "tennis ball")
2. HOW the child is interacting with it (holding, riding, wearing, standing on)
3. WHAT IT LOOKS LIKE (color, size, any distinctive features)
4. HOW IMPORTANT it seems (is it the main focus of the photo, or incidental?)

**THIS IS CRITICAL BECAUSE:** The object/activity will be woven into the child's personalized story as a key plot device. A child photographed riding a bike will get a story where they ride that bike on an adventure. A child holding a magnifying glass will become a detective. A child in ballet shoes will dance their way through the story. The more detail you provide, the better the story.

**If the child is NOT holding anything or doing a specific activity, say so explicitly: "No specific activity or held object detected — child is standing/sitting in a neutral pose."**

## 8. POSE AND POSITION
- How is the subject positioned?
- What personality does the pose suggest?
- Relaxed? Playful? Alert? Floppy?

## 9. CHARACTER TYPE FOR PIXAR TRANSFORMATION
Based on what you see, how should this be rendered in Pixar style?
- If stuffed animal → Alive toy (Toy Story style) with stitching details and fabric texture
- If real animal → Anthropomorphized animal (Zootopia style) standing upright with expressions
- If child → Pixar-stylized human (Inside Out, Coco style)
- If object → Personified object (Cars, Forky style)

# YOUR DETAILED ANALYSIS

Now analyze this photograph of "{character_name}" following ALL rules above.

Structure your response as:

## SUBJECT TYPE
[What is this? Stuffed animal, pet, child, toy, etc.]

## PROPORTIONAL MEASUREMENTS
[Exact % measurements of head, limbs, body relative to total figure]
[Identify ANY unusual proportions as KEY FEATURES]

## SURFACE & TEXTURE
[Fur/material type, texture details, color patterns]

## HEAD/FACE DETAILS
[Eyes, nose, mouth, ears, expression - with precise descriptions]

## BODY DETAILS
[Shape, colors, markings, clothing/accessories]

## LIMBS DETAILS
[Arms/legs/paws - positions, proportions, details]

## COLOR PALETTE
[All colors in order from top to bottom]

## ACTIVITY AND OBJECTS
[What is the child DOING? What are they HOLDING or RIDING or WEARING?]
[Describe each object/activity in detail — these become key story elements]
[If no specific activity: state "No specific activity detected"]

## POSE AND PERSONALITY
[Body position, what personality it suggests]

## CHARACTER TYPE
[How this should be Pixar-ified]

## DISTINCTIVE FEATURES SUMMARY
[List the 3-5 MOST distinctive features that MUST be preserved in the Pixar 3D version]
[These will drive personalized story generation!]

Be EXTREMELY thorough - every detail matters for the 3D Pixar reveal!"""

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
- **Child/person** → Pixar-stylize like Riley from Inside Out or Miguel from Coco! Keep hair, skin tone, clothing, and personality.
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

## Scene Requirements:
- Celebration background (colorful balloons, confetti, magical sparkles)
- Warm lighting that makes character glow
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
