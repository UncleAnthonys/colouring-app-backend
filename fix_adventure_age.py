with open('adventure_endpoints.py', 'r') as f:
    content = f.read()

# Check if normalize_age_level is already imported
if 'normalize_age_level' not in content:
    # Add import - find an existing import from app
    old = 'from adventure_gemini import'
    new = 'from app import normalize_age_level\nfrom adventure_gemini import'
    content = content.replace(old, new, 1)
    
    with open('adventure_endpoints.py', 'w') as f:
        f.write(content)
    print('Added normalize_age_level import')
else:
    print('Already imported')
