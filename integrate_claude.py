#!/usr/bin/env python3
"""
Integrate Claude Haiku 4.5 for story generation.
Keeps Gemini for image generation, swaps story text generation to Claude.
Run this from your backend folder: python3 integrate_claude.py
"""

with open('adventure_gemini.py', 'r') as f:
    content = f.read()

changes = 0

# ============================================================
# FIX 1: Add anthropic import at top of file
# ============================================================
if 'import anthropic' not in content:
    old = 'import random'
    new = 'import random\nimport anthropic'
    if old in content:
        content = content.replace(old, new, 1)
        changes += 1
        print('FIX 1 OK - Added import anthropic')
else:
    print('FIX 1 SKIP - anthropic already imported')

# ============================================================
# FIX 2: Add ANTHROPIC_API_KEY environment variable
# ============================================================
if 'ANTHROPIC_API_KEY' not in content:
    # Find where GEMINI_API_KEY is configured
    old = 'GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")'
    if old in content:
        new = 'GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")\nANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")'
        content = content.replace(old, new, 1)
        changes += 1
        print('FIX 2 OK - Added ANTHROPIC_API_KEY env var')
    else:
        # Try alternative pattern
        old2 = "genai.configure(api_key="
        idx = content.find(old2)
        if idx != -1:
            # Find the line
            line_start = content.rfind('\n', 0, idx) + 1
            line_end = content.find('\n', idx)
            line = content[line_start:line_end]
            new_line = line + '\nANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")'
            content = content[:line_start] + new_line + content[line_end:]
            changes += 1
            print('FIX 2 OK - Added ANTHROPIC_API_KEY after genai.configure')
else:
    print('FIX 2 SKIP - ANTHROPIC_API_KEY already exists')

# ============================================================
# FIX 3: Replace the Gemini story generation with Claude Haiku
# This is the critical change - swap the model call in 
# generate_personalized_stories function
# ============================================================

# Find the old Gemini model setup and API call
old_model_setup = """    try:
        # Use newer client API with response_mime_type for JSON
        model = genai.GenerativeModel(
            'gemini-2.5-flash',
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json"
            )
        )"""

new_model_setup = """    try:
        # Use Claude Haiku 4.5 for story generation (much better creative quality)
        claude_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)"""

if old_model_setup in content:
    content = content.replace(old_model_setup, new_model_setup)
    changes += 1
    print('FIX 3 OK - Replaced Gemini model setup with Claude client')
else:
    print('FIX 3 SKIP/ERROR - Could not find Gemini model setup')
    # Try to find what's there
    idx = content.find("generate_personalized_stories")
    if idx != -1:
        snippet = content[idx:idx+500]
        print(f'  Found function at char {idx}')
        print(f'  Snippet: {snippet[:200]}...')

# ============================================================
# FIX 4: Replace the Gemini generate_content call with Claude
# ============================================================

old_generate = """        response = model.generate_content([prompt])
        
        # Parse the JSON response
        text = response.text.strip()"""

new_generate = """        claude_response = claude_client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=8000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        # Parse the JSON response
        text = claude_response.content[0].text.strip()"""

if old_generate in content:
    content = content.replace(old_generate, new_generate)
    changes += 1
    print('FIX 4 OK - Replaced generate_content with Claude messages.create')
else:
    print('FIX 4 SKIP/ERROR - Could not find generate_content call')

# ============================================================
# FIX 5: Add nuanced resolution instruction to the prompt
# (Carry over from Sonnet's stronger story resolutions)
# ============================================================

old_rules = """*** 5 NON-NEGOTIABLE RULES ***

1. CHARACTERS: At least 2 named supporting characters with funny personalities who appear throughout, not just once.
2. SETBACK ON EPISODE 3: Character tries and FAILS or makes things worse. Makes the win feel earned.
3. DIALOGUE: At least 3 of 5 episodes need characters talking in speech marks.
4. ENDING: Episode 5 resolves the specific problem from episode 1. No generic happy endings.
5. NEVER copy a scenario word-for-word. Adapt it, remix it, make it feel fresh and unique to this character."""

new_rules = """*** 6 NON-NEGOTIABLE RULES ***

1. CHARACTERS: At least 2 named supporting characters with funny personalities who appear throughout, not just once.
2. SETBACK ON EPISODE 3: Character tries and FAILS or makes things worse. Makes the win feel earned.
3. DIALOGUE: At least 3 of 5 episodes need characters talking in speech marks.
4. ENDING: Episode 5 resolves the specific problem from episode 1. No generic happy endings.
5. NEVER copy a scenario word-for-word. Adapt it, remix it, make it feel fresh and unique to this character.
6. NUANCED RESOLUTION: The character's feature should NOT directly fix the problem alone. Instead, a SUPPORTING CHARACTER should suggest a new way to use the feature, OR the character should learn to use it differently after the setback. The solution should feel like a team effort or a moment of growth, not just "feature solves everything"."""

if old_rules in content:
    content = content.replace(old_rules, new_rules)
    changes += 1
    print('FIX 5 OK - Added nuanced resolution rule')
else:
    print('FIX 5 SKIP/ERROR - Could not find rules section')

# ============================================================
# SAVE
# ============================================================

if changes > 0:
    with open('adventure_gemini.py', 'w') as f:
        f.write(content)
    print(f'\n✅ {changes} changes applied to adventure_gemini.py')
else:
    print('\n❌ No changes applied')

# ============================================================
# VERIFY
# ============================================================
import ast
try:
    with open('adventure_gemini.py') as f:
        ast.parse(f.read())
    print('✅ SYNTAX OK')
except SyntaxError as e:
    print(f'❌ SYNTAX ERROR line {e.lineno}: {e.msg}')
