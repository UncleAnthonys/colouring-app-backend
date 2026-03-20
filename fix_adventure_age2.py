with open('adventure_endpoints.py', 'r') as f:
    content = f.read()

old = '    age_level = request.age_level\n'
new = '    age_level = normalize_age_level(request.age_level)\n'

count = content.count(old)
print(f'Found {count} occurrence(s) of age_level = request.age_level')

if count >= 1:
    content = content.replace(old, new, 1)

# Also normalize on line 485 area (the Form endpoint)
old2 = '    age_level: str = Form("age_6"),'
if old2 in content:
    print('Form endpoint found - that one uses default so should be fine')

with open('adventure_endpoints.py', 'w') as f:
    f.write(content)
print('Patched')
