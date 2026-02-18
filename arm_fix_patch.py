"""
Patch script: Add arm comparison rule to character_extraction_gemini.py
Run from the backend directory:
  python3 arm_fix_patch.py
"""
import re

filepath = "character_extraction_gemini.py"

with open(filepath, 'r') as f:
    content = f.read()

old_text = """## 8. POSE AND POSITION

- Standing? Sitting? Action pose?
- Arms position (up, down, out, one different than other)
- Legs position (together, apart, one forward)
- Body orientation (front view, side view, 3/4 view)"""

new_text = """## 8. ARM AND LIMB COMPARISON (CRITICAL — PREVENTS MISIDENTIFICATION!)

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
- Body orientation (front view, side view, 3/4 view)"""

if old_text in content:
    content = content.replace(old_text, new_text)
    
    # Also renumber sections 9, 10 -> 10, 11
    content = content.replace("## 9. UNIQUE ATTACHMENTS", "## 10. UNIQUE ATTACHMENTS")
    content = content.replace("## 10. CHARACTER TYPE", "## 11. CHARACTER TYPE")
    
    with open(filepath, 'w') as f:
        f.write(content)
    print("✅ Patch applied successfully!")
    print("   Added: Section 8 - ARM AND LIMB COMPARISON")
    print("   Renumbered: Sections 9-10 -> 10-11")
else:
    print("❌ Could not find target text. File may have been modified.")
    print("   Looking for: '## 8. POSE AND POSITION'")
