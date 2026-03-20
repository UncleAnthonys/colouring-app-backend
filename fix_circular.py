with open('adventure_endpoints.py', 'r') as f:
    content = f.read()

# Remove the top-level import
content = content.replace('from app import normalize_age_level\n', '')

# Add inline import where it's used - the JSON endpoint
old1 = '    age_level = normalize_age_level(request.age_level)'
new1 = '    from app import normalize_age_level\n    age_level = normalize_age_level(request.age_level)'

content = content.replace(old1, new1, 1)

# Add inline import for form endpoints
old2 = '    age_level = normalize_age_level(age_level)'
new2 = '    from app import normalize_age_level\n    age_level = normalize_age_level(age_level)'

content = content.replace(old2, new2)

with open('adventure_endpoints.py', 'w') as f:
    f.write(content)
print('Fixed circular import')
