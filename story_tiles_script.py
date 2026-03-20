import google.generativeai as genai
import base64
import time
import os
from firebase_utils import upload_to_firebase

genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
model = genai.GenerativeModel('gemini-2.5-flash-image')

AGE_OVERLAY = """Age level: 5 years
- Medium-thick outlines
- Simple but recognisable figures
- Clothing: simple shapes, NO frills, NO layered skirts, NO intricate patterns
- Maximum 20-25 colourable areas
- MINIMAL background only - simple ground line, 1-2 simple clouds
- NO rainbow, NO detailed scenery, NO flowers, NO scattered stars
- Keep it simple and clean

CRITICAL: NO border, NO frame, NO rounded corners around the image. Drawing fills entire canvas edge to edge."""

# Front cover descriptions based on all 3 blurbs per theme
themes = [
    # FANTASY & MAGIC
    ("dragons_egg", "FRONT COVER SCENE: A large glowing cracked egg in the centre of a village square with sparkles coming out of the crack. A tiny baby dragon is peeking out of the top. Two children on either side looking amazed with hands over their mouths. Simple village houses in background."),
    
    ("wizards_apprentice", "FRONT COVER SCENE: A young wizard apprentice in a pointy hat standing in a chaotic magic school hallway. Spell books are flying through the air, a broom is sweeping by itself, frogs are hopping out of a doorway, and homework scrolls are zooming past like paper planes. The apprentice looks overwhelmed but excited."),
    
    ("unicorn_stable", "FRONT COVER SCENE: A magical stable with a unicorn whose horn has been replaced by a party hat, looking confused but happy. A child is holding the real horn in one hand and looking at it puzzled. Another unicorn behind them has glitter in its mane. Sparkles floating everywhere."),
    
    ("pixie_village", "FRONT COVER SCENE: A child shrunk to tiny size standing at the gate of a pixie village made of mushroom houses and acorn lanterns. Friendly pixies flying around them. A giant leaf overhead like an umbrella. A ladybird the same size as the child walking past."),
    
    ("enchanted_garden", "FRONT COVER SCENE: A magical garden at night with a child kneeling by a glowing fairy door at the base of a huge old tree. Flowers around them are glowing softly. A small trail of fairy footprints leads to the door. Fireflies floating in the air."),
    
    # NATURE & ANIMALS
    ("butterfly_ball", "FRONT COVER SCENE: A grand garden party scene with a child in the centre wearing a flower crown, arms outstretched, surrounded by dozens of large beautiful butterflies mid-dance. A small orchestra of crickets playing instruments on a mushroom stage. Bunting made of leaves."),
    
    ("whispering_woods", "FRONT COVER SCENE: A child standing at the entrance to a mysterious forest path. Trees have gentle faces in their bark, whispering to each other. A rabbit is beckoning the child forward. An owl watches from a branch. Soft light filtering through leaves."),
    
    ("ice_palace", "FRONT COVER SCENE: A magnificent ice palace with tall frozen towers. A child bundled in winter clothes standing at the ice door with a friendly penguin holding the door open. A polar bear cub sliding down an icy banister. Snowflakes gently falling."),
    
    ("blossom_festival", "FRONT COVER SCENE: A child running joyfully under cherry blossom trees with petals falling like pink snow. Paper lanterns hanging from branches. A koi pond with fish jumping. A friendly tanuki (raccoon dog) wearing a festival headband waving."),
    
    ("great_safari", "FRONT COVER SCENE: A child standing up in an open-top safari jeep with binoculars. A tall giraffe bending down to look at them face-to-face. An elephant spraying water from its trunk in the background. A lion cub sitting on the bonnet of the jeep."),
    
    # ADVENTURE & EXPLORATION
    ("pirate_cove", "FRONT COVER SCENE: A child dressed as a pirate standing on a beach holding up a treasure map triumphantly. A friendly parrot on their shoulder. Behind them a pirate ship with skull and crossbones flag. An X marks the spot in the sand with gold coins peeking out. Palm tree to the side."),
    
    ("lost_temple", "FRONT COVER SCENE: A child explorer with a torch and adventure hat standing at the grand entrance of an ancient stone temple covered in vines. Mysterious symbols carved into the stone archway. A friendly monkey sitting on top of the temple pointing inside. Jungle plants around."),
    
    ("big_top_mystery", "FRONT COVER SCENE: A circus big top tent at night with colourful flags on top. A child peeking through the tent curtain with wide eyes. Inside you can see a clown juggling, a seal balancing a ball, and a mysterious empty spotlight in the centre. Stars in the sky."),
    
    ("dusty_map", "FRONT COVER SCENE: A child sitting cross-legged on the floor of an attic, holding open a huge ancient map that's bigger than them. The map glows with a golden trail. A compass spins on the floor beside them. Dusty trunks and old adventure gear in the background."),
    
    ("sunken_ship", "FRONT COVER SCENE: An underwater scene viewed through a huge submarine porthole. A child pressing their face against the glass in wonder. Outside the porthole: a sunken pirate ship on the seabed, treasure chest with lid open, colourful fish swimming past, an octopus waving."),
    
    # REAL LIFE
    ("brave_rescue", "FRONT COVER SCENE: A child wearing an oversized firefighter helmet sitting in the driver seat of a big red fire truck, gripping the steering wheel. A dalmatian dog in the passenger seat wearing a tiny helmet. Fire station with open doors behind them. A cat stuck in a tree visible to the side."),
    
    ("midnight_hospital", "FRONT COVER SCENE: A child in a doctor's white coat with stethoscope around their neck, tiptoeing down a moonlit hospital corridor with a torch. Teddy bear patients peeking out from doorways. A friendly nurse owl at the reception desk. Moon visible through a window."),
    
    ("runaway_train", "FRONT COVER SCENE: A child conductor in a big hat pulling the whistle cord of a steam train. Steam billowing everywhere. The train is going fast along tracks through rolling countryside. Sheep in a field looking surprised. Passengers waving from windows."),
    
    ("first_day", "FRONT COVER SCENE: A small child with a huge backpack standing at tall school gates looking up at the school building. A friendly teacher waving from the doorway. Other children playing in the background. A butterfly landing on the child's backpack. Mix of nervous and excited expression."),
    
    ("trophy_trouble", "FRONT COVER SCENE: Sports day chaos — a child tangled in a finish line ribbon with arms up celebrating while trophies are tumbling off a table behind them. A dog has run onto the track carrying a relay baton. Bunting and flags everywhere. Other children laughing."),
    
    # SCI-FI
    ("star_chasers", "FRONT COVER SCENE: A child astronaut floating in space outside a rocket ship, reaching out to catch a bright shooting star that's zooming past. Colourful planets in the background — one with rings, one stripy. The rocket has a child's drawing of a smiley face painted on it."),
    
    ("dinosaur_door", "FRONT COVER SCENE: A child's bedroom with a magical glowing door standing in the middle of the room. The door is half open and through it you can see a prehistoric jungle world. A friendly baby T-Rex is poking its head through the door into the bedroom. Toys scattered on the bedroom floor."),
    
    ("robot_inventor", "FRONT COVER SCENE: A child in goggles tightening a bolt on the head of a friendly robot that's sitting on a workbench. The robot is smiling and giving a thumbs up as it comes to life. Gears, springs, nuts and bolts scattered on the bench. A lightbulb glowing above the robot's head."),
    
    ("friendly_aliens", "FRONT COVER SCENE: A park scene with a small colourful spaceship that has crash-landed on the grass. Three small friendly aliens with big eyes stepping out looking curious. A child offering one of them an ice cream. A dog sniffing another alien. People in the background pointing and smiling."),
    
    ("moon_base", "FRONT COVER SCENE: A child astronaut bouncing high in low gravity on the moon surface with a huge grin. A moon base with glass domes behind them. A moon buggy parked to the side. Earth glowing blue and green in the dark sky. Footprints in the moon dust. An alien peeking from behind a crater."),
    
    # MAKE BELIEVE
    ("candy_castle", "FRONT COVER SCENE: A child standing open-mouthed in front of a castle made entirely of sweets. The towers are candy canes, the walls are chocolate blocks, the door is a giant cookie. Lollipop trees line a path of jelly beans. Gingerbread guards stand at attention either side of the door. A gumdrop fountain in front."),
    
    ("cloud_kingdom", "FRONT COVER SCENE: A child walking across a rainbow bridge high in the sky toward a castle made of fluffy white clouds. Cloud people waving from windows. A cloud dog bouncing alongside the child. Birds flying around. The sun peeking over a cloud tower with a smiley face."),
    
    ("magic_paintbrush", "FRONT COVER SCENE: A child holding a glowing paintbrush, painting on a huge canvas. The things they've painted are coming alive and stepping out of the canvas — a butterfly flying off, a flower growing from the frame, a painted cat stretching as it becomes real. Paint splashes on the floor."),
    
    ("musical_forest", "FRONT COVER SCENE: A child standing on a tree stump conducting with a stick. The forest trees around them have musical instruments growing on their branches — trumpets blooming like flowers, drums as tree stumps, violin vines hanging down. Musical notes floating through the air. Woodland animals playing along."),
    
    ("toy_box", "FRONT COVER SCENE: The lid of a giant toy box flying open with golden light pouring out. A child climbing in or being pulled in by a friendly teddy bear. Toy soldiers marching out over the edge. A toy rocket launching upward. Building blocks stacking themselves. A jack-in-the-box springing up."),
    
    # EXTRA 10
    ("invisible_zoo", "FRONT COVER SCENE: A child at a zoo holding a magnifying glass, looking bewildered. The enclosures appear empty but there are clues everywhere — floating bananas being eaten by nothing, paw prints appearing in mud, water splashing from an empty pool, a zookeeper scratching their head."),
    
    ("upside_down_house", "FRONT COVER SCENE: A cross-section view of a house where everything is flipped. A child walking on the ceiling looking delighted. Furniture stuck to the ceiling above them — a chair, table with food not falling off. A cat hanging from a lamp. A goldfish bowl somehow still full of water upside down."),
    
    ("tiny_explorers", "FRONT COVER SCENE: A child shrunk to the size of an ant, standing on a leaf in a garden. A massive daisy towers above them like a tree. A ladybird next to them is the size of a car. A dewdrop on the leaf looks like a crystal ball. An ant carrying a crumb that's bigger than the child walks past."),
    
    ("dream_machine", "FRONT COVER SCENE: A child standing next to a fantastical machine covered in colourful buttons, dials, levers and pipes. The child has just pulled a big lever. Dream bubbles are floating out the top of the machine — inside each bubble is a different tiny world: one has a dinosaur, one has a spaceship, one has a mermaid."),
    
    ("weather_factory", "FRONT COVER SCENE: A child inside a factory in the sky standing at a huge control panel. They've accidentally pulled the wrong lever — snow is pouring from one pipe, rain from another, and sunshine from a third, all at the same time. A worried cloud worker running toward them. Rainbow accidentally forming."),
    
    ("midnight_bakery", "FRONT COVER SCENE: A child in pyjamas peeking through a bakery window at midnight. Inside, bread loaves are stretching and yawning as they come alive. A croissant is doing yoga. Cupcakes are having a party with tiny candles lit. A baguette is sword-fighting another baguette. The baker's hat is floating on its own."),
    
    ("paper_plane_race", "FRONT COVER SCENE: Children on a hilltop launching giant colourful paper planes into a bright sky. One child is riding ON their paper plane like a surfboard. The planes are soaring through cloud hoops. A bird is racing alongside looking competitive. Countryside below."),
    
    ("haunted_funfair", "FRONT COVER SCENE: A funfair at night with a spooky but silly atmosphere. A child laughing on a ghost train cart. Friendly ghosts operating the rides — one spinning the ferris wheel, one selling candy floss. Cobwebs as decoration. Jack-o-lanterns as lights. A vampire running a hook-a-duck stall."),
    
    ("time_travellers_watch", "FRONT COVER SCENE: A child holding up a glowing golden pocket watch. The scene is split in half — on the left is the modern world (houses, cars, lampposts) and on the right the same scene has transformed into a prehistoric world (jungle, volcano, friendly dinosaurs). The child stands right on the dividing line."),
    
    ("superhero_school", "FRONT COVER SCENE: A school classroom where everything is going crazy. One child is hovering above their desk wearing a cape. Another has accidentally turned invisible — just floating glasses and shoes visible. A third has super-strength and lifted the teacher's desk. The teacher is ducking. A chalkboard says 'Flying 101'."),
]

total = len(themes)
print(f"Generating {total} story theme tiles with Gemini...\n")

urls = {}

for i, (key, desc) in enumerate(themes, 1):
    print(f"[{i}/{total}] {key}...")
    try:
        prompt = f'''[STRICT CONTROLS]: Monochrome black and white 1-bit line art only.
[VISUAL DOMAIN]: Technical Vector Graphic / Die-cut sticker template.
[COLOR CONSTRAINTS]: Strictly binary 1-bit color palette. Output must contain #000000 (Black) and #FFFFFF (White) ONLY. Any other color or shade of grey is a FAILURE.

[STYLE]: Clean, bold, uniform-weight black outlines. Pure white empty interiors. Thick, heavy marker outlines. Bold 5pt vector strokes.

[MANDATORY EXCLUSIONS]: No gradients. No volume. No depth. No shadows. No grayscale. No shading. No color leaks. No 3D volume. Paper-white fills only. No grey fills on clothing. No solid black fills on clothing or hair.

Create a professional kids' COLORING BOOK PAGE — pure BLACK LINES on WHITE PAPER.

{desc}

🚫 ABSOLUTELY NO TEXT IN THE IMAGE 🚫
- Do NOT write ANY words, letters, names, labels, signs, or captions
- ONLY illustrations — black lines on white paper

{AGE_OVERLAY}'''

        response = model.generate_content([prompt])
        
        if response.parts:
            for part in response.parts:
                if hasattr(part, 'inline_data') and part.inline_data:
                    img_b64 = base64.b64encode(part.inline_data.data).decode('utf-8')
                    with open(f"story_tile_{key}.png", "wb") as f:
                        f.write(part.inline_data.data)
                    firebase_url = upload_to_firebase(img_b64, folder="story_tiles")
                    urls[key] = firebase_url
                    print(f"  ✓ URL: {firebase_url}")
                    break
            else:
                print(f"  ✗ No image in response")
        else:
            print(f"  ✗ Empty response")
    except Exception as e:
        print(f"  ✗ Exception: {e}")
    time.sleep(15)

print(f"\n{'='*80}")
print("ALL FIREBASE URLS:")
print(f"{'='*80}")
for key, url in urls.items():
    print(f"{key}: {url}")
print(f"\n🎉 Done! {len(urls)}/{total} generated successfully")
