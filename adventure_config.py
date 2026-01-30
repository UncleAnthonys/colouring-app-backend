"""
🎨 My Character's Adventures - Configuration & Story Data
==========================================================

Complete configuration for the adventure story system including:
- Age complexity rules (matching existing Little Lines system)
- Story data for all adventure themes
- Character prompt templates
- Episode scene prompts

Add to backend folder: ~/Downloads/kids-colouring-app/backend/adventure_config.py
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

# =============================================================================
# AGE COMPLEXITY RULES (Matching existing Little Lines system)
# =============================================================================

AGE_RULES = {
    "under_3": {
        "age": "Under 3 years",
        "colourable_areas": "8-10",
        "rules": """
AGE GROUP: UNDER 3 (BLOB STYLE)

CRITICAL RULES:
- EXTREMELY THICK outlines (6-8px stroke width)
- BLOB/KAWAII style - everything is rounded chunky shapes
- Maximum 5-7 colourable areas in ENTIRE image
- Face: just 2 dots for eyes, simple curve smile
- Character fills 80-90% of the page
- Think "baby's very first coloring page"

SCENE: MINIMAL
- Pure white OR just a simple ground line
- Maximum 1 story element (just the magic door OR just 1 mushroom)
- NO fairies, NO detailed trees, NO multiple objects
- The character IS the scene

STYLE:
- Like a rubber stamp or cookie cutter shape
- Toddler-friendly chunky blob shapes
- Could be colored with a fist holding a crayon

BANNED: Multiple objects, thin lines, details, background scenery, patterns
"""
    },
    "age_3": {
        "age": "3 years",
        "colourable_areas": "10-12",
        "rules": """
AGE GROUP: 3 YEARS OLD

CRITICAL RULES:
- EXTREMELY THICK outlines (5-6px stroke width)
- Blob/kawaii style - super rounded chunky shapes
- Maximum 8-10 colourable areas in ENTIRE image
- Face: dots for eyes, simple curve for mouth
- Character fills 70-80% of the page
- Think "baby's first coloring book"

SIMPLE SCENE:
- Add 1-2 VERY SIMPLE large shapes (big sun, big cloud, or big mushroom)
- Ground line is okay
- Keep background elements HUGE and SIMPLE - same blob style as character
- Each element = 1 simple colourable area

BANNED: Thin lines, patterns, small details, multiple objects, complex shapes
"""
    },
    "age_4": {
        "age": "4 years",
        "colourable_areas": "15-18",
        "rules": """
AGE GROUP: 4 YEARS OLD

RULES:
- VERY THICK outlines (4-5px stroke width)
- Maximum 10-14 colourable areas
- Simple blob-like shapes
- Face: dots for eyes, simple smile
- Character fills 50-60% of page

SIMPLE SCENE ELEMENTS:
- Add 2-3 SIMPLE large shapes for setting (cloud, sun, tree, flower, mushroom)
- Ground line with simple grass bumps
- Keep all elements LARGE and ROUNDED
- Scene elements use same thick lines as character

BANNED: Patterns, small details, thin lines, complex shapes
"""
    },
    "age_5": {
        "age": "5 years",
        "colourable_areas": "20-25",
        "rules": """
AGE GROUP: 5 YEARS OLD

RULES:
- THICK outlines (3-4px stroke width)
- Maximum 15-20 colourable areas
- Simple rounded figures
- Basic clothing shapes (no patterns)
- Character fills 45-55% of page

SCENE ELEMENTS:
- Add 3-4 simple background elements related to the story
- Simple trees, flowers, clouds, sun, basic mushrooms
- Ground with simple grass or path
- Elements should be simple shapes but recognizable
- Good spacing between all elements

BANNED: Patterns, tiny details, complex overlapping
"""
    },
    "age_6": {
        "age": "6 years",
        "colourable_areas": "25-30",
        "rules": """
AGE GROUP: 6 YEARS OLD

RULES:
- Medium outlines (2-3px stroke width)
- 25-30 colourable areas
- Full themed background
- Detailed costumes, expressive faces
- Simple patterns on clothing okay
- Character fills 30-40% of page

SCENE COMPOSITION:
- Rich story scene with 6-8 background elements
- Foreground and background separation
- Setting-appropriate details (fairy village, forest, underwater, etc.)
- Secondary characters welcome (fairies, animals, friends)
- Environmental storytelling - props and objects from the story
- Some layering okay with clear outlines

BANNED: Very intricate patterns, tiny details under 0.5cm
"""
    },
    "age_7": {
        "age": "7 years",
        "colourable_areas": "30-35",
        "rules": """
AGE GROUP: 7 YEARS OLD

RULES:
- Medium outlines (1.5-2.5px stroke width)
- 30-35 colourable areas
- More detail WITHIN objects
- Hair sections, clothing patterns allowed
- Multiple characters okay
- Character fills 25-35% of page

SCENE COMPOSITION:
- Rich, detailed story scene with 8-10 elements
- Clear foreground/midground/background
- Architectural details on buildings
- Nature with texture (leaves, bark, grass)
- Action and movement in the scene
- Story-relevant props and environmental details
- Depth through overlapping with clear outlines
"""
    },
    "age_8": {
        "age": "8 years",
        "colourable_areas": "40-45",
        "rules": """
AGE GROUP: 8 YEARS OLD

RULES:
- Medium-thin outlines (1-2px stroke width)
- 40-45 colourable areas
- More intricate patterns allowed
- Detailed accessories
- Character fills 20-30% of page

SCENE COMPOSITION:
- Rich, detailed background scenes with 10-12 elements
- Complex environments with depth
- Texture variety (wood grain, stone, foliage, fabric)
- Weather and atmospheric elements welcome
- Dynamic compositions with interesting angles
- Multiple characters with expressions
- Detailed props and story elements
"""
    },
    "age_9": {
        "age": "9 years",
        "colourable_areas": "50-65",
        "rules": """
AGE GROUP: 9 YEARS OLD

RULES:
- Fine outlines (0.75-1.5px stroke width)
- 50-65 colourable areas
- 90% of page filled with content
- Large themed landmarks included
- Complex patterns allowed

SCENE COMPOSITION:
- Highly detailed scenes with 12-15 elements
- Professional illustration quality
- Strong sense of depth and perspective
- Detailed textures throughout
- Atmospheric effects (light rays, sparkles, mist)
- Complex character poses and expressions
- Rich environmental storytelling
- Cinematic framing
"""
    },
    "age_10": {
        "age": "10+ years",
        "colourable_areas": "70-90",
        "rules": """
AGE GROUP: 10+ YEARS OLD

RULES:
- Fine thin outlines (0.5-1px stroke width)
- 70-90 colourable areas
- Fill ALL empty space
- Dense and intricate
- Complex patterns and textures
- Maximum detail

SCENE COMPOSITION:
- Adult coloring book quality
- 15-20 detailed elements filling the scene
- Sophisticated compositions with dynamic angles
- Multiple depth layers with atmospheric perspective
- Intricate textures on all surfaces
- Detailed character anatomy and expressions
- Complex environmental storytelling
- Decorative patterns where appropriate
- Cinematic, dramatic framing
"""
    }
}


# =============================================================================
# MASTER PROMPTS
# =============================================================================

MASTER_COLORING_PROMPT = """
This is a colouring book page for children.

ABSOLUTE REQUIREMENTS:
- BLACK LINES ONLY on pure WHITE background
- NO colours, NO grey, NO shading
- All shapes must be fully enclosed for colouring
- Lines must be continuous and smooth
- Print-friendly output
- NO text or titles in the image

{age_rules}
"""

CHARACTER_REFERENCE_PROMPT = """Create a Disney/Pixar-style character illustration for a children's storybook.

CHARACTER: {name}

EXACT APPEARANCE (preserve these details precisely):
{character_description}

PERSONALITY: {personality}

COLOR PALETTE: {colors}

STYLE REQUIREMENTS:
- Disney/Pixar animation quality - expressive, charming, appealing
- Big expressive eyes with catchlights
- Warm, inviting character design
- Dynamic pose showing personality
- Soft painterly background with gentle bokeh/sparkles
- Character fills 80% of frame
- This is the HERO REVEAL - make them look like the star of their own movie!

CRITICAL - PRESERVE THE CHILD'S DESIGN:
- If the outfit has LAYERS or SECTIONS, draw them as distinct separate areas
- If there are BUTTONS, include the buttons
- If there are PATTERNS, include the patterns
- The child designed this character - honor their creative choices exactly!
"""

EPISODE_SCENE_PROMPT = """Create a BLACK AND WHITE COLOURING PAGE for children.

{master_prompt}

=== THE MAIN CHARACTER - MUST BE DRAWN EXACTLY AS DESCRIBED ===
Character Name: {character_name}

{character_description}

KEY IDENTIFYING FEATURE: {key_feature}

⚠️ CRITICAL: This is a SPECIFIC character from a child's drawing, NOT a generic character.
The child will be looking for THEIR character's unique features.

=== SCENE: "{episode_title}" ===
{scene_description}

=== COMPOSITION ===
- {character_name} must be the LARGEST figure, clearly in the center/foreground
- {character_name}'s unique features must be clearly visible and recognizable
- Show {character_name}'s face with a happy, excited expression

OUTPUT: Pure black outlines on pure white background. Ready for a child to colour with crayons.
"""


# =============================================================================
# ADVENTURE THEMES
# =============================================================================

ADVENTURE_THEMES = {
    "forest": {
        "name": "Enchanted Forest",
        "description": "A magical forest adventure with fairies, friendly dragons, and rainbow crystals",
        "icon": "🌳",
        "supporting_characters": ["Sparkle the Fairy", "Flicker the Dragon"],
        "settings": ["fairy village", "mushroom houses", "dark hollow", "magical trees"]
    },
    "underwater": {
        "name": "Ocean Quest", 
        "description": "An underwater adventure with fish friends, whales, and hidden treasure",
        "icon": "🌊",
        "supporting_characters": ["Finn the Fish", "Wally the Whale", "Ollie the Octopus"],
        "settings": ["coral reef", "sunken ship", "deep canyon", "underwater caves"]
    },
    "safari": {
        "name": "Savanna Friends",
        "description": "An African safari adventure with lions, elephants, and giraffes",
        "icon": "🦁",
        "supporting_characters": ["Zuri the Lion Cub", "Tembo the Baby Elephant", "Amara the Lioness"],
        "settings": ["watering hole", "acacia trees", "Pride Rock", "tall grass"]
    },
    "space": {
        "name": "Cosmic Journey",
        "description": "A space adventure with friendly aliens, rockets, and distant planets",
        "icon": "🚀",
        "supporting_characters": ["Zip the Alien", "Comet the Robot", "Luna the Moon Princess"],
        "settings": ["space station", "alien planet", "asteroid field", "moon base"]
    },
    "dinosaur": {
        "name": "Dino Discovery",
        "description": "A prehistoric adventure with friendly dinosaurs and ancient mysteries",
        "icon": "🦕",
        "supporting_characters": ["Rex the T-Rex", "Trixie the Triceratops", "Ptera the Pterodactyl"],
        "settings": ["volcano valley", "prehistoric jungle", "dinosaur nest", "tar pits"]
    }
}


# =============================================================================
# ENCHANTED FOREST ADVENTURE - COMPLETE STORY DATA
# =============================================================================

FOREST_ADVENTURE = {
    "theme_key": "forest",
    "title": "The Enchanted Forest",
    
    "episodes": {
        1: {
            "title": "Through the Magic Tree",
            "stories": {
                "under_3": "{name} finds a magic tree. There's a little door! A fairy waves hello.",
                "age_3": "{name} finds a big tree with a glowing door. A tiny fairy flies out and waves. \"Come play!\"",
                "age_4": "{name} sees a magical tree in the forest. A doorway glows in the trunk! A fairy named Sparkle says \"Come inside!\"",
                "age_5": "{name} discovers a glowing tree in the forest. A sparkly doorway shimmers in its trunk. Tiny fairies dance around it. \"Adventure awaits!\" they whisper.",
                "age_6": "{name} discovers a glowing magical tree in the forest. A doorway shimmers in its trunk, and tiny fairies dance around it. \"Come inside,\" they whisper. \"Adventure awaits!\"",
                "age_7": "{name} wanders into a clearing and gasps - an ancient tree pulses with magical light. A doorway carved into its trunk glows with invitation. Fairies spiral around it like living sparkles. \"We've been waiting for you,\" they chime together.",
                "age_8": "Deep in the forest, {name} discovers something extraordinary - an ancient oak tree emanating soft magical light. Intricate patterns glow around a doorway in its trunk. A group of fairies flutter excitedly around it. \"A visitor at last!\" one exclaims. \"Come inside - the Enchanted Forest awaits!\"",
                "age_9": "{name} pushes through the undergrowth and freezes in wonder. Before them stands an enormous oak tree, its bark etched with glowing runes. A perfectly arched doorway shimmers in its trunk, casting dancing lights on the forest floor. Fairies of all colors swirl around it like a living aurora. \"The prophecy spoke of one who would come,\" whispers the nearest fairy. \"We've waited a hundred years. Welcome, brave one.\"",
                "age_10": "The forest had always whispered of secrets, but {name} never imagined finding one like this. The ancient oak stands impossibly tall, its gnarled branches reaching toward the sky like protective arms. Luminescent runes spiral up its trunk, pulsing with an inner light that seems to breathe. The doorway carved into its heart radiates pure magic - warm, inviting, alive. Dozens of fairies cease their eternal dance to turn and stare. \"At last,\" the eldest breathes, her wings shimmering with centuries of wisdom. \"The one the trees have sung about. Come, young hero. Your adventure begins now.\""
            },
            "scene": """
SCENE: {name} discovers the enchanted tree

DRAW:
- {name} {character_pose} reaching toward the tree, looking excited
- A large magical tree with a glowing arched doorway in the trunk
- 2 small fairies with delicate wings flying nearby
- Magical sparkles and stars around the doorway
- Spotted mushrooms at the base of the tree
- Simple grass and flowers on the ground
- A few leaves falling from the tree

{character_must_include}
{area_count} colourable areas. {name} should be the largest figure.
"""
        },
        
        2: {
            "title": "The Fairy Village",
            "stories": {
                "under_3": "{name} goes inside! Tiny houses everywhere! So many fairies!",
                "age_3": "{name} steps through the door. Wow! Little mushroom houses everywhere! Fairies are flying all around!",
                "age_4": "{name} goes through the magic door and gasps! It's a tiny village with mushroom houses! Fairies fly everywhere carrying flowers.",
                "age_5": "{name} steps through the doorway into a magical village. Mushroom houses have tiny windows and doors. Fairies tend glowing flowers. One named Sparkle waves hello!",
                "age_6": "{name} steps through the doorway and gasps! It's a tiny village of mushroom houses. Fairies fly everywhere, tending glowing flowers and carrying dewdrops. A fairy named Sparkle floats up to greet them.",
                "age_7": "Through the doorway, {name} enters a world of wonder. Mushroom houses cluster around a village square, their spotted caps serving as roofs. Fairies bustle about - some tend luminous flowers, others carry dewdrops in acorn cups. A fairy with particularly bright wings approaches. \"I'm Sparkle, the village greeter! Welcome to our home!\"",
                "age_8": "{name} emerges into a breathtaking fairy village. Mushroom houses of every color line cobblestone paths. Tiny lanterns hang from flower stems. Fairies go about their daily tasks - watering plants with dewdrops, painting butterfly wings, polishing moonbeams. A confident fairy with shimmering wings flies forward. \"I'm Sparkle! We don't get many visitors. What brings you to our enchanted home?\"",
                "age_9": "The fairy village takes {name}'s breath away. Mushroom houses spiral up toward the canopy, connected by bridges woven from flower stems. A crystalline stream winds through the center, crossed by tiny arched bridges. Fairies of all sizes bustle about - artists painting sunset colors, bakers pulling star-shaped cookies from acorn ovens, musicians playing instruments made from seeds and shells. A fairy with wings like stained glass approaches. \"I'm Sparkle, Head of Welcomings. In all my centuries, we've never had a human visitor. This is momentous!\"",
                "age_10": "{name} stands speechless at the threshold of impossible beauty. The fairy village sprawls before them like a living dream - mushroom houses with smoke curling from acorn chimneys, streets paved with polished pebbles, fountains spouting liquid starlight. Every detail rewards attention: fairies teaching young ones to fly, elders reading from flower-petal books, craftsmen weaving moonlight into fabric. The village hums with purpose and joy. A fairy whose wings shift through every color of the rainbow descends gracefully. \"I am Sparkle, Keeper of First Impressions. In the five hundred years since the last human crossed our threshold, we had begun to wonder if the magic still worked. And yet here you stand. The village has much to show you - but first, I sense you've arrived just when we need you most.\""
            },
            "scene": """
SCENE: {name} arrives in the fairy village

DRAW:
- {name} {character_pose} standing amazed, hands on cheeks in wonder
- Multiple cute mushroom houses with round doors and windows
- Several small fairies flying around doing tasks
- Glowing flowers in a garden
- A friendly fairy (Sparkle) hovering in front of {name}, waving
- Tiny lanterns hanging from mushroom stems
- A small winding path through the village

{character_must_include}
{area_count} colourable areas. Magical fairy village atmosphere.
"""
        },
        
        3: {
            "title": "The Missing Rainbow",
            "stories": {
                "under_3": "Oh no! Something is missing! The fairy looks sad. {name} wants to help!",
                "age_3": "Sparkle looks worried. \"Our magic crystal is gone!\" The flowers look droopy. {name} wants to help find it!",
                "age_4": "\"Oh no!\" cries Sparkle. \"Our Rainbow Crystal is missing! Without it, our flowers won't glow.\" {name} decides to help find it.",
                "age_5": "\"Princess, you came just in time!\" says Sparkle sadly. \"Our Rainbow Crystal is gone! Without it, our magic is fading.\" {name} promises to help find it.",
                "age_6": "\"Oh, you came just in time!\" cries Sparkle. \"The Rainbow Crystal is missing! Without it, our flowers won't glow and our magic will fade. Will you help us find it?\" {name} nods bravely.",
                "age_7": "Sparkle's expression turns worried. \"I must tell you why we're so excited you're here. Our Rainbow Crystal - the source of all our magic - has vanished!\" Around them, flowers are beginning to droop, their glow fading. \"Without it, our entire village will lose its magic. Please, will you help us?\"",
                "age_8": "Sparkle's wings droop as she leads {name} to the village square. Where a magnificent crystal should stand on a marble pedestal, there's only empty air. \"The Rainbow Crystal powered everything - our flower lights, our flying magic, even the warmth in our homes,\" Sparkle explains, voice trembling. \"Someone took it three days ago. We've searched everywhere. Will you be the hero we need?\"",
                "age_9": "The village square tells a sad story. A beautiful pedestal stands empty, surrounded by wilting flowers that once glowed like captured rainbows. Fairies huddle in worried groups, some comforting crying children whose wings have lost their shimmer. \"The Rainbow Crystal,\" Sparkle explains, her voice heavy with sorrow, \"was a gift from the First Stars. It's been the heart of our village for a thousand years. Three nights ago, it vanished. Our magic is fading - soon we won't even be able to fly.\" She looks at {name} with desperate hope. \"The ancient prophecies spoke of an outsider who would come in our darkest hour. Please... will you help us?\"",
                "age_10": "The heart of the fairy village is breaking. {name} stands before what was once clearly a place of joy - the central square now feels hollow, its magic draining away like water through sand. The Rainbow Crystal's pedestal, an intricate work of carved moonstone, stands empty. Around it, the evidence of decline is everywhere: flowers dimming, fountains slowing, even the fairies' wings beating slower, their colors fading to pale shadows of their former brilliance. Elder fairies weep openly while younger ones try to understand why their world is dying. Sparkle approaches {name} with tears in her eyes. \"For a thousand generations, the Rainbow Crystal has been our soul - the gift of the ancient ones, the promise that magic would never leave us. Three nights ago, I came to perform the morning blessing... and it was gone. We've searched every leaf, every shadow. Nothing.\" She clasps {name}'s hands. \"The trees whisper of you. They say you're the one who can restore what we've lost. I don't know why fate brought you here, but please - our entire existence depends on finding that crystal. Will you help us?\""
            },
            "scene": """
SCENE: Sparkle tells {name} about the missing Rainbow Crystal

DRAW:
- {name} {character_pose} looking determined and brave
- Sparkle the fairy looking worried, hands clasped together
- A pedestal in the center of the village, EMPTY where the crystal should be
- Wilting flowers around the pedestal showing the magic fading
- 2-3 sad fairies in the background
- The mushroom houses looking slightly dim
- Sparkles fading in the air

{character_must_include}
{area_count} colourable areas. Show the sadness but also {name}'s determination.
"""
        },
        
        4: {
            "title": "Following the Clues",
            "stories": {
                "under_3": "{name} looks for clues. There are sparkly footprints! Let's follow them!",
                "age_3": "Sparkle gives {name} a magic looking glass. \"Look! Glowing footprints!\" They lead to the forest!",
                "age_4": "{name} gets a magical magnifying glass. Through it, glowing footprints appear! They lead toward the Dark Hollow.",
                "age_5": "Sparkle gives {name} a magical magnifying glass. \"This will help you see fairy clues!\" Through the glass, {name} spots glowing footprints leading toward the Dark Hollow.",
                "age_6": "Sparkle gives {name} a magical magnifying glass. \"This will help you see fairy clues!\" Through the glass, {name} spots glowing footprints leading toward the Dark Hollow. Taking a deep breath, {name} follows them.",
                "age_7": "\"Take this,\" Sparkle says, handing over an ornate magnifying glass that shimmers with magic. \"It reveals what's hidden to normal eyes.\" {name} peers through it and gasps - glowing footprints appear on the ground, leading away from the pedestal. They're small, not fairy-sized, and head toward a dark path marked 'Dark Hollow.' {name} squares their shoulders and follows the trail.",
                "age_8": "Sparkle produces an ancient magnifying glass from her satchel, its frame carved from enchanted wood. \"This is the Revealer - it shows truth hidden from ordinary sight.\" When {name} looks through it, the world transforms. Glowing footprints materialize, weaving between houses and heading toward the forest's edge. They're accompanied by drag marks - something heavy was taken. A signpost at the trail's start reads 'Dark Hollow - Enter with Courage.' {name} takes the first step.",
                "age_9": "From a velvet pouch, Sparkle withdraws the Lens of Truth, an heirloom of the fairy elders. \"Few have used this,\" she whispers. \"It shows things as they truly are - even things that wish to remain hidden.\" The moment {name} raises it to their eye, the world blooms with secrets. Glowing footprints appear - but they're strange, almost hesitant, circling the pedestal several times before finally approaching. Beside them, teardrops shimmer on the ground, as if whoever took the crystal was crying. The trail leads to a path overgrown with shadows, marked by a weathered sign: 'Dark Hollow - Where Lost Things Hide.' Something about those teardrops makes {name} more curious than afraid.",
                "age_10": "Sparkle reaches into her ceremonial robes and withdraws something wrapped in silk - the Lens of Truth, created by the first fairies from a dragon's tear and a piece of frozen moonlight. \"This has not been used in three hundred years,\" she says solemnly. \"It shows not just what is hidden, but why it hides.\" {name} raises the lens, and reality peels back like layers of paint. The footprints that appear are fascinating - they start confident, then become hesitant, pacing back and forth near the pedestal. The moment of taking shows struggle - not greed, but desperation. Most striking are the tears that glitter like tiny diamonds along the trail, each one containing a flash of emotion: loneliness, fear, longing. The footprints lead to the Dark Hollow, but {name} no longer sees a thief's trail - they see someone hurting, someone who made a terrible choice for reasons that might break your heart. \"I'll find them,\" {name} says quietly, \"but maybe they need help more than punishment.\""
            },
            "scene": """
SCENE: {name} follows the magical clues

DRAW:
- {name} {character_pose} holding a large ornate magnifying glass, looking through it
- Glowing footprints on the ground leading into the distance
- Sparkle flying beside {name}, pointing the way
- The path leading toward darker trees in the background
- Flowers along the path
- A signpost pointing to "Dark Hollow"
- Butterflies flying nearby for encouragement

{character_must_include}
{area_count} colourable areas. {name} looks brave and curious.
"""
        },
        
        5: {
            "title": "The Dark Hollow",
            "stories": {
                "under_3": "{name} finds a little dragon. The dragon is crying! \"I just wanted a friend,\" he says.",
                "age_3": "In the Dark Hollow, {name} finds a small dragon crying. \"I'm sorry I took it,\" he sniffles. \"I was lonely.\"",
                "age_4": "{name} finds a sad little dragon with the crystal. \"I didn't mean to be bad,\" he cries. \"I just wanted something pretty because I have no friends.\"",
                "age_5": "In the Dark Hollow, {name} finds a small dragon crying next to the Rainbow Crystal. \"I didn't mean to take it,\" he sniffles. \"I just wanted something pretty because I'm so lonely.\"",
                "age_6": "{name} reaches the Dark Hollow. It's shadowy but not scary - just full of sleeping fireflies! In the middle sits a small dragon, crying. \"I didn't mean to take it,\" he sniffles. \"I just wanted something pretty because I have no friends.\"",
                "age_7": "The Dark Hollow isn't as scary as its name suggests - it's actually quite peaceful, filled with softly glowing fireflies. In a small clearing sits a young dragon, no bigger than a large dog, his scales a gentle green. Beside him rests the Rainbow Crystal, but he's not admiring it - he's crying. \"I didn't want to steal,\" he sobs when he sees {name}. \"I just... I've been alone so long. The crystal glowed so beautifully. I thought maybe... maybe it could be my friend.\"",
                "age_8": "Fireflies light the way as {name} enters the Dark Hollow, their gentle glow dispelling any fear. In a mossy clearing sits the culprit - not a fearsome thief, but a young dragon barely larger than a golden retriever. His wings are folded sadly, and tears stream down his scaled cheeks as he clutches the Rainbow Crystal. \"Please don't be angry,\" he whispers when he sees {name}. \"I know what I did was wrong. I've watched the fairies from afar for so long - their laughter, their friendship. I've never had anyone. When I saw the crystal glowing, I thought... maybe something that beautiful could fill the empty space inside me. But it didn't work. The only thing I feel now is shame.\"",
                "age_9": "The Dark Hollow opens into a clearing carpeted with soft moss and illuminated by thousands of sleeping fireflies. And there, curled around the Rainbow Crystal like a child with a teddy bear, is the last thing {name} expected - a young dragon, perhaps only a few years old in dragon terms. His scales are a soft sage green, his eyes red from crying. When he sees {name}, he doesn't run or threaten - he simply looks up with overwhelming sadness. \"I knew someone would come,\" he says, voice barely a whisper. \"I've been waiting to be punished. I deserve it.\" He pushes the crystal toward {name}. \"I'm Flicker. I've lived in this hollow my whole life, watching everyone else have families, have friends. I just wanted... something. Something that wasn't lonely. But the crystal can't love you back.\" Fresh tears fall. \"I'm sorry. I'm so sorry.\"",
                "age_10": "The Dark Hollow reveals itself not as a place of fear, but of exile - a quiet corner of the forest where unwanted things come to rest. Fireflies sleep in the branches above, their gentle light creating a melancholy beauty. And at the center of this forgotten place, {name} finds the crystal thief: a young dragon named Flicker, curled around the Rainbow Crystal with the desperate grip of someone holding onto their last hope. He's small for a dragon, his scales the pale green of new leaves, his wings too big for his body. The crystal illuminates the hollow but not his eyes - those remain dim with despair. When he notices {name}, he doesn't startle. Instead, a sad acceptance crosses his face. \"So the fairies sent someone,\" he says quietly. \"I understand. I'll come peacefully.\" He carefully sets the crystal aside. \"I want you to know - I never meant to hurt anyone. My mother left when I was just an egg. My father... I never knew him. I've spent my whole life watching the fairy village from afar, seeing families laugh together, friends play together, and I wanted... I just wanted so badly to matter to someone. When I saw the crystal - so warm, so beautiful - I thought maybe it could fill this hole inside me.\" He laughs bitterly. \"It didn't. Nothing can. I've just made things worse, like always.\" He looks at {name} with eyes that have forgotten how to hope. \"Whatever punishment the fairies choose, I accept it. But please... could you maybe stay? Just for a minute? It's been so long since anyone talked to me who wasn't a tree.\""
            },
            "scene": """
SCENE: {name} finds the sad little dragon

DRAW:
- {name} {character_pose} looking kind and sympathetic
- A small cute dragon sitting on a rock, tears in his eyes, the Rainbow Crystal beside him
- The Dark Hollow with twisted but gentle trees
- Sleeping fireflies dotted around like little lights
- Soft moss on the ground
- The dragon's small wings drooped sadly

{character_must_include}
{area_count} colourable areas. The dragon should look sad but cute, not scary.
""",
            "is_choice_point": True,
            "choice_prompt": "What should {name} do?",
            "choices": {
                "A": {
                    "label": "Invite the dragon to be their friend",
                    "short_label": "Friendship First",
                    "icon": "💕",
                    "theme": "Compassion and acceptance"
                },
                "B": {
                    "label": "Ask the dragon to return the crystal first", 
                    "short_label": "Responsibility First",
                    "icon": "💎",
                    "theme": "Doing the right thing"
                }
            }
        },
        
        # Episodes 6-10 continue with branching paths...
        # (6A, 6B, 7A, 7B, 8, 9AA, 9AB, 9BA, 9BB, 10)
    },
    
    # Branching episodes stored separately
    "branch_episodes": {
        "6A": {
            "title": "A New Friend",
            "stories": {
                "age_6": "\"I'll be your friend!\" says {name} warmly. The little dragon's eyes light up. \"Really? My name is Flicker!\" He hugs the crystal. \"I'm sorry I took this. Friends share, don't they? Let's return it together!\""
            },
            "scene": """
SCENE: {name} befriends Flicker the dragon

DRAW:
- {name} {character_pose} hugging or reaching out to Flicker
- Flicker the small dragon looking overjoyed, big smile, happy tears
- The Rainbow Crystal glowing brightly between them
- Hearts floating in the air around them
- The Dark Hollow looking brighter now
- Fireflies starting to wake up and glow
- Flowers blooming nearby

{character_must_include}
{area_count} colourable areas. Joyful friendship moment!
"""
        },
        
        "6B": {
            "title": "The Right Thing",
            "stories": {
                "age_6": "\"The fairies need their crystal back,\" {name} says gently. \"But I understand being lonely. What if you return it, and THEN we can all be friends?\" Flicker thinks, then nods. \"You're right. That's the fair thing to do.\""
            },
            "scene": """
SCENE: Flicker agrees to do the right thing

DRAW:
- {name} {character_pose} kneeling down, talking kindly to Flicker
- Flicker the dragon holding out the Rainbow Crystal, looking thoughtful but hopeful
- A gentle glow around the crystal
- The Dark Hollow trees seeming less dark
- Fireflies floating around
- A small smile forming on Flicker's face

{character_must_include}
{area_count} colourable areas. A gentle, understanding moment.
"""
        },
        
        "7A": {
            "title": "The Journey Back",
            "stories": {
                "age_6": "{name} and Flicker walk back together, chatting and laughing. Flicker shows how he can make tiny flames in fun shapes - stars, hearts, and flowers! \"The fairies will love your tricks!\" {name} giggles."
            },
            "scene": """
SCENE: {name} and Flicker journey back together as friends

DRAW:
- {name} {character_pose} walking and laughing
- Flicker the dragon walking beside them, breathing small flame shapes (stars, hearts)
- The forest path looking cheerful and bright
- Small animals (bunny, squirrel) watching them curiously
- Flowers along the path
- The Rainbow Crystal being carried carefully by Flicker
- Birds flying overhead

{character_must_include}
{area_count} colourable areas. Happy adventure companions!
"""
        },
        
        "7B": {
            "title": "The Brave Return",
            "stories": {
                "age_6": "Flicker is nervous as they walk back. \"What if the fairies are angry?\" {name} holds his tiny paw. \"I'll be right beside you. Saying sorry is brave, and I think they'll understand.\" Flicker stands a little taller."
            },
            "scene": """
SCENE: {name} supports Flicker on their walk back

DRAW:
- {name} {character_pose} holding Flicker's paw supportively
- Flicker the dragon looking nervous but determined, carrying the Rainbow Crystal
- The path from Dark Hollow toward the fairy village
- Gentle sunbeams breaking through the trees
- A butterfly landing on Flicker, flowers turning toward them
- The fairy village visible in the distance

{character_must_include}
{area_count} colourable areas. Supportive, encouraging atmosphere.
"""
        },
        
        8: {
            "title": "Return to the Village",
            "stories": {
                "A": {
                    "age_6": "They arrive at the fairy village. The fairies gasp when they see Flicker - then Sparkle flies forward. \"You brought back our crystal! And... you brought a dragon friend?\" She looks at {name} questioningly."
                },
                "B": {
                    "age_6": "They arrive at the fairy village. Flicker steps forward bravely. \"I'm sorry I took your crystal. I was lonely, but that wasn't right.\" The fairies look surprised. Sparkle flies forward slowly."
                }
            },
            "scene": """
SCENE: {name} and Flicker arrive at the fairy village

DRAW:
- {name} {character_pose} presenting Flicker to the fairies
- Flicker the dragon holding out the Rainbow Crystal, looking hopeful
- Sparkle the fairy flying toward them, curious expression
- Several other fairies watching with mixed expressions (surprised, curious)
- The empty crystal pedestal in the background
- The fairy village mushroom houses
- Anticipation in the scene

{character_must_include}
{area_count} colourable areas. A moment of hopeful tension.
""",
            "is_choice_point": True,
            "choice_prompt": "How should the fairies respond?",
            "choices": {
                "A": {
                    "label": "The fairies welcome Flicker with open arms",
                    "short_label": "Immediate Welcome",
                    "icon": "🤗",
                    "theme": "Open-hearted acceptance"
                },
                "B": {
                    "label": "The fairies are unsure and need convincing",
                    "short_label": "Earning Trust",
                    "icon": "🤔",
                    "theme": "Trust must be earned"
                }
            }
        },
        
        "9AA": {
            "title": "Welcome to the Family",
            "stories": {
                "age_6": "\"Any friend of {name} is a friend of ours!\" cheers Sparkle. The fairies swarm around Flicker with hugs and introductions. \"Can you really breathe fire shapes?\" they ask excitedly. Flicker beams with happiness."
            },
            "scene": """
SCENE: The fairies welcome Flicker joyfully

DRAW:
- {name} {character_pose} clapping happily
- Flicker the dragon surrounded by happy fairies hugging him
- Sparkle the fairy shaking Flicker's paw
- The Rainbow Crystal back on its pedestal, glowing brightly
- Flowers blooming again around the village
- Other fairies throwing flower petals in celebration
- Everyone smiling and joyful

{character_must_include}
{area_count} colourable areas. Pure celebration and joy!
"""
        },
        
        "9AB": {
            "title": "Proving Friendship",
            "stories": {
                "age_6": "Some fairies look worried. \"But he took our crystal...\" {name} speaks up: \"Flicker made a mistake, but he brought it back. And he's been so kind on our journey. Everyone deserves a second chance.\" The fairies look at each other and slowly smile."
            },
            "scene": """
SCENE: {name} speaks up for Flicker

DRAW:
- {name} {character_pose} standing confidently, speaking to the fairies
- Flicker the dragon behind them, looking grateful
- Some fairies looking thoughtful, starting to smile
- Sparkle considering {name}'s words
- The Rainbow Crystal glowing gently
- The atmosphere shifting from uncertain to warm
- Small hearts appearing as the fairies start to accept Flicker

{character_must_include}
{area_count} colourable areas. {name} being brave and kind.
"""
        },
        
        "9BA": {
            "title": "Forgiveness Given",
            "stories": {
                "age_6": "Sparkle sees how sorry Flicker truly is. \"It takes courage to admit when we're wrong,\" she says softly. \"And everyone gets lonely sometimes. Welcome, Flicker. Would you like to stay with us?\" Flicker's happy tears fall as he nods."
            },
            "scene": """
SCENE: Sparkle forgives Flicker

DRAW:
- {name} {character_pose} smiling warmly, hand on heart
- Flicker the dragon with happy tears, being welcomed by Sparkle
- Sparkle the fairy touching Flicker's cheek kindly
- Other fairies coming forward to welcome him
- The Rainbow Crystal placed back on pedestal, starting to glow
- Flowers beginning to perk up
- A rainbow starting to form in the sky

{character_must_include}
{area_count} colourable areas. Touching forgiveness moment.
"""
        },
        
        "9BB": {
            "title": "Earning Trust",
            "stories": {
                "age_6": "\"Trust takes time,\" says Sparkle. \"But everyone deserves a chance to show who they really are.\" She looks at Flicker. \"Stay with us. Help tend the flowers. Let us get to know the real you.\" Flicker nods eagerly, determined to prove himself."
            },
            "scene": """
SCENE: Flicker is given a chance to earn trust

DRAW:
- {name} {character_pose} looking encouraging
- Flicker the dragon being given a small watering can by Sparkle
- Sparkle explaining how to care for the magical flowers
- Some fairies watching curiously, starting to warm up
- The Rainbow Crystal back on its pedestal
- A small plot of flowers for Flicker to tend
- Hope in the scene

{character_must_include}
{area_count} colourable areas. New beginnings atmosphere.
"""
        },
        
        10: {
            "title": "The Rainbow Celebration",
            "stories": {
                "base": "That evening, the fairies throw a grand Rainbow Celebration! The crystal makes all the flowers glow in beautiful colors. {name} dances with new friends - fairies AND Flicker - under a sky full of magical rainbows.",
                "endings": {
                    "AA": " \"Thank you for showing me that friendship can be found in unexpected places,\" Flicker whispers to {name}. \"And thank you for being so welcoming,\" {name} tells the fairies. It's the best adventure ending ever!",
                    "AB": " \"You stood up for me,\" Flicker says to {name} gratefully. \"That's what friends do,\" {name} smiles. The fairies have learned that giving second chances creates the most magical friendships of all.",
                    "BA": " \"I'm glad I did the right thing,\" Flicker tells {name}. \"And I'm proud of you,\" {name} replies. Sparkle adds, \"Forgiveness and honesty make the strongest magic!\" Everyone cheers.",
                    "BB": " Flicker has worked hard tending the gardens, and now the fairies truly trust him. \"You've earned your place here,\" Sparkle announces. \"Some friendships are worth waiting for,\" {name} smiles. Flicker has never been happier."
                }
            },
            "scene": """
SCENE: The grand Rainbow Celebration!

DRAW:
- {name} {character_pose} dancing joyfully in the center
- Flicker the dragon dancing too, breathing pretty flame shapes into the air
- Multiple fairies dancing and flying around, throwing flower petals
- The Rainbow Crystal on its pedestal glowing brilliantly
- Magical rainbows arching across the sky
- All the flowers glowing in different colors
- Lanterns and streamers decorating the fairy village
- Pure joy and celebration everywhere
- Stars twinkling in the evening sky

{character_must_include}
{area_count} colourable areas. Maximum celebration! The happiest ending!
"""
        }
    }
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_age_rules(age_level: str) -> dict:
    """Get the age rules for a specific age level."""
    return AGE_RULES.get(age_level, AGE_RULES["age_6"])


def get_story_for_age(episode_stories: dict, age_level: str) -> str:
    """Get the appropriate story text for the given age level."""
    # Try exact match first
    if age_level in episode_stories:
        return episode_stories[age_level]
    
    # Fall back to closest age
    age_order = ["under_3", "age_3", "age_4", "age_5", "age_6", "age_7", "age_8", "age_9", "age_10"]
    
    try:
        target_idx = age_order.index(age_level)
    except ValueError:
        return episode_stories.get("age_6", list(episode_stories.values())[0])
    
    # Try lower ages first, then higher
    for offset in range(len(age_order)):
        for direction in [-1, 1]:
            check_idx = target_idx + (offset * direction)
            if 0 <= check_idx < len(age_order):
                check_age = age_order[check_idx]
                if check_age in episode_stories:
                    return episode_stories[check_age]
    
    # Last resort
    return list(episode_stories.values())[0]


def get_episode_data(theme: str, episode_num: int, choice_path: str = "") -> dict:
    """
    Get episode data for a specific episode number and choice path.
    
    Args:
        theme: Adventure theme key (e.g., "forest")
        episode_num: Episode number (1-10)
        choice_path: For branching episodes, the path taken (e.g., "A", "AA", "AB")
    
    Returns:
        Episode data dictionary
    """
    if theme == "forest":
        adventure = FOREST_ADVENTURE
    else:
        # TODO: Add other adventures
        adventure = FOREST_ADVENTURE
    
    # Direct episodes (1-5)
    if episode_num <= 5:
        return adventure["episodes"].get(episode_num, {})
    
    # Branching episodes (6-10)
    branch_key = None
    
    if episode_num == 6:
        branch_key = f"6{choice_path[0]}" if choice_path else "6A"
    elif episode_num == 7:
        branch_key = f"7{choice_path[0]}" if choice_path else "7A"
    elif episode_num == 8:
        return adventure["branch_episodes"].get(8, {})
    elif episode_num == 9:
        branch_key = f"9{choice_path}" if len(choice_path) >= 2 else "9AA"
    elif episode_num == 10:
        return adventure["branch_episodes"].get(10, {})
    
    return adventure["branch_episodes"].get(branch_key, {})


def format_scene_prompt(
    scene_template: str,
    character_name: str,
    character_description: str,
    character_pose: str,
    character_must_include: str,
    key_feature: str,
    age_level: str
) -> str:
    """Format a scene prompt with character and age-specific details."""
    
    age_rules = get_age_rules(age_level)
    master_prompt = MASTER_COLORING_PROMPT.format(age_rules=age_rules["rules"])
    
    return EPISODE_SCENE_PROMPT.format(
        master_prompt=master_prompt,
        character_name=character_name,
        character_description=character_description,
        key_feature=key_feature,
        episode_title="",  # Will be set by caller
        scene_description=scene_template.format(
            name=character_name,
            character_pose=character_pose,
            character_must_include=character_must_include,
            area_count=age_rules["colourable_areas"]
        )
    )


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "AGE_RULES",
    "MASTER_COLORING_PROMPT", 
    "CHARACTER_REFERENCE_PROMPT",
    "EPISODE_SCENE_PROMPT",
    "ADVENTURE_THEMES",
    "FOREST_ADVENTURE",
    "get_age_rules",
    "get_story_for_age",
    "get_episode_data",
    "format_scene_prompt"
]
