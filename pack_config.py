# pack_config.py
# Pack definitions using the actual theme keys from themes.json.
# These keys get passed to build_text_to_image_prompt() which looks them
# up in themes.json to build the proper age-adjusted prompt.
#
# "subjects" = list of theme keys (what the backend generates)
# "display_names" = list of human-readable names (what ConfirmPack shows)

PACK_CATALOG = {

    "farm_animals": {
        "name": "Farm Animals",
        "description": "All your favourite farmyard friends",
        "category": "animals",
        "cover_emoji": "🐄",
        "subjects": [
            "animal_cow", "animal_pig", "animal_horse", "animal_sheep",
            "animal_chicken", "animal_rooster", "animal_duck", "animal_goat",
            "animal_donkey", "animal_rabbit",
        ],
        "display_names": [
            "Cow", "Pig", "Horse", "Sheep", "Chicken",
            "Rooster", "Duck", "Goat", "Donkey", "Rabbit",
        ],
    },

    "zoo_animals": {
        "name": "Zoo Animals",
        "description": "Explore the zoo from page to page",
        "category": "animals",
        "cover_emoji": "🦁",
        "subjects": [
            "animal_lion", "animal_tiger", "animal_elephant", "animal_giraffe",
            "animal_zebra", "animal_monkey", "animal_gorilla", "animal_hippo",
            "animal_rhino", "animal_panda", "animal_koala", "animal_kangaroo",
            "animal_penguin", "animal_polar_bear", "animal_snake", "animal_crocodile",
            "animal_bear", "animal_wolf", "animal_fox", "animal_deer",
        ],
        "display_names": [
            "Lion", "Tiger", "Elephant", "Giraffe", "Zebra",
            "Monkey", "Gorilla", "Hippo", "Rhino", "Panda",
            "Koala", "Kangaroo", "Penguin", "Polar Bear", "Snake",
            "Crocodile", "Bear", "Wolf", "Fox", "Deer",
        ],
    },

    "sea_animals": {
        "name": "Sea Animals",
        "description": "Dive into the deep blue sea",
        "category": "animals",
        "cover_emoji": "🐙",
        "subjects": [
            "animal_dolphin", "animal_whale", "animal_shark", "animal_octopus",
            "animal_jellyfish", "animal_seahorse", "animal_turtle", "animal_crab",
            "animal_starfish", "animal_clownfish", "animal_lobster", "animal_seal",
            "animal_walrus", "animal_orca", "animal_stingray",
        ],
        "display_names": [
            "Dolphin", "Whale", "Shark", "Octopus", "Jellyfish",
            "Seahorse", "Turtle", "Crab", "Starfish", "Clownfish",
            "Lobster", "Seal", "Walrus", "Orca", "Stingray",
        ],
    },

    "insects": {
        "name": "Insects",
        "description": "Tiny creatures, big fun",
        "category": "animals",
        "cover_emoji": "🐛",
        "subjects": [
            "animal_butterfly", "animal_bee", "animal_ladybug", "animal_caterpillar",
            "animal_dragonfly", "animal_grasshopper", "animal_snail", "animal_spider",
            "animal_ant", "animal_firefly", "animal_beetle", "animal_worm",
        ],
        "display_names": [
            "Butterfly", "Bee", "Ladybug", "Caterpillar", "Dragonfly",
            "Grasshopper", "Snail", "Spider", "Ant", "Firefly",
            "Beetle", "Worm",
        ],
    },

    "dinosaurs": {
        "name": "Dinosaurs",
        "description": "Roar into prehistoric times",
        "category": "animals",
        "cover_emoji": "🦕",
        "subjects": [
            "animal_trex", "animal_triceratops", "animal_brachiosaurus",
            "animal_stegosaurus", "animal_pterodactyl", "animal_velociraptor",
            "animal_diplodocus", "animal_ankylosaurus", "animal_spinosaurus",
            "animal_parasaurolophus", "animal_apatosaurus", "animal_pachycephalosaurus",
        ],
        "display_names": [
            "T-Rex", "Triceratops", "Brachiosaurus", "Stegosaurus",
            "Pterodactyl", "Velociraptor", "Diplodocus", "Ankylosaurus",
            "Spinosaurus", "Parasaurolophus", "Apatosaurus", "Pachycephalosaurus",
        ],
    },

    "fruits": {
        "name": "Fruits",
        "description": "A juicy collection to colour",
        "category": "nature",
        "cover_emoji": "🍎",
        "subjects": [
            "fruit_apple", "fruit_banana", "fruit_strawberry", "fruit_watermelon",
            "fruit_pineapple", "fruit_orange", "fruit_grapes", "fruit_cherry",
            "fruit_mango", "fruit_peach", "fruit_lemon", "fruit_kiwi",
            "fruit_coconut", "fruit_pear", "fruit_blueberry",
        ],
        "display_names": [
            "Apple", "Banana", "Strawberry", "Watermelon", "Pineapple",
            "Orange", "Grapes", "Cherry", "Mango", "Peach",
            "Lemon", "Kiwi", "Coconut", "Pear", "Blueberry",
        ],
    },

    "vegetables": {
        "name": "Vegetables",
        "description": "Learn your veggies while you colour",
        "category": "nature",
        "cover_emoji": "🥕",
        "subjects": [
            "veg_carrot", "veg_broccoli", "veg_tomato", "veg_corn",
            "veg_pumpkin", "veg_potato", "veg_onion", "veg_peas",
            "veg_pepper", "veg_mushroom", "veg_cucumber", "veg_lettuce",
            "veg_eggplant", "veg_celery", "veg_radish",
        ],
        "display_names": [
            "Carrot", "Broccoli", "Tomato", "Corn", "Pumpkin",
            "Potato", "Onion", "Peas", "Pepper", "Mushroom",
            "Cucumber", "Lettuce", "Aubergine", "Celery", "Radish",
        ],
    },

    "flowers": {
        "name": "Flowers",
        "description": "A beautiful garden to colour in",
        "category": "nature",
        "cover_emoji": "🌸",
        "subjects": [
            "flower_rose", "flower_sunflower", "flower_daisy", "flower_tulip",
            "flower_lily", "flower_orchid", "flower_poppy", "flower_lavender",
            "flower_daffodil", "flower_bluebell", "flower_pansy", "flower_violet",
            "flower_marigold", "flower_hibiscus", "flower_lotus",
        ],
        "display_names": [
            "Rose", "Sunflower", "Daisy", "Tulip", "Lily",
            "Orchid", "Poppy", "Lavender", "Daffodil", "Bluebell",
            "Pansy", "Violet", "Marigold", "Hibiscus", "Lotus",
        ],
    },


    "pet_animals": {
        "name": "Pet Animals",
        "description": "Your favourite furry and scaly friends",
        "category": "animals",
        "cover_emoji": "🐱",
        "subjects": [
            "animal_cat", "animal_dog", "animal_parrot", "animal_budgie",
            "animal_tarantula", "animal_mouse", "animal_rat", "animal_guinea_pig",
            "animal_hamster", "animal_tortoise", "animal_gecko",
        ],
        "display_names": [
            "Cat", "Dog", "Parrot", "Budgie", "Tarantula",
            "Mouse", "Rat", "Guinea Pig", "Hamster", "Tortoise", "Gecko",
        ],
    },

    "alphabet": {
        "name": "Alphabet",
        "description": "Learn your letters A to Z",
        "category": "educational",
        "cover_emoji": "🔤",
        "subjects": [
            "alphabet_a", "alphabet_b", "alphabet_c", "alphabet_d",
            "alphabet_e", "alphabet_f", "alphabet_g", "alphabet_h",
            "alphabet_i", "alphabet_j", "alphabet_k", "alphabet_l",
            "alphabet_m", "alphabet_n", "alphabet_o", "alphabet_p",
            "alphabet_q", "alphabet_r", "alphabet_s", "alphabet_t",
            "alphabet_u", "alphabet_v", "alphabet_w", "alphabet_x",
            "alphabet_y", "alphabet_z",
        ],
        "display_names": [
            "A", "B", "C", "D", "E", "F", "G", "H", "I",
            "J", "K", "L", "M", "N", "O", "P", "Q", "R",
            "S", "T", "U", "V", "W", "X", "Y", "Z",
        ],
    },

    "world_cities": {
        "name": "World Cities",
        "description": "Travel the world one page at a time",
        "category": "educational",
        "cover_emoji": "🌍",
        "subjects": [
            "city_london", "city_paris", "city_new_york", "city_rome",
            "city_tokyo", "city_sydney", "city_dubai", "city_barcelona",
            "city_amsterdam", "city_cairo", "city_rio", "city_los_angeles",
            "city_san_francisco", "city_venice", "city_athens",
        ],
        "display_names": [
            "London", "Paris", "New York", "Rome", "Tokyo",
            "Sydney", "Dubai", "Barcelona", "Amsterdam", "Cairo",
            "Rio de Janeiro", "Los Angeles", "San Francisco", "Venice", "Athens",
        ],
    },
}
