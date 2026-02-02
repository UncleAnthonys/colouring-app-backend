"""
Add hardcoded objects to photo alphabet prompts (under_3, age_3, age_4)
"""

with open('app.py', 'r') as f:
    content = f.read()

# The best_object dictionary code to insert
best_obj_code = '''best_object = {
                'a': 'apple', 'b': 'ball', 'c': 'cat', 'd': 'dog', 'e': 'elephant',
                'f': 'fish', 'g': 'goat', 'h': 'hat', 'i': 'ice cream', 'j': 'jellyfish',
                'k': 'kite', 'l': 'lion', 'm': 'monkey', 'n': 'nose', 'o': 'owl',
                'p': 'penguin', 'q': 'queen', 'r': 'rainbow', 's': 'star', 't': 'tiger',
                'u': 'umbrella', 'v': 'violin', 'w': 'whale', 'x': 'xylophone',
                'y': 'yo-yo', 'z': 'zebra'
            }.get(letter.lower(), 'apple')
            '''

# ============================================
# UNDER_3 - Add best_object lookup and object line
# ============================================
old_under3 = '''        if theme.startswith("alphabet_"):
            letter = theme.replace("alphabet_", "").upper()
            return f"""Create the SIMPLEST possible BLACK AND WHITE colouring page for a 2 year old baby.

DRAW:
- The people from the photo as VERY simple blob shapes (round heads, simple body)
- A big bold letter {letter} (plain block letter or bubble letter - NO face, NO arms, NO legs)'''

new_under3 = '''        if theme.startswith("alphabet_"):
            letter = theme.replace("alphabet_", "").upper()
            ''' + best_obj_code + '''return f"""Create the SIMPLEST possible BLACK AND WHITE colouring page for a 2 year old baby.

DRAW:
- The people from the photo as VERY simple blob shapes (round heads, simple body)
- A big bold letter {letter} (plain block letter or bubble letter - NO face, NO arms, NO legs)
- ONE simple {best_object} next to the letter'''

if old_under3 in content:
    content = content.replace(old_under3, new_under3)
    print("✅ Updated UNDER_3 photo alphabet")
else:
    print("❌ Could not find UNDER_3")

# ============================================
# AGE_3 - Add best_object lookup and object line
# ============================================
old_age3 = '''        if theme.startswith("alphabet_"):
            letter = theme.replace("alphabet_", "").upper()
            return f"""Create an EXTREMELY SIMPLE toddler alphabet colouring page for letter {letter}.

CRITICAL: Only draw what is ACTUALLY in the photo. DO NOT add any animals, objects, or elements not in the original image.

DRAW:
- The people from the photo as VERY simple blob shapes (round heads, simple chunky body)
- Plain simple clothing - NO patterns, NO costumes
- A big bold letter {letter} (plain block letter or bubble letter - NO face, NO arms, NO legs)'''

new_age3 = '''        if theme.startswith("alphabet_"):
            letter = theme.replace("alphabet_", "").upper()
            ''' + best_obj_code + '''return f"""Create an EXTREMELY SIMPLE toddler alphabet colouring page for letter {letter}.

DRAW:
- The people from the photo as VERY simple blob shapes (round heads, simple chunky body)
- Plain simple clothing - NO patterns, NO costumes
- A big bold letter {letter} (plain block letter or bubble letter - NO face, NO arms, NO legs)
- ONE simple {best_object} next to the letter'''

if old_age3 in content:
    content = content.replace(old_age3, new_age3)
    print("✅ Updated AGE_3 photo alphabet")
else:
    print("❌ Could not find AGE_3")

# ============================================
# AGE_4 - Add best_object lookup and object line
# ============================================
old_age4 = '''        if theme.startswith("alphabet_"):
            letter = theme.replace("alphabet_", "").upper()
            return f"""Create a SIMPLE alphabet colouring page for letter {letter} for a 4 year old.

CRITICAL: Only draw what is ACTUALLY in the photo. DO NOT add any animals, objects, or elements not in the original image.

DRAW:
- The people from the photo as simple cute figures
- A big bold letter {letter} (plain block letter or bubble letter - NO face, NO arms, NO legs)
- 2-3 simple objects that start with {letter} (e.g. for E: elephant, egg)'''

new_age4 = '''        if theme.startswith("alphabet_"):
            letter = theme.replace("alphabet_", "").upper()
            ''' + best_obj_code + '''return f"""Create a SIMPLE alphabet colouring page for letter {letter} for a 4 year old.

DRAW:
- The people from the photo as simple cute figures
- A big bold letter {letter} (plain block letter or bubble letter - NO face, NO arms, NO legs)
- A {best_object} and one other simple object that starts with {letter}'''

if old_age4 in content:
    content = content.replace(old_age4, new_age4)
    print("✅ Updated AGE_4 photo alphabet")
else:
    print("❌ Could not find AGE_4")

with open('app.py', 'w') as f:
    f.write(content)

print()
print("Done! Hardcoded objects added to photo alphabet prompts.")
