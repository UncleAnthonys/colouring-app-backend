with open('pattern_endpoints.py', 'r') as f:
    content = f.read()

# Add import of normalize_age_level
old = 'from app import generate_from_text  # Adjust import as needed'
new = 'from app import generate_from_text, normalize_age_level  # Adjust import as needed'

# Add normalization before the age level is used
old2 = '    # Validate age level\n    if request.age_level not in AGE_CONFIG:'
new2 = '    # Normalize age level (handles "age_Under 3", "age_10+" etc)\n    request.age_level = normalize_age_level(request.age_level)\n\n    # Validate age level\n    if request.age_level not in AGE_CONFIG:'

content = content.replace(old, new)
content = content.replace(old2, new2)

with open('pattern_endpoints.py', 'w') as f:
    f.write(content)

print('Patched pattern_endpoints.py')
