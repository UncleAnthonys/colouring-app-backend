"""
Patch script: Add age-specific alphabet handling to build_text_to_image_prompt in app.py
This mirrors the photo mode alphabet prompts but without "people from the photo"
"""

# Read the current app.py
with open('app.py', 'r') as f:
    content = f.read()

# The alphabet handling block to insert
alphabet_block = '''    # Handle alphabet themes with age-specific prompts (mirrors photo mode)
    if description.startswith("alphabet_"):
        letter = description.replace("alphabet_", "").upper()
        
        # UNDER 3 - blob letter character
        if age_level == "under_3":
            return f"""Create the SIMPLEST possible BLACK AND WHITE colouring page for a 2 year old baby.

DRAW:
- A big friendly letter {letter} CHARACTER with a cute face, arms and legs
- ONE simple object that starts with {letter} next to it

STYLE:
- BLACK OUTLINES ON WHITE ONLY - no colour, no grey, no shading
- NO pink cheeks, NO blush, NO rosy cheeks - pure black lines only
- EXTREMELY THICK black outlines
- Blob/kawaii style - super rounded and chunky
- Faces: just dots for eyes, simple curve for mouth
- Maximum 8-10 colourable areas TOTAL

BACKGROUND:
- PURE WHITE - absolutely nothing else

OUTPUT: Simple blob letter {letter} character with one {letter} object on pure white."""

        # AGE 3 - simple letter character
        if age_level == "age_3":
            return f"""Create an EXTREMELY SIMPLE toddler alphabet colouring page for letter {letter}.

DRAW:
- A big friendly letter {letter} CHARACTER with a cute face, arms and legs
- 1-2 simple objects that start with {letter}

STYLE:
- BLACK OUTLINES ON WHITE ONLY - no colour, no grey, no shading
- NO pink cheeks, NO blush, NO rosy cheeks - pure black lines only
- EXTREMELY THICK black outlines
- Blob/kawaii style - super rounded and chunky figures
- Faces: just dots for eyes, simple curve for mouth
- Maximum 10-12 colourable areas TOTAL

BACKGROUND:
- PURE WHITE - absolutely nothing else

OUTPUT: Simple friendly letter {letter} character with a couple of {letter} objects on pure white."""

        # AGE 4 - letter character with more objects
        if age_level == "age_4":
            return f"""Create a SIMPLE alphabet colouring page for letter {letter} for a 4 year old.

DRAW:
- 1-2 cute children in simple outfits
- A big friendly letter {letter} CHARACTER with a cute face, arms and legs standing with them
- 2-3 simple objects that start with {letter}

STYLE:
- BLACK OUTLINES ON WHITE ONLY - no colour, no grey, no shading
- NO pink cheeks, NO blush, NO rosy cheeks - pure black lines only
- THICK black outlines
- Simple rounded cartoon figures
- The letter {letter} must be LARGE and clearly visible
- Maximum 15-18 colourable areas

NO TEXT - do not write any words or labels

BACKGROUND:
- PURE WHITE - no ground, no scenery

OUTPUT: Simple figures with friendly letter {letter} character and a few {letter} objects. No text."""

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

# Find the insertion point - right before "# Check in themes section for text_only themes"
target = '    # Check in themes section for text_only themes'

if target in content:
    content = content.replace(target, alphabet_block + target)
    
    with open('app.py', 'w') as f:
        f.write(content)
    
    print("✅ Added alphabet-specific handling to build_text_to_image_prompt")
    print("   - under_3, age_3, age_4: Letter as friendly CHARACTER with face/arms/legs")
    print("   - age_5+: Letter as large decorative element (no face/arms/legs)")
else:
    print("❌ Could not find insertion point in app.py")
    print("   Looking for:", target)
