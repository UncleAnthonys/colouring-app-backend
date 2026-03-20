with open('app.py', 'r') as f:
    content = f.read()

old = 'OUTPUT: Bold black lines on pure white background. No grey. No texture."""'

new = '''OUTPUT: Bold black lines on pure white background. No grey. No texture.

CRITICAL - NO BORDER: Do NOT add any border, frame, or rounded corners around the image. The drawing must fill the entire canvas edge to edge with NO border whatsoever."""'''

count = content.count(old)
print(f'Found {count} occurrence(s)')

if count == 1:
    content = content.replace(old, new)
    with open('app.py', 'w') as f:
        f.write(content)
    print('Patched successfully')
else:
    print('Not unique - check manually')
