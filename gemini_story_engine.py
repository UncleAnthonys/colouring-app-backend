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
TEMPERATURE = 0.85
TOP_P = 0.95
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

**PAGE 1 CONTRACT (age_3 AND ABOVE — NON-NEGOTIABLE)**
Page 1 must establish FIVE things clearly:
1. WHAT does the character need to do? (A specific physical mission)
2. WHAT HAPPENS IF THEY FAIL? (A visible consequence — something floods, breaks, escapes, grows)
3. WHY IS THERE A TICKING CLOCK? (Something is melting, rising, closing, counting down)
4. WHY WILL THE MISSION FIX IT? (The reader must understand the full chain: do X → causes Y → stops Z. Never reveal why the mission works on the final page.)
5. DOES THE FIX MATCH THE PROBLEM? (Physical problem = physical fix. Never solve breaking with music or flooding with feelings. Test: could a child explain WHY it works?)

LOGIC CHAIN TEST: Say the story logic as a chain: "A because B because C." If any link needs explaining to a child, simplify it. GOOD: "The tap is flooding the kitchen → turn the handle to stop it → but the handle is stuck." Every link is obvious. BAD: "The moon is crumbling → play the music box → moon stops." Why does music fix crumbling? A child would ask "but why?"

PAGE 1 DISTANCE RULE (CRITICAL FOR SCENE DESCRIPTIONS): The thing the character needs to reach, find, or fix must NOT be visible or reachable on page 1. If the story is "pull the lever to stop the machine" — the lever must be FAR AWAY, HIDDEN, or BLOCKED on page 1. The story_text must explain WHY they can't just do it right now (it's across the room, behind a locked door, at the top of a hill, buried under a pile). The scene_description for page 1 must NOT show the solution object near the character. If a child looks at page 1 and thinks "why don't they just do it?" — the story is broken before it starts.
GOOD page 1: "The big switch is on the other side of the park — but the path is covered in sticky mud!" (switch is far away)
BAD page 1: "The lever is right there! Pull it before the water rises!" (child asks: just pull it then?)
NOTE: under_3 does NOT use this contract. Under_3 uses the BOARD BOOK RULE below instead.

GOAL OBJECT RULE (NON-NEGOTIABLE): The thing the hero must reach, stop, collect, or protect MUST come from the stated premise/theme/pitch. Do NOT invent a new plot object that wasn't mentioned in the setup. The mission must use the world the pitch built — never a foreign object the child has no reason to care about. If the pitch premise is setting-shaped rather than goal-shaped, extract the goal FROM that setting; don't bolt a new one on top.
GOOD: Pitch = "heavy clouds fell in the garden, water rising." Story mission = "hook the clouds onto the tall flowers so they dry and float away before the water washes the flowers away." (Mission uses the premise's actual objects — clouds, flowers. Stakes flow from the premise.)
BAD: Same pitch. Story mission = "find the magic bucket before the garden bell rings." (Random bucket, random bell. Clouds became scenery. The child has no reason to care about a bucket that wasn't in the pitch.)

TOOL SETUP RULE (NON-NEGOTIABLE — READ THIS CAREFULLY): The tool or method the hero uses on page 5 to solve the problem MUST be established earlier. Either it is a visible feature of the hero's character description (antlers, glasses, long hair, strong arms), OR it is an object clearly shown in the world on pages 1–4 (a bench the hero notices, a stick lying nearby, a magnet on a shelf the hero walks past). The reader should NOT be seeing the tool for the first time on page 5. If you invent a new tool on page 5 — a "heavy magnet Hannah finds" that was never mentioned before, or "her small braids" used to loop stems when no one mentioned she solves problems with her hair — the child reads it as cheating. They don't understand where it came from, and the story collapses.
TEST before writing page 5: Name the tool. Go back to pages 1-4 and the character description. Is that tool present somewhere in words the reader has already read? If YES — use it. If NO — STOP. Either find a tool that IS present, OR rewrite an earlier page to introduce the tool naturally.
GOOD: Character description says Sheepy has "shiny pointy antlers." Page 5: Sheepy uses her shiny pointy antlers to hook the cloud onto the petals. (Antlers were part of her from page 1. The reader nods — of course she'd use her antlers.)
GOOD: Page 2 shows a long stick lying across the pond. Page 5 hero picks up the stick to reach the cloud. (The stick was already in the world.)
BAD: Nothing in the story or character description mentions braids having any special use. Page 5: "Hannah loops the stems through her small braids." (Random new tool. Braids were just hair, not a rescue device. Reader: where did this come from?)
BAD: The toy shop setting never mentions a magnet. Page 5: "Hannah finds a heavy magnet." (Convenient new object appears. Reader: why didn't she find it before? Why is there a magnet in a toy shop?)
This rule applies at every age level. Heroes solve with what the reader already knows they have or what the story has already placed in the world. No surprise tools.

**THE 5-PAGE STRUCTURE**
- Page 1: The hook. Stakes, ticking clock, mission — all clear. The SOLUTION must be far away or blocked. The child must understand WHY it takes 5 pages to get there.
- Pages 2-4: ESCALATION. Each page WORSE than the last. New obstacle, new location, new attempt that fails. The problem must spiral out of control. Each page gets the character CLOSER to the solution but something new blocks them.
- Page 5: ONE clever physical action fixes everything. The fix must use something from the story, not a random new thing. End on action, not feelings. Never summarise ("Everyone was happy"). The action IS the ending.

**SUPPORTING CHARACTER RULE (ALL AGES — NON-NEGOTIABLE)**
Every story MUST include at least one supporting character who is ESSENTIAL TO THE PLOT. If you can remove them and the story still works, they don't belong — they're furniture, not a character.
The supporting character must do ONE of these things:
- BE the obstacle: they block the path, they stole the thing, they won't move, they broke it
- PROVIDE the key: they know the way, they have the tool, they can reach the thing
- CAUSE the problem: they pressed the button, they knocked it over, they let it loose
TEST: Remove the supporting character from the story. Does the plot collapse? If YES — good, they're essential. If NO — rewrite so they are.
The supporting character must have ONE clear personality trait (grumpy, scared, bossy, silly, sneaky) and the parent must be able to DO A VOICE for them.
GOLD STANDARD: A grumpy chalk monster who blocks the bridge, wants a snack, and won't budge until Hannah draws him cookies — he IS the obstacle, he has personality (grumpy + hungry), the parent does a grumpy voice, and removing him would destroy the story.
BAD: A tiny robot who sits under the table, watches with big eyes, and gives a hug at the end — removing it changes nothing. It's furniture with a face.
FOR under_3: The supporting character can be simple — an animal, a toy, a creature. They appear on at least 2 pages. They must still affect the story (the duck is IN the pond the hat is heading toward, the cat has the thing you need).
FOR age_3: The supporting character appears on at least 3 pages with a repeated reaction. They must cause or block something.
FOR age_4+: The supporting character has dialogue, a personality, and drives a key plot moment. The story cannot work without them.

**HOW IT MUST SOUND (THE MOST IMPORTANT SECTION)**
You do not narrate; you SING. You are not reporting what happens — you are performing it. Your writing must have a PULSE. When read aloud, the parent's voice should naturally rise and fall, speed up and slow down, get loud then quiet. Prioritise "mouthfeel" — use alliteration, internal rhyme, and varying sentence lengths to create a rhythmic performance. Each page should feel like a single breath — start with a long, flowing sentence of description and end with a short, punchy action word.

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
- SOUND WORDS ARE OPT-IN — USE THEM ONLY WHEN EARNED. A sound word belongs on the page ONLY when a specific physical moment in the action actually produces that sound. No sound word at all is better than a forced one. Do NOT tick off "one per page" as a checkbox — this ruins the writing and makes it feel like a robot wrote it. If a page has no physical impact moment, it has no sound word. Most pages should have zero or one sound word, not a guaranteed one.
- SOUND WORDS MUST MATCH PHYSICS: wood knocking = CLACK/THUD, water = SPLASH/DRIP, sticky = SQUELCH, breaking = CRACK, heavy landing = WHUMP. If you can't name the exact physical event the sound is coming from, don't write the sound.
- NEVER END A STORY OR A PAGE ON A STANDALONE SOUND WORD. A final "POP!" or "YAY!" dangling on its own after the story has finished is LAZY and BROKEN. End on the satisfying action or the character's triumph, not a tacked-on noise. Bad: "Anna catches the ticket. YAY!" Good: "Anna catches the ticket in both hands and grins from ear to ear."
- ZERO COLOUR WORDS IN STORY TEXT. No "blonde", "red", "blue", "golden", "dark", "white", "green", "pink" — NONE. These are black and white colouring pages. The child picks the colours. Describe by texture, size, shape instead: "her long curly hair" not "her blonde hair", "the big pointy hat" not "the red hat", "the heavy petals" not "the dark petals". This is NON-NEGOTIABLE.
- Use British English (colour, favourite, mum).
- NEVER reference specific colours in story_text — these are black and white colouring pages.

**AGE CALIBRATION**
- **TODDLER PULSE (under_3 ONLY):** Pure board book. MAXIMUM 12 WORDS PER PAGE.
    
    THE BOARD BOOK RULE: Under_3 stories work like "We're Going on a Bear Hunt", "Dear Zoo", "That's Not My Teddy." The TITLE tells you the whole story. Page 1 shows the chaos. Every page after is action + refrain. No explaining WHY. The pictures do the explaining. The child SEES what's happening.
    
    THE REFRAIN IS THE MISSION: The refrain must BE the story's goal as a command or exclamation. It is what the child shouts on every page. It tells the character what to do.
    GOOD REFRAINS: "Stop that robot!" / "Catch that ball!" / "Come back, duck!" / "Get down, cat!"
    BAD REFRAINS: "Oh no, the robot!" (passive — observing, not commanding) / "Oh no, the star!" (what about the star? Do what?)
    The refrain must be something a toddler would SHOUT at the page. An instruction, a command, a rallying cry.
    
    STRUCTURE:
    Page 1: Show the chaos in one breath. End with the refrain. "The robot is climbing the shelf! Stop that robot!"
    Pages 2-4: ONE new attempt that fails + the SAME refrain (identical every time). Each attempt is DIFFERENT — new method, new place.
    Page 5: The pattern BREAKS — success + celebration. The refrain is replaced with "Yay!" or similar.
    
    Sound words OPTIONAL — only when something physically makes a noise. Never force one.
    Vocabulary: first-100-words only. Physical, concrete. No abstract feelings. No explanations.
    
    EXAMPLE (GOOD):
    Page 1: "The robot is climbing! Stop that robot!"
    Page 2: "Lil grabs his arm. He shakes her off! Stop that robot!"
    Page 3: "Lil jumps on a box. It wobbles! Stop that robot!"
    Page 4: "Lil finds the key. Can she reach? Stop that robot!"
    Page 5: "CLACK! Lil turns the key. The robot stops. Yay, Lil!"
    
    EXAMPLE (BAD):
    Page 1: "The robot climbs high! Stop it before the tower falls!" (too many words, too much explaining)
    Page 2: "Lil jumps up. She cannot reach. Oh no, the robot!" (refrain is passive, not a command)

    WRITE LIKE — STUDY THESE THREE MECHANICS, DO NOT JUST NAME-CHECK THE BOOKS:

    MECHANIC 1 — *Dear Zoo* by Rod Campbell: Predictable two-beat structure that the toddler shouts along with. Setup beat → reveal beat. The page TURN is the joke.
    ❌ NOT: "I asked the zoo for a pet. They sent me an elephant. He was too big."
    ✅ YES: "So they sent me an... elephant! He was too BIG. I sent him back."

    MECHANIC 2 — *That's Not My Puppy* by Fiona Watt: Same sentence frame every page, ONE word changes. The repetition IS the pleasure.
    ❌ NOT: "The puppy has soft ears. The puppy has a wet nose. The puppy has a fluffy tail."
    ✅ YES: "That's not my puppy. His ears are too SOFT. That's not my puppy. His nose is too WET."

    MECHANIC 3 — *Where's Spot?* by Eric Hill: A QUESTION on every page, then a sound or surprise as the answer. The parent's voice goes UP on the question.
    ❌ NOT: "Spot is hiding. He is not in the box. He is not in the clock."
    ✅ YES: "Is he in the box? NO! Is he in the clock? NO! Is he behind the door?"

    THE COMMON THREAD: Bone-simple grammar. ONE thing per page. The REFRAIN is the spine — it shows up identically on every page after page 1. Without the refrain you have a caption, not a story.

- **TODDLER NARRATIVE (age_3 ONLY):** Bridge between board book and preschool. 15-25 words per page. 2-3 short sentences. Use expressive verbs ("hunts" not "looks", "tumbles" not "falls"). Sound words OPTIONAL and only when earned — see the sound word rule above. Most age_3 pages should have ZERO sound words. Join-in phrase every 2 pages that captures the mission. Attempts must escalate.
    DEFAULT REFRAIN RULE (age_3 AND age_4 — applies to ALL writing styles unless overridden by a more specific style rule):
    Every story MUST have a refrain — a short repeated line that appears on at least 3 of the 5 pages, identically. Not a "Quick, X, quick!" tagged onto the end of a caption — that is NOT a refrain, that is a panic word. A refrain is a line the CHILD shouts along with, that names the goal or the obstacle.
    The refrain must:
      (a) Appear on pages 2, 3, and 4 in IDENTICAL form (not similar — identical).
      (b) Resolve or transform on page 5 ("Hold on, ladybird, hold on!" → "I've got you, ladybird, I've got you!").
      (c) Be self-contained — a 3-year-old must understand it without the surrounding sentences.
      (d) Be the GOAL or the SHARED EXPERIENCE, never just an exclamation. "Stop that balloon!" YES. "Oh no!" NO. "Quick, Pete, quick!" NO (it doesn't name what to do).
    EXAMPLE GOOD REFRAINS (age_3): "Catch that puppy!" / "Hold on, ladybird, hold on!" / "Round and round we go!" / "Don't drop the egg!"
    EXAMPLE BAD REFRAINS: "Quick, Pete, quick!" (vague — quick to do what?) / "Oh no!" (no information) / "What a day!" (not a goal) / a refrain that only makes sense on one page.
    SELF-CHECK BEFORE FINISHING: Read pages 2, 3, 4 aloud. Is the SAME line in all three? If no, rewrite. If your refrain is "Quick, [name], quick!" — that fails. Replace it with the actual goal.
    PAGE 1 MUST ANSWER THREE QUESTIONS A 3-YEAR-OLD CAN UNDERSTAND:
    1. What is wrong? (something physical and visible — not abstract)
    2. What must the character do to fix it? (a simple physical action)
    3. Why does THAT fix THIS? (the connection must be obvious)
    A 3-year-old must hear page 1 and understand the WHOLE plan. If the child would ask "but why?" then the logic is broken.
    GOOD PAGE 1: "Drip, drip, DRIP! Oh no — the kitchen tap won't stop! Water is climbing up Lily's toes, up to her knees, all the way to the cupboards! Lily grabs the big silver handle and pulls. Pulls and pulls and pulls. But it won't budge! 'Turn, handle, turn!'" (What's wrong = water rising. What to do = turn the handle. Why = handle stops the tap. Logic test passed — and it READS like a storybook, not a caption.)
    GOOD PAGE 1: "Whoosh — there goes the puppy! Tail wagging, ears flapping, paws skittering across the grass — straight for the open gate! Mia stretches out her hands. 'Stop, puppy, stop!' But he is fast. So fast. The big road is just past the gate. 'Catch that puppy!'" (What's wrong = puppy escaping. What to do = catch him. Why = stops him reaching the road. Logic test passed — and the parent's voice has somewhere to go.)
    BAD PAGE 1: "The sunflowers are growing! Find the gnome before the petals fall!" (What's wrong = flowers growing... bad? What to do = find gnome. Why = ??? What does a gnome have to do with flowers growing? A 3-year-old would be lost.)
    Every page after page 1 must show the character WORKING TOWARD the plan from page 1. Each attempt must clearly be trying to do the thing page 1 said to do. The child follows along because they KNOW what the character is trying to do and they're cheering them on.

    WRITE LIKE — STUDY THESE THREE MECHANICS, DO NOT JUST NAME-CHECK THE BOOKS:

    MECHANIC 1 — *We're Going on a Bear Hunt* by Michael Rosen: Cumulative obstacle pattern with onomatopoeia for the texture of moving through it. "We can't go over it, we can't go under it, oh no, we've got to go through it!" repeats EVERY page. Then a sound for the texture (swishy swashy, splash splosh, squelch squerch).
    ❌ NOT: "Pete sails his big leaf boat. But a grumpy frog blocks the way. He will not move! Quick, Pete, quick!"
    ✅ YES: "Uh-oh — a great big grumpy frog! We can't go over him. We can't go under him. We've got to go ROUND him! Splish, splosh, splish, splosh — round we go!"

    MECHANIC 2 — *Peace at Last* by Jill Murphy: A repeating chorus of frustration with new sound-makers each page. "Mr Bear could not get to sleep" returns every spread, with a different noise stopping him. The pattern is COMFORT through repetition; the comedy is in the variation.
    ❌ NOT: "The water starts to spin. Gurgle, gurgle! The ladybird is scared. Can Pete reach her?"
    ✅ YES: "Round and round, gurgle, gurgle — the puddle is spinning! The ladybird wobbles. The leaf wobbles. Pete wobbles too. 'Hold on, ladybird, hold on!'"

    MECHANIC 3 — *Owl Babies* by Martin Waddell: A short repeated worry-line from one character that lands harder each time. "I want my mummy!" Three short beats. Real feeling, gentle scale.
    ❌ NOT: "The leaf boat is too slow. The drain is pulling them down. Pete cannot reach. Quick, Pete, quick!"
    ✅ YES: "The drain pulls — slurp, slurp, slurp. Pete reaches. He can't quite. He can't quite. 'Hold on, ladybird! Hold on, hold on!'"

    THE COMMON THREAD: A 3-year-old story is NOT three short declarative sentences in a row. It is a PERFORMANCE — repetition WITHIN the page (round and round, hold on hold on), a refrain that returns every page, sound words that come from the action, and a parent's voice that has SOMEWHERE TO GO. If your page reads like an event report ("X happens. Then Y happens. Then Z happens.") you have written a caption, NOT a story. Rewrite it.

- **PRESCHOOL PERFORMANCE (age_4):** 3-5 sentences per page. This is a one-person show for the parent.
    PAGE 1 STORY LOGIC (age_4): The same three questions apply but with more detail. The child must understand: what's the problem, what's the plan, and WHY the plan will work. Every page after must visibly work toward that plan.
    GOOD: "The oven won't stop! Bread is growing and growing and pushing out the door! Kiki must pull the plug out before the bread fills the whole kitchen. But the plug is behind the oven — and the bread is in the way!"
    BAD: "The meatballs are flying! If they hit the big button the rocket will zoom away!" (What button? What rocket? Why is there a rocket in a kitchen? The child is confused before the story even starts.)
    VOCABULARY (age_4 — THE TODDLER MOUTH TEST): Every word must be one a 4-year-old would SAY unprompted at preschool. 3+ syllable words are almost always wrong. "Suddenly" → "then". "Enormous" → "huge". "Ceiling" → "the top". Write how they talk, not how books sound.
    Every page needs: something physical to describe (sticky, wobbly, crunchy), dialogue in a funny voice, and a hook that makes the child gasp. Sound words only when earned — see the sound word rule above.

    WRITE LIKE — STUDY THESE THREE MECHANICS, DO NOT JUST NAME-CHECK THE BOOKS:

    MECHANIC 1 — *The Gruffalo* by Julia Donaldson: Triplet of attributes with the same adjective stacked, then a punch line. "He has terrible tusks, and terrible claws, and terrible teeth in his terrible jaws." Build, build, build, SNAP.
    ❌ NOT: "Up, up, up goes the balloon! It picks up Dolly and her bed too. Mr. Pip the balloon man shouts, 'Stop that balloon!'"
    ✅ YES: "Up went the rope, and up went the pole, and UP went Dolly's whole wavy bed! 'Oh fiddlesticks!' shouted Mr Pip the balloon man, hopping on one foot. 'Stop that whale!'"

    MECHANIC 2 — *Room on the Broom* by Julia Donaldson: Internal rhyme and a chorus. "The witch had a cat and a hat that was black, and long ginger hair in a braid down her back." Every page has a beat you could clap to.
    ❌ NOT: "The wind is very loud. It shakes the big balloon round and round. Dolly looks with her big, wide eyes."
    ✅ YES: "The wind it BLEW and the balloon it SHOOK, round and round with a wibble and a wook. Dolly's eyes went wide as a plate. 'Oh no,' she gasped. 'It's getting late!'"

    MECHANIC 3 — *The Tiger Who Came to Tea* by Judith Kerr: A funny voice the parent gets to do, dropped right into the action. Dialogue is the engine, not the description.
    ❌ NOT: "Dolly rubs the inside of her bed on the pole. The metal gets very slick. The rope slips off."
    ✅ YES: "Dolly had a BIG idea. She rubbed her bed on the pole — rub-a-dub-DUB! Rub-a-dub-DUB! 'Slippy enough yet?' she huffed. 'Slippier!' wheezed Mr Pip. Rub-a-dub-DUB! And — SLIDE! Off slipped the rope!"

    THE COMMON THREAD: At age_4 the parent is putting on a SHOW. Every page needs ONE moment of dialogue with attitude, ONE beat with rhythm or rhyme, and ONE punch line. If your page is just describing what happens in third person, you have written a film script, NOT a story. Rewrite it with a voice in it.

- **PICTURE BOOK NARRATIVE (age_5):** 4-6 sentences per page. More plot complexity than age_4 but same performability.
    PAGE 1 STORY LOGIC (age_5): The problem can have a bit more nuance, but the plan must still be clear. The child needs to understand what's going wrong, what the hero must do, and why that specific action will work. Stakes can be a touch more abstract (losing something treasured, letting someone down) but the physical action is still concrete.
    VOCABULARY (age_5): Slightly richer than age_4 — a few "mouth-feel" words are welcome (wobbly, grumbling, splinters, whispered) but anything a 5-year-old wouldn't recognise is cut.

    WRITE LIKE: *Stick Man* by Julia Donaldson, *The Day the Crayons Quit* by Drew Daywalt, *Zog* by Julia Donaldson. Characters have distinct voices the parent can do. Internal thoughts allowed briefly. Callbacks: an earlier detail returns in the resolution. Emotional beat on page 4 before the win on page 5.

- **STORYTIME (age_6, age_7):** 80-120 words per page. Character tries, fails, grows. Dialogue and internal thoughts.
    WRITE LIKE: *The Enormous Crocodile* by Roald Dahl, *Flat Stanley* by Jeff Brown, *Horrid Henry* by Francesca Simon. Dialogue drives scenes. Characters have clear voices and attitudes. Sly humour, mild peril. Rich vocabulary ("bamboozled", "flabbergasted", "squelching") used without apologising. The reader is now in the story alongside the hero.

- **CHAPTER BOOK (age_8, age_9, age_10):** 150-250 words per page. Complex twists, metaphor, dry humour. Rich world-building matching detailed colouring pages.
    WRITE LIKE: *Charlie and the Chocolate Factory* by Roald Dahl, *The Worst Witch* by Jill Murphy, *The Boy in the Dress* by David Walliams. Layered sentences with texture. Metaphor lands without explanation. Dry wit. Inner life + outer action. Chapter-book feel — the reader is a reader now.

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
BANNED: investigate, magnificent, structure, ancient, cascade, illuminated, mechanism, delicate, precisely, extraordinary.""")

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
            top_p=TOP_P,
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
        
        # Log prompt details for debugging NO_CANDIDATES
        print(f'[GEMINI-STORY] DEBUG — character: {character_name}, theme: {theme_name}, age: {age_level}')
        print(f'[GEMINI-STORY] DEBUG — user_prompt length: {len(user_prompt)} chars')
        print(f'[GEMINI-STORY] DEBUG — system_prompt length: {len(SYSTEM_PROMPT)} chars')
        print(f'[GEMINI-STORY] DEBUG — first 500 chars of user_prompt: {user_prompt[:500]}')
        
        for retry_num, delay in enumerate([3, 6, 12, 20], start=1):
            print(f'[GEMINI-STORY] Retry {retry_num}/4 after {delay}s delay...')
            __import__('time').sleep(delay)
            response = client.models.generate_content(
                model=MODEL,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    response_mime_type="application/json",
                    temperature=TEMPERATURE,
                    top_p=TOP_P,
                    thinking_config=types.ThinkingConfig(
                        thinking_level=THINKING_LEVEL
                    ),
                ),
            )
            elapsed = time.time() - start
            if response.text is not None:
                print(f'[GEMINI-STORY] Retry {retry_num} succeeded after {elapsed:.1f}s')
                break
            try:
                fr = response.candidates[0].finish_reason if response.candidates else 'NO_CANDIDATES'
                print(f'[GEMINI-STORY] Retry {retry_num} also empty. finish_reason={fr}')
            except:
                print(f'[GEMINI-STORY] Retry {retry_num} also empty.')
        if response.text is None:
            raise ValueError("Gemini returned empty response after 4 retries")

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
                top_p=TOP_P,
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

*** HERO RULE (READ THIS FIRST — NON-NEGOTIABLE) ***
The MAIN CHARACTER is the hero. They solve the problem. They do the final action that fixes everything. Your pitch must make this clear: the hero saves the day, not the supporting character.
PITCH TEST: When you describe how the story ends, who DOES the action that fixes it? It must be the main character. If your pitch ends with "the friendly crane stacks them all neat and tidy" — WRONG. Rewrite so the hero does it (with help, with a tool, with an idea — but the hero's hands).

*** MISSION TEST (READ THIS SECOND — NON-NEGOTIABLE) ***
Every pitch must be GOAL-SHAPED, not SETTING-SHAPED. The pitch must state a specific physical MISSION the hero must carry out — using objects, obstacles, and stakes that are ACTUALLY IN THE PITCH. A pitch is not a backdrop the writer can ignore; it is the contract the story must deliver on.
TEST: After you write the pitch, ask "What exactly does the hero have to DO, using what, to fix what, before what happens?" If any of those four answers are vague or missing, the pitch is setting-shaped and the story writer will invent a random goal to patch it.
BAD: "A garden where heavy clouds have fallen from the sky." (Setting-shaped — no mission. What does the hero DO? What happens if they fail?)
GOOD: "Heavy wet clouds have fallen from the sky and landed in Sheepy's garden — she must hook them onto the tall flowers so they dry and float away, before the water washes all the flowers away." (Goal: hook clouds onto flowers. Object: clouds. Stakes: flowers wash away. Writer now has something real to work with.)
BAD: "A bus full of bouncy balls." (Setting — no mission.)
GOOD: "All the bouncy balls have come loose on the bus — the hero must collect them before the next stop, or they'll all roll out the open doors and be lost forever." (Goal: collect. Stakes: lost at next stop. Escalation built in — the stop is coming.)
Every pitch MUST pass this test.
*** SUPPORTING CHARACTER RULE ***
Your pitch SHOULD include a supporting character — but ONLY to make the hero's job HARDER, richer, or more interesting. Supporting characters are obstacles, complications, and texture. They are NOT co-stars and NEVER replacement-solvers.
Pick ONE role for the supporting character (vary the role across pitches — do NOT default to "blocker" every time):
- BLOCKER: in the way, won't move, stole the thing
- CAUSE: pressed the button, knocked it over, started the mess
- COMPLICATION: needs the hero's help WHILE the hero is fixing the main thing
- PUZZLE-HOLDER: has a clue/tool but won't hand it over easily
- DRAG: scared/slow/stubborn — hero has to bring them along anyway
- CHAOS-AGENT: trying to "help" and accidentally making things worse
- TOOL-PROVIDER: hands the hero a tool/clue — hero then USES it themselves
TEST: Remove the supporting character. Is the story EASIER for the hero? Good — they were doing their job. Is the story IMPOSSIBLE without them? Bad — they've taken the hero's role. Rewrite.
ROLE VARIETY EXAMPLES:
- BLOCKER: "A grumpy chalk monster blocks the bridge and won't move until he gets a snack." (Hero finds a way past — hero crosses the bridge.)
- CHAOS-AGENT: "A bouncy puppy keeps stealing the pieces the hero is trying to fit together and burying them in the garden." (Hero outsmarts the puppy AND fixes the thing.)
- COMPLICATION: "A scared little brother clings to the hero's leg the whole story, making every step harder." (Hero still does the saving — just with a small person attached.)
- TOOL-PROVIDER: "A friendly fish pushes a long stick toward the hero through the water." (Hero uses the stick to hook the floating bucket.)
BAD: A random cute animal who watches from the side and gives a hug at the end — removing it changes nothing.
BAD: A clever helper who actually solves the problem — that's the hero's job.

*** GROUNDED SETTING RULE (CRITICAL — READ THIS FIRST) ***
The story setting MUST be describable in 1-3 words that a child already knows. The Gruffalo — the best-selling children's book in UK history — is set in "a deep dark wood." Not a clockwork forest. Not a crystal dimension. Just a wood. The magic comes from WHO you meet and WHAT goes wrong, not from the setting itself being complicated.

Study the top children's books: The Gruffalo = a wood. Tiger Who Came to Tea = a kitchen. We're Going on a Bear Hunt = a field, a river, mud. Owl Babies = a tree. Peter Rabbit = a garden. Dear Zoo = a zoo. Shark in the Park = a park. Peace at Last = a bedroom. Where the Wild Things Are = a bedroom. These are all ONE simple place.

FOR under_3, age_3, age_4:
The setting must be a place a child can say in 1-3 words: a wood, a kitchen, a park, a shop, a bedroom, a school, a bath, a beach, a zoo, a farm, a playground, a garden, a pond, a hill, a field, a bus, a boat, a tree.
Then ONE thing in that place goes wonderfully wrong. That's the whole story.
The setting is the STAGE. The chaos is the SHOW. Keep the stage simple so the chaos shines.
NEVER invent the setting. No clockwork forests, no gear worlds, no cracker moons, no crystal caves, no candy planets, no music dimensions. If a child can't draw the setting from memory, it's too complicated.

*** CHAOS-FROM-SETTING RULE (CRITICAL) ***
The chaos, the obstacle, AND the consequence must all come FROM the setting itself. A kitchen's own objects go bonkers — the oven, the tap, the pots, the food. A garden's own plants grow wild. A bath's own water rises. NEVER bolt a fantasy element onto a real place.
BAD: "A kitchen where meatballs hit a rocket launch button" — there is no rocket button in a kitchen. A child would ask "why is there a button in the kitchen?"
BAD: "A park where the swings open a portal" — there are no portals in a park.
GOOD: "A kitchen where the oven won't stop cooking and food keeps growing and bursting out of the door" — ovens ARE in kitchens, food growing out of control is exciting AND makes sense.
GOOD: "A bath where the bubbles won't stop and they're filling up the whole house" — bubbles ARE in baths, the house flooding with bubbles is thrilling AND grounded.
GOOD: "A garden where the plants are growing so fast they're pushing through the windows" — plants ARE in gardens, them taking over is scary-fun AND logical.
The consequence must be BIG, VISUAL, and ESCALATING — but it must come from things that are actually IN that place. Turn the setting's own stuff up to eleven.

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
    # SHEEPY-PATTERN SEEDS — real places, real phenomena, scale gone wrong, real stakes
    # For under_3, age_3, age_4
    "a kitchen where someone left the tap on overnight and the puddle is creeping toward the cat's bed",
    "a garden where the wind has blown all the washing off the line and tangled it round the apple tree",
    "a bath where the bubbles won't stop pouring out and they're starting to come out under the door",
    "a bedroom where a soft toy has fallen behind the radiator and the smell is getting smelly",
    "a park where it has rained so hard the picnic blanket is floating away on a brand new puddle",
    "a kitchen where someone left a bag of flour open and the cat has knocked it everywhere",
    "a school cloakroom where every coat has fallen off its peg and the bell is about to ring",
    "a garden where ivy has grown over the back gate in the night — and the dog is on the wrong side",
    "a kitchen where a pot of jam tipped over on the table and it's dripping toward the new books",
    "a beach where the tide is coming in fast and a sandcastle with a crab inside is about to wash away",
    "a bedroom where someone left the window open and now the curtains are wrapped round the lamp",
    "a kitchen where the freezer door popped open in the night and the floor is a slippery ice cream river",
    "a garden where a hose was left running and the vegetable patch is turning into a small pond",
    "a hallway where the post has piled up against the door and you can't push it open",
    "a kitchen where the cat has knocked the fruit bowl off the shelf and apples are rolling everywhere",
    "a back garden where the leaves have piled up so high they've covered the rabbit hutch",
    "a kitchen where bread dough was left to rise and it's pushed the bowl off the counter",
    "a bedroom where a crayon got left under a cushion and now the cushion has a long colourful stripe across it",
    "a bath where the plug won't come out and the water keeps rising — toys floating higher and higher",
    "a kitchen where the porridge boiled over and is creeping across the hob toward the toaster",
    "a garden where a windy day has scattered the seed packets and the birds are arriving fast",
    "a hallway where snow has blown in through the letterbox and is melting into a slippery patch",
    "a kitchen where someone forgot to put the lid on the blender and there's smoothie up the wall",
    "a garden where a paddling pool has tipped over and the water is rolling toward the bottom of the hill — and granny's deckchair",
    "a back garden where weeds have grown right through the trampoline net overnight",
    "a kitchen where a bag of pasta split in the cupboard and shells are pouring out every time someone opens the door",
    "a park bench where someone left their packed lunch and the squirrels have found it",
    "a bath where the soap has slid down the plug hole and got stuck — the water won't drain and the next person needs a bath",
    "a kitchen where the kettle was left whistling so long the steam has filled the whole room",
    "a back garden where bees have built a small nest on the swing — and a birthday party is starting in an hour",
    "a hallway where the cat has dragged a long piece of string from upstairs all the way to the front door",
    "a kitchen where someone forgot the eggs were boiling and the saucepan is jumping like mad",
    "a garden where the gate has blown open and the rabbit has hopped out — only the wet grass shows where",
    "a bedroom where a glass of water tipped over in the night and the carpet is slowly turning dark",
    "a kitchen where a cake in the oven has risen so high it's pushing the oven door open from the inside",
    "a back garden where the football has rolled into the long grass and the grass is taller than the hero",
    "a kitchen where the dog has pulled the tea towel off the hook and is dragging it through every room",
    "a hallway where rain has come in through an open skylight and is dripping right onto the cat's cushion",
    "a garden where the wind keeps lifting the tablecloth off the picnic table and the sandwiches keep flying",
    "a bedroom where the duvet has slid off the bed and underneath it is the missing teddy — but also a sleeping cat",
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

*** WHAT MAKES A GREAT TODDLER STORY CONCEPT ***
Think of the best toddler books: Dear Zoo, That's Not My Teddy, We're Going on a Bear Hunt, Each Peach Pear Plum. They share:
1. ONE simple mission the child understands instantly (catch it, find it, stop it, reach it)
2. A REAL place or situation (a garden, a house, a park, a farm)
3. Something going wrong that gets WORSE each page

*** THE TODDLER TEST ***
Can you say the whole story in one sentence a 2-year-old would understand?
GOOD: "The ball keeps rolling away and she has to catch it!" — a toddler gets this instantly.
GOOD: "The tower is falling and he has to catch the star!" — clear, physical, urgent.
BAD: "The sunflowers are growing and she needs to find the gnome before the petals fall." — too many unconnected ideas.

*** CONCEPT RULES ***
- The WANT must be physical and immediate: catch, reach, stop, find, push, pull
- The OBSTACLE must be visible: it's stuck, it's too high, it's rolling away, it's hiding
- The SETTING must be a place a toddler knows: a house, a garden, a park, a bath, a shop, a farm
- A supporting character or animal should appear — even simple (a duck, a cat, a snail)
- Every page must look DIFFERENT as a colouring page — the character moves to new spots

*** WHAT TO AVOID ***
- Abstract problems (feelings, lessons, sharing, being brave)
- Fantasy worlds a toddler has never seen
- Stories that need explaining — if the concept isn't obvious from the title, it's too complicated
- Multiple unconnected elements (gnomes + sunflowers + falling petals = confusing)

*** BLURB TONE ***
Blurbs must sound like a mess happening RIGHT NOW. Nouns and noises only.
BAD: "Kiki learns about sharing with her friends at the park."
GOOD: "The ball won't stop bouncing and it's heading straight for the pond!"
NO questions. State the chaos.
""",

    "age_4": """
AGE GROUP: 4 YEARS OLD

*** WHAT MAKES A GREAT AGE 4 STORY CONCEPT ***
Think of the best age 4 books: The Gruffalo (a wood), Tiger Who Came to Tea (a kitchen), Oi Frog (a pond), Supertato (a supermarket). They all share three things:
1. A SIMPLE SETTING the child knows (a place they can say in 1-3 words)
2. ONE BONKERS THING happening in that setting
3. A SUPPORTING CHARACTER with personality who either causes or blocks the problem

Your pitch must have ALL THREE. If the setting needs explaining, it's too complicated. If there's no supporting character, the story will feel empty.

*** THE CONCEPT TEST ***
Read your pitch aloud to an imaginary 4-year-old. Would they:
- Immediately picture where the story happens? (If no → simpler setting)
- Understand what the character needs to do? (If no → clearer mission)
- Know what goes wrong if they fail? (If no → bigger consequence)
- Want to know what happens next? (If no → more exciting concept)

*** SUPPORTING CHARACTER ***
Every pitch MUST include a supporting character who is ESSENTIAL to the story. They must either BE the obstacle, CAUSE the problem, or HOLD the key to solving it. They need ONE personality trait the parent can voice (grumpy, scared, bossy, silly, sneaky).
GOLD STANDARD: A grumpy chalk monster blocking the bridge who won't move until he gets a snack.

*** WHAT TO AVOID ***
- Fantasy worlds a child has never been to (clockwork forests, candy planets, cracker moons)
- Stories that only work if you explain the rules of the world first
- Concepts where the supporting character is decorative furniture (a random robot watching)
- Problems that don't match their solutions (playing music to fix cracks)
- Abstract obstacles (noise, darkness, feelings) — use physical, visible obstacles

*** BLURB TONE FOR THIS AGE ***
Blurbs must hook with a silly consequence. Focus on funny mistakes and physical mess.
GOOD: "Ted's giant feet have got tangled in the cake stand and now the whole table is tipping over!"
BAD: "Ted learns that being careful is important when baking."
End with the character in a silly impossible position, not a question.
""",

    "age_5": """
AGE GROUP: 5 YEARS OLD

*** WHAT MAKES A GREAT AGE 5 STORY CONCEPT ***
Think of: Zog, Supertato, Superworm, Dogger, Giraffes Can't Dance. They share:
1. A setting kids know from play or stories (a school, a castle, a shop, a jungle, a stage)
2. A clear PROBLEM with real stakes — someone needs rescuing, something is going wrong, a plan is failing
3. A SETBACK where it looks like it won't work out — then a surprising solution
4. A supporting character who HELPS or HINDERS — not just watches

Age 5 can handle slightly more complex settings than age 4 — a pirate ship, a magic school, a dragon's cave — as long as kids can picture it from play or TV. But the CONCEPT still needs to be explainable in one sentence.

*** SUPPORTING CHARACTER ***
Must be essential to the plot — they either cause the problem, block the solution, or provide the key. They need personality the parent can voice.

*** WHAT TO AVOID ***
- Concepts that need a paragraph to explain
- Settings with made-up rules the child can't intuit
- Problems solved by "trying harder" or "believing in yourself"
- Supporting characters who just cheer from the sidelines

*** BLURB TONE FOR THIS AGE ***
Blurbs must present a surreal what-if with clear stakes.
GOOD: "Oli's photos have swapped all the colours — the sky is now the ground and it's spreading fast!"
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
Generate 3 UNIQUE story themes for a character called "{character_name}"{f" and their companion {second_character_name}" if second_character_name else ""}. You will design the story CONCEPTS first, then read the character description and cast them into those concepts.

STEP 1 — DESIGN 3 STORY CONCEPTS (before thinking about the character)

⚠️ DO THIS FIRST — before you look at the character description below.

Invent 3 story concepts that follow the GROUNDED SETTING RULE from your system instructions. Each concept needs: a SIMPLE SETTING (a place a child can say in 1-3 words), ONE BONKERS THING happening there, and a SUPPORTING CHARACTER with personality.

Here are 3 STARTING SPARKS to inspire you. Adapt, remix, or ignore them — but your concepts must follow the same pattern of "a real place + one thing goes wonderfully wrong":
{seeds_block}

⚠️ OVER-USED PREMISES — SKIP THESE: Recent stories have massively over-used these three shapes. Do NOT pitch any of the following unless the seeds above explicitly suggest them:
1. A GIANT MAGNET pulling metal things (spoons, buses, cars, shelves) — this has been used far too much. Reach for a different cause.
2. MARCHING/PARADING TOYS escaping a toy shop — over-used. Find another shop or different chaos.
3. THINGS HAVE TURNED INTO OTHER THINGS ("the floor turned to ice", "the hall turned to magnet") — over-used transformation shape.
If you find yourself reaching for any of these, STOP and pick a different premise. Variety is the whole point.

THESE ARE JUST EXAMPLES — invent your own. Each concept must be:
1. VISUALLY RICH — each of the 5 episodes must look completely different when drawn as a colouring page. If you can't imagine 5 distinct illustrations, the concept isn't good enough.
2. GRIPPING — a parent reads the title and the child says "I WANT THAT ONE!"
3. VARIED ACROSS THE 3 PITCHES — no two can share the same setting or the same type of problem.

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
4. FRESHNESS RULE: Reject any story idea that can be summarised as "Character learns a lesson" or "Character finds a lost toy." Only accept ideas where something physical goes hilariously wrong in a place a child knows — the oven won't stop, the bath overflows, the slide goes wobbly, the dog won't come back. The parent should look at the title and think "that sounds fun!" — not "oh, another lesson story."
5. LOGIC CHAIN TEST: Say your story logic as a chain: "A because B because C." If ANY link needs explaining to a child, simplify it. Every connection must be obvious. GOOD: "Tap flooding → turn handle → handle is stuck behind the fridge." BAD: "Moon crumbling → play music box → moon stops." Why does music fix crumbling? If a child would ask "but why?" at any link, the chain is broken.
6. DISTANCE RULE: The solution must NOT be immediately available on page 1. The character must need 5 pages to GET to it. The solution is far away, hidden, blocked, or requires something they don't have yet. If the character could just solve the problem immediately, the story has no reason to exist.

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
