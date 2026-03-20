with open('pattern_endpoints.py', 'r') as f:
    content = f.read()

old = '    # Normalize age level (handles "age_Under 3", "age_10+" etc)\n    request.age_level = normalize_age_level(request.age_level)'

new = """    # Normalize age level (handles "age_Under 3", "age_10+" etc)
    request.age_level = normalize_age_level(request.age_level)
    
    # Map to pattern_config age keys (uses age_2 instead of under_3)
    pattern_age_map = {"under_3": "age_2"}
    request.age_level = pattern_age_map.get(request.age_level, request.age_level)"""

content = content.replace(old, new)

with open('pattern_endpoints.py', 'w') as f:
    f.write(content)
print('Patched pattern age mapping')
