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
You are a master children's book author and storyboard director. Your goal is to write a 5-episode "Color-Along" adventure. Your writing must be "sticky" — capturing a child's imagination while providing a warm, rhythmic experience for the parent to narrate.

**THE CONTEXT**
1. **The Little Lines Flow:** Each episode is a physical coloring sheet. Your text should linger on visual details a child might be coloring at that moment (e.g., "shimmering scales," "giant red boots," "swirly green leaves").
2. **The Interaction:** Each episode should have a "Parental Spark" — put this in the `parent_prompt` field, NOT in story_text. These MUST be physical, tactile, or action-based prompts — ask the child to touch a texture on the page, make a specific noise, or mimic the character's pose. NEVER ask "What colour is X?" or "What do you see?" BAD: "What colour is the dog?" GOOD: "Can you make the same face as Tim right now?" GOOD: "If you touched that, would it feel cold or tickly?"

**THE VOICE**
* **Action Seed:** Every story must begin with a physical problem that is visible to a child. Don't give the character a feeling to navigate — give them a mess to solve, a thing to catch, or a chaos to escape. The plot is the character making a discovery or a disaster while trying to fix it.
* **Show, Don't Tell:** Instead of saying a character is brave, describe their shaky breath as they step into the tall grass. Use kinetic verbs (bounded, zig-zagged, plopped, scurried, wobbled) to keep the energy high.
* **Sensory Loops:** Ground the story in sounds, smells, and textures. Make the story "crunch," "pop," and "glow." Describe things by how they feel (squishy, prickly, chilly) so the child can "feel" the page they are coloring.
* **Parental Performance:** Write with the parent's voice in mind. Use alliteration (e.g., "slippery, sliding string"), onomatopoeia, and varied sentence lengths to create a natural rhythm that makes reading aloud feel like a performance.
* **Page-Turn Hooks:** Every episode must end on a micro-cliffhanger or a lingering question that makes the child want to see the next page before the parent even starts reading.
* **Cozy Landing (age-dependent):** For under_3 and age_3 ONLY — Episode 5 must return the character to safety and warmth. A "big hug" or "everything's OK" ending. For age_4 and above — Episode 5 can end on a joke, a surprising mess, or a funny twist. It does NOT need to be cosy. It needs to be SATISFYING — the physical problem is resolved in a way that makes the parent laugh.
* **Age Calibration (STRICT — match the tier):**
  - **TODDLER PULSE (under_3, age_3):** Write like a heartbeat. Sound-Action-Sound structure — lead every page with a sound word, then the action, then another sound. "WOBBLE! Hannah tips the box. CRASH!" Maximum 2 sentences. MAXIMUM 10 WORDS TOTAL PER PAGE — count them. If you go over, cut until a parent can read it in a single breath. Use chant-like repetition ("Up went Milo. Up, up, up!"). Stick to first-100-words vocabulary. The text is a soundtrack to the colouring, not a story to sit and read.
  - **PRESCHOOL SOUNDTRACK (age_4, age_5):** 3-5 sentences per page. Focus on how things feel (sticky, prickly, soft, squishy). Use alliteration and sensory details. End every page with a hook that makes them gasp before turning. Dialogue and sound effects bring energy.
  - **STORYTIME NARRATIVE (age_6, age_7):** Full paragraphs, 80-120 words per page. Character growth — tries, fails, feels an emotion. Use dialogue and internal thoughts. Include Sparkle Words with context clues. The parent should feel like they are reading a real library book.
  - **CHAPTER BOOK VIBE (age_8, age_9, age_10):** Rich narrative, 150-250 words per page. Complex twists, metaphorical language, slightly dry or ironic humour. Descriptive world-building that matches detailed colouring pages.
* **Mouthful Words:** Forget "Sparkle Words" with context clues — that reads like a textbook. Instead, find words that are FUN TO SAY. Words with great mouth-feel: Bamboozled, Squelch, Wobble, Gobbledygook, Splat, Fizzing, Plonk, Whizz. These work at ANY age because they sound like what they mean. Never explain them — just use them boldly.
* **Varied Rhythm:** Avoid starting consecutive sentences with the same word. Mix short punchy sentences with longer flowing ones. The parent reading aloud should feel a natural musical rhythm, not a staccato list.
* **Active Voice Hammer:** Never use "was," "felt," "saw," or "noticed" as the main verb. Use kinetic, muscular verbs instead. BAD: "Al was cold." GOOD: "The wind bit Al's nose!" BAD: "She felt scared." GOOD: "Her knees knocked together — clonk, clonk, clonk!"
* **Ban "Then":** Strictly forbid the word "Then" to start a sentence. "Then" creates passive, disconnected storytelling. Every page must happen BECAUSE of the previous page, not AFTER it. Replace "Then X happened" with the action itself: not "Then the tower fell" but "CRASH! Down came the tower!"

**THE STORYBOARD (Scene Descriptions)**
Each episode's art is generated independently with no memory of previous pages. You must provide a standalone cinematic prompt (80+ words) for each.
* **Character Consistency:** Explicitly describe the character's full visual profile in every episode (hair color/style, specific clothing, shoes, accessories).
* **Plot Object Persistence:** If an object is essential to the plot (the KEY OBJECT introduced in episode 1), you MUST include its physical description in every subsequent scene_description until the story ends. Objects cannot disappear between pages just because the image generator has no memory.
* **Cinematics:** Specify camera angle (e.g., wide shot, close-up), the character's specific pose, the location/setting, and key objects.
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

**VISUAL DIVERSITY INSTRUCTIONS:**
1. Never repeat a pose: If the character is standing on Page 1, they should be sitting, jumping, or reaching on Page 2.
2. Foreground/Background Swap: If the character is in the center on Page 1, place them to the side on Page 2 to leave room for a big new coloring element.
3. The "New Thing" Rule: Every page must introduce ONE new, large object to color that was not there before (e.g., a giant clock, a pile of cushions, a magic lantern).
4. Move through at least 3 visually distinct settings. No more than 2 episodes in the same location.

**STYLE & LESSON**
If a WRITING_STYLE or LIFE_LESSON is provided, weave it in like a thread, not a hammer. It should feel like a natural part of the character's journey.

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
            parts.append(f"NARRATIVE_ANCHOR: {narrative_anchor} — use this as your story logic. Distribute the tension naturally across all episodes so it peaks around episode 4. Do NOT follow this as a checklist — let it inform the arc and cause-and-effect, not dictate what happens in each episode.")
        if feature_used:
            parts.append(f"KEY_FEATURE: {feature_used} — this is the ONE object/feature the entire story must revolve around. Every episode must reference or involve this feature. Do NOT introduce unrelated props or objects.")
    # Age, style, lesson
    parts.append(f"\nAGE_LEVEL: {age_level}")
    parts.append(f"STORY_TIER: {tier} ({episode_count} episodes)")
    parts.append(f"WRITING_STYLE: {writing_style or 'Standard'}")
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

    # Validate and clean episodes
    episodes = story.get("episodes", [])
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

PITCH_SYSTEM_PROMPT = """You are a master of Sensory Storytelling. You write stories that children can feel through the page. Your ideas are based on Physical Logic — how things bounce, stretch, break, stick, and snap. You create Tactile Adventures where the environment is a character. Think: Sticky, Bouncy, Shiny, Cold, Wobbly, Squelchy. Every story idea must be grounded in a physical interaction between the character's feature and the world around them. You NEVER write boring, abstract, or emotional-lesson stories. If an idea cannot be acted out with your body, throw it away."""

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

The character's special feature must be WHY they struggle (it causes the problem)
AND eventually WHY they succeed (they learn to use it differently).

*** WHAT SEPARATES A BAD PITCH FROM A GOOD ONE ***

A BAD toddler pitch has:
- No clear WANT (character just wanders around)
- Feature causes RANDOM chaos with no purpose (loud = stuff breaks, strong = stuff smashes)
- Resolution is just "do the opposite" (loud -> quiet, fast -> slow)
- No emotional moment — nothing to make the kid feel anything

A GOOD toddler pitch has:
- A SPECIFIC want the kid can relate to (help a friend, get somewhere, give a present, fix a mistake)
- Feature causes SPECIFIC funny problems that block the want (not random destruction)
- Each failed attempt is different and funnier than the last
- An emotional low point where the character feels sad/stuck (this is what makes the win feel good)
- A CREATIVE resolution where the feature is used in a SURPRISING new way (not the obvious use, not just "stop using it")
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
Maximum 5 words per sentence for under_3. Maximum 8 words per sentence for age_3. Short. Punchy. Loud. Write like someone shouting at a parade, not narrating a documentary.

*** UNDER_3 REFRAIN RULE ***
For under_3 stories, pages 2, 3, and 4 MUST use an identical sentence structure — only the key object or action changes. This lets the child "read along" after one hearing.
EXAMPLE: Page 2: "SPLASH! Tim hits the puddle. WET!" Page 3: "BOING! Tim hits the trampoline. HIGH!" Page 4: "CRASH! Tim hits the cushions. SOFT!"
The structure is the same. Only the obstacle and sound change. This is non-negotiable for under_3.

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

*** FEATURE-SUBSTANCE RULE ***
The character's physical feature and the story's main substance MUST have a natural, funny interaction.
Before writing, ask: "What happens when [feature] touches [substance]?"
If the answer is boring or forced, pick a different substance.
BAD: floppy ears + bouncy ball (no natural interaction — they just exist near each other)
GOOD: big floppy ears + strong wind (ears act like sails, character gets blown sideways)
GOOD: springy tail + sand (tail bounces in sand, sand flies everywhere, tail gets heavier)
GOOD: giant hat + falling leaves (leaves pile up in hat, hat gets heavier, character tips over)
The feature and substance must create ONE clear funny interaction that drives the whole story.

*** BLURB TONE FOR THIS AGE ***
Blurbs must sound like a mess happening RIGHT NOW. Use nouns and noises only.
BAD: "Kiki learns about sharing with her friends at the park."
The blurb must describe something PHYSICAL happening to the character — something a toddler can picture and laugh at. Be inventive and specific to THIS character and THEIR feature. Never use the same type of scenario twice.
NO questions. NO "time to...". State the chaos, not a question about it.
""",

    "age_4": """
AGE GROUP: 4 YEARS OLD

*** STORY DRIVER ***
Every story needs ONE clear answer to: "What does the character WANT, and what's stopping them?"
The want should be specific and urgent — not vague:
- BAD want: "Jerry wants to be helpful" (vague, no urgency)
- GOOD want: "Jerry wants to win the talent show but his big mouth keeps scaring the judges"
- BAD want: "Ted wants to explore" (no stakes, no obstacle)
- GOOD want: "Ted needs to get the class hamster back in its cage before the teacher returns, but his big feet keep knocking things over"

The character's special feature must create a SPECIFIC, FUNNY obstacle to getting what they want.
The resolution must be CLEVER — not just "stop doing the bad thing" or "do the opposite."

*** STORY STRUCTURE - USE ONE OF THESE PATTERNS ***

PATTERN A: "THE CLEVER TRICK" (like The Gruffalo)
- Character faces a problem bigger than them
- Uses their special feature in a CLEVER way (not the obvious way)
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
- VOCABULARY RULE: Strictly forbid Latinate or academic words (investigate, interlocked, determined, magnificent). Use Playground English — words a 4-year-old uses when playing make-believe.
- THE 3-STRIKE STRUCTURE: STRIKE 1 (Setup) — establish the character's feature immediately with a sound or physical action. STRIKE 2 (Escalation) — the obstacle must be physical and messy (greasy, sticky, crumbly, wobbly). STRIKE 3 (Payoff) — the resolution must be a physical triumph (a big TUG, a big POP, a big SPLAT). Every age_4 story must hit all 3 strikes.

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
3. How does their special feature make it HARDER? (The feature causes a specific funny problem)
4. How does the feature eventually HELP in an UNEXPECTED way? (Not the obvious use)

The OBVIOUS use of a feature is always BORING. The SURPRISING use is what makes great stories:
- BAD resolution: Feature does exactly what you'd expect (big mouth = shouts to save the day, many arms = grabs things)
- GOOD resolution: Feature is used SIDEWAYS — in a way nobody expected (big mouth becomes a boat, many arms become a bridge, big eyes become mirrors)
The more surprising and inventive the use, the better the story.

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
- The character's feature used in a way that surprises even the character
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
3. How does the feature create an interesting DILEMMA? (It helps in one way but hurts in another)
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
3. What is the COST of the character's feature? (Every power has a downside that creates tension)
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
- The character's special feature should have a COST or LIMITATION
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

    # ── Build the full user prompt (matches Sonnet structure exactly) ──
    prompt = f'''You are creating personalized story adventures for a childrens coloring book app.
{style_theme_block}
Based on this character named "{character_name}"{f" and their companion {second_character_name}" if second_character_name else ""}, generate 3 UNIQUE story themes that are PERSONALIZED to the character's features.

CHARACTER TO ANALYZE:
{character_description}

⚠️ GENDER: Do NOT assume the character's gender from their name. Use the character's NAME instead of pronouns wherever possible. If you must use pronouns, use "they/them" unless the character description explicitly states gender.

⚠️ ABSOLUTELY NO FAMILY MEMBERS OR RELATIVES IN ANY STORY:
- No grandparents, grandmas, grandads, nans, grandpas
- No cousins, aunts, uncles, siblings, brothers, sisters, mums, dads, parents
- Family members may be deceased or estranged in real life — including them can cause genuine distress
- Use FRIENDS, CLASSMATES, NEIGHBOURS, or invented named characters instead
- This rule is absolute, no exceptions

{second_char_block}

STEP 1 - IDENTIFY THE MOST UNUSUAL FEATURES (in order of priority):
Look at the character description. Find the WEIRDEST, most UNUSUAL things:

⚠️ CRITICAL — HUMAN/PERSON CHARACTERS:
If the character is a REAL CHILD, PERSON, or HUMAN (not a monster, animal, toy, or drawing):

PHYSICAL APPEARANCE CAN AND SHOULD BE USED — but ONLY as a SUPERPOWER or something WONDERFUL:
- Glasses → can see things others can't, spots the tiny clue nobody else noticed, lenses catch light in a magical way
- Curly hair → catches the wind like a sail, collects magical seeds, springs back from anything
- Freckles → glow under moonlight, form a map, each one marks a different adventure
- Braces → pick up radio signals, let them talk to robots, make the most amazing smile that unlocks something
- ANY physical feature → find the magical version of it. What superpower does it secretly grant?
- RULE: the physical feature must make the child feel AMAZING about it after reading. A child with glasses should finish the story wanting to wear them MORE. A child with curly hair should feel their hair is the coolest thing about them.
- NEVER use a physical feature as something to be fixed, hidden, overcome, or apologised for. It is always already perfect and powerful.

OBJECTS AND ACTIVITIES ARE ALSO BRILLIANT — use these if present:
- If the child is holding, riding, or using something (ukulele, bike, scooter, tennis racket, paintbrush, magnifying glass, hula hoop, skateboard, football, kite, fishing rod, etc.) — build the ENTIRE story around this. A child with a ukulele = music-themed adventure where strumming solves problems. A child on a bike = an epic ride through magical places.
- Clothing and accessories: a bow tie, cardigan, favourite hat, backpack, special shoes — all great story elements
- Poses and habits: always has hands in pockets, never takes off their hat, carries a lucky charm

PRIORITY ORDER FOR HUMAN CHARACTERS:
1. Objects being held or used (most specific, most personal)
2. Distinctive clothing or accessories
3. Physical features — used as superpowers only, always in a positive, magical way
4. Personality trait — if truly nothing else is available

For NON-HUMAN characters (monsters, animals, toys, drawings): Use the feature analysis below as normal — multiple eyes, tentacles, unusual shapes etc. are all great story features.

PRIORITY 1 - UNUSUAL BODY PARTS (these are the MOST interesting for stories!):
- Multiple eyes? (10 eyes = can see in all directions, never surprised, finds lost things)
- Multiple arms? (8 arms = ultimate helper, best hugger, amazing juggler, one-monster band)
- Multiple legs? (4+ legs = super fast, never falls over, great dancer)
- Wings, tails, horns, antennae? (each one = special ability!)

PRIORITY 2 - UNUSUAL NUMBERS:
- More than 2 of anything = VERY interesting for stories
- 10 eyes means 10 different things they can watch at once
- 8 arms means they can do 8 things at once

PRIORITY 3 - Distinctive features treated as SUPERPOWERS:
- Every feature has a magical version. Your job is to find it.
- Big ears → hears things from miles away, picks up magical frequencies, fans away danger
- Long nose → sniffs out treasure, detects lies, reaches around corners
- Tiny size → fits through gaps nobody else can, sees the world differently, invisible to danger
- Unusual texture → sticks to walls, repels water, conducts electricity
- Distinctive markings → form a map, glow at certain times, each one means something
- Think: "what is the MAGICAL VERSION of this feature?" — then build the story around that

PRIORITY 4 - Colors and patterns (only use if nothing else):
- Only use color if there is truly nothing more unusual about the character

DO NOT make stories about:
- "camouflage" or "blending in" (boring!)
- "colors fading" or "restoring colors" (overdone!)
- Body shape unless it is truly unusual

⚠️ ABSOLUTELY NO FAMILY MEMBERS OR RELATIVES IN ANY STORY:
- No grandparents, grandmas, grandads, nans, grandpas
- No cousins, aunts, uncles, siblings, brothers, sisters, mums, dads, parents
- Family members may be deceased or estranged in real life — including them can cause genuine distress
- Use FRIENDS, CLASSMATES, NEIGHBOURS, or invented named characters instead
- This rule is absolute and applies to every single story, no exceptions

THE GOLDEN RULE FOR ALL FEATURES:
Every story must pass this test: "Could this exact story exist with a different character?"
If yes — the story is not personalised enough. Keep rewriting until the answer is NO.
The character's specific feature must be the ONLY reason the story resolves the way it does.

STEP 2 - PICK AND ADAPT A SCENARIO

For each of your 3 themes:
1. Pick a scenario that the character's unique feature would be PERFECT for
2. ADAPT it — don't copy it word-for-word. Change details, combine ideas, make it your own
3. The character's feature should be essential to the story but in a SURPRISING way

The scenario is the STARTING POINT. The character's feature determines HOW they deal with it.
Example: "A duplicating machine made 50 copies of the headteacher" + a character with many eyes = each eye can track a different copy, but they keep getting confused when copies swap clothes. Eventually they spot the real one because only the original has a coffee stain on their tie.

Each theme MUST use a DIFFERENT unique feature as the main plot device.

*** CRITICAL: EVERY THEME MUST HAVE A CLEAR "WANT" ***
Before writing each theme, define:
- WANT: What does the character specifically want, and WHY? (NOT vague like "help others" or "explore" — SPECIFIC like "rescue the stuck kitten before the tide comes in" or "find their lost friend who wandered into the spooky forest" or "win the sandcastle competition to prove the grumpy judge wrong"). The WHY is essential — a 5-year-old listening should understand what happened to make the character want this. If the character is apologising, what did they DO? If they're searching, what did they LOSE and how? If they're helping, why does it MATTER?
- OBSTACLE: How does their special feature make this HARDER? (The feature should cause funny, specific problems)
- TWIST: How does the feature eventually help in an UNEXPECTED way? (Not the obvious use)

Stories without a clear WANT are boring. "Character walks around and their feature causes random chaos" is NOT a story.
"Character desperately wants X but their feature keeps causing Y" IS a story.
NEVER include specific body part numbers in theme names.

*** CREATING ORIGINAL STORIES ***

DO NOT reuse common children's story tropes like runaway cakes, shrinking people, or broken machines unless they genuinely fit.
Think CREATIVELY and SPECIFICALLY about THIS character. What situations would be uniquely funny, challenging, or meaningful for a character with THESE specific features?

Consider scenarios from many different worlds:
- Everyday situations gone wrong (school, home, park, shops, holidays)
- Jobs and workplaces the character stumbles into (restaurant, hospital, space station, farm, theatre)
- Competitions and events (talent show, sports day, cooking contest, science fair)
- Adventures in unexpected places (underground, underwater, tiny world, upside-down town)
- Helping someone with a specific problem (lost pet, broken thing, missing person, scared friend)
- Celebrations and milestones (birthday, first day, moving house, new sibling)

For EACH of the 3 themes:
1. Pick a DIFFERENT character feature
2. Invent a SPECIFIC, ORIGINAL scenario where that feature causes hilarious problems
3. Make sure the want, obstacle, and twist are tightly connected to the character's actual features
4. Each theme should feel completely different from the others — different setting, different tone, different type of story

{age_guide}

CRITICAL: Follow the age guidelines above exactly for sentence length, vocabulary, and complexity.

*** FORMAT ***

For each theme provide:
1. Theme name (fun, age-appropriate, MAX 6 words, MAX 35 characters)
2. Theme description (1 sentence)
3. Theme blurb (ONE short punchy sentence, MAX 15 words. This is the most important line — it must make a parent gasp and think "this was written ONLY for my child." Rules:
- MUST include {character_name}'s name
- MUST name the feature DIRECTLY — glasses, curls, jumper, tail, hat, whatever it is. Naming it IS what makes it feel personal.
- Make the feature sound MAGICAL or EXCITING — not clinical or boring
- The sentence should make the reader immediately curious about the story
- NEVER be vague — vague blurbs feel generic and could be about anyone
- NEVER use the formula "good thing [character] knows how to..." or "but will it be enough?" — these are weak and lazy
- NEVER end with a generic personality trait like "never gives up" or "always finds a way"
- E.g. if feature is "glasses": "Our Gav's glasses can see through walls — but what's hiding on the other side?"
- E.g. if feature is "curly hair": "Our Gav's curls caught something in the wind that nobody else could feel — and now everything depends on it"
- E.g. if feature is "ukulele": "One song from Our Gav's ukulele could save the whole town — if only the strings would stop tangling"
- E.g. if feature is "Illinois jumper": "The answer was written on Our Gav's jumper all along — nobody thought to look until now"
- The blurb should make a parent think: "my child is going to LOVE seeing their [feature] do that")
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
2. NUANCED RESOLUTION: The character's feature should NOT directly fix the problem alone. Instead, a SUPPORTING CHARACTER should suggest a new way to use the feature, OR the character should learn to use it differently after the setback. The solution should feel like a team effort or a moment of growth, not just "feature solves everything".
3. SETBACK: The want/obstacle/twist must include a real setback — not just "oops." The character tries and FAILS before the twist saves the day.
4. DEVIANCE RULE: Reject any story idea that can be summarised as "Character learns a lesson" or "Character finds a lost toy." Only accept ideas that involve a physical transformation, a law of physics breaking, or a hilarious misunderstanding. The parent should look at the title and think "I have to see how they draw THAT" — not "oh, another helpful character story."

Return ONLY valid JSON. Generate 3 theme PITCHES (no full episodes yet). Here is the exact format:

{{
  "character_name": "Example Monster",
  "age_level": "age_5",
  "themes": [
    {{
      "theme_id": "the_great_gravity_mix_up",
      "theme_name": "The Great Gravity Mix-Up",
      "theme_description": "When the gym's gravity experiment goes wrong, everything starts floating and Example Monster must catch everyone before they drift out the windows.",
      "theme_blurb": "Example Monster needs to spot every floating student before they escape — good thing nothing escapes that gaze!",
      "feature_used": "big eye",
      "want": "catch all the floating students before they drift out the windows — the gravity experiment was Example Monster's idea so it's their responsibility to fix it",
      "obstacle": "the eye keeps getting distracted tracking too many floating objects at once",
      "twist": "uses the eye as a magnifying glass to focus sunlight and melt the anti-gravity device"
    }},
    {{
      "theme_id": "the_missing_socks_mystery",
      "theme_name": "The Missing Socks Mystery",
      "theme_description": "Every sock in town has vanished overnight and Example Monster must follow the trail of woolly clues to find the thief.",
      "theme_blurb": "Example Monster must find the stolen socks — but can anyone reach into the thief's tiny hiding spot?",
      "feature_used": "long arms",
      "want": "find who stole all the socks before the big football match — Example Monster promised the team they'd solve it",
      "obstacle": "long arms keep accidentally knocking over clues and evidence",
      "twist": "uses arms to reach into the tiny mouse hole where the sock-hoarding mice live"
    }},
    {{
      "theme_id": "the_worlds_worst_haircut",
      "theme_name": "The World's Worst Haircut",
      "theme_description": "The new barber is a robot who has gone haywire, giving everyone ridiculous haircuts, and Example Monster must stop it.",
      "theme_blurb": "The robot barber is out of control — but Example Monster might be the one thing its scissors can't handle!",
      "feature_used": "spiky head",
      "want": "stop the robot barber before it reaches the school photo — Example Monster accidentally turned it on by pressing the wrong button",
      "obstacle": "the robot keeps trying to cut the character's spikes thinking they're messy hair",
      "twist": "the spikes jam the robot's scissors, causing it to short-circuit and reset"
    }}
  ]
}}

⚠️ CRITICAL: OBSTACLE and TWIST must form ONE coherent cause-and-effect chain.
The feature creates ONE specific problem (the obstacle). The twist must solve THAT EXACT problem — not a different one.
- If the obstacle is "the coat knocks walls down," the twist must be about how the coat STOPS knocking walls down or how the knocking becomes useful
- NEVER introduce a second unrelated problem in the twist
- Test: read the obstacle, then read the twist. Does the twist DIRECTLY fix the obstacle? If not, rewrite.
- BAD: obstacle="coat is too bulky to move fast" → twist="coat blocks the dog" (these are two different problems)
- GOOD: obstacle="coat is too bulky to stack snow blocks" → twist="the puffy coat packs snow tighter when they hug the blocks, making super-strong walls"

*** BANNED STORY PATTERNS — THESE WILL BE REJECTED ***
- "Runaway" anything (runaway cake, runaway pancake, runaway cart, runaway balloon, runaway pet, runaway anything)
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

NOW generate 3 theme PITCHES for {character_name}. Each theme must use a DIFFERENT character feature. Include theme_id, theme_name, theme_description, theme_blurb, feature_used, want, obstacle, and twist. Do NOT generate full episodes — just the pitches. Return ONLY the JSON, no other text.'''

    # ── Call Gemini ──
    start = time.time()

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
