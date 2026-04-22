"""
Little Lines — Gemini 3 Flash Story Engine
===========================================
Drop-in replacement for the Sonnet story writer in adventure_gemini.py.
Outputs episodes in the exact same format so the existing endpoint works unchanged.

Usage (standalone test):
  export GEMINI_API_KEY="your-key-here"
  python3 gemini_story_engine.py

Usage (backend integration):
  Replace the call to generate_story_for_theme() with generate_story_gemini()
  The output format is identical — episodes with episode_num, title, story_text,
  scene_description, character_emotion.
"""

import os
import json
import time
from google import genai
from google.genai import types

# ──────────────────────────────────────────────
# CONFIG
# ──────────────────────────────────────────────

MODEL = "gemini-3-flash-preview"
TEMPERATURE = 1.0
THINKING_LEVEL = "MEDIUM"

# ──────────────────────────────────────────────
# MASTER SYSTEM PROMPT
# ──────────────────────────────────────────────

SYSTEM_PROMPT = """
**ROLE**
You are a master children's book author writing a 5-page "Colour-Along" adventure. Your writing must sound like the best picture books — Julia Donaldson, Oliver Jeffers, Mo Willems. A parent reading this aloud should feel like a campfire storyteller, not a newsreader.

**THE CONTEXT**
1. Each episode is a physical colouring page. Linger on visual details the child might be colouring ("giant wobbly boots," "swirly green leaves," "big sticky paws").
2. Each episode has a `parent_prompt` — a physical, tactile prompt for the child. NEVER "What colour is X?" ALWAYS action-based: "Can you make the same face as Tim?" or "Pretend to pull that rope!"

**PAGE 1 CONTRACT (ALL AGES — NON-NEGOTIABLE)**
Page 1 must establish FIVE things clearly:
1. WHAT does the character need to do? (A specific physical mission)
2. WHAT HAPPENS IF THEY FAIL? (A visible consequence — something floods, breaks, escapes, grows)
3. WHY IS THERE A TICKING CLOCK? (Something is melting, rising, closing, counting down)
4. WHY WILL THE MISSION FIX IT? (The reader must understand the full chain: do X → causes Y → stops Z. Never reveal why the mission works on the final page.)
5. DOES THE FIX MATCH THE PROBLEM? (Physical problem = physical fix. Never solve breaking with music or flooding with feelings. Test: could a child explain WHY it works?)

**THE 5-PAGE STRUCTURE**
- Page 1: The hook. Stakes, ticking clock, mission, solution logic — all clear.
- Pages 2-4: ESCALATION. Each page WORSE than the last. New obstacle, new location, new attempt that fails. The problem must spiral out of control.
- Page 5: ONE clever physical action fixes everything. The fix must use something from the story, not a random new thing. End on action, not feelings. Never summarise ("Everyone was happy"). The action IS the ending.

**HOW IT MUST SOUND (THE MOST IMPORTANT SECTION)**
Your writing must have a PULSE. When read aloud, the parent's voice should naturally rise and fall, speed up and slow down, get loud then quiet. This comes from sentence variety.

TECHNIQUES:
- Build with a long rolling sentence, then PUNCH with a short one: "She ran past the carrots and over the stones and through the long wet grass and — SPLAT! Mud everywhere."
- Use triplets for comedy: "She pulled. She tugged. She sat on it."
- One-word sentences for impact: "Stuck." "Gone." "Uh-oh."
- Repetition within sentences: "round and round and round it rolled"
- "And" chains for momentum: "and she grabbed it and she squeezed it and she pulled and pulled and —"
- Questions the parent performs: "Would it fit? Could she reach?"
- Direct speech for energy: "Stop!" shouts Erin. NOT: Erin tells it to stop.

BAD RHYTHM (every sentence the same length — reads like a police report):
"Penny pushes the pea. It is heavy. She pulls it out. The mud is thick. The gate is closing."

GOOD RHYTHM (musical, performable, alive):
"Penny pushes and pushes and PUSHES — but that big green pea won't budge! It is stuck. Thick, gloopy, squelchy mud. She pulls. She tugs. She HEAVES — POP! Out it comes, rolling and rolling and rolling down the hill!"

RULES:
- Never start 3+ sentences in a row with the same structure.
- Never write "Then" to start a sentence. Every page happens BECAUSE of the last, not AFTER it.
- Never use "was," "felt," "saw," or "noticed" as main verbs. Use kinetic verbs: "the wind bit his nose" not "he was cold."
- At least one ALL CAPS sound word per page. Build the sentence around it.
- Sound words must match physics: wood = CLACK/THUD, water = SPLASH/DRIP, sticky = SQUELCH.
- Use British English (colour, favourite, mum).
- NEVER reference specific colours in story_text — these are black and white colouring pages.

**AGE CALIBRATION**
- **TODDLER PULSE (under_3 ONLY):** Pure board book. MAXIMUM 12 WORDS PER PAGE.
    The REPEATING REFRAIN is the engine — not sound effects. The child knows what's coming and shouts it.
    STRUCTURE: Page 1 sets the goal with jeopardy. Pages 2-4 each have ONE failed attempt followed by the SAME refrain (3-6 words, identical each time). Page 5 breaks the pattern — success + celebration.
    Refrain fires ONLY after failure. Never after success. Never on page 5.
    Each attempt must be DIFFERENT — new method, new place. Never repeat the same action.
    Sound words OPTIONAL — only when something physically makes a noise. Never force one.
    Vocabulary: first-100-words only. Physical, concrete. No abstract feelings.
    EXAMPLE:
    Page 1: "The big tower wobbles! The star is falling! Catch it, Limey!"
    Page 2: "Limey climbs the blocks. CRASH! They tumble down. Oh no, the star!"
    Page 3: "Limey jumps up high. The star rolls away! Oh no, the star!"
    Page 4: "Limey slides down the hill. WHOOSH! The star is at the edge! Oh no, the star!"
    Page 5: "Limey grabs it! SNAP! The star is safe. Limey did it! YAY!"

- **TODDLER NARRATIVE (age_3 ONLY):** Bridge between board book and preschool. 15-25 words per page. 2-3 short sentences. Use expressive verbs ("hunts" not "looks", "tumbles" not "falls"). One sound word per page matching the action. Join-in phrase every 2 pages that captures the mission. Goal on page 1 must have jeopardy. Attempts must escalate.

- **PRESCHOOL PERFORMANCE (age_4, age_5):** 3-5 sentences per page. This is a one-person show for the parent.
    VOCABULARY (age_4 — THE TODDLER MOUTH TEST): Every word must be one a 4-year-old would SAY unprompted at preschool. 3+ syllable words are almost always wrong. "Suddenly" → "then". "Enormous" → "huge". "Ceiling" → "the top". Write how they talk, not how books sound.
    Every page needs: a sound word to shout, something physical to describe (sticky, wobbly, crunchy), dialogue in a funny voice, and a hook that makes the child gasp.

- **STORYTIME (age_6, age_7):** 80-120 words per page. Character tries, fails, grows. Dialogue and internal thoughts. Fun "mouthful words" (bamboozled, gobbledygook, squelch) used boldly without explanation.

- **CHAPTER BOOK (age_8, age_9, age_10):** 150-250 words per page. Complex twists, metaphor, dry humour. Rich world-building matching detailed colouring pages.

* **Cozy Landing:** For under_3/age_3 — warm, safe ending ("SNUGGLE! Toastie rests on his warm plate."). For age_4+ — satisfying physical payoff, can be funny/messy. ALL AGES: end on action, never a summary sentence. The last line must belong to THIS story — if it could fit any story, rewrite it.

**THE STORYBOARD (Scene Descriptions)**
Each episode's art is generated independently with no memory of previous pages. You must provide a standalone cinematic prompt (80+ words) for each.
* **Character Consistency:** Explicitly describe the character's full visual profile in every episode (hair color/style, specific clothing, shoes, accessories).
* **Plot Object Persistence:** If an object is essential to the plot (the KEY OBJECT introduced in episode 1), you MUST include its physical description in every subsequent scene_description until the story ends. Objects cannot disappear between pages just because the image generator has no memory.
* **Cinematics:** Specify camera angle (e.g., wide shot, close-up), the character's specific pose, the location/setting, and key objects. CRITICAL: the character's pose in the scene_description must physically match what the story_text says is happening. If the story_text says the character is lying flat, the scene_description must say "lying flat." If the story_text says the character stretches across a gap as a bridge, the scene_description must explicitly say "body stretched horizontally across the puddle like a bridge, flat and rigid." Never describe a character standing upright if the story_text has them doing something else entirely.
* **Style Constraint:** You MUST include the appropriate style phrase in every scene_description based on AGE_LEVEL:
  - **under_3**: "High-contrast black and white coloring book style, EXTREMELY THICK chunky outlines (6-8px line weight), like a board book illustration, zero fine detail, no shading, massive white spaces, kawaii style, the simplest possible drawing a toddler can colour with fat crayons."
  - **age_3**: "High-contrast black and white coloring book style, VERY THICK bold outlines (4px+ line weight), no fine detail, no shading, wide-open white spaces, chunky kawaii style."
  - **age_4 to age_5**: "High-contrast black and white coloring book style, thick bold outlines (3px+), no shading, wide-open white spaces, simple clear shapes."
  - **age_6 to age_7**: "High-contrast black and white coloring book style, bold clean lines, no shading, wide-open white spaces."
  - **age_8+**: "High-contrast black and white coloring book style, clean detailed lines, no shading, white spaces for coloring, fine detail encouraged."

**SCENE COMPLEXITY BY AGE (CRITICAL — match the child's colouring ability)**
Your scene_description MUST respect the child's age. Write the complexity instructions directly into every scene_description.
- **under_3**: KAWAII STYLE. Character fills 60%+ of page. Super thick outlines. NO background detail — just the character and maybe ONE big simple shape (a hill, a cloud, a ball). Pure white space everywhere. Think: chunky, cute, bold. A toddler colours this in 5 minutes with chunky crayons.
- **age_3**: KAWAII STYLE. Character fills 55%+ of page. Thick bold outlines. 1-2 big simple background shapes ONLY (one tree, one house — not both). No textures, no patterns, no fine detail. Lots of white space. Still chunky and cute.
- **age_4**: Character fills 50% of page. 3-4 background elements using big simple shapes. 1 supporting character drawn simply. Bold outlines. No intricate environments. One step up from kawaii — still chunky.
- **age_5**: Character fills 45% of page. 4-5 background elements. 1-2 supporting characters. Medium detail.
- **age_6**: Character fills 40% of page. 5-6 background elements. 2 supporting characters. Foreground/background separation.
- **age_7**: Character fills 30% of page. 6-8 background elements. 2-3 supporting characters. Foreground/midground/background layers.
- **age_8+**: Character fills 25% or less. 8+ background elements. 3+ supporting characters. Rich detail, hidden elements, patterns. Fill the scene — older children enjoy detailed pages.

**SCENE VARIETY LOGIC (THE "CAMERA" RULE)**
This is a colouring book. If every page shows the same location from the same angle, the child is colouring the same picture 5 times. Each episode MUST have a unique visual composition:
- Page 1 (The Hero Shot): Wide shot. Show the CHARACTER and their setting. Large, clear shapes.
- Page 2 (The Action Shot): Medium shot. Show the CHARACTER interacting with the OBSTACLE (e.g., reaching, climbing, or tangled).
- Page 3 (The Close-Up/Detail): Zoom in! Focus on a specific object or textured background (e.g., a giant pile of sand, a wall of books, a sparkly letter).
- Page 4 (The High-Energy Shot): Low-angle or high-angle shot. Use action lines to show the TWIST happening (e.g., things flying, a big splash).
- Page 5 (The Wide Resolution): Wide shot again, but different from Page 1. Show the CHARACTER happy and safe, surrounded by the results of their success.

**LOCATION MOVEMENT RULE (NON-NEGOTIABLE):**
The story MUST move through at least 3 visually distinct locations. No more than 2 episodes in the same place. A child is colouring 5 separate pages — each page must feel like a NEW picture with different surroundings, different objects, and different things to colour. If your story stays in one room, one shop, or one field for more than 2 pages, REWRITE IT so the character moves somewhere new. The story's plot should naturally take the character to different places.

**VISUAL DIVERSITY INSTRUCTIONS:**
1. Never repeat a pose: If the character is standing on Page 1, they should be sitting, jumping, or reaching on Page 2.
2. Foreground/Background Swap: If the character is in the center on Page 1, place them to the side on Page 2 to leave room for a big new coloring element.
3. The "New Thing" Rule: Every page must introduce ONE new, large object to color that was not there before (e.g., a giant clock, a pile of cushions, a magic lantern).
4. Move through at least 3 visually distinct settings. No more than 2 episodes in the same location.

**STYLE & LESSON**
If a WRITING_STYLE or LIFE_LESSON is provided, weave it in like a thread, not a hammer. It should feel like a natural part of the character's journey.

**COLOUR REFERENCES BAN**
NEVER reference specific colours in story_text (e.g. "his blue arms", "the red ball", "her golden hair"). These are black and white colouring pages — the child chooses the colours. Describe things by texture, size, or shape instead. GOOD: "his big arms", "the wobbly ball", "her curly hair". BAD: "his blue arms", "the red ball", "her golden hair". The ONLY exception is if the colour IS the story (e.g. "the golden crown" where gold is the point of the object).

**LANGUAGE**
Use British English spelling throughout (colour, favourite, mum, neighbour, realise, centre, etc.). Never use American spellings.

**OUTPUT FORMAT**
Return valid JSON only. No markdown, no backticks, no preamble. Start immediately with a { character.

"""

# ──────────────────────────────────────────────
# TIER MAPPING
# ──────────────────────────────────────────────

TIER_MAP = {
    "under_3": ("Standard", 5),
    "age_3": ("Standard", 5),
    "age_4": ("Standard", 5),
    "age_5": ("Standard", 5),
    "age_6": ("Standard", 5),
    "age_7": ("Standard", 5),
    "age_8": ("Standard", 5),
    "age_9": ("Standard", 5),
    "age_10": ("Standard", 5),
}

VALID_EMOTIONS = ["nervous", "excited", "scared", "determined", "happy", "curious", "sad", "proud", "worried", "surprised", "embarrassed", "panicked"]


def get_tier(age_level):
    tier, episodes = TIER_MAP.get(age_level, ("Standard", 5))
    return tier, episodes


# ──────────────────────────────────────────────
# STORY GENERATION (Sonnet-compatible output)
# ──────────────────────────────────────────────

def generate_story_gemini(
    character_name: str,
    character_description: str,
    theme_name: str = "",
    theme_description: str = "",
    theme_blurb: str = "",
    feature_used: str = "",
    want: str = "",
    obstacle: str = "",
    twist: str = "",
    age_level: str = "age_6",
    writing_style: str = None,
    life_lesson: str = None,
    custom_theme: str = None,
    second_character_name: str = None,
    second_character_description: str = None,
    api_key: str = None,
) -> dict:
    """
    Generate a complete Little Lines story using Gemini 3 Flash.
    
    Returns dict matching Sonnet's output format:
    {
        "story_title": "...",
        "episodes": [
            {
                "episode_num": 1,
                "title": "...",
                "story_text": "...",
                "scene_description": "...",
                "character_emotion": "..."
            },
            ...
        ]
    }
    """
    key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not key:
        raise ValueError("GEMINI_API_KEY not set")

    client = genai.Client(api_key=key)
    tier, episode_count = get_tier(age_level)

    # ── Build user prompt ──
    parts = []
    parts.append(f"Generate a {tier} ({episode_count}-episode) Color-Along story.\n")

    # Character
    parts.append(f"CHARACTER_NAME: {character_name}")
    parts.append(f"CHARACTER_DESCRIPTION: {character_description}")

    # Second character
    if second_character_name and second_character_description:
        parts.append(f"\nSECOND_CHARACTER_NAME: {second_character_name}")
        parts.append(f"SECOND_CHARACTER_DESCRIPTION: {second_character_description}")
        parts.append(f"""{second_character_name} is {character_name}'s companion and absolute CO-STAR. CRITICAL RULES for {second_character_name}:
- They MUST appear in EVERY single episode — not just mentioned, but physically present and DOING something
- They must have their OWN reactions, emotions, and personality — not just follow {character_name} silently
- Their features must cause AT LEAST ONE problem OR solve AT LEAST ONE problem across the story
- At least 2 episodes must have {second_character_name} and {character_name} working together OR disagreeing
- {second_character_name} should feel like a real character, not a sidekick prop
- NEVER have {second_character_name} just "watch" or "cheer" — they must DO things
- The story is incomplete if {second_character_name} could be removed without changing the plot""")

    # Theme — either pre-written or custom
    if custom_theme:
        parts.append(f"\nCUSTOM_THEME: {custom_theme}")
        parts.append("""THE CUSTOM THEME IS THE ENGINE — not a backdrop, not a mention. CRITICAL RULES:
1. EVERY episode must take place IN or DIRECTLY REGARDING this theme/setting/event. If the theme is "dentist", all 5 pages are at the dentist. If the theme is "birthday", every page is part of the birthday.
2. The character's unique feature must collide with this specific setting to create the problem AND the solution. (Feature + Theme Setting = Unique Story)
3. Use the physical objects of this setting as story props. A dentist has a chair, a mirror, a drill, a sticker. A birthday has a cake, balloons, candles, wrapping paper. These objects must appear in the story and the art.
4. NEVER use the custom theme as a vague "flavour." It must be structurally essential — remove the theme and the story should not work.
5. The parent chose this theme because it is REAL and PERSONAL to their child. Make it feel like this story could only exist for THIS child in THIS moment.""")
        if theme_name:
            parts.append(f"THEME_NAME: {theme_name}")
    else:
        if theme_name:
            parts.append(f"\nTHEME_NAME: {theme_name}")
        if theme_description:
            parts.append(f"THEME_DESCRIPTION: {theme_description}")
        if theme_blurb:
            parts.append(f"THEME_BLURB: {theme_blurb}")
        # Build narrative anchor from want/obstacle/twist — single causal sentence
        # works better than separate fields for Gemini (avoids mechanical checklist writing)
        if want or obstacle or twist:
            anchor_parts = []
            if want:
                anchor_parts.append(want)
            if obstacle:
                anchor_parts.append(f"which means {obstacle}")
            if twist:
                anchor_parts.append(f"so they must {twist}")
            narrative_anchor = ", ".join(anchor_parts)
            parts.append(f"NARRATIVE_ANCHOR: {narrative_anchor} — use this as your story logic. Episode 1 MUST establish the consequence of failure and the ticking clock — the child should feel urgency from the very first page. Distribute the tension naturally across all episodes so it peaks around episode 4. The consequence should feel like it's getting CLOSER and WORSE with each page — not staying the same. Do NOT follow this as a checklist — let it inform the arc and cause-and-effect, not dictate what happens in each episode.")
        if feature_used:
            parts.append(f"KEY_FEATURE: {feature_used} — this is a notable aspect of the character. It should appear naturally in the story — causing an incidental funny moment, shaping how the character interacts with the world, or playing a role in the resolution. But the STORY and the WORLD drive the plot, not this feature. Do NOT mention it in every line. A reader should finish thinking 'what a great adventure' not 'wow that character really has [feature]'.")
    # Age, style, lesson
    parts.append(f"\nAGE_LEVEL: {age_level}")
    parts.append(f"STORY_TIER: {tier} ({episode_count} episodes)")

    # Age-specific vocabulary reinforcement — this fires LAST so Gemini remembers it
    if age_level in ("under_3",):
        parts.append("⚠️ VOCABULARY REMINDER (under_3): Max 12 words per page. First-100-words only. Pure board book.")
    elif age_level == "age_3":
        parts.append("⚠️ VOCABULARY REMINDER (age_3): Max 25 words per page. 2-3 short sentences. Simple words only — if a 3-year-old wouldn't say it, don't write it.")
    elif age_level == "age_4":
        parts.append("""⚠️ VOCABULARY REMINDER (age_4 — THIS IS THE MOST IMPORTANT RULE):
THE TODDLER MOUTH TEST: Every single word must pass this test — could a 4-year-old SAY this word unprompted while playing? Not understand it when read to them. Actually say it themselves at preschool. If the answer is no, use the word they WOULD say instead.
SYLLABLE RULE: If a word has 3+ syllables, replace it with a 1-2 syllable word. "Suddenly" → "then". "Becoming" → "now it's". "Enormous" → "huge". "Ceiling" → "the top". "Beautiful" → "pretty". No exceptions.
SENTENCE RULE: A 4-year-old speaks in simple declarations. "She grabs the big red ball." NOT "Reaching forward, she carefully grasps the enormous crimson sphere." Write how they talk.
SELF-CHECK: After writing each page, reread every word. For EACH word ask: would I hear this word in a preschool classroom? If no, swap it. This applies to EVERY word — nouns, verbs, adjectives, adverbs, all of them.""")
    elif age_level == "age_5":
        parts.append("""⚠️ VOCABULARY REMINDER (age_5):
Max 10 words per sentence. Max 50 words per page.
Use playground words — fun to say, easy to understand. No Latinate or academic vocabulary.
BANNED: investigate, magnificent, structure, ancient, cascade, illuminated, mechanism, delicate, precisely, extraordinary.
Every page must have at least one sound word in ALL CAPS and be written for a parent to PERFORM aloud.""")

    parts.append(f"WRITING_STYLE: {writing_style or 'Standard'}")

    # Writing style detailed rules
    if writing_style == "Repetition":
        parts.append("""REPETITION STYLE RULES — READ CAREFULLY:
This is NOT about repeating individual words. This is STRUCTURAL REFRAIN repetition — like real board books.
THE PATTERN: Every page has TWO parts:
  1. A new observation or action specific to that page (changes every page)
  2. AN IDENTICAL REFRAIN LINE that is exactly the same every single page

EXAMPLE STRUCTURE:
  Page 1: Introduction — set up the character and situation
  Page 2: [New detail about what the character sees/does]... [REFRAIN]
  Page 3: [New detail about what the character sees/does]... [REFRAIN]
  Page 4: [New detail about what the character sees/does]... [REFRAIN]
  Page 5: Big finale that calls back to the refrain with a twist or celebration

EXAMPLE IN PRACTICE (character: a dog, refrain: "Is that the most amazing dog ever?"):
  Page 2: "I can see a big fluffy tail going wag, wag, wag... Is that the most amazing dog ever?"
  Page 3: "I can see two floppy ears going flap, flap, flap... Is that the most amazing dog ever?"
  Page 4: "I can see four muddy paws going stomp, stomp, stomp... Is that the most amazing dog ever?"
  Page 5: "I can see the most amazing dog ever — and it's YOU!"

RULES:
- Choose ONE refrain line and keep it IDENTICAL every page — not similar, IDENTICAL
- The refrain should be warm, celebratory, or funny — something a child loves to shout along with
- The observation line must describe something VISIBLE on the coloring page
- NEVER repeat words within a sentence ("big, big hill") — that is NOT this style
- The child should be able to predict and shout the refrain after hearing it twice
- CRITICAL: The refrain must be tied to the CHARACTER'S GOAL, IDENTITY, or EMOTIONAL DRIVE — not a description of what an object is doing. It must make sense on every single page regardless of what is happening. GOOD: "Is that the most amazing dog ever?" (identity — always true). GOOD: "We have to find that treasure!" (goal — always relevant). BAD: "The map is slipping!" (situational — only true on one page).
- NOTE FOR AGE_3: If the age is age_3, this Repetition style refrain replaces the standard age_3 join-in refrain. Do not use both. The Repetition style refrain appears on pages 2, 3, and 4. Page 5 gets the twist callback instead.
- CRITICAL: The refrain must be completely self-contained — a child must understand it with zero context from surrounding sentences. Never use pronouns like "them", "it", "they", "her" unless the noun they refer to is inside the refrain itself. WRONG: "Oh no, wipe them dry!" (what is "them"?). RIGHT: "We must find that key!" (self-contained, no ambiguous pronouns).""")
    elif writing_style == "Rhyming":
        parts.append("""RHYMING STYLE RULES: Every page must contain at least one rhyming couplet. Simple, natural rhymes only. The rhythm must feel like a nursery rhyme — bouncy and predictable. Never sacrifice story clarity for a rhyme.""")
    elif writing_style == "Silly":
        parts.append("""SILLY STYLE RULES: Over-the-top absurd situations. Made-up words encouraged. Physical slapstick. Things going hilariously wrong in unexpected ways. The parent should be giggling while reading it.""")
    elif writing_style == "Gentle":
        parts.append("""GENTLE STYLE RULES: Soft, warm, cozy language. Quiet moments. Slow pacing. Describe textures and feelings gently. Perfect for bedtime. The ending should feel like a warm hug.""")
    elif writing_style == "Suspenseful":
        parts.append("""SUSPENSEFUL STYLE RULES: Every page except the last must end on a mini cliffhanger. Use dramatic pauses. Build tension. "But what nobody knew was..." and "And then... silence." The child must be desperate to turn the page.""")

    if life_lesson:
        parts.append(f"LIFE_LESSON: {life_lesson}")

    # Output format — matching Sonnet's structure exactly
    emotions_str = ', '.join(f'"{e}"' for e in VALID_EMOTIONS)
    parts.append(f"""
Return valid JSON matching this EXACT structure:
{{
  "story_title": "string — a creative title for the story",
  "episodes": [
    {{
      "episode_num": 1,
      "title": "string — short episode title",
      "story_text": "string — the story text for this episode",
      "scene_description": "string — COMPLETE standalone image prompt (80+ words)",
      "character_emotion": "string — one of: {emotions_str}",
      "parent_prompt": "string or null — a one-sentence Parental Spark question for this page (NOT in story_text)"
    }}
  ]
}}

Generate exactly {episode_count} episodes numbered 1 to {episode_count}.""")

    user_prompt = "\n".join(parts)

    # ── Call Gemini ──
    start = time.time()

    print(f"[GEMINI-STORY] User prompt length: {len(user_prompt)} chars")
    print(f"[GEMINI-STORY] System prompt length: {len(SYSTEM_PROMPT)} chars")
    print(f"[GEMINI-STORY] Params: character={character_name}, theme={theme_name}, age={age_level}, second_char={second_character_name}")

    response = client.models.generate_content(
        model=MODEL,
        contents=user_prompt,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            response_mime_type="application/json",
            temperature=TEMPERATURE,
            thinking_config=types.ThinkingConfig(
                thinking_level=THINKING_LEVEL
            ),
        ),
    )

    elapsed = time.time() - start

    # ── Parse response ──
    if response.text is None:
        try:
            finish_reason = response.candidates[0].finish_reason if response.candidates else 'NO_CANDIDATES'
            safety = response.candidates[0].safety_ratings if response.candidates else 'N/A'
            print(f'[GEMINI-STORY] WARNING: Empty response. finish_reason={finish_reason}, safety={safety}')
        except Exception as e:
            print(f'[GEMINI-STORY] WARNING: Empty response. Could not read finish_reason: {e}')
        for retry_num, delay in enumerate([3, 6], start=1):
            print(f'[GEMINI-STORY] Retry {retry_num}/2 after {delay}s delay...')
            __import__('time').sleep(delay)
            response = client.models.generate_content(
                model=MODEL,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    response_mime_type="application/json",
                    temperature=TEMPERATURE,
                    thinking_config=types.ThinkingConfig(
                        thinking_level="MEDIUM"
                    ),
                ),
            )
            elapsed = time.time() - start
            if response.text is not None:
                break
            try:
                fr = response.candidates[0].finish_reason if response.candidates else 'NO_CANDIDATES'
                print(f'[GEMINI-STORY] Retry {retry_num} also empty. finish_reason={fr}')
            except:
                print(f'[GEMINI-STORY] Retry {retry_num} also empty.')
        if response.text is None:
            raise ValueError("Gemini returned empty response after 2 retries")

    try:
        story = json.loads(response.text)
    except json.JSONDecodeError:
        text = response.text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1] if "\n" in text else text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
        decoder = json.JSONDecoder()
        story, _ = decoder.raw_decode(text)

    # Handle Gemini returning a list instead of a dict
    if isinstance(story, list):
        story = {"story_title": "", "episodes": story}

    # Validate episode count — retry once if Gemini returned too few
    episodes = story.get("episodes", [])
    if len(episodes) < episode_count:
        print(f"[GEMINI-STORY] WARNING: Got {len(episodes)} episodes, expected {episode_count}. Retrying...")
        import time as _time
        _time.sleep(3)
        response = client.models.generate_content(
            model=MODEL,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                response_mime_type="application/json",
                temperature=TEMPERATURE,
                thinking_config=types.ThinkingConfig(
                    thinking_level=THINKING_LEVEL
                ),
            ),
        )
        if response.text:
            try:
                retry_story = json.loads(response.text)
                if isinstance(retry_story, list):
                    retry_story = {"story_title": "", "episodes": retry_story}
                retry_episodes = retry_story.get("episodes", [])
                if len(retry_episodes) > len(episodes):
                    story = retry_story
                    episodes = retry_episodes
                    print(f"[GEMINI-STORY] Retry succeeded: {len(episodes)} episodes")
                else:
                    print(f"[GEMINI-STORY] Retry also returned {len(retry_episodes)} episodes, using original")
            except json.JSONDecodeError:
                print(f"[GEMINI-STORY] Retry JSON parse failed, using original")

    # Validate and clean episodes
    for ep in episodes:
        # Ensure emotion is valid
        if ep.get("character_emotion") not in VALID_EMOTIONS:
            ep["character_emotion"] = "happy"
        # Ensure episode_num exists
        if "episode_num" not in ep:
            ep["episode_num"] = episodes.index(ep) + 1
        # Normalise parent_prompt — empty string becomes None
        if not ep.get("parent_prompt"):
            ep["parent_prompt"] = None

    print(f"[GEMINI-STORY] Generated '{story.get('story_title', '')}' — {len(episodes)} episodes in {elapsed:.1f}s")

    return story


# ──────────────────────────────────────────────
# PITCH GENERATION
# ──────────────────────────────────────────────

PITCH_SYSTEM_PROMPT = """You are a master children's story pitch writer. You create story premises that feel completely original and surprising — ideas a parent reads and thinks "I have never seen that before." You START with a brilliant story concept — a situation, a problem, a world — and then weave the character into it naturally. You NEVER start by picking a body part and building a story around it. The character's appearance and traits should colour the adventure, but the STORY CONCEPT is king. Your ideas are grounded in Physical Logic (how things bounce, stretch, break, stick, snap) but the PREMISE must be fresh every time. You draw from the full range of human experience — jobs, places, events, relationships, machines, nature, food, sport, science, weather, animals — not a fixed palette of materials. You NEVER default to the same substances or scenarios. You NEVER write boring, abstract, or emotional-lesson stories.

*** GROUNDED SETTING RULE (CRITICAL — READ THIS FIRST) ***
The story setting MUST be describable in 1-3 words that a child already knows. The Gruffalo — the best-selling children's book in UK history — is set in "a deep dark wood." Not a clockwork forest. Not a crystal dimension. Just a wood. The magic comes from WHO you meet and WHAT goes wrong, not from the setting itself being complicated.

Study the top children's books: The Gruffalo = a wood. Tiger Who Came to Tea = a kitchen. We're Going on a Bear Hunt = a field, a river, mud. Owl Babies = a tree. Peter Rabbit = a garden. Dear Zoo = a zoo. Shark in the Park = a park. Peace at Last = a bedroom. Where the Wild Things Are = a bedroom. These are all ONE simple place.

FOR under_3, age_3, age_4:
The setting must be a place a child can say in 1-3 words: a wood, a kitchen, a park, a shop, a bedroom, a school, a bath, a beach, a zoo, a farm, a playground, a garden, a pond, a hill, a field, a bus, a boat, a tree.
Then ONE thing in that place goes wonderfully wrong. That's the whole story.
The setting is the STAGE. The chaos is the SHOW. Keep the stage simple so the chaos shines.
NEVER invent the setting. No clockwork forests, no gear worlds, no cracker moons, no crystal caves, no candy planets, no music dimensions. If a child can't draw the setting from memory, it's too complicated.
GOOD: "A deep dark wood where the puddles have turned to trampolines" (a wood + one bonkers thing)
GOOD: "A kitchen where the fridge won't stop spitting out food" (a kitchen + one bonkers thing)
GOOD: "A park where the slide goes underground" (a park + one bonkers thing)
BAD: "A clockwork forest with a glass house and a noise dial" (child has never seen any of these things)
BAD: "A cracker moon crumbling into starry soup" (every single element is invented)

FOR age_5, age_6, age_7:
The setting can be a FANTASY VERSION of a place kids know from play and stories — a pirate ship, a castle, a space rocket, a dragon's cave, an underwater kingdom, a magic school. Kids this age play pretend in these worlds. Still avoid pure abstraction — the child must be able to picture it.

FOR age_8, age_9, age_10:
Any setting is fine — fully invented worlds, alternate dimensions, complex fantasy. The reader can build the world from description alone.
"""

# ──────────────────────────────────────────────
# RANDOM WORLD SEEDS — breaks Gemini's repetition loop
# ──────────────────────────────────────────────

import random

WORLD_SEEDS_GROUNDED = [
    # REAL PLACES GONE WRONG — for under_3, age_3, age_4
    "a swimming pool where the water has turned to bouncy jelly",
    "a supermarket where all the tins have come alive and are rolling everywhere",
    "a kitchen where the fridge is spitting out food at top speed",
    "a garden where the flowers have grown as tall as houses overnight",
    "a playground where the slide has gone wobbly and bendy",
    "a bakery where the bread dough is growing and filling every room",
    "a car wash that has gone wrong and is washing everything — dogs, bikes, postmen",
    "a farm where the chickens have learned to fly and won't come down",
    "a hair salon where the hairdryer is blowing everything out the door",
    "a fish and chip shop where the chips keep growing longer and longer",
    "a bath where the bubbles won't stop and are filling the whole house",
    "a birthday party where the balloons keep getting bigger and bigger",
    "a bedroom where the pillows have come alive and are bouncing everywhere",
    "a park where the puddles are getting deeper and deeper",
    "a school where all the paint pots have tipped over and paint is everywhere",
    "a zoo where the animals have swapped their enclosures",
    "a bus that won't stop picking up more and more passengers",
    "a dentist where the spinny chair won't stop spinning",
    "a restaurant where the food keeps sliding off the plates",
    "a library where all the books are flapping their pages like birds",
    "a greenhouse where the plants are growing so fast they're pushing through the glass roof",
    "a fire station where the fire engine has been filled with silly string instead of water",
    "a football match where the ball keeps getting bigger and bigger",
    "a post office where the parcels are delivering themselves — to the wrong places",
    "a construction site where the crane is building a tower of sandwiches",
    "a launderette where the machines are eating the clothes and spitting out something else",
]

WORLD_SEEDS_FANTASY = [
    # FANTASY SETTINGS — for age_5+
    "inside a giant's wellington boot — it's raining and the boot is filling up",
    "a planet made entirely of trampolines where nothing stays on the ground",
    "a library where the books suck you inside the story",
    "an upside-down town where everything is on the ceiling",
    "a world inside a snow globe that someone keeps shaking",
    "a volcano that erupts marshmallows instead of lava",
    "a cloud city where the buildings are made of candyfloss and keep melting in the sun",
    "a jungle made of giant vegetables where the carrots are taller than trees",
    "a desert where the sand is actually sugar and ants the size of dogs are coming for it",
    "inside a giant pinball machine where the character IS the ball",
    "a mountain made entirely of pillows that keeps collapsing",
    "a frozen lake where the ice keeps cracking into puzzle pieces",
    "a sky full of floating islands connected by wobbly rope bridges",
    "a space station where the gravity has switched off during dinner",
    "a circus where all the performers have gone home and the animals are doing the show",
    "a pirate ship where the treasure map keeps changing every time you look at it",
    "a zoo at night where the animals are having a secret sports day",
    "a museum where all the dinosaur bones have started moving",
    "a magic show where the magician has disappeared and left all the tricks running",
    "a theme park where the rollercoaster has turned into a dragon",
    "a space rocket that has launched with nobody driving it",
    "a submarine that has accidentally shrunk to the size of a goldfish",
    "a toy shop at midnight where everything is having a party",
    "a concert hall where the instruments are playing themselves — very badly",
]

def get_random_world_seeds(n=3, age_level="age_5"):
    """Pick n random world seeds — grounded only for young ages, all seeds for older."""
    young_ages = ("under_3", "age_3", "age_4")
    if age_level in young_ages:
        pool = WORLD_SEEDS_GROUNDED
    else:
        pool = WORLD_SEEDS_GROUNDED + WORLD_SEEDS_FANTASY
    return random.sample(pool, min(n, len(pool)))

PITCH_AGE_GUIDELINES = {
    "age_3": """
AGE GROUP: 2-3 YEARS OLD (TODDLER)

*** STORY DRIVER ***
Every great toddler story has ONE clear answer to: "What does the character WANT?"
The want must be PHYSICAL and IMMEDIATE — something a 2-3 year old can see and touch:
- Wanting to reach a ball that rolled under something
- Wanting to catch a bouncing thing that won't stop moving
- Wanting to catch a bouncing thing that won't stop moving
- Wanting to climb to the top of something very tall
- Wanting to find something that is hiding
- Wanting to give someone a thing but it keeps falling/rolling/flying away

The character's appearance or traits can play into the story naturally — but the WANT and the OBSTACLE are what matter most. The obstacle can be situational (the ball is stuck, the tower keeps falling) or character-driven (big paws make it slippery) or both.

*** WHAT SEPARATES A BAD PITCH FROM A GOOD ONE ***

A BAD toddler pitch has:
- No clear WANT (character just wanders around)
- Feature causes RANDOM chaos with no purpose (loud = stuff breaks, strong = stuff smashes)
- Resolution is just "do the opposite" (loud -> quiet, fast -> slow)
- No emotional moment — nothing to make the kid feel anything

A GOOD toddler pitch has:
- A SPECIFIC want the kid can relate to (help a friend, get somewhere, give a present, fix a mistake)
- A clear, funny obstacle that blocks the want — this can be situational (too high, too slippery, keeps bouncing away) or involve the character's traits, or both
- Each failed attempt is different and funnier than the last
- An emotional low point where the character feels sad/stuck (this is what makes the win feel good)
- A CREATIVE resolution that surprises — not the obvious solution
- The resolution connects emotionally to the want — not just "problem fixed" but "friendship strengthened" or "character accepted"

CRITICAL: Create completely original scenarios based on the character.

*** STORY STRUCTURE - USE ONE OF THESE 3 PROVEN PATTERNS ***

PATTERN A: "REPETITION WITH SURPRISE" (like Dear Zoo, Brown Bear Brown Bear)
- Episodes 1-3: Same pattern repeats with a different funny thing each time
- Episode 4: The pattern changes or breaks in a surprising way
- Episode 5: Satisfying conclusion that calls back to episode 1

PATTERN B: "ACCUMULATING CHAOS" (like The Very Hungry Caterpillar)
- Each episode adds ONE more silly thing to a growing pile of chaos
- By episode 3-4, everything is hilariously out of control
- Episode 5: one big action fixes everything (or makes it even funnier)

PATTERN C: "JOURNEY WITH OBSTACLES" (like We're Going on a Bear Hunt)
- Character goes somewhere, hits an obstacle, gets past it with a fun sound/action
- Each obstacle is different and fun to act out
- Final obstacle leads to a big surprise
- Then rush back home!

*** WHAT MAKES TODDLER STORIES WORK ***
- At least ONE moment where the kid will LAUGH (physical comedy, something going splat, a funny noise)
- The character DOES things - never just looks or observes
- Predictable pattern that kids can "join in" with after one hearing
- A satisfying physical payoff — the mess resolves in one big funny action (a giant POP, a big SPLAT, a huge WHOOSH)
- The ending must MAKE SENSE: the "mistake" should secretly BE the answer

*** BANNED FOR AGE 3 ***
- Passive searching (look here, look there, found it, done)
- Character just observing or noticing things
- Abstract or conceptual themes
- Stories with no funny moment or surprise
- Connective tissue sentences: "Then he...", "Because of that...", "He felt..." — each page is a standalone exclamation
- Words longer than 2 syllables — use "big" not "enormous", "silly" not "determined"
- Any moral or lesson — the goal is a silly mess, not a life lesson

*** SENTENCE RULE ***
- under_3: Maximum 5 words per sentence. Maximum 10 words total per page. Pure board book — labels and sounds only.
- age_3: Maximum 12 words per sentence. 15-25 words total per page. Simple causal sequences — setup, action, result.

*** UNDER_3 REFRAIN RULE ***
For under_3 stories, pages 2, 3, and 4 MUST follow a repeating pattern with a REFRAIN that fires every page. The refrain is a single word or short phrase that captures the consequence of what just happened — it must make sense every time it fires.
There are two valid patterns:

PATTERN A (Consequence Refrain): New action each page, same consequence refrain fires at the end.
EXAMPLE: Page 2: "CRASH! Al walks into the books. SHHH!" Page 3: "WHOOSH! Al slips on the rug. SHHH!" Page 4: "SQUEAK! Al's shoes wake the cat. SHHH!" — the SHHH fires because the same rule applies every time (must stay quiet). The child will shout it before the parent finishes the sentence.

PATTERN B (Structure Refrain): Identical sentence structure, only the key object or action changes.
EXAMPLE: Page 2: "SPLASH! Tim hits the puddle. WET!" Page 3: "BOING! Tim hits the trampoline. HIGH!" Page 4: "CRASH! Tim hits the cushions. SOFT!"

Choose the pattern that fits the story — Pattern A works best when there is a rule being broken (must stay quiet, must not wake the baby, must not spill). Pattern B works best for exploration stories (trying different things). The refrain must be chosen BEFORE writing — it comes from the episode 1 goal. This is non-negotiable for under_3.
CRITICAL SOUND MATCHING RULE: The opening sound word on every page must physically match the action that follows it. GOOD: "SPLASH! Tim hits the puddle." (splashing matches puddle). GOOD: "SQUEAK! Al walks on the shiny floor." (squeaking matches shiny shoes on floor). BAD: "HONK! Al reaches for the corner." (honking does not match reaching). If the sound word could not realistically come from the action described, replace it with one that could.

*** AGE_3 JOIN-IN RULE ***
For age_3 stories, use a repeating phrase every 2 pages that the child can predict and shout along with.
EXAMPLE: Pages 2 and 4 both end with "But it was still too [adjective]!" or "Is that the most amazing [character] ever?"
The join-in phrase must be the MISSION STATEMENT of the story — a rallying cry that captures exactly what the character is trying to achieve. It must make sense on every single page it appears because it is always true until the very moment the goal is achieved. Think of it as the one sentence that sums up the whole story's drive. GOOD: "We must find that lucky coin!" (names the goal explicitly). GOOD: "Come on, we can reach the top!" (captures the emotional drive). BAD: "Oh no, the dusty eyebrows!" (describes a side effect, not the goal). BAD: "The map is slipping!" (situational — stops making sense the moment the situation changes). Choose the refrain BEFORE writing the episodes — it should come naturally from the episode 1 goal. The phrase should be warm, urgent, or funny. It must only appear when a specific thing goes wrong — never after a calm or successful moment, and NEVER on the resolution page. CRITICAL: The refrain must be completely self-contained — a child must understand it with zero context. Never use ambiguous pronouns. WRONG: "Oh no, wipe them dry!" WRONG: "Oh no, it slipped!" RIGHT: "We must find that lucky coin!" RIGHT: "Oh no, the rabbit is gone!"

*** PRE-REQUISITE RULE (CRITICAL FOR UNDER_3) ***
No new object may cause an action unless it was introduced and visible in the PREVIOUS episode.
Object A appears → Object B appears → A meets B → chaos → resolution.
This is non-negotiable. A toddler's brain tracks one thing at a time. Objects cannot appear from nowhere to drive the plot.
BAD: Page 3 — "The ring went BOING!" (ring never appeared before)
GOOD: Page 2 — Hannah finds a sparkly ring. Page 3 — She rolls it down the hill. BOING!

*** CUMULATIVE BUILD RULE ***
Each episode must build directly on the previous one. The story is a chain, not a collection of scenes.
Use this 5-beat structure for under_3:
- Episode 1: Introduce Object A (the main thing)
- Episode 2: Introduce Object B (the new thing)
- Episode 3: Object A meets Object B — something goes wrong
- Episode 4: The mess gets bigger — physical chaos peak
- Episode 5: One big action fixes it — warm ending (hug, laugh, yum)

*** CAUSAL CHAIN RULE ***
Every episode must CAUSE the next one. Episode 3 happens BECAUSE of episode 2. Not alongside it. Not instead of it. BECAUSE of it.
Before writing each episode ask: "What did the LAST episode leave behind that makes THIS episode happen?"
BAD chain: ball → random bowl breaks → coconut appears → cake (no causal links)
GOOD chain: ball rolls → knocks over tower → tower falls on bucket → bucket tips → everything tumbles → big laugh
If you cannot answer WHY each episode follows from the last, rewrite it.

*** CHARACTER-STORY FIT RULE ***
The story's central situation and the character should feel like a natural fit. Ask: "Is it funny or interesting to imagine THIS character in THIS situation?"
GOOD: a round fluffy chicken on a wobbly beam (funny because of physics)
GOOD: a tiny mouse in a giant kitchen (funny because of scale)
GOOD: a loud parrot at a library (funny because of contrast)
The character's appearance can make the situation funnier — but the situation must be funny on its own too.

*** BLURB TONE FOR THIS AGE ***
Blurbs must sound like a mess happening RIGHT NOW. Use nouns and noises only.
BAD: "Kiki learns about sharing with her friends at the park."
The blurb must describe something PHYSICAL happening to the character — something a toddler can picture and laugh at. Be inventive and specific to THIS character. Never use the same type of scenario twice.
NO questions. NO "time to...". State the chaos, not a question about it.
""",

    "age_4": """
AGE GROUP: 4 YEARS OLD

*** STORY DRIVER ***
Every story needs ONE clear answer to: "What does the character WANT, and what's stopping them?"
The want should be specific and urgent — not vague:
- BAD want: "Jerry wants to be helpful" (vague, no urgency)
- GOOD want: "Jerry wants to win the talent show but keeps accidentally scaring the judges"
- BAD want: "Ted wants to explore" (no stakes, no obstacle)
- GOOD want: "Ted needs to get the class hamster back in its cage before the teacher returns, but the hamster keeps finding new hiding spots"

The obstacle must be specific, funny, and create real complications. It can be situational (the hamster keeps escaping, the cake keeps sliding), involve the character's traits, or both. The key is that the obstacle blocks the WANT in a way that escalates.
The resolution must be CLEVER — not just "stop doing the bad thing" or "do the opposite."

*** STORY STRUCTURE - USE ONE OF THESE PATTERNS ***

PATTERN A: "THE CLEVER TRICK" (like The Gruffalo)
- Character faces a problem bigger than them
- Character uses a CLEVER trick to solve it (not the obvious way)
- Moment of "oh no, it didn't work!" then a smarter version works
Key: Character should be SMART, not just lucky.

PATTERN B: "THE GROWING TEAM" (like Room on the Broom)
- Character sets off on a mission alone, meets helpers with funny personalities
- Individual efforts fail - they must work TOGETHER
Key: Each helper adds something funny AND useful.

PATTERN C: "THE BIG MISTAKE" (like Elmer, Oi Frog)
- Character does something causing an unexpected chain reaction
- Things get progressively sillier and more out of control
- The "mistake" turns out to be something good or useful
Key: Comedy from things going wrong in UNEXPECTED ways.

*** WHAT MAKES AGE 4 STORIES GREAT ***
- A moment where the kid gasps or says "oh no!"
- A genuinely funny bit that makes the parent laugh too
- Supporting characters with ONE clear personality trait (the grumpy one, the scared one, the bossy one)
- The main character solving the problem THEMSELVES (no adult swooping in)
- The solution must LOGICALLY follow from the problem — not a random new action
- NO MAGIC SOLUTIONS: The character cannot solve the problem by their feature magically "working." They must use the mess, the chaos, or a specific tool they find to solve it. BAD: "Her spots glowed and lit up the room." GOOD: "Her glowing spots lit up a bucket — and inside was the torch they needed."
- Write for a parent to PERFORM aloud, not just read. Every page should give the parent a chance to make a funny voice, a loud noise, or a silly face.
- Use ACTIVE verbs not passive ones: "stomped" not "walked", "peered" not "looked", "snatched" not "took"
- Every page must have at least ONE sound word in ALL CAPS (CRASH, SQUISH, BOING, SPLAT)
- Vary sentence length: short sentences for tension ("Oh no."), longer ones for build-up
- ALLITERATION RULE: Every page must include at least one alliterative phrase (three words starting with the same letter, e.g. "cold, crinkly crack" or "stomped and squelched and slipped"). This makes it fun to read aloud.
- VOCABULARY RULE: THE TODDLER MOUTH TEST — every word must be one a 4-year-old would say unprompted at preschool. 3+ syllable words are almost always wrong. Write how they talk, not how books sound.
- THE 3-STRIKE STRUCTURE: STRIKE 1 (Setup) — establish the character and the problem immediately with a sound or physical action. STRIKE 2 (Escalation) — the obstacle must be physical and messy (greasy, sticky, crumbly, wobbly). STRIKE 3 (Payoff) — the resolution must be a physical triumph (a big TUG, a big POP, a big SPLAT). Every age_4 story must hit all 3 strikes.

*** WORD COUNT RULE ***
Maximum 40 words per episode. ABSOLUTE MAXIMUM. Count them. If you go over, cut adjectives first, then cut connective sentences ("Because of this...", "Then she..."). Never cut the sound word.

*** SOUND-FIRST RULE ***
Write the sound word FIRST, then describe what caused it. This forces active writing.
BAD: "Lily had a clever idea. She picked it up carefully and put it down. Done."
GOOD: "CRASH! WOBBLE! Lily grabbed the tower with both hands — and the whole thing came tumbling down!"
The sound word is the heartbeat of every page. Build the sentence around it, not after it.

*** BLURB TONE FOR THIS AGE ***
Blurbs must hook with a silly consequence. Focus on funny mistakes and physical mess.
GOOD: "Ted's giant feet have got tangled in the cake stand and now the whole table is tipping over!"
BAD: "Ted learns that being careful is important when baking."
End with the character in a silly impossible position, not a question.
""",

    "age_5": """
AGE GROUP: 5 YEARS OLD

*** STORY DRIVER ***
Answer these before writing:
1. What does the character WANT? (Must be specific: "save the baby penguin" not "help others")
2. WHY do they want it? (Emotional reason: "because the penguin is crying and alone")
3. What makes it HARDER? (A specific, funny obstacle — situational, character-driven, or both)
4. How is it eventually solved in an UNEXPECTED way? (Not the obvious solution)

The OBVIOUS solution is always BORING. The SURPRISING solution is what makes great stories.

*** STORY STRUCTURE ***

STRUCTURE A: "RESCUE/DELIVERY UNDER PRESSURE" (like Zog, Supertato)
- Clear urgent problem → first attempt → SETBACK (fails or makes it worse) → creative sideways solution → victory connecting back to episode 1
Key: The setback must feel real. The kid should worry it won't work out.

STRUCTURE B: "MYSTERY/DETECTIVE"
- Something weird is happening → follow clues → red herring (funny misunderstanding) → real answer discovered → everything explained with a sweet/funny reason
Key: The mystery answer should be funny or heartwarming, not scary.

STRUCTURE C: "ACCIDENTAL HERO" (like Dogger, Giraffes Can't Dance)
- Character feels they can't do something → forced to try → attempt goes hilariously wrong → the "wrong" thing accidentally solves a bigger problem → character celebrated for being exactly who they are
Key: Message through ACTION not moralising.

*** WHAT MAKES AGE 5 STORIES GREAT ***
- A setback that makes the kid say "uh oh, NOW what?!"
- Supporting characters who actively HELP or HINDER - not just stand around watching
- The character should surprise themselves — and the reader — with how they solve it
- The solution must come FROM the problem — the "disaster" secretly created the answer
- Write for a parent to PERFORM aloud. Dialogue should beg to be done in funny voices. At least 2 episodes must have direct speech.
- Use ACTIVE verbs: "scrambled" not "went", "bellowed" not "said", "squelched" not "walked"
- Every page must have at least ONE sound word in ALL CAPS
- Mix short punchy sentences with longer descriptive ones for rhythm

*** BLURB TONE FOR THIS AGE ***
Blurbs must present a surreal what-if with clear stakes.
GOOD: "Oli's magic photos have swapped all the colours — the sky is green and the grass is blue and it's spreading fast!"
BAD: "Oli discovers that his photos have a special power that could change everything."
One surprising image, one clear problem, no questions.
""",

    "age_6": """
AGE GROUP: 6 YEARS OLD

*** STORY DRIVER ***
1. What does the character WANT? (Specific, urgent goal)
2. What are the STAKES? (What happens if they fail? Someone gets hurt/disappointed/left out)
3. What creates an interesting DILEMMA? (Competing goals, unintended consequences, or a situation where helping one thing hurts another)
4. What does the character LEARN? (Not a preachy lesson — an earned realisation through action)

The resolution must be CLEVER and EARNED — not just "try harder" or "believe in yourself."
The character should solve the problem in a way that reframes the whole story.

*** STORY STRUCTURE ***
Age 6 can handle real plot twists and emotional stakes:
- Episode 1: Establish the world AND the problem in the same beat. Hook immediately.
- Episode 2: First plan - starts well but a complication appears
- Episode 3: MAJOR SETBACK - plan fails badly. Lowest point.
- Episode 4: Realisation or unexpected help. New approach using what they LEARNED from failing.
- Episode 5: Resolution surprises the reader while making sense. A detail from episode 1 reappears in a new light. NEVER end with a lesson statement.

*** KEY PRINCIPLES ***
- The setback must be REAL - not just "oops, wrong place." Something genuinely goes wrong.
- Supporting characters have their own mini-motivations (not just cheerleaders)
- Dramatic irony where possible (reader knows something the character doesn't)
- The ending is EARNED - character MAKES things work out

*** BLURB TONE FOR THIS AGE ***
Blurbs can have irony and wit. Hook the child AND the parent.
GOOD: "Tapey accidentally glued the school roof to the playground — and the head teacher is stuck to both."
BAD: "Tapey goes on a journey that will test everything they know about friendship."
High concept, specific objects, adult wink of irony. No questions.
""",

    "age_7": """
AGE GROUP: 7-8 YEARS OLD

*** STORY DRIVER ***
1. What does the character WANT? (Compelling, specific goal with real urgency)
2. What are the STAKES? (Real consequences — someone is counting on them)
3. What is the COST of trying? (Every plan has a downside that creates tension — trade-offs, unintended consequences, things getting worse before they get better)
4. What is the TWIST? (Something the reader thinks they understand that gets reframed)

The best stories at this age have a moment where the reader's assumption is flipped.

*** STORY STRUCTURE ***
Full 5-act structure with genuine stakes:
- Episode 1: Hook immediately. Problem with urgency and real consequences.
- Episode 2: Investigation/preparation. Build world. Introduce allies and obstacles with personality.
- Episode 3: MAJOR FAILURE. Plan backfires spectacularly. Real consequences. Supporting characters affected too.
- Episode 4: Character adapts. Uses feature in unexpected creative way. Combines what they learned from failure.
- Episode 5: Genuine twist resolution. Ending reframes something from episode 1. NEVER a moral lesson or summary statement.

*** KEY PRINCIPLES ***
- Real stakes: feelings get hurt, something important is at risk, time runs out
- Multiple characters with competing goals (not just good vs evil)
- The obstacle/villain should have an understandable motivation
- Humour and tension ALTERNATE
- The character's plan should have a COST or LIMITATION that creates real tension
- Subvert expectations at least once
""",

    "age_8": """
AGE GROUP: 8 YEARS OLD
- Complex plots with character development
- Themes: responsibility, discovery, challenges
- Wordplay, puns, double meanings kids feel smart getting
- The character should face a real dilemma, not just a puzzle to solve
""",
    "age_9": """
AGE GROUP: 9 YEARS OLD
- Deep character development and relationships
- Themes: identity, belonging, leadership
- Emotional depth: show how characters FEEL inside, not just what they do
- Stories should have layers — what the character SAYS they want vs what they ACTUALLY need
""",
    "age_10": """
AGE GROUP: 10+ YEARS OLD
- Nuanced storytelling with moral complexity
- Themes: self-discovery, hard choices, complex friendships
- The twist should challenge the character's assumptions about themselves or the world
- Real consequences for choices — not everything wraps up neatly
"""
}


def generate_story_pitches_gemini(
    character_name: str,
    character_description: str,
    age_level: str = "age_6",
    writing_style: str = None,
    life_lesson: str = None,
    custom_theme: str = None,
    second_character_name: str = None,
    second_character_description: str = None,
    api_key: str = None,
) -> dict:
    """
    Generate 3 story theme pitches using Gemini 3 Flash.
    
    Drop-in replacement for generate_personalized_stories() in adventure_gemini.py.
    Same signature, same output format.
    
    Returns dict:
    {
        "character_name": "...",
        "age_level": "...",
        "themes": [
            {
                "theme_id": "snake_case_id",
                "theme_name": "...",
                "theme_description": "...",
                "theme_blurb": "...",
                "feature_used": "...",
                "want": "...",
                "obstacle": "...",
                "twist": "..."
            },
            ...
        ]
    }
    """
    key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not key:
        raise ValueError("GEMINI_API_KEY not set")

    client = genai.Client(api_key=key)

    # Age mapping — under_3 uses age_3 guidelines (same as Sonnet)
    pitch_age = "age_3" if age_level == "under_3" else age_level
    age_guide = PITCH_AGE_GUIDELINES.get(pitch_age, PITCH_AGE_GUIDELINES["age_6"])

    # Age display string
    age_display = age_level.replace("age_", "")
    if age_display == "3" or age_level == "under_3":
        age_display = "2-3"
    elif age_display == "10":
        age_display = "10+"

    # ── Build optional style/theme/lesson override block ──
    style_theme_block = ""
    if writing_style:
        style_theme_block += f"""
*** WRITING STYLE NOTE ***
The user has chosen the writing style: "{writing_style}"
Keep this in mind when crafting theme descriptions and blurbs — they should hint at the tone of the story.
For example, "Silly" themes should have absurd premises, "Gentle" themes should have soft/cozy settings, "Suspenseful" themes should have mystery/tension in the blurb.
Do NOT write actual story text — just let the style influence the CONCEPT and TONE of each pitch.
CRITICAL: The writing style applies to the STORY only, NOT to the blurb. Blurbs must always be plain prose — never rhyming, never rhythmic, never mimicking the writing style. A blurb for a Rhyming story must NOT rhyme. A blurb for a Repetition story must NOT use refrains. The blurb is a parent-facing hook, not a sample of the story's style.

CRITICAL — IF WRITING_STYLE IS "Repetition":
Do NOT use doubled words in theme names or blurbs (NOT "The Snap-Snap Parade" or "bump-bump-bump").
Repetition style means STRUCTURAL REFRAIN — a phrase that repeats at the same moment every 2 pages, like "Is that the most amazing dog ever?" or "Watch out for those big floppy ears!".
The pitch concept should lend itself to a repeating situation — something that keeps going wrong in the same way, or a question the child can shout along with.
Theme names should be normal title-case names, not gimmicky doubled words.
"""
    if life_lesson:
        style_theme_block += f"""
*** LIFE LESSON OVERRIDE ***
The user wants the story to teach or explore this life lesson: "{life_lesson}"
ALL 3 story pitches must weave this lesson naturally into the narrative:
- If "Friendship": The story should explore making friends, loyalty, helping each other, or what it means to be a good friend.
- If "Being brave": The character should face fears, show courage, or learn that being brave doesn't mean not being scared.
- If "It's OK to make mistakes": The character should mess up, feel bad, but discover that mistakes lead to learning or something good.
- If "Kindness": The story should show acts of kindness, empathy, or helping others without expecting anything back.
- If "Being yourself": The character should learn to embrace what makes them different or unique.
- If "Sharing": The story should explore sharing, generosity, or discovering that sharing makes things better.
- If "Perseverance": The character should keep trying when things get hard, showing that persistence pays off.
- If "Patience": The character learns that rushing makes things worse and that waiting, slowing down, or taking their time leads to better results.
- If "Teamwork": The character tries to do everything alone and struggles, then discovers that working together with others achieves much more.
- If "Trying new things": The character is reluctant or scared to try something unfamiliar, but discovers something wonderful when they do.
- If "Saying sorry": The character makes a mistake that hurts someone, struggles to apologise, but learns that saying sorry and making amends fixes things.
- If "Listening to others": The character ignores advice or doesn't listen, things go wrong, then they learn that hearing other perspectives helps everyone.
- If "Gratitude": The character takes something for granted, loses it or nearly loses it, and learns to appreciate what they have.
- For any other lesson: interpret it naturally and weave it throughout the story arc.
IMPORTANT: The lesson should emerge THROUGH THE STORY, not through lecturing or moralising. Show don't tell. The character EXPERIENCES the lesson through what happens to them.
"""
    if custom_theme:
        style_theme_block += f"""
*** CUSTOM THEME FROM PARENT ***
The parent has written a personal note about what this story should include: "{custom_theme}"
This could be a birthday ("It's Tom's 5th birthday!"), a milestone ("Tom just learned to ride a bike"), a new experience ("Tom starts school on Monday"), or anything personal.
ALL 3 story pitches must weave this personal detail naturally into the story:
- It should feel like the story was written specifically for THIS moment in the child's life
- The custom theme should be a central part of the plot, not just a passing mention
- Combine it creatively with the character's features — e.g. if the theme is "birthday" and the character has big boots, maybe the boots are a birthday present, or they bounce to their birthday party
"""

    # ── Build second character block ──
    second_char_block = ""
    if second_character_name and second_character_description:
        second_char_block = f"""
*** SECOND CHARACTER (COMPANION/FRIEND/PET) ***
Name: {second_character_name}
Description: {second_character_description}

This is {character_name}'s companion who appears in EVERY scene. {second_character_name}'s features and personality should ALSO drive the story:
- Their features can cause problems (muddy paws track dirt everywhere, long tail knocks things over, curiosity leads them into trouble)
- Their features can also help solve problems (keen nose sniffs out clues, strong arms lift heavy things, tiny size fits through gaps)
- They should have their OWN personality and reactions — not just follow the main character silently
- At least ONE of the 3 themes should use {second_character_name}'s features as a key story element
- {second_character_name} and {character_name} should work as a TEAM — sometimes disagreeing, sometimes complementing each other
"""

    # ── Pick random world seeds to break repetition ──
    seeds = get_random_world_seeds(3, age_level=age_level)
    seeds_block = "\n".join(f"- {s}" for s in seeds)

    # ── Build the full user prompt (matches Sonnet structure exactly) ──
    prompt = f'''You are creating personalized story adventures for a childrens coloring book app.
{style_theme_block}
Generate 3 UNIQUE, HIGH-CONCEPT story themes for a character called "{character_name}"{f" and their companion {second_character_name}" if second_character_name else ""}. You will design the story WORLDS first, then read the character description and cast them into those worlds.

STEP 1 — DESIGN 3 EXCITING WORLDS (before thinking about the character)

⚠️ DO THIS FIRST — before you look at the character description below.

Invent 3 HIGH-CONCEPT story worlds that a child would BEG to colour. These must be visually spectacular settings that produce 5 completely different colouring pages. Each world must be so exciting that ANY character dropped into it would have an amazing adventure.

Here are 3 STARTING SPARKS to inspire you. You can adapt these, remix them, combine them, or use them as a jumping-off point for something completely different. Do NOT copy them word-for-word — use them to SPARK an original idea:
{seeds_block}

You may also invent something entirely from scratch that has NOTHING to do with these sparks. The only rule is: each of your 3 worlds must be DIFFERENT from each other, DIFFERENT from the sparks above, and something a child has NEVER seen before.

THESE ARE JUST EXAMPLES — invent your own. The world must be:
1. VISUALLY RICH — each of the 5 episodes must look completely different when drawn as a colouring page. If you can't imagine 5 distinct, exciting illustrations, the world isn't good enough.
2. HIGH CONCEPT — a parent reads the title and thinks "I HAVE to see this." Not "Sheepy goes shopping" but "Sheepy and the Upside-Down Zoo."
3. VARIED ACROSS THE 3 PITCHES — one everyday-gone-wrong, one fantastical/impossible, one involving a specific job/event/mission. No two can share the same type of setting.

STEP 2 — NOW READ THE CHARACTER

CHARACTER NAME: "{character_name}"
DESCRIPTION:
{character_description}

⚠️ GENDER: Do NOT assume the character's gender from their name. Use the character's NAME instead of pronouns wherever possible. If you must use pronouns, use "they/them" unless the character description explicitly states gender.

⚠️ ABSOLUTELY NO FAMILY MEMBERS OR RELATIVES IN ANY STORY:
- No grandparents, grandmas, grandads, nans, grandpas
- No cousins, aunts, uncles, siblings, brothers, sisters, mums, dads, parents
- Family members may be deceased or estranged in real life — including them can cause genuine distress
- Use FRIENDS, CLASSMATES, NEIGHBOURS, or invented named characters instead
- This rule is absolute, no exceptions

{second_char_block}

⚠️ CRITICAL — HOW TO USE PHYSICAL FEATURES:
- For HUMAN/PERSON characters: physical features (glasses, curly hair, freckles, braces) must ONLY appear as positives, superpowers, or something wonderful. NEVER as something to fix, hide, or overcome.
- Objects being held or used (ukulele, bike, football, paintbrush) are brilliant story elements — weave them in naturally.
- For NON-HUMAN characters (monsters, animals, toys): unusual body parts are great for comedy — use them freely but don't make them the entire plot.
- DO NOT make stories about "camouflage", "blending in", or "colours fading/restoring" — these are overdone.

STEP 3 — CAST THE CHARACTER INTO YOUR WORLDS

Now take your 3 high-concept worlds from Step 1 and drop {character_name} into them. The character's appearance, clothing, and traits should naturally affect HOW they experience each world — causing incidental comedy, shaping the obstacle, or making the resolution personal. But the WORLD is the star, not the character's body parts.

For each pitch, the WANT must answer THREE questions:

1. WHAT does {character_name} need to do? (A specific physical action — build, escape, deliver, rescue, stop, find)
2. WHY? What happens if they FAIL? (The consequence must be dramatic and visual — something floods, explodes, escapes, takes over, melts, collapses, grows out of control. NOT "they'll be late" or "they'll be sad.")
3. WHAT'S THE CLOCK? Why can't they take their time? (Something is shrinking, melting, rising, hatching, inflating, counting down, spreading, getting closer. There must be a ticking bomb.)

ALL THREE must be present. If ANY is missing, the pitch is boring. Test:
- BAD WANT: "Tim wants to build a marshmallow tower higher than the fence." (WHY? No consequence. No clock. Who cares?)
- GOOD WANT: "Tim must build a marshmallow tower tall enough to climb over the wall before the rising gloop covers the whole park — but the sun is melting the marshmallows as fast as he stacks them."
- BAD WANT: "Oli wants to lead the toys home before the lights go out." (Consequence is boring. Clock is weak.)
- GOOD WANT: "Oli must get the marching robots back in the toy box before they reach the kitchen — because the robots think the oven is a spaceship and they're about to launch it."

The OBSTACLE must come from the WORLD and the SITUATION — not just from a body part malfunctioning.
The TWIST must solve the problem in a way nobody expected — not just "try harder."

*** THE STAKES MUST BE DRAMATIC (NON-NEGOTIABLE) ***
A child must hear the pitch and feel URGENCY. The consequence of failure must be exciting, visual, and slightly scary (in a fun way). Think: countdown to something BIG happening.
- BAD STAKES: "before the lights go out" / "before bedtime" / "before it gets dark" / "before the clock stops" — BORING. Nobody cares.
- BAD STAKES: "lead the toys home" / "tidy up the mess" / "find the lost thing" / "stack something tall" — DOMESTIC. Not exciting.
- GOOD STAKES: "before the volcano fills the whole town with marshmallow lava"
- GOOD STAKES: "before the robots take over the entire school"
- GOOD STAKES: "before the giant wakes up and finds them in his kitchen"
- GOOD STAKES: "before the ice cream factory melts everything in the park"
- GOOD STAKES: "before the bouncy castle inflates so big it floats into space"
The stakes should make a child's eyes go wide. If a parent reads the pitch and their kid doesn't say "I WANT THAT ONE!" — the stakes aren't high enough. Rewrite until they are.

THE 5-PAGE COLOURING TEST (CRITICAL):
Before finalising each pitch, imagine the 5 colouring pages a child will receive. Are they 5 genuinely different illustrations — different locations, different objects, different compositions? If more than 2 pages would look similar, the world isn't rich enough. REJECT IT and pick a more visually varied setting.

BAD (fails the test): "Sheepy and the Wobbly Trolley" — 5 pages of supermarket aisles
BAD (fails the test): "Al and the Bouncy Hair Day" — 5 pages of a character's hair doing things
GOOD (passes the test): "Sheepy and the Upside-Down Zoo" — page 1: entrance gate flipping, page 2: penguins on the ceiling, page 3: elephant dangling from a tree, page 4: Sheepy climbing the gift shop wall, page 5: everything flips back with a giant splash
GOOD (passes the test): "Al and the Runaway Robot Chef" — page 1: kitchen chaos, page 2: robot loose in the dining room, page 3: food fight in the garden, page 4: chase through the park, page 5: robot makes the perfect cake by accident

{age_guide}

CRITICAL: Follow the age guidelines above exactly for sentence length, vocabulary, and complexity.

*** FORMAT ***

For each theme provide:
1. Theme name (fun, age-appropriate, MAX 6 words, MAX 35 characters)
2. Theme description (1 sentence)
3. Theme blurb (ONE short punchy sentence, MAX 15 words. This is the most important line — it must make a parent gasp and think "this was written ONLY for my child." Rules:
- MUST include {character_name}'s name
- The sentence should make the reader immediately curious about the story
- NEVER be vague — vague blurbs feel generic and could be about anyone
- NEVER use the formula "good thing [character] knows how to..." or "but will it be enough?" — these are weak and lazy
- NEVER end with a generic personality trait like "never gives up" or "always finds a way"
- The blurb should describe the SITUATION with dramatic stakes. What is happening? What terrible/hilarious thing will happen if the character fails?
- E.g. "Kiki accidentally turned on every ride at the fairground and now the whole park is spinning out of control!"
- E.g. "Our Gav opened the wrong door and now a hundred tiny robots are marching into the school hall!"
- E.g. "Kiki's sandcastle started growing and it won't stop — it's already taller than the lifeguard tower!"
- CRAYON TEST: Every blurb must mention at least ONE thing a child can clearly picture colouring (e.g. a giant wobbly tower, a bouncy trampoline, a huge splashing puddle, a wobbly bridge)
- NO ABSTRACT NOUNS: NEVER use words like "wonder", "harmony", "discovery", "beauty", "perspective", "balance", "chaos" or "the unexpected" — these are uncolourable and meaningless to a child
- ACTION-OBJECT RULE: The blurb must contain a clear silly problem a child can picture. BAD: "Milo learns about friendship." GOOD: "Milo is stuck inside a giant bouncy ball and cannot get out!"
- BANNED WORDS: NEVER use these words in a blurb: "wonder", "discovery", "journey", "magic", "everyday", "heart", "harmony", "balance", "perspective", "unseen", "hidden", "small things", "big feelings"
- PHYSICAL COMEDY TEST: The blurb must describe a physical mishap — getting stuck, swapping colours, floating away, breaking physics. If nothing is physically happening, rewrite it.
- HALLMARK TEST: If the blurb sounds like a greetings card, it is wrong. If it sounds like a 4-year-old explaining a dream they had, it is correct.
- NO QUESTIONS: NEVER end a blurb with "Can they...?", "Will they...?", "Can [character] help...?" or any question. Questions are weak. State what is happening instead.
- FILLER PHRASE BAN: NEVER use "time to share", "watch out for", "find their way", "learn to", "discover that". These are boring templates.
- CLIFFHANGER ENDING: End with the character in a silly impossible position. BAD: "Can Kiki share the tuft?" GOOD: "Kiki's hair has become a giant nest and three birds have already moved in!"
- SENSORY TEXTURE: Mention something physical and tactile that a child can imagine touching or experiencing. Be inventive and specific to THIS character — never repeat the same type of substance or scenario across blurbs.
- NO COLOURS IN BLURBS: NEVER mention specific colours (purple, pink, yellow, green, blue etc). This is a colouring book — the child decides the colours. Colours in blurbs also confuse the image generator into producing coloured images instead of black and white line art.

*** PITCH QUALITY RULES ***

1. ORIGINALITY: NEVER copy a scenario word-for-word. Adapt it, remix it, make it feel fresh and unique to this character.
2. NUANCED RESOLUTION: The problem should NOT be solved in the obvious way. Instead, a SUPPORTING CHARACTER should suggest a new approach, OR the character should discover something unexpected about the situation. The solution should feel like a team effort or a moment of growth, not just "one big action fixes everything".
3. SETBACK: The want/obstacle/twist must include a real setback — not just "oops." The character tries and FAILS before the twist saves the day.
4. DEVIANCE RULE: Reject any story idea that can be summarised as "Character learns a lesson" or "Character finds a lost toy." Only accept ideas that involve a physical transformation, a law of physics breaking, or a hilarious misunderstanding. The parent should look at the title and think "I have to see how they draw THAT" — not "oh, another helpful character story."

Return ONLY valid JSON. Generate 3 theme PITCHES (no full episodes yet). Here is the exact format:

⚠️ CRITICAL — ABOUT "feature_used": This field records which aspect of the character appears in the story. It does NOT mean the story must BE ABOUT that feature. The story concept comes FIRST — then you note which character trait naturally fits. If no single feature drives the plot, use "general appearance" or "personality". NEVER start by picking a feature and building a story around it. START with a great story concept, THEN fill in feature_used afterwards.

{{
  "character_name": "Example Monster",
  "age_level": "age_5",
  "themes": [
    {{
      "theme_id": "the_great_gravity_mix_up",
      "theme_name": "The Great Gravity Mix-Up",
      "theme_description": "When the gym's gravity experiment goes wrong, everything starts floating and Example Monster must catch everyone before they drift out the windows.",
      "theme_blurb": "Example Monster accidentally switched off gravity and now the whole school is floating towards the ceiling!",
      "feature_used": "big eye",
      "want": "catch all the floating students before they drift out the windows — the gravity experiment was Example Monster's idea so it's their responsibility to fix it",
      "obstacle": "there are too many floating things to track at once and Example Monster keeps grabbing the wrong ones",
      "twist": "realises that if they stand on the roof and look DOWN through the skylight, they can spot the anti-gravity device and switch it off from above"
    }},
    {{
      "theme_id": "the_missing_socks_mystery",
      "theme_name": "The Missing Socks Mystery",
      "theme_description": "Every sock in town has vanished overnight and Example Monster must follow the trail of woolly clues to find the thief.",
      "theme_blurb": "Every single sock in town has vanished and Example Monster just found a woolly trail leading underground!",
      "feature_used": "long arms",
      "want": "find who stole all the socks before the big football match — Example Monster promised the team they'd solve it",
      "obstacle": "long arms keep accidentally knocking over clues and evidence",
      "twist": "uses arms to reach into the tiny mouse hole where the sock-hoarding mice live"
    }},
    {{
      "theme_id": "the_worlds_worst_haircut",
      "theme_name": "The World's Worst Haircut",
      "theme_description": "The new barber is a robot who has gone haywire, giving everyone ridiculous haircuts, and Example Monster must stop it.",
      "theme_blurb": "The robot barber has gone haywire and given the head teacher a mohawk — now it's heading for Example Monster!",
      "feature_used": "spiky head",
      "want": "stop the robot barber before it reaches the school photo — Example Monster accidentally turned it on by pressing the wrong button",
      "obstacle": "the robot keeps chasing Example Monster thinking the spikes are messy hair that needs cutting",
      "twist": "the spikes jam the robot's scissors, causing it to short-circuit and reset"
    }}
  ]
}}

⚠️ CRITICAL: OBSTACLE and TWIST must form ONE coherent cause-and-effect chain.
The obstacle creates a specific problem. The twist must solve THAT EXACT problem — not a different one.
- NEVER introduce a second unrelated problem in the twist
- Test: read the obstacle, then read the twist. Does the twist DIRECTLY fix the obstacle? If not, rewrite.
- BAD: obstacle="coat is too bulky to move fast" → twist="coat blocks the dog" (these are two different problems)
- GOOD: obstacle="coat is too bulky to stack snow blocks" → twist="the puffy coat packs snow tighter when they hug the blocks, making super-strong walls"

*** BANNED STORY PATTERNS — THESE WILL BE REJECTED ***
- "Runaway" anything (runaway cake, runaway pancake, runaway cart, runaway balloon, runaway pet, runaway anything)

*** BANNED SUBSTANCES — IF YOUR STORY CENTRES ON ANY OF THESE, REPLACE IT ***
These substances are overused and produce identical-feeling stories. If the central material or substance of your pitch appears on this list, delete the pitch and write something original:
- Jelly or jelly-like substances
- Bubbles (soap, bath, or otherwise)
- Mud or slime
- Leaves (falling, sticking, or piling)
- Paint or ink splashing
- Sand
- Soup or porridge
- Foam or lather
The test: could this story's central chaos be described using one of the words above? If yes, pick a completely different substance or scenario.
- Hair getting caught/tangled in things
- Carrying a tray/plate and spilling it
- Chasing something that rolled/bounced/flew away
- A bake sale gone wrong
- Paint/ink/colour splashing everywhere
- Something stuck in a tree
If your theme matches ANY of these patterns, DELETE IT and write something original.

*** THE 3 THEMES MUST BE IN 3 DIFFERENT WORLDS ***
Theme 1 must be set in an EVERYDAY location (school, park, shops, home, neighbourhood)
Theme 2 must be set in an UNUSUAL or FANTASTICAL location — examples include underwater city, inside a volcano, shrunk to ant-size, dinosaur era, frozen planet, inside a painting, a world made of music, a floating market. NEVER default to clouds or sky kingdoms — pick something surprising and original each time
Theme 3 must involve a SPECIFIC JOB, EVENT, or MISSION (detective mystery, cooking contest, sports day, rescue mission, science fair, treasure hunt, talent show audition)
No two themes can share the same type of setting, premise, or story structure.

*** CONCEPT SIMPLICITY BY AGE — THIS OVERRIDES EVERYTHING ABOVE FOR YOUNG AGES ***

FOR AGES UNDER_3 AND AGE_3 (toddlers):
🚨 SIMPLE CONCEPTS ONLY. A toddler cannot understand abstract worlds, magic systems, or multi-step logic.

WHAT A TODDLER CAN UNDERSTAND:
- Big thing in small space (or small thing in big space)
- Something keeps falling down / running away / getting lost
- Trying to reach something that's too high / too far
- Making a mess and trying to clean it up
- An animal that makes a funny noise
- Something that won't stop bouncing / rolling / growing
- Hiding and finding (peek-a-boo logic)
- Trying to give someone something but it keeps going wrong

WHAT A TODDLER CANNOT UNDERSTAND:
- Magic kingdoms, enchanted worlds, alternate dimensions
- "Hair as a danger warning system" or any feature-as-signal concept
- Characters with abstract motivations ("save the kingdom", "restore the balance")
- Multi-step cause-and-effect chains (A causes B which triggers C)
- Named royal characters (queens, kings) in fantasy settings
- Any concept that requires EXPLAINING to a toddler before they can follow the story
- Recipes, potions, spells, prophecies, missions

TEST: Describe the story concept in ONE sentence using only words a 3-year-old knows. If you can't, the concept is too complex.
- GOOD: "Dog tries to catch a ball but it keeps bouncing away" ✅
- GOOD: "Monster is too loud and scares all the birds away" ✅
- GOOD: "Cat tries to fit in a box but the box is too small" ✅
- BAD: "Dog enters a bubble kingdom where ears create ripples that pop the recipe bubble" ❌
- BAD: "Character's hair bounces as a warning signal in a glowing mushroom cave" ❌

FOR THIS AGE, OVERRIDE THE "3 DIFFERENT WORLDS" RULE ABOVE:
- Theme 1: EVERYDAY location (home, park, garden, shops, bath time, bed time, meal time)
- Theme 2: SLIGHTLY magical version of an everyday location (the park at night, a puddle that's deeper than expected, a cupboard that's bigger inside, a sandpit with something buried in it) — NOT a fantasy kingdom
- Theme 3: A simple event or activity (bath time, dinner time, bedtime, a walk, a picnic, a trip to the shops, playing in the garden, going to the playground)

FOR AGE_4:
Age 4 stories should be only a SMALL step up from age 3 — not a giant leap. Think Gruffalo, Room on the Broom — physical, funny, and warm.
- ONE simple concept per story. If it takes more than one sentence to explain, it's too complex.
- Maximum 2-3 named characters total (main character + 1-2 others)
- ONE problem, ONE solution. No multi-step engineering or abstract logic.
- The resolution must be ONE physical action a 4-year-old can understand and copy.
- Fantasy is OK but keep it to ONE magical element — not a whole civilisation with its own rules, deadlines, and systems.
- Each page should have ONE clear thing happening — not multiple plot points.
- The story should feel like it's one step above a toddler book, NOT a mini novel.
The WANT must be something a 4-year-old experiences: wanting a toy, wanting to win, wanting to help a friend, wanting to fix something they broke, wanting to not get in trouble.

*** VISUAL VARIETY — THIS IS A COLOURING BOOK ***

We are a COLOURING PAGE business. A child colours each page. If multiple pages show the same location from the same angle with the same objects, the child is colouring the same picture repeatedly. That is a bad experience.

RULE: No more than 2 out of 5 episodes should share the same location. The story should move through at least 2-3 visually distinct settings.
CRITICAL LOCATION LOGIC: Every time the character moves to a new location, there must be a clear reason stated in the story text. The character cannot simply "appear" somewhere new. If episode 1 is in the garden, episode 2 must explain WHY they moved inside. Location changes must follow cause and effect — never jump locations without a narrative bridge.
- Design the WANT/OBSTACLE/TWIST so the plot naturally takes characters to different places
- If a story must stay in one broad area, make sure each episode shows a distinctly different PART of that area with different objects and surroundings
- Every page a child colours should feel like a NEW picture, not a repeat of the last one

FOR AGES UNDER_3 AND AGE_3: Each episode SHOULD be in a completely different location. At this age the REPEATING PATTERN (the phrase, the sound, the character's action) holds the story together — not the setting. Real toddler books jump between locations freely because kids follow the pattern, not the geography. This gives the child 5 totally different pictures to colour.

*** NUMBERS AND COUNTS — NEVER USE THEM ***
NEVER include specific numbers for character features in theme names, blurbs, descriptions, want, obstacle, or twist.
- Say "Bloop's tiny fingers" NOT "Bloop's eight tiny fingers"
- Say "Gerald's knobbly knees" NOT "Gerald's two knobbly knees"
- Say "Bloop's enormous eye" NOT "Bloop's one enormous eye"
- Say "the dog's legs" NOT "the dog's three legs"
No exceptions. The image generator draws from the character description — the story text never needs to repeat counts. This rule exists because getting a number wrong destroys a parent's trust in the product.

*** FINAL QUALITY CHECK BEFORE GENERATING ***
For each theme, ask yourself:
1. "Would a parent read this blurb and think 'wow, this is clever and unique to my child'?" — if the answer is "this could be about any character", throw it away and start again.
2. "Does the want/obstacle/twist chain make LOGICAL sense?" — read them as one sentence: "[character] wants [want] but [obstacle] until [twist]". If it sounds forced, contrived, or silly in a bad way, rewrite it.
3. "Is this story ACTUALLY interesting?" — would a real children's book author be proud of this idea, or is it lazy filler? Be honest. If a 5-year-old would say "that's boring" after hearing the premise, it IS boring.

NOW generate 3 theme PITCHES for {character_name}. Each theme must feel like a completely different story — different setting, different type of problem, different tone. The character's appearance and traits should be woven naturally into each pitch. Include theme_id, theme_name, theme_description, theme_blurb, feature_used, want, obstacle, and twist. Do NOT generate full episodes — just the pitches. Return ONLY the JSON, no other text.'''

    # ── Call Gemini ──
    start = time.time()
    print(f"[GEMINI-PITCH] World seeds injected: {seeds}")

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=PITCH_SYSTEM_PROMPT,
            response_mime_type="application/json",
            temperature=0.9,  # Higher than story writing — pitches need more creativity
            thinking_config=types.ThinkingConfig(
                thinking_level="MEDIUM"  # More reasoning for quality checks
            ),
        ),
    )

    elapsed = time.time() - start

    # ── Parse response ──
    try:
        pitches = json.loads(response.text)
    except json.JSONDecodeError:
        text = response.text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1] if "\n" in text else text[3:]
        if text.endswith("```"):
            text = text[:-3]
        pitches = json.loads(text.strip())

    # Validate structure
    if "themes" not in pitches:
        raise ValueError(f"Gemini pitch response missing 'themes' key: {list(pitches.keys())}")

    themes = pitches["themes"]
    if len(themes) < 3:
        raise ValueError(f"Expected 3 themes, got {len(themes)}")

    # Ensure top-level fields are set
    pitches["character_name"] = character_name
    pitches["age_level"] = age_level

    # Validate each theme has required fields and strip unexpected keys
    allowed_fields = {"theme_id", "theme_name", "theme_description", "theme_blurb",
                      "feature_used", "want", "obstacle", "twist", "setup"}
    required_fields = ["theme_id", "theme_name", "theme_description", "theme_blurb",
                       "feature_used", "want", "obstacle", "twist"]
    for i, theme in enumerate(themes):
        missing = [f for f in required_fields if not theme.get(f)]
        if missing:
            print(f"[GEMINI-PITCH] WARNING: Theme {i+1} missing fields: {missing}")
        # Strip any keys Gemini invented that aren't in our schema
        extra_keys = [k for k in theme if k not in allowed_fields]
        for k in extra_keys:
            del theme[k]
        if extra_keys:
            print(f"[GEMINI-PITCH] Stripped unexpected keys from theme {i+1}: {extra_keys}")

    # Log features used for variety check
    features = [t.get("feature_used", "?") for t in themes]
    print(f"[GEMINI-PITCH] Generated 3 pitches for '{character_name}' ({age_level}) in {elapsed:.1f}s")
    print(f"[GEMINI-PITCH] Features used: {features}")

    return pitches

# ──────────────────────────────────────────────
# TEST CASES
# ──────────────────────────────────────────────

SPARKLE_DESC = "A small girl with a brown bob haircut, big green eyes, rosy pink cheeks, wearing a mint green t-shirt with a green clover shape on it, a grey chevron-patterned skirt, and grey shoes. She has a wide happy smile and an energetic, joyful personality."

TEST_CASES = [
    {
        "name": "age4_Silly",
        "character_name": "Sparkle",
        "character_description": SPARKLE_DESC,
        "theme_name": "The Biggest Welcome Ever",
        "want": "Sparkle wants to welcome a new, scared classmate called Milo through the classroom door before register time",
        "obstacle": "Sparkle's big enthusiastic arms keep accidentally sweeping up the wrong things — the coat rack, a stack of books, the class goldfish bowl",
        "twist": "Milo starts giggling at the chaos and pushes the door open to help Sparkle untangle from the coat rack — Sparkle's accidental silliness was the welcome that actually worked",
        "age_level": "age_4",
        "writing_style": "Silly",
        "life_lesson": "Friendship",
    },
    {
        "name": "age6_Rhyming",
        "character_name": "Sparkle",
        "character_description": SPARKLE_DESC,
        "theme_name": "The Biggest Welcome Ever",
        "want": "Sparkle wants to welcome a new, scared classmate called Milo through the classroom door before register time",
        "obstacle": "Sparkle's big enthusiastic arms keep accidentally sweeping up the wrong things — the coat rack, a stack of books, the class goldfish bowl",
        "twist": "Milo starts giggling at the chaos and pushes the door open to help Sparkle untangle from the coat rack — Sparkle's accidental silliness was the welcome that actually worked",
        "age_level": "age_6",
        "writing_style": "Rhyming",
        "life_lesson": "Friendship",
    },
    {
        "name": "age9_Suspenseful",
        "character_name": "Sparkle",
        "character_description": SPARKLE_DESC,
        "theme_name": "The Biggest Welcome Ever",
        "want": "Sparkle wants to welcome a new, scared classmate called Milo through the classroom door before register time",
        "obstacle": "Sparkle's big enthusiastic arms keep accidentally sweeping up the wrong things — the coat rack, a stack of books, the class goldfish bowl",
        "twist": "Milo starts giggling at the chaos and pushes the door open to help Sparkle untangle from the coat rack — Sparkle's accidental silliness was the welcome that actually worked",
        "age_level": "age_9",
        "writing_style": "Suspenseful",
        "life_lesson": "Friendship",
    },
    {
        "name": "age5_Custom_Birthday",
        "character_name": "Sparkle",
        "character_description": SPARKLE_DESC,
        "custom_theme": "It's Sparkle's 5th birthday and she's having a party at the park with all her friends",
        "age_level": "age_5",
        "writing_style": "Standard",
        "life_lesson": "Sharing",
    },
    {
        "name": "age7_DualChar_Adventurous",
        "character_name": "Sparkle",
        "character_description": SPARKLE_DESC,
        "second_character_name": "Clover",
        "second_character_description": "A chubby orange tabby cat with bright blue eyes, a curly tail, and a tiny red bandana around his neck. He walks on two legs and has a mischievous grin.",
        "theme_name": "The Biggest Welcome Ever",
        "want": "Sparkle wants to welcome a new, scared classmate called Milo through the classroom door before register time",
        "obstacle": "Sparkle's big enthusiastic arms keep accidentally sweeping up the wrong things — the coat rack, a stack of books, the class goldfish bowl",
        "twist": "Milo starts giggling at the chaos and pushes the door open to help Sparkle untangle from the coat rack — Sparkle's accidental silliness was the welcome that actually worked",
        "age_level": "age_7",
        "writing_style": "Adventurous",
        "life_lesson": "Friendship",
    },
    {
        "name": "under3_Gentle",
        "character_name": "Sparkle",
        "character_description": SPARKLE_DESC,
        "theme_name": "The Biggest Welcome Ever",
        "want": "Sparkle wants to welcome a new, scared classmate called Milo through the classroom door before register time",
        "obstacle": "Sparkle's big enthusiastic arms keep accidentally sweeping up the wrong things — the coat rack, a stack of books, the class goldfish bowl",
        "twist": "Milo starts giggling at the chaos and pushes the door open to help Sparkle untangle from the coat rack — Sparkle's accidental silliness was the welcome that actually worked",
        "age_level": "under_3",
        "writing_style": "Gentle",
    },
]


# ──────────────────────────────────────────────
# MAIN (standalone test)
# ──────────────────────────────────────────────

if __name__ == "__main__":
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
    if not GEMINI_API_KEY:
        print("ERROR: Set your API key first:")
        print("  export GEMINI_API_KEY='your-key-here'")
        exit(1)

    OUTPUT_DIR = os.path.expanduser("~/Desktop/gemini_story_test")
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("=" * 60)
    print("Little Lines — Gemini 3 Flash Story Engine Test")
    print("=" * 60)

    for tc in TEST_CASES:
        tier, ep_count = get_tier(tc.get("age_level", "age_5"))
        print(f"\n{'─' * 50}")
        print(f"Test: {tc['name']}")
        print(f"Age: {tc.get('age_level')} | Style: {tc.get('writing_style', 'Standard')} | Tier: {tier} ({ep_count} eps)")
        if tc.get("custom_theme"):
            print(f"Custom theme: {tc['custom_theme'][:60]}...")
        if tc.get("second_character_name"):
            print(f"Second character: {tc['second_character_name']}")
        print(f"{'─' * 50}")

        try:
            story = generate_story_gemini(
                character_name=tc["character_name"],
                character_description=tc["character_description"],
                theme_name=tc.get("theme_name", ""),
                theme_description=tc.get("theme_description", ""),
                theme_blurb=tc.get("theme_blurb", ""),
                feature_used=tc.get("feature_used", ""),
                want=tc.get("want", ""),
                obstacle=tc.get("obstacle", ""),
                twist=tc.get("twist", ""),
                age_level=tc.get("age_level", "age_5"),
                writing_style=tc.get("writing_style"),
                life_lesson=tc.get("life_lesson"),
                custom_theme=tc.get("custom_theme"),
                second_character_name=tc.get("second_character_name"),
                second_character_description=tc.get("second_character_description"),
                api_key=GEMINI_API_KEY,
            )

            # Save JSON
            filepath = os.path.join(OUTPUT_DIR, f"{tc['name']}.json")
            with open(filepath, "w") as f:
                json.dump(story, f, indent=2)

            # Print summary
            episodes = story.get("episodes", [])
            print(f"Title: {story.get('story_title', 'No title')}")
            print(f"Episodes: {len(episodes)}")

            for ep in episodes:
                text = ep.get("story_text", "")
                words = len(text.split())
                scene_words = len(ep.get("scene_description", "").split())
                print(f"  Ep {ep.get('episode_num')}: [{ep.get('character_emotion', '?')}] {ep.get('title', '?')} ({words}w, scene:{scene_words}w)")

            print(f"Saved: {filepath}")

        except Exception as e:
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()

        time.sleep(2)

    print(f"\n{'=' * 60}")
    print(f"All tests complete! Results in: {OUTPUT_DIR}")
    print(f"{'=' * 60}")
    os.system(f"open {OUTPUT_DIR}")
