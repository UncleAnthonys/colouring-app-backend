import json

with open('prompts/themes.json', 'r') as f:
    data = json.load(f)

old_ending = "OUTPUT: Clean black outlines on pure white. No grey. No texture. No shading. No colour."
new_ending = "OUTPUT: Clean black outlines on pure white. No grey. No texture. No shading. No colour.\n\nCRITICAL - NO BORDER: Do NOT add any border, frame, or rounded corners around the image. The drawing must fill the entire canvas edge to edge with NO border whatsoever."

prompt = data['master_text_prompt']['prompt']
count = prompt.count(old_ending)
print(f'Found {count} occurrence(s)')

if count == 1:
    data['master_text_prompt']['prompt'] = prompt.replace(old_ending, new_ending)
    with open('prompts/themes.json', 'w') as f:
        json.dump(data, f, indent=2)
    print('Patched successfully')
else:
    print('Not unique - check manually')
