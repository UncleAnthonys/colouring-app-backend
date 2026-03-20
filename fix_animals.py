import json

with open('prompts/themes.json', 'r') as f:
    data = json.load(f)

# Tiger - add no filled stripes
tiger = data['themes']['animal_tiger']
tiger['overlay'] = tiger['overlay'].replace(
    "- PURE WHITE background",
    "- PURE WHITE background\n- Tiger stripes must be HOLLOW OUTLINES ONLY - do NOT fill stripes with black. Every stripe area must be white inside with black outline so children can colour them in\n- NO filled black areas anywhere\n- NO border, NO frame around the image"
)

# Gorilla - add no border + no filled areas
gorilla = data['themes']['animal_gorilla']
gorilla['overlay'] = gorilla['overlay'].replace(
    "- PURE WHITE background",
    "- PURE WHITE background\n- Gorilla fur must be HOLLOW OUTLINES ONLY - do NOT fill any area with black or dark grey. Every area must be white inside with black outline so children can colour them in\n- NO filled black areas anywhere\n- NO border, NO frame around the image"
)

# Bee - add no filled stripes
bee = data['themes']['animal_bee']
bee['overlay'] = bee['overlay'].replace(
    "- PURE WHITE background",
    "- PURE WHITE background\n- Bee stripes must be HOLLOW OUTLINES ONLY - do NOT fill stripes with black. Every stripe area must be white inside with black outline so children can colour them in\n- NO filled black areas anywhere\n- NO border, NO frame around the image"
)

with open('prompts/themes.json', 'w') as f:
    json.dump(data, f, indent=2)

print('Patched tiger, gorilla, and bee')
