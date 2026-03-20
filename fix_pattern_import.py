with open('pattern_endpoints.py', 'r') as f:
    content = f.read()

# The normalize call is before the import - need to add import before it
old = '    # Normalize age level (handles "age_Under 3", "age_10+" etc)\n    request.age_level = normalize_age_level(request.age_level)'

new = '    # Normalize age level (handles "age_Under 3", "age_10+" etc)\n    from app import normalize_age_level\n    request.age_level = normalize_age_level(request.age_level)'

# Also remove it from the later import line so it's not imported twice
old2 = '        from app import generate_from_text, normalize_age_level  # Adjust import as needed'
new2 = '        from app import generate_from_text  # Adjust import as needed'

content = content.replace(old, new)
content = content.replace(old2, new2)

with open('pattern_endpoints.py', 'w') as f:
    f.write(content)
print('Fixed pattern import location')
