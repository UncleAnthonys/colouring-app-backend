import json

with open('prompts/themes.json', 'r') as f:
    data = json.load(f)

border_line = "\n\nCRITICAL: NO border, NO frame, NO rounded corners around the image. Drawing fills entire canvas edge to edge."

ages_to_patch = ["age_5", "age_6", "age_7", "age_8", "age_9", "age_10"]

count = 0
for age_key in ages_to_patch:
    if age_key in data['age_levels']:
        if 'NO border' not in data['age_levels'][age_key]['overlay']:
            data['age_levels'][age_key]['overlay'] += border_line
            count += 1
            print(f"Patched {age_key}")
        else:
            print(f"{age_key} already patched")

with open('prompts/themes.json', 'w') as f:
    json.dump(data, f, indent=2)

print(f"\nDone - patched {count} age levels")
