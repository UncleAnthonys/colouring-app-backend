"""
Add face accuracy instructions to no-theme photo prompts for age 5+
Keeps existing complexity levels, just adds likeness instructions
"""

with open('app.py', 'r') as f:
    content = f.read()

# ============================================
# AGE 5 NO-THEME
# ============================================
old_age5 = '''    if age_level == "age_5":
        # NO THEME - photo accurate
        if theme == "none" and not custom_theme:
            return """Create a colouring page for a 5 year old.

CRITICAL: Only draw what is ACTUALLY in the photo. DO NOT add any animals, pets, or objects not in the original image.

DRAW:
- The people from the photo as simple figures
- Background elements from the photo (simplified)
- THAT IS ALL - NOTHING ELSE

STYLE:
- BLACK OUTLINES ON WHITE ONLY
- Medium-thick black outlines
- Simple but recognisable figures
- Maximum 20-25 colourable areas

BACKGROUND:
- MINIMAL - simple ground line, 1-2 clouds maximum

DO NOT ADD: Any pets, animals, or objects not in the original photo.

OUTPUT: Simple figures with minimal background. Photo accurate.\""""'''

new_age5 = '''    if age_level == "age_5":
        # NO THEME - photo accurate
        if theme == "none" and not custom_theme:
            return """Create a colouring page for a 5 year old.

CRITICAL: Only draw what is ACTUALLY in the photo. DO NOT add extra people, animals, pets, or objects not in the original image. Keep EVERY person visible in the photo - do NOT remove anyone (including babies being held).

FACE ACCURACY (HIGHEST PRIORITY):
- TRACE the exact facial contours from the photo - do NOT reinterpret or stylize
- Match the PRECISE nose shape, eye spacing, mouth width, chin shape for EVERY person
- Copy the EXACT hairstyle for each person - length, parting, texture
- A parent MUST instantly recognise their specific children
- Keep real clothing details - specific shoes, patterns, stripes, accessories

DRAW:
- The people from the photo as simple but ACCURATE figures
- Background elements from the photo (simplified)
- THAT IS ALL - NOTHING ELSE

STYLE:
- BLACK OUTLINES ON WHITE ONLY
- Medium-thick black outlines
- Simple but recognisable figures
- Maximum 20-25 colourable areas

BACKGROUND:
- MINIMAL - simple ground line, 1-2 clouds maximum

OUTPUT: Simple figures with accurate faces and minimal background.\""""'''

if old_age5 in content:
    content = content.replace(old_age5, new_age5)
    print("✅ Updated AGE_5 no-theme prompt")
else:
    print("❌ Could not find AGE_5 no-theme prompt")

# ============================================
# AGE 7+ NO-THEME (the detailed base_prompt)
# ============================================
old_age7 = '''    # AGE 7 - more detail within objects, fuller scenes
    # PHOTO-ACCURATE MODE - completely different prompt for "none" theme
    if theme == "none" and not custom_theme:
        base_prompt = """Convert this photograph into a colouring book page.

CRITICAL: Only draw what is ACTUALLY in the photo. DO NOT add any animals, people, or objects that are not in the original image.

FACES AND PEOPLE (HIGHEST PRIORITY):
- Faces MUST be recognisable as the actual people in the photo
- Keep exact hairstyles - long hair stays long, short stays short
- Keep real facial features - this is the most important thing
- A parent must recognise their children
- Simplify clothing but keep it accurate to photo'''

new_age7 = '''    # AGE 7 - more detail within objects, fuller scenes
    # PHOTO-ACCURATE MODE - completely different prompt for "none" theme
    if theme == "none" and not custom_theme:
        base_prompt = """Convert this photograph into a colouring book page.

CRITICAL: Only draw what is ACTUALLY in the photo. DO NOT add extra people, animals, or objects not in the original image. Keep EVERY person visible in the photo - do NOT remove anyone (including babies being held).

FACE ACCURACY (HIGHEST PRIORITY):
- TRACE the exact facial contours from the photo - do NOT reinterpret or stylize
- Match the PRECISE nose shape, eye spacing, mouth width, chin shape for EVERY person
- Copy the EXACT hairstyle for each person - length, parting, texture
- A parent MUST instantly recognise their specific children
- Keep real clothing details - specific shoes, patterns, stripes, accessories'''

if old_age7 in content:
    content = content.replace(old_age7, new_age7)
    print("✅ Updated AGE_7+ no-theme prompt")
else:
    print("❌ Could not find AGE_7+ no-theme prompt")

# Write updated content
with open('app.py', 'w') as f:
    f.write(content)

print()
print("Face accuracy instructions added to no-theme prompts for age 5+")
print("- TRACE exact contours")
print("- Keep EVERY person (including babies)")
print("- Keep real clothing details")
