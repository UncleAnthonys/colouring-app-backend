with open('adventure_endpoints.py', 'r') as f:
    content = f.read()

# Add normalize after each Form endpoint receives age_level
# Find the lines after the Form parameters where age_level is first used
old1 = '    age_level: str = Form("age_6"),\n    choice_path: str = Form("")\n):'
new1 = '    age_level: str = Form("age_6"),\n    choice_path: str = Form("")\n):\n    age_level = normalize_age_level(age_level)'

old2 = '    age_level: str = Form("age_6")\n):'
new2 = '    age_level: str = Form("age_6")\n):\n    age_level = normalize_age_level(age_level)'

count1 = content.count(old1)
count2 = content.count(old2)
print(f'Found {count1} choice_path form endpoints')
print(f'Found {count2} simple form endpoints')

if count1 >= 1:
    content = content.replace(old1, new1)
if count2 >= 1:
    content = content.replace(old2, new2)

with open('adventure_endpoints.py', 'w') as f:
    f.write(content)
print('Patched form endpoints')
