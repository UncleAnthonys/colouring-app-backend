"""
Patch script: Add activity/object detection to photo extraction in character_extraction_gemini.py
Run from the backend directory:
  python3 activity_detection_patch.py
"""

filepath = "character_extraction_gemini.py"

with open(filepath, 'r') as f:
    content = f.read()

# Add new section to the PHOTO extraction prompt, before "## 7. POSE AND POSITION"
old_text = """## 7. POSE AND POSITION
- How is the subject positioned?
- What personality does the pose suggest?
- Relaxed? Playful? Alert? Floppy?"""

new_text = """## 7. ACTIVITY AND OBJECTS (CRITICAL FOR STORY PERSONALIZATION!)

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
- Relaxed? Playful? Alert? Floppy?"""

if old_text in content:
    content = content.replace(old_text, new_text)
    
    # Renumber subsequent sections 8 -> 9
    content = content.replace("## 8. CHARACTER TYPE FOR PIXAR TRANSFORMATION", "## 9. CHARACTER TYPE FOR PIXAR TRANSFORMATION")
    
    # Also add ACTIVITY to the structured response section for photos
    old_response = """## POSE AND PERSONALITY
[Body position, what personality it suggests]

## CHARACTER TYPE
[How this should be Pixar-ified]"""
    
    new_response = """## ACTIVITY AND OBJECTS
[What is the child DOING? What are they HOLDING or RIDING or WEARING?]
[Describe each object/activity in detail — these become key story elements]
[If no specific activity: state "No specific activity detected"]

## POSE AND PERSONALITY
[Body position, what personality it suggests]

## CHARACTER TYPE
[How this should be Pixar-ified]"""
    
    content = content.replace(old_response, new_response)
    
    with open(filepath, 'w') as f:
        f.write(content)
    print("✅ Patch applied successfully!")
    print("   Added: Section 7 - ACTIVITY AND OBJECTS (photo extraction)")
    print("   Added: ACTIVITY AND OBJECTS to structured response format")
    print("   Renumbered: Section 8 -> 9")
else:
    print("❌ Could not find target text. File may have been modified.")
    print("   Looking for: '## 7. POSE AND POSITION'")

# Now do the same for the DRAWING extraction prompt
old_drawing = """## 8. POSE AND POSITION

- Standing? Sitting? Action pose?
- Arms position (up, down, out, one different than other)
- Legs position (together, apart, one forward)
- Body orientation (front view, side view, 3/4 view)"""

# Check if drawing section needs the arm comparison patch too
if old_drawing in content:
    print("\n⚠️  Note: Drawing extraction section 8 (POSE AND POSITION) found.")
    print("   The arm_fix_patch.py should be run separately for that fix.")
else:
    print("\n✓ Drawing extraction section may already be patched by arm_fix_patch.py")

