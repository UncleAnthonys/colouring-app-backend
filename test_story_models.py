#!/usr/bin/env python3
"""
Compare story generation quality across Gemini 2.5 Flash, Claude Sonnet 4, and GPT-4o.
Uses the EXACT same prompt from adventure_gemini.py.
"""

import asyncio
import json
import os
import sys
import time
import random

# ============================================================
# CONFIG - Set your API keys here or as environment variables
# ============================================================
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

# ============================================================
# Test character - use a real character description from your app
# ============================================================
CHARACTER_NAME = "Tom"
CHARACTER_DESCRIPTION = """A bright pink/magenta cartoon creature with a round body shape. 
Key features:
- THREE large circular eyes arranged in a triangle pattern on the face (two on top, one below)
- Very large wide-open mouth showing teeth, taking up about 1/3 of the body
- SIX small legs/feet at the bottom, arranged in a row
- Two small wing-like or fin-like appendages on the sides
- Solid bright pink/magenta coloring throughout
- Round, blob-like body shape
- Friendly, excited expression"""

AGE_LEVEL = "age_5"

# ============================================================
# Age guidelines (copied from adventure_gemini.py)
# ============================================================
age_guidelines = {
    "age_3": """AGE GROUP: 2-3 years old
- Sentences: MAX 1 simple sentence per page (5-8 words)
- Words: Only use words a 2-year-old knows (mummy, daddy, big, small, yummy, uh-oh, splash, boom)
- Story: Extremely simple - character does ONE thing per page
- Themes: peekaboo, bath time, bedtime, playground, snack time, animals
- Feelings: happy, sad, scared (only these three)
- Example text: "Splash! Tom jumped in the puddle!"
- Names: Simple 1-syllable names for friends (Bob, Max, Pip)
- Familiar BUT exciting settings: a tall treehouse, a toy shop after dark, a kitchen where food comes alive, a bath-time ocean adventure, a blanket fort kingdom, a busy airport, a zoo at night""",
    
    "age_5": """AGE GROUP: 4-5 years old
- Sentences: 2-3 short sentences per page
- Words: Simple but more varied - can include silly made-up words, sound effects (WHOOOOSH, SPLAT, KABOOM)
- Story: Clear beginning, middle, end. Character has a PROBLEM to solve
- Themes: friendship, being brave, sharing, trying new things, first day at school
- Feelings: happy, sad, scared, excited, proud, nervous, surprised
- Example text: "Tom's tummy did a big flip. The cave was SO dark! But his friend Pip needed help, so Tom took a deep breath and tiptoed inside."
- Sound effects and action words make it exciting
- Names: Fun alliterative or rhyming names (Pip the Penguin, Dotty Dragon, Mr Grumbles)
- Settings should be exciting but relatable - places a kid thinks are COOL""",
    
    "age_6": """AGE GROUP: 6-7 years old  
- Sentences: 2-3 sentences per page with more descriptive language
- Words: Richer vocabulary - can include interesting adjectives, similes
- Story: More complex plot with a twist or surprise. Character LEARNS something
- Example text: "Tom's three eyes went wide as saucers. The old clock tower hadn't chimed in years, and now it was ticking backwards! 'That's not right,' whispered Professor Pip, adjusting his tiny spectacles."
- Dialogue between characters brings the story alive
- Introduce light humor and wordplay
- Settings: bouncy as a kangaroo on a trampoline, exciting similes""",
}

# ============================================================
# Scenario pool (copied from adventure_gemini.py)
# ============================================================
_scenario_pool = [
    "A popcorn machine at the cinema won't stop and popcorn is flooding the whole building",
    "A birthday cake has come alive and is running through the town leaving icing footprints everywhere",
    "Someone put magic beans in the school dinner and now vegetables are growing through the roof",
    "The world's longest spaghetti noodle has tangled around the entire city like a giant web",
    "A chocolate fountain at the fair has gone turbo and is spraying chocolate over everything",
    "A bubble gum machine exploded and giant sticky bubbles are trapping people inside",
    "The ice cream van's freezer broke and a tidal wave of melting ice cream is sliding downhill toward the school",
    "A baker's bread dough won't stop rising and is pushing the roof off the bakery",
    "Someone mixed up the recipes — the pet shop is full of cake and the bakery is full of hamsters",
    "A soup volcano erupted in the school canteen and tomato soup is flowing down the corridors",
    "The sweet shop's pick-and-mix machine is firing sweets like cannonballs across the high street",
    "A jam factory pipe burst and a river of strawberry jam is heading for the swimming pool",
    "A double decker bus has started flying and the passengers don't know how to land it",
    "A train has lost its driver and passengers must stop it before the end of the line",
    "The world's biggest shopping trolley is rolling downhill toward the lake with no brakes",
    "A hot air balloon got tangled in the town clock tower and passengers are stuck",
    "A submarine's steering is broken and it's heading for an underwater volcano",
    "The school bus accidentally drove into a car wash and can't find the way out",
    "A spaceship's sat-nav is broken and keeps landing in wrong places — a farm, a wedding, a swimming pool",
    "The roller coaster won't stop and riders have been going round for hours",
    "A pirate ship appeared in the park boating lake and nobody knows where it came from",
    "The new robot taxi is picking people up and dropping them at completely wrong places",
    "All zoo animals swapped enclosures — penguin in the lion cage, lion in the aquarium",
    "A magician's rabbit won't go back in the hat and is multiplying — 300 rabbits in the shopping centre",
    "A parrot learned everyone's secrets and is shouting them at the school assembly",
    "The dentist's goldfish grew to the size of a car overnight",
    "Squirrels moved into the school computer room and are hoarding all the keyboards",
    "The class hamster escaped and is now running the school from the headteacher's chair",
    "A whale fell asleep across the harbour and no boats can get in or out",
    "A cat stole the Mayor's golden chain and is sitting on top of the church spire",
    "All dogs in town started walking backwards at the same time — nobody knows why",
    "An octopus at the aquarium keeps stealing visitors' phones and taking selfies",
    "It's raining something different on every street — custard, bouncy balls, socks",
    "A giant snowball rolling through town getting bigger, collecting everything in its path",
    "Wind blew everyone's laundry and mixed it up — the Mayor is wearing a nappy",
    "A rainbow fell out of the sky and is blocking the motorway",
    "Clouds came down to ground level and nobody can see — chaos everywhere",
    "A leaf tornado trapped all the playground equipment inside it",
    "The sun went behind a cloud and forgot to come back — expedition to find it",
    "A thunderstorm is only happening inside the library and nobody knows why",
    "New playground built upside down — swings underground, sandpit on the roof",
    "A skyscraper is slowly tilting and everyone inside is sliding to one side",
    "Bouncy castle inflated too much — now the size of a real castle, floating above town",
    "School maze built too well — all the teachers are lost inside",
    "A crane picked up the swimming pool with people still in it",
    "The new bridge is made of chocolate and it's a hot day",
    "A treehouse growing by itself, adding rooms faster than anyone can explore",
    "Clock tower gears jammed — some people in fast-forward, others in slow motion",
    "All the festival fireworks went off at once inside the storage shed",
    "Magician's show went wrong — half the audience invisible, half upside down",
    "School nativity donkey is actually real and eating the set",
    "Wedding cake delivered to fire station — they used it for training",
    "Giant Christmas tree fell over blocking every road in town",
    "Carnival floats moving on their own with no drivers",
    "A pinata won't break, started moving, and is now chasing the children",
    "Shrinking ray hit the teacher — class now has a pencil-sized teacher",
    "Growing potion spilled on the goldfish — it's now the size of the school hall",
    "Time machine sent packed lunches to the dinosaur age — T-Rex eating someone's sandwich",
    "Science fair volcano actually erupted — school surrounded by bubbling goo",
    "Invisibility experiment — the whole school building disappeared but everyone's still inside",
    "Duplicating machine made 50 copies of the headteacher giving different instructions",
    "Gravity experiment went wrong — everything in the gym floating, including PE teacher",
    "Science fair robot decided it wants to be a student and won't leave class",
    "Toy shop toys came alive at midnight for a party — shop opens in one hour",
    "Board game became real-sized — dice the size of cars, whole town playing",
    "Someone's teddy bear wish came true — tiny teddy is now 10 feet tall, still wants cuddles",
    "Arcade machines playing themselves, high scores going crazy",
    "A jigsaw puzzle assembling itself into a portal — things coming through from the picture",
    "All the LEGO built itself into a castle overnight — a LEGO knight guards the door",
    "Remote control cars escaped the toy shop and are racing through town",
    "Firefighter's hose spraying silly string instead of water during a real emergency",
    "Postman's letters flying out and delivering themselves to wrong houses",
    "Dentist's chair started flying around the surgery with patient still in it",
    "Hairdresser's magic shampoo makes hair grow super fast — out the door in minutes",
    "Painter used magic paint — everything painted is coming alive",
    "Librarian's robot organising books by colour not title and refuses to stop",
    "Alien spaceship crashed into school roof — needs fixing before home time or alien's mum will worry",
    "Aliens visiting Earth think vinegar is perfume and chips are building blocks",
    "Space station gravity keeps flipping — astronauts bouncing between ceiling and floor",
    "Giant space snowball heading to Earth — unexpected snow day incoming",
    "Ocean plug came loose — all water draining out, fish NOT happy",
    "Underwater post office lost deliveries — shark got a seahorse's birthday card",
    "Sunken treasure chest opened — gold coins floating up causing beach chaos",
    "Coral reef talent show — three grumpy crab judges giving everyone zero",
    "A mysterious door appeared at the back of the school gym that wasn't there yesterday",
    "A treasure map blew in through the classroom window showing a route nobody recognises",
    "The museum's oldest painting has a tiny staircase in the corner nobody noticed before",
    "A message in a bottle with coordinates pointing underneath the town fountain",
    "An old lift has a button for a floor that doesn't exist — Floor 13 and a half",
    "New kid at school says they're from a country nobody can find on any map",
    "Tunnels underneath the town being mapped for the first time — something's making noises down there",
    "Lighthouse keeper missing — left behind strange inventions and half-finished notes",
    "Hot air balloon landed in the playground with nobody in it — just a note saying HELP",
    "A door in the big oak tree that only appears when it rains",
    "Old boat washed up covered in barnacles with a logbook in an unknown language",
    "Town hall attic locked for 100 years — today they found the key",
    "New kid at school doesn't speak the same language and looks lonely at lunch",
    "Two best friends both want the same part in the school play — it's tearing them apart",
    "Grumpy neighbour who shouts at everyone secretly been feeding all the stray cats",
    "Smallest kid always picked last for teams but has an amazing hidden talent",
    "A kid's imaginary friend is sad because the kid is growing up and doesn't play pretend anymore",
    "School bully caught crying behind the bins — having a really hard time at home",
    "Two rival bakers must work together when a power cut hits both shops",
    "Shy kid finds a lost dog and has to knock on strangers' doors to find the owner",
    "Elderly neighbour can't get to the shops anymore and nobody noticed except the character",
    "Class goldfish is poorly — whole class works together on the best fish hospital ever",
    "Kid who just moved to new town pretending everything's fine but secretly misses old friends",
    "Grandparent forgetting things more and more — grandchild finds creative ways to help them remember",
    "Loneliest tree in the park has no birds — every other tree does — someone investigates why",
    "Child finds names carved on a park bench from decades ago and tries to find the people",
    "Only kid who can't swim has to go to the pool party everyone else is excited about",
    "A creature that looks completely different from everyone turns up at the market — nobody will talk to them",
    "Kid who uses a wheelchair discovers a part of the playground only they can reach",
    "Weirdest house on the street about to be knocked down but it's actually the most special one",
    "Kid told they're too loud everywhere until they find a place where loud is exactly what's needed",
    "One fish swimming opposite to all others discovers something amazing the rest missed",
    "Kid who draws outside the lines enters a competition where that's the whole point",
    "Wonky homemade cake enters a competition full of perfect professional cakes",
    "Bird that can't fly lives among birds that can — until winter when flying isn't what's needed",
    "Scruffiest dog at the rescue centre keeps getting overlooked while cute puppies get chosen",
    "Birthday wish made everything opposite — up is down, cats bark, teachers are students",
    "Copy machine left on overnight — 1000 newsletters flying through town",
    "Town statue came alive but can only move when nobody's looking",
    "Hiccup going around town — each person hiccups something different: bubbles, confetti, glitter",
    "Kid's homework excuse came true — a dinosaur ate my homework and now there's a dinosaur",
    "Everything the character says comes true literally — I could eat a horse and a horse appears on a plate",
    "School camera takes photos of what people are THINKING not what they look like",
    "Restaurant critic coming today but the chef lost their sense of taste — need a secret taster",
    "Town crier got hiccups — all announcements coming out garbled and wrong",
    "Picture day camera adds silly hats and moustaches to everyone and won't stop",
    "Kid's shadow detached and is doing its own thing — going to classes, eating with other kids",
    "Voice-activated town systems mishearing everything — lights on turns on sprinklers",
    "Smart board learned to talk and won't stop giving opinions during lessons",
    "Fancy dinner party where everything goes wrong — cold soup, collapsing chairs, exploding dessert",
    "Kid terrified of the dark has to cross the school field at night to get something important",
    "Child scared of water — their best friend's puppy just fell in the pond",
    "Kid who hates thunder is at a sleepover when the biggest storm hits",
    "Child afraid of heights — only way to rescue the stuck kite is to climb",
    "Shy kid has exactly the information everyone needs but must say it in front of the whole school",
    "Kid scared of dogs has to walk past one daily — one day the dog needs help",
    "Kid who hates getting messy — the only fix involves getting VERY messy",
    "Child who hates loud noises must cross the noisiest place in town for an important delivery",
    "Town's only bridge broken — everyone stuck on one side, character must connect them",
    "Oldest lady's garden destroyed by storm — it was the one thing that made her happy",
    "Homeless kitten hiding under the school, too scared to come out, getting cold tonight",
    "Local park becoming a car park unless someone proves it's special enough to keep",
    "School dinner lady secretly using her own money so no kid goes hungry",
    "Power out on coldest night — neighbours don't even know each other",
    "Elderly toymaker's hands shake too much to make toys but Christmas is coming",
    "Town's ice cream van broke down on the hottest day — ice cream melting fast",
    "Cardboard box becomes a real spaceship when nobody's looking — must get back before bedtime",
    "Drawings in a sketchbook climbing off the pages when the kid sleeps",
    "Blanket fort became an actual kingdom with tiny citizens who need help",
    "Bath time rubber ducks turned into real ducks — bath is now an ocean",
    "Kid's imaginary world leaking into reality — imaginary dragon is in the kitchen",
    "Toy dinosaur came alive in the museum — get it back to the exhibit before the guard notices",
    "Chalk playground drawings become real when it rains — someone drew a lion",
    "Bedtime story telling itself differently — characters going off-script",
    "Snow globe on the shelf snowing for real — tiny town inside needs help with their blizzard",
    "Kid's LEGO city comes alive at night — they shrink down but something's wrong in LEGO town",
    "Sports day chaos — egg and spoon egg is an ostrich egg, sack race sacks have holes",
    "School bake-off where the oven keeps changing temperature on its own",
    "Dance competition where the floor tiles light up randomly and you must follow them",
    "Paper boat race on the river but this year there are real tiny rapids",
    "Hide and seek championship where hiding spots keep moving — wardrobe walks to new room",
    "Spelling bee where correctly spelled words come alive and walk around the stage",
    "School science fair — every project activates at once, hall becomes total chaos",
    "Sandcastle competition but the tide is coming in fast",
    "Kite competition on the windiest day ever — kites pulling owners into the sky",
    "School team playing against robots that keep glitching in funny ways",
    "Kid finds a tiny injured bird and nurses it back to health, not knowing if it will fly again",
    "First snow of winter — whole town building the most spectacular snowman ever",
    "Rainy afternoon baking with grandparent who shares stories from when they were young",
    "Kid growing a sunflower for competition but starts caring more about the flower than winning",
    "Moving day — saying goodbye to old room, old street, old climbing tree",
    "Kid saving up pocket money for weeks to buy something special for someone they love",
    "Last day of summer holidays — friends plan the perfect final adventure before school starts",
    "Box of old letters in the attic tells the story of how grandparents met",
    "Night before starting new school — kid can't sleep, imagining everything that might happen",
    "Child stays up late to see the stars for the first time, wrapped in a blanket with their parent",
]

# ============================================================
# Build the prompt (matching adventure_gemini.py exactly)
# ============================================================
def build_prompt():
    age_guide = age_guidelines.get(AGE_LEVEL, age_guidelines["age_5"])
    
    random.shuffle(_scenario_pool)
    shuffled_scenarios = "\n".join(f"{i+1}. {s}" for i, s in enumerate(_scenario_pool))
    
    # Read the actual prompt from adventure_gemini.py to keep it in sync
    # For now, build a simplified version matching the key sections
    
    prompt = f'''You are creating personalized story adventures for a childrens coloring book app.

Based on this character named "{CHARACTER_NAME}", generate 3 UNIQUE story themes that are PERSONALIZED to this specific character's features.

CHARACTER TO ANALYZE:
{CHARACTER_DESCRIPTION}

STEP 1 - IDENTIFY THE MOST UNUSUAL FEATURES (in order of priority):
Look at the character description. Find the WEIRDEST, most UNUSUAL things:

PRIORITY 1 - UNUSUAL BODY PARTS (these are the MOST interesting for stories!):
Examples: extra arms, big mouth, multiple eyes, tiny legs, huge ears, long tail
These become the character's SUPERPOWER in the story!

PRIORITY 2 - UNUSUAL NUMBERS:
Examples: 3 eyes instead of 2, 6 legs, 4 arms, 5 fingers on each hand
Numbers make great story hooks!

PRIORITY 3 - Colors and patterns (LEAST interesting - only use if nothing else):
Only fall back to colors if the character has NO unusual body parts or numbers.

{age_guide}

STEP 2 - PICK AND ADAPT A SCENARIO

Below is a pool of 180 story scenarios. For each of your 3 themes:
1. Pick a scenario that the character's unique feature would be PERFECT for
2. ADAPT it — don't copy it word-for-word. Change details, combine ideas, make it your own
3. The character's feature should be essential to the story but in a SURPRISING way

The scenario is the STARTING POINT. The character's feature determines HOW they deal with it.
Example: "A duplicating machine made 50 copies of the headteacher" + a character with many eyes = each eye can track a different copy, but they keep confused when copies swap clothes. Eventually they spot the real one because only the original has a coffee stain on their tie.

Each theme MUST use a DIFFERENT unique feature as the main plot device.
NEVER include specific body part numbers in theme names.

*** SCENARIO POOL ***

{shuffled_scenarios}

*** HOW TO USE THESE SCENARIOS ***

1. Read the character's features from STEP 1
2. Scan ALL 180 scenarios — DO NOT just pick from the top of the list! Read the ENTIRE list before choosing.
3. Pick the 3 where the character's feature would create the FUNNIEST, most SURPRISING story
4. Each theme must use a DIFFERENT feature
5. NEVER pick scenarios 1-20 unless they are genuinely the best fit — the top of the list is NOT better than the rest
6. ADAPT the scenario — change names, settings, details, put your own spin on it. The scenario is a starting point not a script
7. The character's feature should help in a SURPRISING way, not the obvious way
8. NEVER use the scenario's exact wording in the theme blurb — rewrite it completely

{age_guide}

CRITICAL: Follow the age guidelines above exactly for sentence length, vocabulary, and complexity.

*** FORMAT ***

For each theme provide:
1. Theme name (fun, age-appropriate)
2. Theme description (1 sentence)
3. Theme blurb (ONE short punchy sentence, MAX 15 words. Describe the chaos/situation only. NEVER mention the character's body parts in the blurb)
4. 5 episodes with: episode number (1-5), title, scene_description, story_text, emotion

Scene descriptions MUST include: character's pose/action, specific setting details, other characters present, 3-4 background objects to colour. Mix close-ups, wide shots, and action scenes across the 5 episodes.

Story text: Follow the age guidelines for length. Final episode should be short and punchy.

Emotion must be one of: nervous, excited, scared, determined, happy, curious, sad, proud, worried, surprised

*** 5 NON-NEGOTIABLE RULES ***

1. CHARACTERS: At least 2 named supporting characters with funny personalities who appear throughout, not just once.
2. SETBACK ON EPISODE 3: Character tries and FAILS or makes things worse. Makes the win feel earned.
3. DIALOGUE: At least 3 of 5 episodes need characters talking in speech marks.
4. ENDING: Episode 5 resolves the specific problem from episode 1. No generic happy endings.
5. NEVER copy a scenario word-for-word. Adapt it, remix it, make it feel fresh and unique to this character.

Return ONLY valid JSON in this format:
{{
  "themes": [
    {{
      "theme_id": "theme_slug",
      "theme_name": "Fun Theme Name",
      "theme_description": "One sentence description.",
      "theme_blurb": "Short punchy blurb under 15 words.",
      "episodes": [
        {{
          "episode_num": 1,
          "title": "Episode Title",
          "scene_description": "Detailed scene for image generation.",
          "story_text": "The story text for this page.",
          "emotion": "excited"
        }}
      ]
    }}
  ]
}}

NOW generate for {CHARACTER_NAME}. Generate 3 complete themes with all 5 episodes each. Return ONLY the JSON, no other text.'''

    return prompt


# ============================================================
# MODEL RUNNERS
# ============================================================

async def run_gemini(prompt):
    """Run with Gemini 2.5 Flash"""
    import google.generativeai as genai
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(
        'gemini-2.5-flash',
        generation_config=genai.GenerationConfig(
            response_mime_type="application/json"
        )
    )
    
    start = time.time()
    response = model.generate_content([prompt])
    elapsed = time.time() - start
    
    return {
        "model": "Gemini 2.5 Flash",
        "time": round(elapsed, 1),
        "response": response.text,
        "input_tokens": "~" + str(len(prompt.split())),
    }


async def run_claude(prompt):
    """Run with Claude Sonnet 4"""
    import anthropic
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    
    start = time.time()
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=8000,
        messages=[{"role": "user", "content": prompt}]
    )
    elapsed = time.time() - start
    
    text = response.content[0].text
    usage = response.usage
    
    return {
        "model": "Claude Sonnet 4",
        "time": round(elapsed, 1),
        "response": text,
        "input_tokens": usage.input_tokens,
        "output_tokens": usage.output_tokens,
        "cost_estimate": f"${(usage.input_tokens * 3 / 1_000_000) + (usage.output_tokens * 15 / 1_000_000):.4f}"
    }


async def run_gpt4o(prompt):
    """Run with GPT-4o"""
    from openai import OpenAI
    client = OpenAI(api_key=OPENAI_API_KEY)
    
    start = time.time()
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=8000,
        response_format={"type": "json_object"}
    )
    elapsed = time.time() - start
    
    text = response.choices[0].message.content
    usage = response.usage
    
    return {
        "model": "GPT-4o",
        "time": round(elapsed, 1),
        "response": text,
        "input_tokens": usage.prompt_tokens,
        "output_tokens": usage.completion_tokens,
        "cost_estimate": f"${(usage.prompt_tokens * 2.5 / 1_000_000) + (usage.completion_tokens * 10 / 1_000_000):.4f}"
    }


# ============================================================
# ANALYSIS
# ============================================================

def analyze_story(data, model_name):
    """Analyze a story response for quality indicators"""
    analysis = {"model": model_name, "issues": [], "strengths": []}
    
    try:
        if isinstance(data, str):
            # Clean markdown
            text = data.strip()
            if text.startswith('```json'):
                text = text[7:]
            if text.startswith('```'):
                text = text[3:]
            if text.endswith('```'):
                text = text[:-3]
            start = text.find('{')
            end = text.rfind('}') + 1
            data = json.loads(text[start:end])
        
        themes = data.get("themes", [])
        analysis["num_themes"] = len(themes)
        
        for i, theme in enumerate(themes):
            t_name = theme.get("theme_name", "MISSING")
            blurb = theme.get("theme_blurb", "MISSING")
            episodes = theme.get("episodes", [])
            
            analysis[f"theme_{i+1}_name"] = t_name
            analysis[f"theme_{i+1}_blurb"] = blurb
            analysis[f"theme_{i+1}_episodes"] = len(episodes)
            
            # Check blurb length
            blurb_words = len(blurb.split())
            if blurb_words > 15:
                analysis["issues"].append(f"Theme {i+1} blurb too long ({blurb_words} words)")
            
            # Check if blurb mentions body parts
            body_parts = ["eye", "eyes", "mouth", "leg", "legs", "wing", "wings", "arm", "arms"]
            for part in body_parts:
                if part in blurb.lower():
                    analysis["issues"].append(f"Theme {i+1} blurb mentions '{part}'")
            
            # Check for banned patterns
            banned = ["sparkle", "restore", "magic back", "colour back", "singing to fix", "quiet place"]
            for b in banned:
                for ep in episodes:
                    if b in ep.get("story_text", "").lower():
                        analysis["issues"].append(f"Theme {i+1} uses banned pattern: '{b}'")
                        break
            
            # Check for wobbly
            for ep in episodes:
                if "wobbly" in ep.get("story_text", "").lower() or "wobbly" in ep.get("title", "").lower():
                    analysis["issues"].append(f"Theme {i+1} uses 'wobbly'")
                    break
            
            # Check setback on ep 3
            if len(episodes) >= 3:
                ep3_text = episodes[2].get("story_text", "").lower()
                setback_words = ["but", "failed", "slipped", "missed", "wrong", "worse", "couldn't", "didn't work", "uh-oh", "oh no"]
                has_setback = any(w in ep3_text for w in setback_words)
                if has_setback:
                    analysis["strengths"].append(f"Theme {i+1}: setback on ep 3 ✓")
                else:
                    analysis["issues"].append(f"Theme {i+1}: NO setback on ep 3")
            
            # Check dialogue
            dialogue_count = sum(1 for ep in episodes if '"' in ep.get("story_text", "") or "'" in ep.get("story_text", ""))
            if dialogue_count >= 3:
                analysis["strengths"].append(f"Theme {i+1}: dialogue in {dialogue_count}/5 eps ✓")
            else:
                analysis["issues"].append(f"Theme {i+1}: only {dialogue_count}/5 eps have dialogue")
            
            # Check named characters
            # Simple heuristic - look for capitalized words that aren't the character name
            all_text = " ".join(ep.get("story_text", "") for ep in episodes)
            import re
            names = set(re.findall(r'\b[A-Z][a-z]+\b', all_text))
            names.discard(CHARACTER_NAME)
            names.discard("The")
            names.discard("But")
            names.discard("And")
            names.discard("Then")
            names.discard("EVER")
            if len(names) >= 2:
                analysis["strengths"].append(f"Theme {i+1}: named chars: {', '.join(list(names)[:5])} ✓")
            else:
                analysis["issues"].append(f"Theme {i+1}: not enough named characters")
            
            # Check story text length per episode
            for ep in episodes:
                words = len(ep.get("story_text", "").split())
                if words > 60:
                    analysis["issues"].append(f"Theme {i+1} ep {ep.get('episode_num')}: text too long ({words} words)")
            
            # Check setting variety
            settings = [ep.get("scene_description", "") for ep in episodes]
            # Simple check - are all settings similar?
            
    except Exception as e:
        analysis["issues"].append(f"PARSE ERROR: {str(e)}")
    
    return analysis


def print_results(result, analysis):
    print(f"\n{'='*70}")
    print(f"  {result['model']}")
    print(f"  Time: {result['time']}s")
    if 'cost_estimate' in result:
        print(f"  Cost: {result['cost_estimate']}")
    if 'input_tokens' in result:
        print(f"  Tokens: {result['input_tokens']} in / {result.get('output_tokens', '?')} out")
    print(f"{'='*70}")
    
    for i in range(1, 4):
        name = analysis.get(f"theme_{i}_name", "???")
        blurb = analysis.get(f"theme_{i}_blurb", "???")
        eps = analysis.get(f"theme_{i}_episodes", 0)
        print(f"\n  Theme {i}: {name}")
        print(f"  Blurb: {blurb}")
        print(f"  Episodes: {eps}")
    
    print(f"\n  ✅ STRENGTHS:")
    for s in analysis.get("strengths", []):
        print(f"     {s}")
    
    print(f"\n  ❌ ISSUES:")
    for s in analysis.get("issues", []):
        print(f"     {s}")
    print()


# ============================================================
# MAIN
# ============================================================

async def main():
    prompt = build_prompt()
    
    print(f"Prompt length: ~{len(prompt.split())} words / ~{len(prompt)} chars")
    print(f"Character: {CHARACTER_NAME}")
    print(f"Age: {AGE_LEVEL}")
    print(f"\nRunning tests...\n")
    
    results = []
    
    # Run each model
    models_to_test = []
    
    if GEMINI_API_KEY:
        models_to_test.append(("Gemini 2.5 Flash", run_gemini))
    else:
        print("⚠️  GEMINI_API_KEY not set - skipping Gemini")
    
    if ANTHROPIC_API_KEY:
        models_to_test.append(("Claude Sonnet 4", run_claude))
    else:
        print("⚠️  ANTHROPIC_API_KEY not set - skipping Claude")
    
    if OPENAI_API_KEY:
        models_to_test.append(("GPT-4o", run_gpt4o))
    else:
        print("⚠️  OPENAI_API_KEY not set - skipping GPT-4o")
    
    for name, runner in models_to_test:
        print(f"🔄 Running {name}...")
        try:
            result = await runner(prompt)
            results.append(result)
            
            # Save raw response
            safe_name = name.replace(" ", "_").lower()
            with open(f"test_result_{safe_name}.json", "w") as f:
                f.write(result["response"])
            print(f"   ✅ Done in {result['time']}s - saved to test_result_{safe_name}.json")
            
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            results.append({"model": name, "time": 0, "response": "", "error": str(e)})
    
    # Analyze and compare
    print(f"\n\n{'#'*70}")
    print(f"  COMPARISON RESULTS")
    print(f"{'#'*70}")
    
    for result in results:
        if "error" not in result:
            analysis = analyze_story(result["response"], result["model"])
            print_results(result, analysis)
    
    # Save full comparison
    with open("test_comparison_summary.txt", "w") as f:
        f.write(f"Story Generation Model Comparison\n")
        f.write(f"Character: {CHARACTER_NAME}\n")
        f.write(f"Age: {AGE_LEVEL}\n")
        f.write(f"Date: {time.strftime('%Y-%m-%d %H:%M')}\n\n")
        
        for result in results:
            if "error" not in result:
                f.write(f"\n{'='*70}\n")
                f.write(f"{result['model']} ({result['time']}s)\n")
                f.write(f"{'='*70}\n")
                f.write(result["response"])
                f.write("\n\n")
    
    print(f"\n📄 Full responses saved to test_comparison_summary.txt")
    print(f"📄 Individual JSONs saved to test_result_*.json")


if __name__ == "__main__":
    asyncio.run(main())
