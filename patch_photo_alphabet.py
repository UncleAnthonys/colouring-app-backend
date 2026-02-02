"""
Update photo upload alphabet prompts in build_photo_prompt:
1. Use same hardcoded objects as text-to-image
2. Remove face/arms/legs from the letter - just a big clear letter
"""

# Same hardcoded objects as text-to-image
best_objects = {
    'a': 'apple',
    'b': 'ball',
    'c': 'cat',
    'd': 'dog',
    'e': 'elephant',
    'f': 'fish',
    'g': 'goat',
    'h': 'hat',
    'i': 'ice cream',
    'j': 'jellyfish',
    'k': 'kite',
    'l': 'lion',
    'm': 'monkey',
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

with open('app.py', 'r') as f:
    content = f.read()

# Build the object lookup dict
obj_dict_str = "{\n"
for letter, obj in best_objects.items():
    obj_dict_str += f"                '{letter}': '{obj}',\n"
obj_dict_str += "            }"

# ============================================
# UNDER_3 PHOTO ALPHABET
# ============================================
old_under3 = '''        # Special handling for alphabet themes
        if theme.startswith("alphabet_"):
            letter = theme.replace("alphabet_", "").upper()
            return f"""Create the SIMPLEST possible BLACK AND WHITE colouring page for a 2 year old baby.

DRAW:
- The people from the photo as VERY simple blob shapes (round heads, simple body)
- A big friendly letter {letter} CHARACTER with a cute face, arms and legs standing next to them

STYLE:
- BLACK OUTLINES ON WHITE ONLY - no colour, no grey, no shading
- EXTREMELY THICK black outlines
- Blob/kawaii style - super rounded and chunky
- Faces: just dots for eyes, simple curve for mouth
- Maximum 8-10 colourable areas TOTAL

BACKGROUND:
- PURE WHITE - absolutely nothing else

OUTPUT: Simple blob figures with friendly letter {letter} character on pure white.\""""'''

new_under3 = '''        # Special handling for alphabet themes
        if theme.startswith("alphabet_"):
            letter = theme.replace("alphabet_", "").upper()
            best_object = ''' + obj_dict_str + '''.get(letter.lower(), 'apple')
            return f"""Create the SIMPLEST possible BLACK AND WHITE colouring page for a 2 year old baby.

DRAW:
- The people from the photo as VERY simple blob shapes (round heads, simple body)
- A big bold letter {letter} (plain block letter or bubble letter - NO face, NO arms, NO legs)
- ONE simple {best_object} next to the letter

STYLE:
- BLACK OUTLINES ON WHITE ONLY - no colour, no grey, no shading
- NO pink cheeks, NO blush - pure black lines only
- EXTREMELY THICK black outlines
- Blob/kawaii style for the people - super rounded and chunky
- Maximum 8-10 colourable areas TOTAL

BACKGROUND:
- PURE WHITE - absolutely nothing else

OUTPUT: Simple blob figures with big clear letter {letter} and one {best_object} on pure white. The letter must NOT have a face, arms, or legs.\""""'''

if old_under3 in content:
    content = content.replace(old_under3, new_under3)
    print("✅ Updated UNDER_3 photo alphabet prompt")
else:
    print("❌ Could not find UNDER_3 photo alphabet prompt")

# ============================================
# AGE_3 PHOTO ALPHABET
# ============================================
old_age3 = '''        # Special handling for alphabet themes
        if theme.startswith("alphabet_"):
            letter = theme.replace("alphabet_", "").upper()
            return f"""Create an EXTREMELY SIMPLE toddler alphabet colouring page for letter {letter}.

CRITICAL: Only draw what is ACTUALLY in the photo. DO NOT add any animals, objects, or elements not in the original image.

DRAW:
- The people from the photo as VERY simple blob shapes (round heads, simple chunky body)
- Plain simple clothing - NO patterns, NO costumes
- A big friendly letter {letter} CHARACTER standing next to them with a cute face, arms and legs

STYLE:
- BLACK OUTLINES ON WHITE ONLY - no colour, no grey, no shading
- EXTREMELY THICK black outlines
- Blob/kawaii style - super rounded and chunky figures
- Faces: just dots for eyes, simple curve for mouth
- NO fingers, NO detailed features
- Bodies as simple rounded shapes
- Maximum 10-12 colourable areas TOTAL

BACKGROUND:
- PURE WHITE - absolutely nothing else
- No ground, no shadows, nothing

OUTPUT: Simple black outline blob figures standing next to a friendly letter {letter} character on pure white.\""""'''

new_age3 = '''        # Special handling for alphabet themes
        if theme.startswith("alphabet_"):
            letter = theme.replace("alphabet_", "").upper()
            best_object = ''' + obj_dict_str + '''.get(letter.lower(), 'apple')
            return f"""Create an EXTREMELY SIMPLE toddler alphabet colouring page for letter {letter}.

DRAW:
- The people from the photo as VERY simple blob shapes (round heads, simple chunky body)
- Plain simple clothing - NO patterns, NO costumes
- A big bold letter {letter} (plain block letter or bubble letter - NO face, NO arms, NO legs)
- ONE simple {best_object} next to the letter

STYLE:
- BLACK OUTLINES ON WHITE ONLY - no colour, no grey, no shading
- NO pink cheeks, NO blush - pure black lines only
- EXTREMELY THICK black outlines
- Blob/kawaii style for the people - super rounded and chunky figures
- Maximum 10-12 colourable areas TOTAL

BACKGROUND:
- PURE WHITE - absolutely nothing else

OUTPUT: Simple blob figures with big clear letter {letter} and one {best_object} on pure white. The letter must NOT have a face, arms, or legs.\""""'''

if old_age3 in content:
    content = content.replace(old_age3, new_age3)
    print("✅ Updated AGE_3 photo alphabet prompt")
else:
    print("❌ Could not find AGE_3 photo alphabet prompt")

# ============================================
# AGE_4 PHOTO ALPHABET
# ============================================
old_age4 = '''        # Special handling for alphabet themes
        if theme.startswith("alphabet_"):
            letter = theme.replace("alphabet_", "").upper()
            return f"""Create a SIMPLE alphabet colouring page for letter {letter} for a 4 year old.

CRITICAL: Only draw what is ACTUALLY in the photo. DO NOT add any animals, objects, or elements not in the original image.

DRAW:
- The people from the photo as simple cute figures
- A big friendly letter {letter} CHARACTER with a cute face, arms and legs standing with them
- 2-3 simple objects that start with {letter} (e.g. for E: elephant, egg)

STYLE:
- BLACK OUTLINES ON WHITE ONLY
- THICK black outlines  
- Simple rounded cartoon figures
- The letter {letter} must be LARGE and clearly visible
- Maximum 15-18 colourable areas

NO TEXT - do not write any words or labels

BACKGROUND:
- PURE WHITE - no ground, no scenery

OUTPUT: Simple figures with friendly letter character and a few {letter} objects. No text.\""""'''

new_age4 = '''        # Special handling for alphabet themes
        if theme.startswith("alphabet_"):
            letter = theme.replace("alphabet_", "").upper()
            best_object = ''' + obj_dict_str + '''.get(letter.lower(), 'apple')
            return f"""Create a SIMPLE alphabet colouring page for letter {letter} for a 4 year old.

DRAW:
- The people from the photo as simple cute figures
- A big bold letter {letter} (plain block letter or bubble letter - NO face, NO arms, NO legs)
- A {best_object} and one other simple object that starts with {letter}

STYLE:
- BLACK OUTLINES ON WHITE ONLY - no colour, no grey, no shading
- NO pink cheeks, NO blush - pure black lines only
- THICK black outlines
- Simple rounded cartoon figures
- The letter {letter} must be LARGE and clearly recognizable
- Maximum 15-18 colourable areas

NO TEXT - do not write any words or labels

BACKGROUND:
- PURE WHITE - no ground, no scenery

OUTPUT: Simple figures with big clear letter {letter}, a {best_object}, and one other {letter} object. The letter must NOT have a face, arms, or legs. No text.\""""'''

if old_age4 in content:
    content = content.replace(old_age4, new_age4)
    print("✅ Updated AGE_4 photo alphabet prompt")
else:
    print("❌ Could not find AGE_4 photo alphabet prompt")

# ============================================
# AGE_5 PHOTO ALPHABET
# ============================================
old_age5 = '''        # Special handling for alphabet themes
        if theme.startswith("alphabet_"):
            letter = theme.replace("alphabet_", "").upper()
            return f"""Create an alphabet colouring page for letter {letter} for a 5 year old.

DRAW:
- The people from the photo wearing simple COSTUMES that start with {letter} (e.g. for E: explorer outfit with hat)
- A big friendly letter {letter} CHARACTER with a cute face, arms and legs
- 3-4 objects that start with {letter} (e.g. for E: elephant, eggs, envelope)

IMPORTANT: Do NOT put the letter {letter} printed on clothing - dress them in themed COSTUMES instead

STYLE:
- BLACK OUTLINES ON WHITE ONLY - NO grey, NO shading
- Medium-thick black outlines
- Simple but clear figures
- The letter {letter} must be LARGE and clearly visible
- Maximum 20-25 colourable areas

NO TEXT - do not write any words or labels

BACKGROUND:
- MINIMAL - simple ground line, maybe 1-2 clouds
- Keep mostly white

OUTPUT: People in {letter}-themed costumes with friendly letter character and several {letter} objects.\""""'''

new_age5 = '''        # Special handling for alphabet themes
        if theme.startswith("alphabet_"):
            letter = theme.replace("alphabet_", "").upper()
            return f"""Create an alphabet colouring page for letter {letter} for a 5 year old.

DRAW:
- The people from the photo wearing simple COSTUMES that start with {letter} (e.g. for E: explorer outfit with hat)
- A big bold letter {letter} displayed prominently (plain block letter or bubble letter - NO face, NO arms, NO legs)
- 3-4 objects that start with {letter}

IMPORTANT: Do NOT put the letter {letter} printed on clothing - dress them in themed COSTUMES instead

STYLE:
- BLACK OUTLINES ON WHITE ONLY - NO grey, NO shading
- NO pink cheeks, NO blush - pure black lines only
- Medium-thick black outlines
- Simple but clear figures
- The letter {letter} must be LARGE and clearly recognizable
- Maximum 20-25 colourable areas

NO TEXT - do not write any words or labels (only the letter {letter} itself)

BACKGROUND:
- MINIMAL - simple ground line, maybe 1-2 clouds
- Keep mostly white

OUTPUT: People in {letter}-themed costumes with big clear letter {letter} and several {letter} objects. The letter must NOT have a face, arms, or legs.\""""'''

if old_age5 in content:
    content = content.replace(old_age5, new_age5)
    print("✅ Updated AGE_5 photo alphabet prompt")
else:
    print("❌ Could not find AGE_5 photo alphabet prompt")

# Write updated content
with open('app.py', 'w') as f:
    f.write(content)

print()
print("Photo alphabet prompts updated:")
print("- Clear letters (no face/arms/legs)")
print("- Hardcoded objects for under_3, age_3, age_4")
print("- Consistent with text-to-image alphabet prompts")
