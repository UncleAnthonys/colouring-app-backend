# pack_config.py
# Pack definitions — each pack is a curated list of subjects for a theme.
# Add/remove packs here. The subjects list is what gets passed to your
# existing colouring page generation function one at a time.

PACK_CATALOG = {

    # --- Animals ---
    "farm_animals": {
        "name": "Farm Animals",
        "description": "All your favourite farmyard friends",
        "category": "animals",
        "cover_emoji": "🐄",
        "subjects": [
            "a friendly cow standing in a meadow",
            "a cute pig rolling in mud",
            "a fluffy sheep on a grassy hill",
            "a proud rooster crowing on a fence",
            "a baby chick hatching from an egg",
            "a horse galloping in a field",
            "a playful goat jumping on rocks",
            "a duck swimming in a pond",
            "a donkey carrying baskets",
            "a fluffy rabbit eating a carrot",
        ],
    },

    "dinosaurs": {
        "name": "Dinosaurs",
        "description": "Roar into prehistoric times",
        "category": "animals",
        "cover_emoji": "🦕",
        "subjects": [
            "a friendly T-Rex with a big smile",
            "a long-necked Brachiosaurus eating leaves from a tree",
            "a Triceratops with three big horns",
            "a Stegosaurus with plates on its back",
            "a baby dinosaur hatching from a big egg",
            "a Pterodactyl flying through the sky",
            "an Ankylosaurus with a club tail",
            "a Velociraptor running fast",
            "a Diplodocus with a very long tail",
            "a Parasaurolophus with a crest on its head",
        ],
    },

    "ocean_creatures": {
        "name": "Ocean Creatures",
        "description": "Dive into the deep blue sea",
        "category": "animals",
        "cover_emoji": "🐙",
        "subjects": [
            "a smiling dolphin jumping out of the water",
            "a friendly octopus waving its tentacles",
            "a big whale spouting water",
            "a colourful clownfish hiding in coral",
            "a sea turtle swimming through the ocean",
            "a starfish on a sandy seabed",
            "a seahorse floating in seaweed",
            "a happy crab on the beach",
            "a jellyfish glowing underwater",
            "a playful seal balancing a ball",
        ],
    },

    "safari_animals": {
        "name": "Safari Animals",
        "description": "An African adventure on every page",
        "category": "animals",
        "cover_emoji": "🦁",
        "subjects": [
            "a lion with a big fluffy mane",
            "a tall giraffe eating from a tree",
            "a large elephant spraying water with its trunk",
            "a zebra with bold black and white stripes",
            "a hippo wallowing in a river",
            "a cheeky monkey swinging from a vine",
            "a rhinoceros with a big horn",
            "a flamingo standing on one leg",
            "a cheetah running very fast",
            "a friendly gorilla sitting in the jungle",
        ],
    },

    "minibeasts": {
        "name": "Minibeasts",
        "description": "Tiny creatures, big fun",
        "category": "animals",
        "cover_emoji": "🐛",
        "subjects": [
            "a ladybird with spots on its back",
            "a caterpillar crawling on a leaf",
            "a butterfly with big patterned wings",
            "a busy bee collecting pollen from a flower",
            "a snail with a spiral shell",
            "a spider spinning a web",
            "a dragonfly hovering over a pond",
            "an ant carrying a crumb",
        ],
    },

    # --- Vehicles ---
    "vehicles": {
        "name": "Things That Go",
        "description": "Cars, trucks, planes and more",
        "category": "vehicles",
        "cover_emoji": "🚗",
        "subjects": [
            "a big red fire engine with a ladder",
            "a yellow digger on a building site",
            "a police car with flashing lights",
            "an ambulance racing to help",
            "a double decker bus on a city street",
            "a steam train on railway tracks",
            "a big aeroplane flying in the sky",
            "a rocket blasting off into space",
            "a sailing boat on the ocean",
            "a tractor ploughing a farm field",
        ],
    },

    # --- Space ---
    "space": {
        "name": "Outer Space",
        "description": "Blast off to the stars",
        "category": "space",
        "cover_emoji": "🚀",
        "subjects": [
            "an astronaut floating in space",
            "a rocket ship blasting off",
            "the planet Saturn with its rings",
            "a friendly alien waving hello",
            "the moon with craters on its surface",
            "a space station orbiting Earth",
            "a shooting star streaking across the sky",
            "the sun with rays shining outward",
            "a UFO flying saucer in the sky",
            "a robot exploring the surface of Mars",
        ],
    },

    # --- Fairy Tales ---
    "fairy_tales": {
        "name": "Fairy Tales",
        "description": "Once upon a time...",
        "category": "fantasy",
        "cover_emoji": "🏰",
        "subjects": [
            "a princess in a beautiful castle",
            "a knight riding a horse with a shield",
            "a friendly dragon breathing a small flame",
            "a magical unicorn in an enchanted forest",
            "a fairy with sparkly wings",
            "a wizard with a long beard and a pointy hat",
            "a mermaid sitting on a rock in the sea",
            "a pirate ship sailing on the ocean",
            "a treasure chest full of gold coins and jewels",
            "an enchanted tree house in a magical forest",
        ],
    },
}
