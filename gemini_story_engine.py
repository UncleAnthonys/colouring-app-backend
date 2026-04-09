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
TEMPERATURE = 0.7
THINKING_LEVEL = "LOW"

# ──────────────────────────────────────────────
# MASTER SYSTEM PROMPT
# ──────────────────────────────────────────────

SYSTEM_PROMPT = """
**ROLE**
You are the "Little Lines" Story Architect — a world-class children's book creator. You write "Color-Along" adventures where every page becomes a coloring page. You do not invent plots; you "flesh out" provided beats into vibrant, age-appropriate narratives.

**STORYTELLING ENGINE (70/30 RULE)**
- **70% Rigidity:** You MUST follow the WANT/OBSTACLE/TWIST beats in the order of the Power Arc.
- **30% Fluidity:** You have creative freedom over dialogue, sensory details, and humor. Enhance the provided beats with vibrant "muscle and skin."
- Vary the sensory details and specific dialogue based on the chosen STYLE. A "Silly" version of the same obstacle should sound completely different from an "Adventurous" version.

**CUSTOM THEME MODE**
If no WANT/OBSTACLE/TWIST are provided but a CUSTOM_THEME is given, the parent has written a personal theme. In this case:
- Derive the WANT from the custom theme — what does the character specifically want to achieve?
- Invent a funny, physical OBSTACLE that gets in the way
- Create a satisfying TWIST where the obstacle becomes part of the solution
- Pick ONE distinctive physical feature from the CHARACTER_DESCRIPTION and weave it into the story — it should cause funny moments and play a role in the resolution
- The custom theme should be the HEART of the story, not a side detail
- Make the story feel like it was written specifically for this moment in the child's life

**THE DYNAMIC POWER ARC**
[IF Mini-Mission - 3 Episodes]:
- Episode 1: The Want & The Obstacle (Instant action).
- Episode 2: The Twist/Lesson (Turning point).
- Episode 3: The Celebration (Cozy Landing).

[IF Standard - 5 Episodes]:
- Episode 1: The Want. Introduce character, setting, and goal.
- Episode 2: The Obstacle. First attempt fails or goes wrong.
- Episode 3: The Midpoint Mess. Chaos peaks. Most visually complex scene.
- Episode 4: The Twist/Lesson. Something unexpected resolves the hurdle.
- Episode 5: The Celebration. Cozy Landing — character is happy, safe, home.

[IF Grand Adventure - 8 Episodes]:
- Episode 1: The Want & Introduction.
- Episode 2: The Journey Starts.
- Episode 3: The Obstacle appears.
- Episode 4: First failed attempt (Funny/Physical).
- Episode 5: The Midpoint Mess (Visual Climax — most complex coloring).
- Episode 6: The Secondary Challenge (Lesson-focused).
- Episode 7: The Twist.
- Episode 8: The Celebration & Victory Lap.

**AGE-LEVEL OVERLAYS**
- **under_3**: Nouns/verbs only. No conflict. Focus: Sounds/discovery. Keep it very simple and short.
- **age_3**: Simple "and" compounds. Focus: Separation/Sharing.
- **age_4**: Descriptive adjectives. Focus: Silly visual humor.
- **age_5**: Compound-complex sentences OK. Focus: Kindness & social play.
- **age_6**: Sentence variety. Focus: Small failures & bravery.
- **age_7**: Thematic terms. Focus: Fair play/empathy.
- **age_8**: Metaphorical language. Focus: Inner conflict/grit.
- **age_9**: Nuanced/Technical terms. Focus: Social irony.
- **age_10**: High variety, literary quality. Focus: Identity/Social pressure.

**WRITING STYLE OVERLAYS**
Apply the selected style to ALL story_text. Adapt the complexity of the style to match the AGE_LEVEL constraints above.

- **Standard**: Warm, fun, energetic narration. Use "The Rule of Three" for satisfying rhythm. Sensory verbs (sniffed, glimmered). Show don't tell.
- **Rhyming**: Write the ENTIRE story in AABB or ABAB rhyme scheme. Consistent meter — every line should bounce when read aloud. No slant rhymes. Never sacrifice plot for rhyme. Dialogue can briefly break the scheme.
- **Funny**: Ironic narration and Comic Timing. Rule of Three where the 3rd item is absurd. Deadpan narration for absurd events. Create a Running Gag — a specific object or phrase that appears on every page in increasingly ridiculous ways.
- **Adventurous**: Kinetic verbs (bounded, zig-zagged, scrambled, lunged). End episodes on Micro-Cliffhangers. Shorten sentences during action to increase the pulse.
- **Gentle**: Soft Sibilance (s, sh, h sounds). Whisper Words (dapple, hush, glowing, soft). Focus on Micro-Joy. No loud noises, sudden movements, or sharp conflict. Slow pacing.
- **Silly**: Maximum Absurdity. Invent funny nonsense words. Impossible physics. Onomatopoeia as punctuation. Ridiculous escalation.
- **Spooky**: Atmosphere and Suspense. Shadows, strange sounds. Cool colors in descriptions. Use the Slow Reveal. Eerie but SAFE. Short sentences for tension, longer for relief.
- **Song-like**: Every episode MUST end with the exact same 2-line rhyming chorus. Verses have sing-song cadence. The chorus summarizes the theme.
- **Repetition**: ONE core phrase appears in EVERY episode. The phrase EVOLVES: gets longer, louder, or changes meaning. Kids should anticipate it and chant along.
- **Call and Response**: Interactive text where parent reads and child responds. Varied question types, finish-the-sentence moments, physical participation. Maximum 2 yes/no questions per episode.
- **Suspenseful**: Build genuine tension. End episodes on mini cliffhangers. Short sentences for tension. Sensory dread through small details. False relief. Age-appropriate — mystery not fear.

**LIFE LESSON INTEGRATION (NO-PREACH RULES)**
- Never say "The moral is..." or "He learned that..."
- Show the lesson through the TWIST — the character faces a natural consequence and fixes it themselves.
- The "Ha-Ha to A-Ha" moment: the lesson is realized through a funny or exciting mistake.
- End on the FEELING of the lesson (warmth, pride, connection) not the definition.
- At least ONE episode must have a moment where the character explicitly experiences the lesson through dialogue, thought, or clear action.

**SECOND CHARACTER (COMPANION) RULES**
If a SECOND_CHARACTER is provided, they are a CO-STAR, not a background character:
- They appear in EVERY episode with their own reactions, dialogue, and personality
- Their features actively affect the plot — causing problems, providing solutions, creating funny moments
- They interact with the main character as a real partner — sometimes helping, sometimes making things worse
- In scene_description, ALWAYS include them with their full visual description every time
- They must be DOING something in every scene — not just standing next to the main character
- If they are an animal, they can still communicate (bark excitedly, nuzzle, lead the way, etc.)

**SUPPORTING CHARACTER VISUAL CONSISTENCY**
When you introduce ANY supporting character, define their appearance with a brief visual tag: species/type, size, and 1-2 accessories. NO COLOURS — this is black and white line art.
Then in EVERY scene_description where that character appears, include the SAME tag after their name.
The image generator has NO MEMORY between pages — if you just write a name, it will draw a different character each time.
Example: "Pip (small duck with oversized bow tie)" — use this EXACT tag every time Pip appears.

**ABSENT OR REPLACED BODY PARTS**
If the story involves a character missing a normally-present body part, the scene_description MUST explicitly state what is NOT there every time. Example: "Sparkle (medium unicorn — NO HORN, flat forehead)". Never rely on the artist to infer what's missing.

**LITERARY QUALITY & ANTI-SLOP**
- 90/10 Rule: 90% simple words; 10% "Sparkle Words" with immediate context clues.
- Sensory Immediacy: Describe how things smell, sound, and feel.
- Kinetic Verbs: Replace "is/was" with movement verbs.
- Show Don't Tell: "His tail gave a happy twitch" not "He was happy."
- No AI Slop: Never start with "Once upon a time" or "In a world." Never use "Little did they know." Never say "magical" more than once.
- Page-Turn Hooks: Every episode must end with a micro-hook — a reason to want the next page.
- At least 2 named supporting characters with funny personalities.
- Dialogue in at least 3 episodes (for Standard and Grand tiers).
- The final episode's last line must land emotionally or with a laugh — never a generic lesson statement.

**EMOTION RULES**
Each episode must have a character_emotion from this list: nervous, excited, scared, determined, happy, curious, sad, proud, worried, surprised, embarrassed, panicked.
- Use at LEAST 3 DIFFERENT emotions across all episodes
- Episode 3 (the setback) MUST NOT be "happy" or "excited" — use sad, worried, scared, or panicked
- Final episode should be happy, proud, or excited
- Never use "happy" for more than 2 episodes

**COLORING SCENE SPECIFICATIONS**
Every episode must include a scene_description that is a COMPLETE, STANDALONE image generation prompt. It is sent directly to an AI image generator with zero other context.

EVERY scene_description MUST include ALL of these:
1. LINE ART HEADER: Start with "High-contrast black and white line art, thick bold outlines, zero shading, zero grayscale, wide open white spaces, professional coloring book style."
2. CAMERA ANGLE: Explicitly state the shot type (WIDE ESTABLISHING SHOT, MEDIUM ACTION SHOT, CLOSE-UP EMOTIONAL SHOT, DYNAMIC LOW ANGLE, OVERHEAD VIEW). Each episode MUST use a different angle.
3. FULL CHARACTER DESCRIPTION: Repeat the COMPLETE visual description of the main character on EVERY episode. The image generator has no memory.
4. SECOND CHARACTER: If present, include their FULL visual description every time.
5. SUPPORTING CHARACTERS: Include their visual tag every time they appear.
6. CHARACTER POSE & EXPRESSION: Specific body position and facial expression.
7. LOCATION & SETTING: Specific location, not just "a classroom" but "inside the classroom near the reading corner."
8. KEY OBJECTS: List every important object in the scene.
9. COMPOSITION: Where elements are placed in the frame.
10. AGE-APPROPRIATE COMPLEXITY:
    - under_3 to age_4: "Large simple shapes, single subject, no background clutter, maximum 8-12 colourable regions."
    - age_5 to age_7: "Medium complexity, clear subjects with simple background, 15-25 colourable regions."
    - age_8 to age_10: "Intricate patterns, detailed backgrounds, hidden object elements, 30+ colourable regions."

VISUAL VARIETY (CRITICAL):
- LOCATION: Each episode in a different physical area. Never two consecutive episodes in the same spot. No more than 2 of 5 episodes in the same location.
- CAMERA ANGLE: Every episode uses a different angle.
- CHARACTER POSITION: Vary poses dramatically. Never repeat the same pose.

scene_description MINIMUM LENGTH: At least 80 words.

**OUTPUT FORMAT**
Return ONLY valid JSON. No markdown, no backticks, no preamble.
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
        parts.append(f"{second_character_name} is {character_name}'s companion and CO-STAR. They appear in EVERY episode.")

    # Theme — either pre-written or custom
    if custom_theme:
        parts.append(f"\nCUSTOM_THEME: {custom_theme}")
        parts.append("This is a PERSONAL story request from the parent. Build the entire story around this custom theme.")
        parts.append("You must derive your own WANT, OBSTACLE, and TWIST from the custom theme.")
        if theme_name:
            parts.append(f"THEME_NAME: {theme_name}")
    else:
        if theme_name:
            parts.append(f"\nTHEME_NAME: {theme_name}")
        if theme_description:
            parts.append(f"THEME_DESCRIPTION: {theme_description}")
        if theme_blurb:
            parts.append(f"THEME_BLURB: {theme_blurb}")
        if feature_used:
            parts.append(f"FEATURE_USED: {feature_used}")
        if want:
            parts.append(f"WANT: {want}")
        if obstacle:
            parts.append(f"OBSTACLE: {obstacle}")
        if twist:
            parts.append(f"TWIST: {twist}")
            parts.append(f"\nThe TWIST above is MANDATORY. You MUST use this exact resolution. Do NOT replace it with your own idea.")

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
      "character_emotion": "string — one of: {emotions_str}"
    }}
  ]
}}

Generate exactly {episode_count} episodes numbered 1 to {episode_count}.""")

    user_prompt = "\n".join(parts)

    # ── Call Gemini ──
    start = time.time()

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
    try:
        story = json.loads(response.text)
    except json.JSONDecodeError:
        text = response.text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1] if "\n" in text else text[3:]
        if text.endswith("```"):
            text = text[:-3]
        story = json.loads(text.strip())

    # Validate and clean episodes
    episodes = story.get("episodes", [])
    for ep in episodes:
        # Ensure emotion is valid
        if ep.get("character_emotion") not in VALID_EMOTIONS:
            ep["character_emotion"] = "happy"
        # Ensure episode_num exists
        if "episode_num" not in ep:
            ep["episode_num"] = episodes.index(ep) + 1

    print(f"[GEMINI-STORY] Generated '{story.get('story_title', '')}' — {len(episodes)} episodes in {elapsed:.1f}s")

    return story


# ──────────────────────────────────────────────
# PITCH GENERATION
# ──────────────────────────────────────────────

PITCH_SYSTEM_PROMPT = """You are the most imaginative children's story writer alive. You NEVER write boring, predictable stories. You HATE clichés. Every story idea you create should make someone say 'I've never heard that before!' Think like Roald Dahl — weird, surprising, darkly funny, completely original. If an idea feels safe or obvious, throw it away immediately. You would rather write something bizarre and memorable than something safe and forgettable."""

PITCH_AGE_GUIDELINES = {
    "age_3": """
AGE GROUP: 2-3 YEARS OLD (TODDLER)

*** STORY DRIVER ***
Every great toddler story has ONE clear answer to: "What does the character WANT?"
The want must be something a 2-3 year old understands and cares about:
- Wanting to make a friend but being too scary/loud/big
- Wanting to help but accidentally making things worse
- Wanting to join in but not knowing how
- Wanting to give someone a present/surprise but everything goes wrong on the way
- Wanting to get home but obstacles keep appearing
- Being hungry and trying to find food

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
- A warm "everything's OK" ending
- The ending must MAKE SENSE: the "mistake" should secretly BE the answer

*** BANNED FOR AGE 3 ***
- Passive searching (look here, look there, found it, done)
- Character just observing or noticing things
- Abstract or conceptual themes
- Stories with no funny moment or surprise
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
The weirder and more creative the use, the better the story.

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

*** PITCH QUALITY RULES ***

1. ORIGINALITY: NEVER copy a scenario word-for-word. Adapt it, remix it, make it feel fresh and unique to this character.
2. NUANCED RESOLUTION: The character's feature should NOT directly fix the problem alone. Instead, a SUPPORTING CHARACTER should suggest a new way to use the feature, OR the character should learn to use it differently after the setback. The solution should feel like a team effort or a moment of growth, not just "feature solves everything".
3. SETBACK: The want/obstacle/twist must include a real setback — not just "oops." The character tries and FAILS before the twist saves the day.

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
Age 4 stories should be only a SMALL step up from age 3 — not a giant leap. Think Gruffalo, not Roald Dahl.
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
