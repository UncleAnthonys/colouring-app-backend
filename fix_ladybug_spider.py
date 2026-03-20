import json

with open('prompts/themes.json', 'r') as f:
    data = json.load(f)

# Ladybug - no filled spots
lb = data['themes']['animal_ladybug']
lb['overlay'] = lb['overlay'].replace(
    "- PURE WHITE background",
    "- PURE WHITE background\n- Ladybird spots must be HOLLOW OUTLINES ONLY - do NOT fill spots with black. Every spot must be white inside with black outline so children can colour them in\n- NO filled black areas anywhere\n- NO border, NO frame around the image"
)

# Spider - no border
sp = data['themes']['animal_spider']
sp['overlay'] = sp['overlay'].replace(
    "- PURE WHITE background",
    "- PURE WHITE background\n- NO filled black areas anywhere\n- NO border, NO frame around the image"
)

with open('prompts/themes.json', 'w') as f:
    json.dump(data, f, indent=2)

print('Patched ladybug and spider')
