"""
Update alphabet prompts to hardcode the best single object for each letter
for under_3 and age_3 (young ages where we only show 1-2 objects)
"""

# Best single object for each letter - instantly recognizable for toddlers
best_objects = {
    'a': 'apple',
    'b': 'ball',
    'c': 'cat',
    'd': 'dog',
    'e': 'elephant',
    'f': 'fish',
    'g': 'goat',
    'h': 'hat',
    'i': 'igloo',
    'j': 'jellyfish',
    'k': 'kite',
    'l': 'lion',
    'm': 'moon',
    'n': 'nose',
    'o': 'owl',
    'p': 'penguin',
    'q': 'queen',
    'r': 'rainbow',
    's': 'star',
    't': 'tiger',
    'u': 'umbrella',
    'v': 'violin',
    'w': 'whale',
    'x': 'xylophone',
    'y': 'yo-yo',
    'z': 'zebra',
}

# Read app.py
with open('app.py', 'r') as f:
    content = f.read()

# Find and replace the alphabet handling block in build_text_to_image_prompt
# We need to replace everything from "# Handle alphabet themes with age-specific prompts"
# to just before "# Check in themes section for text_only themes"

old_start = '    # Handle alphabet themes with age-specific prompts (mirrors photo mode)\n    if description.startswith("alphabet_"):\n        letter = description.replace("alphabet_", "").upper()'

if old_start not in content:
    print("❌ Could not find the alphabet block to replace")
    print("Looking for:", old_start[:80])
    exit(1)

# Find the end of the alphabet block (right before the text_only themes check)
end_marker = '    # Check in themes section for text_only themes'

# Extract everything between start and end
start_idx = content.index(old_start)
end_idx = content.index(end_marker)

# Build the new alphabet block with hardcoded objects
# We need to build the object lookup as Python code
obj_dict_str = "{\n"
for letter, obj in best_objects.items():
    obj_dict_str += f"            '{letter}': '{obj}',\n"
obj_dict_str += "        }"

new_block = '''    # Handle alphabet themes with age-specific prompts (mirrors photo mode)
    if description.startswith("alphabet_"):
        letter = description.replace("alphabet_", "").upper()
        letter_lower = letter.lower()
        
        # Best single object for each letter - hardcoded for consistency
        best_object = ''' + obj_dict_str + '''.get(letter_lower, 'apple')
        
        # UNDER 3 - blob letter character + one hardcoded object
        if age_level == "under_3":
            return f"""Create the SIMPLEST possible BLACK AND WHITE colouring page for a 2 year old baby.

DRAW:
- A big friendly letter {letter} CHARACTER with a cute face, arms and legs
- ONE simple ''' + '{best_object}' + ''' next to it

STYLE:
- BLACK OUTLINES ON WHITE ONLY - no colour, no grey, no shading
- NO pink cheeks, NO blush, NO rosy cheeks - pure black lines only
- EXTREMELY THICK black outlines
- Blob/kawaii style - super rounded and chunky
- Faces: just dots for eyes, simple curve for mouth
- Maximum 8-10 colourable areas TOTAL

BACKGROUND:
- PURE WHITE - absolutely nothing else

OUTPUT: Simple blob letter {letter} character with one ''' + '{best_object}' + ''' on pure white."""

        # AGE 3 - simple letter character + one hardcoded object
        if age_level == "age_3":
            return f"""Create an EXTREMELY SIMPLE toddler alphabet colouring page for letter {letter}.

DRAW:
- A big friendly letter {letter} CHARACTER with a cute face, arms and legs
- ONE simple ''' + '{best_object}' + ''' next to it

STYLE:
- BLACK OUTLINES ON WHITE ONLY - no colour, no grey, no shading
- NO pink cheeks, NO blush, NO rosy cheeks - pure black lines only
- EXTREMELY THICK black outlines
- Blob/kawaii style - super rounded and chunky figures
- Faces: just dots for eyes, simple curve for mouth
- Maximum 10-12 colourable areas TOTAL

BACKGROUND:
- PURE WHITE - absolutely nothing else

OUTPUT: Simple friendly letter {letter} character with one ''' + '{best_object}' + ''' on pure white."""

        # AGE 4 - letter character with a couple objects
        if age_level == "age_4":
            return f"""Create a SIMPLE alphabet colouring page for letter {letter} for a 4 year old.

DRAW:
- A big friendly letter {letter} CHARACTER with a cute face, arms and legs
- A ''' + '{best_object}' + ''' and one other simple object that starts with {letter}

STYLE:
- BLACK OUTLINES ON WHITE ONLY - no colour, no grey, no shading
- NO pink cheeks, NO blush, NO rosy cheeks - pure black lines only
- THICK black outlines
- Simple rounded cartoon style
- The letter {letter} must be LARGE and clearly visible
- Maximum 15-18 colourable areas

NO TEXT - do not write any words or labels

BACKGROUND:
- PURE WHITE - no ground, no scenery

OUTPUT: Friendly letter {letter} character with a ''' + '{best_object}' + ''' and one other {letter} object. No text."""

        # AGE 5 - costumes, big letter (no arms/legs), more objects
        if age_level == "age_5":
            return f"""Create an alphabet colouring page for letter {letter} for a 5 year old.

DRAW:
- 1-2 cute children wearing simple COSTUMES that start with {letter}
- A big bold letter {letter} displayed prominently in the scene (NOT a character - just the letter)
- 3-4 objects that start with {letter} scattered around the scene

IMPORTANT: Do NOT put the letter {letter} printed on clothing - dress them in themed COSTUMES instead
The letter {letter} should be a large decorative letter in the scene, NOT a character with face/arms/legs

STYLE:
- BLACK OUTLINES ON WHITE ONLY - NO grey, NO shading
- NO pink cheeks, NO blush, NO rosy cheeks - pure black lines only
- Medium-thick black outlines
- Simple but clear figures
- Maximum 20-25 colourable areas

NO TEXT - do not write any words or labels (only the letter {letter} itself)

BACKGROUND:
- MINIMAL - simple ground line, maybe 1-2 clouds
- Keep mostly white

OUTPUT: Children in {letter}-themed costumes with a large letter {letter} and several {letter} objects."""

        # AGE 6 - themed scene with prominent letter
        if age_level == "age_6":
            return f"""Create an alphabet colouring page for letter {letter} for a 6 year old.

DRAW:
- 1-2 children wearing costumes or outfits themed around {letter}
- A large decorative letter {letter} prominently placed in the scene (NOT a character - just the letter)
- 4-5 objects that start with {letter} arranged in a fun scene

STYLE:
- BLACK OUTLINES ON WHITE ONLY - NO grey, NO shading
- NO pink cheeks, NO blush, NO rosy cheeks - pure black lines only
- Medium-thick black outlines
- More detail than younger ages but still clear
- Maximum 25-30 colourable areas

NO TEXT - do not write any words or labels (only the letter {letter} itself)

BACKGROUND:
- Simple themed background related to {letter}

OUTPUT: Fun {letter}-themed scene with children, large letter {letter}, and multiple {letter} objects."""

        # AGE 7-8 - detailed scene
        if age_level in ("age_7", "age_8"):
            return f"""Create a detailed alphabet colouring page for letter {letter} for a {age_level.replace('age_', '')} year old.

DRAW:
- A creative scene where EVERYTHING relates to the letter {letter}
- A large decorative letter {letter} as a focal point (NOT a character - just the letter, can be ornate/decorated)
- 5-6 objects that start with {letter} integrated naturally into the scene
- Optional: 1-2 children interacting with the {letter} objects

STYLE:
- BLACK OUTLINES ON WHITE ONLY - NO grey, NO shading
- NO pink cheeks, NO blush, NO rosy cheeks - pure black lines only
- Medium black outlines with more detail
- More intricate patterns and details appropriate for older children
- Maximum 30-40 colourable areas

NO TEXT - do not write any words or labels (only the letter {letter} itself)

OUTPUT: Detailed {letter}-themed scene with decorative letter and many {letter} objects to discover."""

        # AGE 9-10 - complex educational scene
        if age_level in ("age_9", "age_10"):
            return f"""Create a complex alphabet colouring page for letter {letter} for a {age_level.replace('age_', '')} year old.

DRAW:
- An elaborate scene built around the letter {letter}
- A large artistic/decorative letter {letter} as centrepiece (NOT a character - ornate block letter or bubble letter)
- 6-8 objects that start with {letter} woven throughout the scene
- Detailed backgrounds and environments related to {letter} words

STYLE:
- BLACK OUTLINES ON WHITE ONLY - NO grey, NO shading
- NO pink cheeks, NO blush, NO rosy cheeks - pure black lines only
- Finer black outlines with lots of detail
- Intricate patterns, textures suggested by line work
- Many small colourable areas for patient colouring
- Maximum 40-50+ colourable areas

NO TEXT - do not write any words or labels (only the letter {letter} itself)

OUTPUT: Complex detailed {letter}-themed illustration with artistic letter and many {letter} objects."""

    '''

# Replace the old block with the new one
new_content = content[:start_idx] + new_block + content[end_idx:]

with open('app.py', 'w') as f:
    f.write(new_content)

print("✅ Updated alphabet prompts with hardcoded objects for young ages")
print()
print("Hardcoded objects:")
for letter, obj in sorted(best_objects.items()):
    print(f"  {letter.upper()} → {obj}")
